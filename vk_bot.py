"""VK Bot adapter for WeatherTomBot (phase 2: identical to Telegram)."""
import os, json, threading, requests, logging, time, re
from flask import request
from dotenv import load_dotenv

load_dotenv()
VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "")
VK_SECRET = os.getenv("VK_SECRET", "")
VK_CONFIRM = os.getenv("VK_CONFIRM", "")

logger = logging.getLogger(__name__)

from storage import get_user_city, save_user_city, get_user_lang, set_user_lang
from weather import (get_weather_aggregated, get_forecast_aggregated,
                     format_weather_text, format_forecast_text)
from features import (favorites, add_favorite, remove_favorite,
                      notification_prefs, set_notification_prefs)
from texts import T

recent_events = set()
MAX_EVENTS = 200
_vk_state = {}
STATE_TTL = 300

def _set_state(uid, mode):
    _vk_state[uid] = {"mode": mode, "ts": time.time()}

def _get_state(uid):
    st = _vk_state.get(uid)
    if not st:
        return None
    if time.time() - st["ts"] > STATE_TTL:
        _vk_state.pop(uid, None)
        return None
    return st["mode"]

def _clear_state(uid):
    _vk_state.pop(uid, None)

def vk_send(peer_id, message, keyboard=None):
    if not VK_TOKEN:
        logger.error("VK_TOKEN not set")
        return None
    params = {
        "peer_id": peer_id,
        "message": message[:4096],
        "random_id": int(time.time() * 1000) % 2147483647,
        "access_token": VK_TOKEN,
        "v": "5.199"
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    try:
        resp = requests.get("https://api.vk.com/method/messages.send", params=params, timeout=10)
        result = resp.json()
        if "error" in result:
            logger.error(f"VK send error: {result['error']}")
        return result
    except Exception as e:
        logger.error(f"VK send exception: {e}")
        return None

def vk_strip_md(text):
    if not text:
        return ""
    return text.replace("*", "").replace("`", "")

def _btn(label, cmd, color="primary"):
    return {"action": {"type": "text", "label": label[:40],
                       "payload": json.dumps({"cmd": cmd}, ensure_ascii=False)},
            "color": color}

def vk_menu_keyboard(lang="ru"):
    return {"one_time": False, "inline": False, "buttons": [
        [_btn("🌤 Погода сейчас", "weather"), _btn("📅 Прогноз 5 дней", "forecast")],
        [_btn("⭐ Избранное", "favorites"), _btn("🏙 Город", "city")],
        [_btn("🔔 Оповещения", "notifications"), _btn("🌐 Язык", "lang")],
        [_btn("❓ Помощь", "help")],
    ]}

def _notif_keyboard(uid, lang):
    p = notification_prefs(uid)
    if not isinstance(p, dict):
        p = {}
    on = lambda k: "✅" if p.get(k, True) else "❌"
    en = "❌ Выключены" if p.get("enabled") else "✅ Включены"
    return {"one_time": False, "inline": False, "buttons": [
        [_btn(en, "notif_toggle"), _btn("⏰ Время", "notif_time")],
        [_btn(f"💧 Дождь: {on('rain')}", "notif_rain"), _btn(f"💨 Ветер: {on('wind')}", "notif_wind")],
        [_btn(f"❄️ Мороз: {on('frost')}", "notif_frost"), _btn(f"🔥 Жара: {on('heat')}", "notif_heat")],
        [_btn("⬅ Назад", "back")],
    ]}

def _fav_keyboard():
    return {"one_time": False, "inline": False, "buttons": [
        [_btn("➕ Добавить", "fav_add"), _btn("🗑 Удалить", "fav_del")],
        [_btn("⬅ Назад", "back")],
    ]}

def _show_weather(uid, peer_id, lang):
    city = get_user_city(uid)
    if not city:
        vk_send(peer_id, vk_strip_md(T(lang, "cities_empty")) + "\nНажмите '🏙 Город' и введите название.", vk_menu_keyboard(lang))
        return
    w = get_weather_aggregated(city, lang)
    if not w or "error" in w:
        vk_send(peer_id, vk_strip_md(T(lang, "weather_error")), vk_menu_keyboard(lang))
        return
    vk_send(peer_id, vk_strip_md(format_weather_text(uid, w)), vk_menu_keyboard(lang))

def _show_forecast(uid, peer_id, lang):
    city = get_user_city(uid)
    if not city:
        vk_send(peer_id, vk_strip_md(T(lang, "cities_empty")) + "\nНажмите '🏙 Город'.", vk_menu_keyboard(lang))
        return
    f = get_forecast_aggregated(city, 5, lang)
    vk_send(peer_id, vk_strip_md(format_forecast_text(uid, f, city, 5)), vk_menu_keyboard(lang))

def _show_favorites(uid, peer_id, lang):
    favs = favorites(uid)
    listing = "\n".join(f"📍 {x}" for x in favs) if favs else vk_strip_md(T(lang, "cities_empty"))
    text = vk_strip_md(T(lang, "cities_title")) + "\n\n" + listing + "\n\n" + vk_strip_md(T(lang, "cities_choose"))
    vk_send(peer_id, text, _fav_keyboard())

def _show_notifications(uid, peer_id, lang):
    p = notification_prefs(uid)
    if not isinstance(p, dict):
        p = {}
    status = T(lang, "notification_enabled") if p.get("enabled") else T(lang, "notification_disabled")
    city = p.get("city") or get_user_city(uid) or "—"
    text = T(lang, "notification_settings", status=status,
             rain="✅" if p.get("rain", True) else "❌",
             wind="✅" if p.get("wind", True) else "❌",
             frost="✅" if p.get("frost", True) else "❌",
             heat="✅" if p.get("heat", True) else "❌",
             time=p.get("time", "08:00"), city=city)
    vk_send(peer_id, vk_strip_md(text), _notif_keyboard(uid, lang))

def _show_help(uid, peer_id, lang):
    text = ("🌤 WeatherTomBot для ВКонтакте\n\n"
            "🌤 Погода сейчас — текущая погода\n"
            "📅 Прогноз 5 дней — прогноз по дням\n"
            "⭐ Избранное — ваши города (добавить/удалить)\n"
            "🏙 Город — установить город (следующим сообщением)\n"
            "🔔 Оповещения — статус, время и тумблеры\n"
            "🌐 Язык — переключить русский/english\n"
            "❓ Помощь — это сообщение")
    vk_send(peer_id, text, vk_menu_keyboard(lang))

def _handle_state(uid, peer_id, lang, text):
    mode = _get_state(uid)
    if not mode:
        return False
    _clear_state(uid)
    if mode == "city":
        save_user_city(uid, text)
        vk_send(peer_id, f"✅ Город сохранён: {text}", vk_menu_keyboard(lang))
    elif mode == "time":
        m = re.match(r"^(\d{1,2}):(\d{2})$", text.strip())
        if m:
            hh = int(m.group(1)); mm = int(m.group(2))
            if 0 <= hh <= 23 and 0 <= mm <= 59:
                set_notification_prefs(uid, time=f"{hh:02d}:{mm:02d}")
                vk_send(peer_id, f"✅ Время оповещений: {hh:02d}:{mm:02d}", _notif_keyboard(uid, lang))
            else:
                vk_send(peer_id, "❌ Неверный формат. Пример: 08:00", _notif_keyboard(uid, lang))
        else:
            vk_send(peer_id, "❌ Неверный формат. Пример: 08:00", _notif_keyboard(uid, lang))
    elif mode == "fav_add":
        ok = add_favorite(uid, text.strip())
        vk_send(peer_id, "✅ Город добавлен в избранное!" if ok else "❌ Не удалось добавить (лимит 50 или дубликат).", _fav_keyboard())
    elif mode == "fav_del":
        ok = remove_favorite(uid, text.strip())
        vk_send(peer_id, "✅ Город удалён из избранного." if ok else "❌ Такого города нет в избранном.", _fav_keyboard())
    return True

def _route(uid, peer_id, lang, cmd, text):
    low = (text or "").strip().lower()
    if cmd == "weather" or low in ("погода", "🌤 погода сейчас"):
        _show_weather(uid, peer_id, lang)
    elif cmd == "forecast" or low in ("прогноз", "📅 прогноз 5 дней"):
        _show_forecast(uid, peer_id, lang)
    elif cmd == "favorites" or low in ("избранное", "⭐ избранное"):
        _show_favorites(uid, peer_id, lang)
    elif cmd == "city" or low in ("город", "🏙 город"):
        _set_state(uid, "city")
        vk_send(peer_id, "✏️ Введите название города одним сообщением:", vk_menu_keyboard(lang))
    elif cmd == "notifications" or low in ("оповещения", "🔔 оповещения"):
        _show_notifications(uid, peer_id, lang)
    elif cmd == "lang" or low in ("язык", "🌐 язык"):
        new = "en" if lang == "ru" else "ru"
        set_user_lang(uid, new)
        vk_send(peer_id, "✅ Language switched to English." if new == "en" else "✅ Язык переключён на русский.", vk_menu_keyboard(new))
    elif cmd == "help" or low in ("помощь", "❓ помощь", "/start", "start", "старт", ""):
        _show_help(uid, peer_id, lang)
    elif cmd == "back":
        vk_send(peer_id, vk_strip_md(T(lang, "cities_choose")) if False else "🏠 Главное меню:", vk_menu_keyboard(lang))
    elif cmd == "notif_toggle":
        p = notification_prefs(uid)
        set_notification_prefs(uid, enabled=not (p.get("enabled") if isinstance(p, dict) else False))
        _show_notifications(uid, peer_id, lang)
    elif cmd in ("notif_rain", "notif_wind", "notif_frost", "notif_heat"):
        key = cmd[6:]
        p = notification_prefs(uid)
        cur = p.get(key, True) if isinstance(p, dict) else True
        set_notification_prefs(uid, **{key: not cur})
        _show_notifications(uid, peer_id, lang)
    elif cmd == "notif_time":
        _set_state(uid, "time")
        vk_send(peer_id, "⏰ Введите время в формате ЧЧ:ММ (например 08:00):")
    elif cmd == "fav_add":
        _set_state(uid, "fav_add")
        vk_send(peer_id, "➕ Введите город для добавления в избранное:")
    elif cmd == "fav_del":
        _set_state(uid, "fav_del")
        vk_send(peer_id, "🗑 Введите город для удаления из избранного:")
    else:
        vk_send(peer_id, "Не знаю такой команды. Нажмите '❓ Помощь'.", vk_menu_keyboard(lang))

def vk_process_event(event):
    try:
        obj = event.get("object", {})
        message = obj.get("message", {})
        from_id = message.get("from_id", 0)
        peer_id = message.get("peer_id", 0)
        uid = f"vk_{from_id}"
        lang = get_user_lang(uid) or "ru"
        text = (message.get("text") or "").strip()
        cmd = None
        payload = message.get("payload")
        if payload:
            try:
                cmd = json.loads(payload).get("cmd")
            except Exception:
                cmd = None
        if _handle_state(uid, peer_id, lang, text):
            return
        _route(uid, peer_id, lang, cmd, text)
    except Exception as e:
        logger.error(f"VK process error: {e}", exc_info=True)

def vk_webhook():
    data = request.json
    if not data:
        return "no data", 400
    if VK_SECRET and data.get("secret") != VK_SECRET:
        logger.warning(f"VK: bad secret from {request.remote_addr}")
        return "forbidden", 403
    if data.get("type") == "confirmation":
        return VK_CONFIRM
    event_id = (data.get("object") or {}).get("id") or ((data.get("object") or {}).get("message") or {}).get("id")
    if event_id and event_id in recent_events:
        return "ok"
    if event_id:
        recent_events.add(event_id)
        if len(recent_events) > MAX_EVENTS:
            recent_events.pop()
    threading.Thread(target=vk_process_event, args=(data,), daemon=True).start()
    return "ok"

def register_vk_routes(app):
    app.add_url_rule("/vk_webhook", "vk_webhook", vk_webhook, methods=["POST"])
    logger.info("✅ VK webhook registered at /vk_webhook")
