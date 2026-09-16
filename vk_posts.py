"""Автопостинг в VK сообщество: текст от LLM + картинка PIL."""
import os, json, time, logging, random, requests
from io import BytesIO
from datetime import datetime
from dotenv import load_dotenv
from PIL import Image, ImageDraw, ImageFont

load_dotenv()
VK_POST_TOKEN = os.getenv("VK_POST_TOKEN", "")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "")
logger = logging.getLogger(__name__)

TOPICS = ["weather_fact", "travel", "humor", "tip"]
TOPIC_PROMPTS = {
    "weather_fact": "Короткий интересный факт о погоде, климате или атмосферных явлениях (2-3 предложения, живо, с эмодзи, на русском).",
    "travel": "Совет путешественнику про погоду, одежду или лучшее время для поездки в интересный регион (2-3 предложения, живо, с эмодзи, на русском).",
    "humor": "Забавная шутка или каламбур про погоду, дождь, солнце или зиму (1-2 предложения, с юмором, с эмодзи, на русском).",
    "tip": "Практический совет на сегодня по погоде (что взять, как одеться, куда не стоит идти) (2 предложения, с эмодзи, на русском).",
}
TOPIC_LABELS = {
    "weather_fact": "Факт о погоде",
    "travel": "Путешествия",
    "humor": "Юмор",
    "tip": "Совет дня",
}

FALLBACK_TEXTS = {
    "weather_fact": [
        "Знаете ли вы, что молния нагревает воздух вокруг себя до 30 000 C - это в 5 раз горячее поверхности Солнца?",
        "Одно облако среднего размера весит около 500 тонн - как 100 слонов! Но оно держится в воздухе за счёт восходящих потоков.",
        "В пустыне Атакама (Чили) дождя не было 400 лет подряд - самое сухое место на планете.",
    ],
    "travel": [
        "Планируете поездку? Смотрите прогноз за 2 недели до вылета и за 3 дня - так выше шанс поймать хорошую погоду.",
        "Лучшее время для Средиземноморья - сентябрь: море ещё тёплое, а толпы уже уехали.",
        "В горах погода меняется каждые 15 минут. Всегда берите дождевик и тёплый слой, даже если внизу +25 C.",
    ],
    "humor": [
        "Погода - единственная тема, на которую можно жаловаться бесконечно, и все согласятся!",
        "Мой зонт всегда ломается именно в тот день, когда прогноз обещал ясно. Совпадение? Не думаю.",
        "Синоптики - единственные люди, которые могут ошибаться каждый день и всё равно получать зарплату!",
    ],
    "tip": [
        "Если утром туман - днём, скорее всего, будет солнечно и тепло. Отличная погода для прогулки!",
        "Правило слоёв: футболка + рубашка + лёгкая куртка. Так вы сможете подстроиться под любую погоду за день.",
        "При высокой влажности +25 C ощущаются как +30 C. Берите воду и ищите тень.",
    ],
}

_state = {"topic_idx": 0, "last_post_ts": 0}
STATE_FILE = "vk_posts_state.json"

def _load_state():
    global _state
    try:
        if os.path.exists(STATE_FILE):
            with open(STATE_FILE, "r", encoding="utf-8") as f:
                _state.update(json.load(f))
    except Exception:
        pass

def _save_state():
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(_state, f)
    except Exception as e:
        logger.warning(f"VK posts state save error: {e}")

_load_state()

def _pick_topic():
    topic = TOPICS[_state["topic_idx"] % len(TOPICS)]
    _state["topic_idx"] = (_state["topic_idx"] + 1) % len(TOPICS)
    return topic

def _generate_text_with_ll(topic):
    try:
        from features import _get_ai_provider
        provider, api_key, model, base_url = _get_ai_provider()
        if not provider or not api_key:
            return None
        prompt = TOPIC_PROMPTS.get(topic, "Напиши пост о погоде на русском, 2-3 предложения.")
        system = "Ты ведёшь уютный паблик о погоде в VK. Пиши живо, коротко, с юмором или пользой. Ответ только текстом поста, без пояснений и кавычек."
        headers = {"Content-Type": "application/json", "Authorization": f"Bearer {api_key}"}
        if provider == "huggingface":
            data = {"inputs": prompt, "parameters": {"max_new_tokens": 200}}
            resp = requests.post(base_url, headers=headers, json=data, timeout=20)
            if resp.status_code == 200:
                return resp.json()[0].get("generated_text", "").strip()
        else:
            data = {
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": prompt}
                ],
                "max_tokens": 250,
                "temperature": 0.8
            }
            resp = requests.post(base_url, headers=headers, json=data, timeout=25)
            if resp.status_code == 200:
                try:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                except Exception as e:
                    logger.warning(f"LLM parse error: {e}")
    except Exception as e:
        logger.warning(f"LLM generate error: {e}")
    return None

def _generate_text(topic):
    text = _generate_text_with_ll(topic)
    if not text or len(text) < 30:
        text = random.choice(FALLBACK_TEXTS.get(topic, ["Погода - это настроение дня!"]))
    label = TOPIC_LABELS.get(topic, "Погода")
    emoji = {"weather_fact": "🌤", "travel": "✈️", "humor": "😄", "tip": "💡"}.get(topic, "🌤")
    return f"{emoji} {label}\n\n{text}\n\n#погода #WeatherTomBot"

def _make_image(topic):
    """Картинка 1200x630 (стандарт VK OG, соотношение 1.9:1)."""
    themes = {
        "weather_fact": ((135, 206, 250), (70, 130, 180), "☁"),
        "travel":       ((255, 200, 120), (200, 100, 50), "T"),
        "humor":        ((255, 230, 150), (255, 160, 100), "H"),
        "tip":          ((180, 220, 180), (80, 140, 80),   "i"),
    }
    c1, c2, icon = themes.get(topic, ((200,200,200),(100,100,100),"W"))
    W, H = 1200, 630
    img = Image.new("RGB", (W, H))
    draw = ImageDraw.Draw(img)
    for y in range(H):
        r = int(c1[0] + (c2[0] - c1[0]) * y / H)
        g = int(c1[1] + (c2[1] - c1[1]) * y / H)
        b = int(c1[2] + (c2[2] - c1[2]) * y / H)
        draw.line([(0, y), (W, y)], fill=(r, g, b))
    try:
        font_big = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 220)
        font_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 56)
        font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 32)
    except Exception:
        font_big = font_title = font_small = ImageFont.load_default()
    # Тёмная полоса внизу для текста
    draw.rectangle([(0, H-160), (W, H)], fill=(20, 20, 20, 200))
    # Крупная буква-символ рубрики
    draw.text((W//2, H//2 - 40), icon, font=font_big, fill=(255, 255, 255), anchor="mm")
    label = TOPIC_LABELS.get(topic, "WeatherTomBot")
    draw.text((W//2, H-110), label, font=font_title, fill=(255, 255, 255), anchor="mm")
    draw.text((W//2, H-50), "WeatherTomBot", font=font_small, fill=(200, 200, 200), anchor="mm")
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=92)
    buf.seek(0)
    return buf

def _vk_api(method, params, files=None, timeout=15):
    if not VK_POST_TOKEN or not VK_GROUP_ID:
        return {"error": {"error_msg": "VK_POST_TOKEN or VK_GROUP_ID not set"}}
    p = dict(params)
    p["access_token"] = VK_POST_TOKEN
    p["v"] = "5.199"
    try:
        if files:
            resp = requests.post(f"https://api.vk.com/method/{method}", data=p, files=files, timeout=timeout)
        else:
            resp = requests.post(f"https://api.vk.com/method/{method}", data=p, timeout=timeout)
        return resp.json()
    except Exception as e:
        return {"error": {"error_msg": str(e)}}

def _upload_photo(img_bytes):
    """Загрузка фото через messages-сервер (разрешён group-токенам).
    Сохранённое фото прикрепляется к посту на стену как вложение."""
    up = _vk_api("photos.getMessagesUploadServer", {"group_id": VK_GROUP_ID})
    if "error" in up or "response" not in up:
        return None, up.get("error", {}).get("error_msg", "upload server error")
    upload_url = up["response"]["upload_url"]
    try:
        r = requests.post(upload_url, files={"photo": ("post.png", img_bytes, "image/png")}, timeout=30)
        saved = r.json()
    except Exception as e:
        return None, f"upload error: {e}"
    save = _vk_api("photos.saveMessagesPhoto", {
        "photo": saved.get("photo"),
        "server": saved.get("server"),
        "hash": saved.get("hash"),
    })
    if "error" in save or "response" not in save:
        return None, save.get("error", {}).get("error_msg", "save error")
    photos = save["response"]
    if not photos:
        return None, "no photos returned"
    p = photos[0]
    return f"photo{p['owner_id']}_{p['id']}", None

def publish_post(topic=None):
    if not VK_POST_TOKEN:
        return False, "VK_POST_TOKEN not set"
    topic = topic or _pick_topic()
    text = _generate_text(topic)
    ts = int(time.time())
    fname = f"p{ts}.jpg"
    media_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vk_media")
    try:
        os.makedirs(media_dir, exist_ok=True)
        img = _make_image(topic)
        with open(os.path.join(media_dir, fname), "wb") as f:
            f.write(img.read())
        for old_f in sorted(os.listdir(media_dir))[:-30]:
            try:
                os.remove(os.path.join(media_dir, old_f))
            except Exception:
                pass
    except Exception as e:
        logger.warning(f"VK media save error: {e}")
        fname = None
    message = text
    if fname:
        message += f"\n\n🖼 Открытка часа: https://mob100500lvl.pythonanywhere.com/vkpost/{ts}"
    params = {
        "owner_id": f"-{VK_GROUP_ID}",
        "from_group": 1,
        "message": message,
    }
    post = _vk_api("wall.post", params)
    if "error" in post:
        return False, f"wall.post error: {post['error']}"
    _state["last_post_ts"] = ts
    _save_state()
    return True, {"topic": topic, "post_id": post.get("response", {}).get("post_id"), "text": text[:100]}

def hourly_job():
    if not VK_POST_TOKEN:
        return None
    elapsed = time.time() - _state.get("last_post_ts", 0)
    if elapsed < 55 * 60:
        return None
    ok, info = publish_post()
    if ok:
        logger.info(f"VK POST: {info}")
        return info
    else:
        logger.error(f"VK POST fail: {info}")
        return None
