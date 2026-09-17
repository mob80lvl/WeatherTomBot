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

TOPICS = ["weather_fact", "travel", "humor", "tip", "history", "science", "folklore", "records", "myths", "season"]
TOPIC_PROMPTS = {
    "weather_fact": "Короткий интересный факт о погоде, климате или атмосферных явлениях (2-3 предложения, живо, с эмодзи, на русском).",
    "travel": "Совет путешественнику про погоду, одежду или лучшее время для поездки в интересный регион (2-3 предложения, живо, с эмодзи, на русском).",
    "humor": "Забавная шутка или каламбур про погоду, дождь, солнце или зиму (1-2 предложения, с юмором, с эмодзи, на русском).",
    "tip": "Практический совет на сегодня по погоде (что взять, как одеться, куда не стоит идти) (2 предложения, с эмодзи, на русском).",
    "history": "Расскажи интересный исторический факт о погоде или климате.",
    "science": "Объясни научное явление погоды простым языком.",
    "folklore": "Расскажи народную примету о погоде и её происхождение.",
    "records": "Расскажи о мировом рекорде погоды (температура, осадки, ветер).",
    "myths": "Развенчай популярный миф о погоде.",
    "season": "Опиши текущий сезон и что характерно для погоды сейчас.",
}
TOPIC_LABELS = {
    "weather_fact": "Факт о погоде",
    "travel": "Путешествия",
    "humor": "Юмор",
    "tip": "Совет дня",
    "history": "📜 История",
    "science": "🔬 Наука",
    "folklore": "🌾 Народные приметы",
    "records": "🏆 Рекорды",
    "myths": "🧩 Мифы и правда",
    "season": "🍂 Сезон сейчас",
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
    "history": [
        "В 1816 году был «год без лета» после извержения вулкана Тамбора — снег выпадал даже в июне!",
        "Великий лондонский смог 1952 года унёс жизни 12 000 человек — после этого приняли закон о чистом воздухе.",
        "В 1972 году в Иране выпал снег высотой 8 метров — самый сильный снегопад в истории.",
    ],
    "science": [
        "Молния нагревает воздух до 30 000°C — в 5 раз горячее поверхности Солнца!",
        "Снежинки имеют 6 лучей из-за молекулярной структуры воды — каждая уникальна.",
        "Радуга появляется, когда солнечный свет преломляется в каплях воды под углом 42°.",
    ],
    "folklore": [
        "Если ласточки летают низко — будет дождь. Они ловят насекомых, которые опускаются перед ненастьем.",
        "Красный закат — к ветреной погоде. Пыль в воздухе рассеивает красный свет.",
        "Если кошки умываются лапой — к гостям. На самом деле они чувствуют изменение давления.",
    ],
    "records": [
        "Самая высокая температура на Земле: +56.7°C в Долине Смерти (1913 год).",
        "Самый сильный ветер: 407 км/ч на острове Барроу (Австралия, 1996 год).",
        "Самый сильный град: камни весом 1 кг падали в Бангладеш (1986 год), погибли 92 человека.",
    ],
    "myths": [
        "Миф: молния никогда не бьёт дважды в одно место. Правда: в Эмпайр-стейт-билдинг попадает до 25 раз в год!",
        "Миф: если слышишь гром, значит дождь близко. Правда: гром слышен за 15 км, а дождь может быть далеко.",
        "Миф: животные чувствуют землетрясение. Правда: они реагируют на предварительные толчки, которые люди не замечают.",
    ],
    "season": [
        "Сентябрь — время бабьего лета: тёплые дни, прохладные ночи, золотая листва.",
        "Октябрь — месяц первых заморозков и листопада. Природа готовится к зиме.",
        "Ноябрь — предзимье: холодно, пасмурно, но снег ещё не ложится надолго.",
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
    "history": "📜 История погоды\n\nВ 1816 году был «год без лета» после извержения вулкана Тамбора — снег выпадал даже в июне!",
    "science": "🔬 Наука о погоде\n\nМолния нагревает воздух до 30 000°C — в 5 раз горячее поверхности Солнца!",
    "folklore": "🌾 Народная примета\n\nЕсли ласточки летают низко — будет дождь. Они ловят насекомых, которые опускаются перед ненастьем.",
    "records": "🏆 Рекорд погоды\n\nСамая высокая температура на Земле: +56.7°C в Долине Смерти (1913 год).",
    "myths": "🧩 Миф о погоде\n\nМиф: молния никогда не бьёт дважды в одно место. Правда: в Эмпайр-стейт-билдинг попадает до 25 раз в год!",
    "season": "🍂 Сезон сейчас\n\nСентябрь — время бабьего лета: тёплые дни, прохладные ночи, золотая листва.",
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

CARD_THEMES = {
    "weather_fact": ((135, 206, 250), (70, 130, 180), (25, 60, 110)),
    "travel":       ((255, 200, 120), (200, 100, 50), (120, 55, 20)),
    "humor":        ((255, 230, 150), (255, 160, 100), (150, 80, 30)),
    "tip":          ((180, 220, 180), (80, 140, 80), (35, 80, 35)),
    "history":      ((210, 180, 140), (120, 90, 60), (70, 50, 30)),
    "science":      ((170, 150, 230), (90, 70, 160), (45, 35, 95)),
    "folklore":     ((190, 220, 150), (100, 140, 70), (50, 80, 35)),
    "records":      ((255, 160, 150), (190, 70, 60), (110, 30, 25)),
    "myths":        ((160, 175, 195), (70, 90, 115), (35, 45, 60)),
    "season":       ((250, 200, 130), (160, 100, 60), (95, 55, 30)),
}

import re as _re
_EMOJI_RE = _re.compile(
    "[\U0001F300-\U0001FAFF\U0001F000-\U0001F02F\U00002600-\U000027BF"
    "\U00002B00-\U00002BFF\U0000FE0F\U0000200D]", flags=_re.UNICODE)

def _make_card(topic, text):
    """Карточка под рубрику и текст поста (1280px, JPEG)."""
    import textwrap
    c1, c2, hdr = CARD_THEMES.get(topic, ((150, 150, 150), (80, 80, 80), (40, 40, 40)))
    clean = _EMOJI_RE.sub("", text or "")
    clean = _re.sub(r"\n{3,}", "\n\n", clean).strip()
    lines = []
    for para in clean.split("\n"):
        para = para.strip()
        if not para:
            lines.append("")
            continue
        lines.extend(textwrap.wrap(para, width=30) or [""])
    if len(lines) > 12:
        lines = lines[:12]
        lines[-1] = lines[-1][:29] + "…"
    W, line_h, top = 1280, 62, 190
    H = top + len(lines) * line_h + 140
    img = Image.new("RGB", (W, H))
    d = ImageDraw.Draw(img)
    for y in range(H):
        k = y / H
        d.line([(0, y), (W, y)], fill=(int(c1[0] + (c2[0] - c1[0]) * k),
                                       int(c1[1] + (c2[1] - c1[1]) * k),
                                       int(c1[2] + (c2[2] - c1[2]) * k)))
    overlay = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    ImageDraw.Draw(overlay).rectangle([0, 0, W, H], fill=(0, 0, 0, 110))
    img = Image.alpha_composite(img.convert("RGBA"), overlay).convert("RGB")
    d = ImageDraw.Draw(img)
    d.rectangle([0, 0, W, 120], fill=hdr)
    try:
        f_title = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 52)
        f_body = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 42)
        f_foot = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 30)
    except Exception:
        f_title = f_body = f_foot = ImageFont.load_default()
    label = _EMOJI_RE.sub("", TOPIC_LABELS.get(topic, "WeatherTomBot")).strip().upper()
    d.text((60, 60), label, font=f_title, fill=(255, 255, 255), anchor="lm")
    y = top + 10
    for ln in lines:
        d.text((60, y), ln, font=f_body, fill=(255, 255, 255))
        y += line_h
    d.text((60, H - 70), "WeatherTomBot", font=f_foot, fill=(225, 225, 225))
    buf = BytesIO()
    img.save(buf, format="JPEG", quality=88)
    buf.seek(0)
    return buf

def _tg_send_photo(topic, text):
    """Фото-карточка + подпись в TG-канал."""
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chan = os.getenv("TG_CHANNEL_ID", "").strip()
    if not token or not chan:
        return False
    try:
        buf = _make_card(topic, text)
        r = requests.post(f"https://api.telegram.org/bot{token}/sendPhoto",
                          data={"chat_id": chan, "caption": (text or "")[:1024]},
                          files={"photo": ("card.jpg", buf, "image/jpeg")}, timeout=30)
        d = r.json()
        if d.get("ok"):
            return True
        logger.error(f"TG sendPhoto error: {d}")
        return False
    except Exception as e:
        logger.error(f"TG sendPhoto exception: {e}")
        return False

def _tg_send(text):
    """Отправка текста в TG-канал (кросспостинг)."""
    token = os.getenv("TELEGRAM_TOKEN", "").strip()
    chan = os.getenv("TG_CHANNEL_ID", "").strip()
    if not token or not chan:
        return False
    try:
        r = requests.post(f"https://api.telegram.org/bot{token}/sendMessage",
                          json={"chat_id": chan, "text": text}, timeout=15)
        d = r.json()
        if d.get("ok"):
            return True
        logger.error(f"TG channel send error: {d}")
        return False
    except Exception as e:
        logger.error(f"TG channel send exception: {e}")
        return False

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

def publish_post(topic=None, also_tg=False):
    if not VK_POST_TOKEN:
        return False, "VK_POST_TOKEN not set"
    topic = topic or _pick_topic()
    text = _generate_text(topic)
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Europe/Moscow"))
    except Exception:
        now = datetime.utcnow()
    current_slot = f"{now.hour:02d}:00_{now.strftime('%Y-%m-%d')}"
    message = text
    params = {
        "owner_id": f"-{VK_GROUP_ID}",
        "from_group": 1,
        "message": message,
    }
    post = _vk_api("wall.post", params)
    if "error" in post:
        return False, f"wall.post error: {post['error']}"
    _state["last_slot"] = current_slot
    _save_state()
    tg_ok = None
    if also_tg:
        tg_ok = _tg_send_photo(topic, text)
        if not tg_ok:
            tg_ok = _tg_send(text)
    return True, {"topic": topic, "post_id": post.get("response", {}).get("post_id"), "text": text[:100], "tg": tg_ok}

def hourly_job():
    if not VK_POST_TOKEN:
        return None
    from datetime import datetime
    try:
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Europe/Moscow"))
    except Exception:
        now = datetime.utcnow()
    # Расписание: 09:00, 12:00, 15:00, 18:00, 21:00 МСК (сверка по часу — устойчиво к задержкам планировщика)
    slot_key = f"{now.hour:02d}:00_{now.strftime('%Y-%m-%d')}"
    if now.hour not in (9, 12, 15, 18, 21):
        return None
    # Защита от дублей в одном слоте
    if _state.get("last_slot", "") == slot_key:
        return None
    ok, info = publish_post(also_tg=True)
    if ok:
        logger.info(f"VK POST: {info}")
        return info
    else:
        logger.error(f"VK POST fail: {info}")
        return None
