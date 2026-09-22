# -*- coding: utf-8 -*-
"""Видео-автопостинг в TG-канал из YouTube.
Расписание: :30 каждого часа 8-22 МСК (текстовые посты в :00).
"""
import os
import json
import logging
import requests

logger = logging.getLogger("video_posts")

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATE_FILE = os.path.join(BASE_DIR, "video_posts_state.json")

YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY", "").strip()

TOPICS = ["weather_fact", "travel", "humor", "tip", "history", "science",
          "folklore", "records", "myths", "season", "clothing", "cozy",
          "health", "mood", "activity"]

YT_QUERIES = {
    "weather_fact": "интересные факты о погоде",
    "travel": "путешествия и погода природа",
    "humor": "погода приколы юмор",
    "tip": "советы по погоде лайфхаки",
    "history": "исторические катаклизмы погода",
    "science": "метеорология наука атмосфера",
    "folklore": "народные приметы о погоде",
    "records": "рекорды погоды в мире",
    "myths": "мифы о погоде разоблачение",
    "season": "времена года природа красота",
    "clothing": "как одеться по погоде стиль",
    "cozy": "уют дома осенний вечер атмосфера",
    "health": "погода и здоровье советы",
    "mood": "погода и настроение психология",
    "activity": "активный отдых на природе погода",
}

LABELS = {
    "weather_fact": "🌤 Факт о погоде",
    "travel": "✈️ Путешествия",
    "humor": "😄 Юмор",
    "tip": "💡 Совет дня",
    "history": "📜 История",
    "science": "🔬 Наука",
    "folklore": "🌾 Народные приметы",
    "records": "🏆 Рекорды погоды",
    "myths": "🧩 Мифы и правда",
    "season": "🍂 Сезон сейчас",
    "clothing": "👕 Одежда по погоде",
    "cozy": "☕ Уют",
    "health": "🩺 Здоровье",
    "mood": "💭 Настроение",
    "activity": "🎯 Активность",
}


def _state():
    try:
        with open(STATE_FILE, encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {"last_slot": "", "topic_idx": 0, "used_yt": {}}


def _save_state(st):
    try:
        with open(STATE_FILE, "w", encoding="utf-8") as f:
            json.dump(st, f, ensure_ascii=False, indent=1)
    except Exception as e:
        logger.warning(f"video state save error: {e}")


def _pick_topic(st):
    idx = int(st.get("topic_idx", 0)) % len(TOPICS)
    st["topic_idx"] = idx + 1
    return TOPICS[idx]


def _get_tomsk_weather_snippet():
    """Короткая сводка погоды в Томске для AI-промпта."""
    try:
        import config
        fn = config.CFG.get("get_weather_aggregated")
        if fn:
            w = fn("Tomsk")
            if isinstance(w, dict):
                t = w.get("temp") or w.get("temperature")
                desc = w.get("description", "")
                if t is not None:
                    return f"Сейчас в Томске {t}°C, {desc}."
    except Exception as e:
        logger.warning(f"tomsk weather snippet error: {e}")
    return "Сейчас в Томске обычная осенняя погода."


def _ai_description(topic, title):
    """AI-описание под видео: учитывает погоду Томска и тему канала."""
    try:
        from features import _get_ai_provider
        provider, api_key, model, base_url = _get_ai_provider()
        if not provider or not api_key:
            return None
        label = LABELS.get(topic, "🎬 Видео")
        tomsk = _get_tomsk_weather_snippet()
        prompt = (f"Ты ведёшь уютный паблик «Погода в Томске». "
                  f"{tomsk}\n"
                  f"Составь короткое описание (2-3 предложения, до 250 символов) "
                  f"для видеоролика «{title}» в рубрике «{label}». "
                  f"Свяжи тему видео с погодой или настроением, добавь пользу или интересную мысль. "
                  f"Стиль: дружелюбно, живо, 1-2 эмодзи, на русском. "
                  f"Ответ только текстом описания, без кавычек и пояснений.")
        headers = {"Content-Type": "application/json",
                   "Authorization": f"Bearer {api_key}"}
        if provider == "huggingface":
            data = {"inputs": prompt, "parameters": {"max_new_tokens": 150}}
            resp = requests.post(base_url, headers=headers, json=data, timeout=20)
            if resp.status_code == 200:
                return resp.json()[0].get("generated_text", "").strip()
        else:
            data = {"model": model,
                    "messages": [{"role": "user", "content": prompt}],
                    "max_tokens": 150, "temperature": 0.8}
            resp = requests.post(base_url, headers=headers, json=data, timeout=25)
            if resp.status_code == 200:
                try:
                    return resp.json()["choices"][0]["message"]["content"].strip()
                except Exception:
                    return None
    except Exception as e:
        logger.warning(f"video AI description error: {e}")
    return None


def _search_youtube(topic, used):
    """Поиск короткого YouTube-видео по теме, пропуская использованные."""
    if not YOUTUBE_API_KEY:
        return None
    q = YT_QUERIES.get(topic, "погода")
    try:
        r = requests.get("https://www.googleapis.com/youtube/v3/search",
                         timeout=20,
                         params={"part": "snippet", "q": q, "type": "video",
                                 "videoDuration": "short", "maxResults": 15,
                                 "relevanceLanguage": "ru",
                                 "key": YOUTUBE_API_KEY})
        d = r.json()
        if "error" in d:
            logger.error(f"YT search error: {d['error'].get('message')}")
            return None
        for it in d.get("items", []):
            vid = it.get("id", {}).get("videoId")
            if not vid or vid in used:
                continue
            title = it.get("snippet", {}).get("title", "")
            return {"id": vid, "title": title}
    except Exception as e:
        logger.error(f"YT search exception: {e}")
    return None


def publish_tg_video(topic=None):
    """Публикует YouTube-видео с AI-описанием в TG-канал."""
    from vk_posts import _tg_send
    st = _state()
    topic = topic or _pick_topic(st)
    used = st.setdefault("used_yt", {}).setdefault(topic, [])
    vid = _search_youtube(topic, used)
    if not vid:
        _save_state(st)
        return False, "no youtube video found"
    desc = _ai_description(topic, vid["title"])
    label = LABELS.get(topic, "🎬 Видео")
    if not desc:
        desc = f"{label}: интересное короткое видео о погоде! ☀️"
    text = (f"{label}\n\n{desc}\n\n📺 Смотреть видео: "
            f"https://youtu.be/{vid['id']}\n\n"
            f"📍 Погода в Томске от WeatherTomBot")
    ok = _tg_send(text)
    if ok:
        used.append(vid["id"])
        if len(used) > 40:
            st["used_yt"][topic] = used[-40:]
        _save_state(st)
        logger.info(f"TG VIDEO POST: topic={topic} vid={vid['id']}")
        return True, {"topic": topic, "video_id": vid["id"],
                      "title": vid["title"], "text": text}
    _save_state(st)
    return False, "tg send failed"


def half_hour_job():
    """Автопостинг в :30 каждого часа 8-22 МСК."""
    try:
        from datetime import datetime
        from zoneinfo import ZoneInfo
        now = datetime.now(ZoneInfo("Europe/Moscow"))
    except Exception:
        return None
    if now.hour not in (8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22):
        return None
    if now.minute != 30:
        return None
    st = _state()
    slot = f"{now.hour:02d}:30_{now.strftime('%Y-%m-%d')}"
    if st.get("last_slot") == slot:
        return None
    st["last_slot"] = slot
    _save_state(st)
    ok, info = publish_tg_video()
    if ok:
        logger.info(f"TG VIDEO POST ok: {info.get('topic')} {info.get('video_id')}")
    else:
        logger.error(f"TG VIDEO POST fail: {info}")
    return ok
