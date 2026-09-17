"""VK Bot adapter for WeatherTomBot (phase 2.1: full localization, identical to Telegram)."""
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
from texts import TEXTS

recent_events = set()
MAX_EVENTS = 200
_vk_state = {}
STATE_TTL = 300

LANG_NAMES = {"ru": "🇷🇺 Русский", "en": "🇬 English", "es": "🇪🇸 Español", "zh": "🇨🇳 中文"}

MSG = {
    "ru": {
        "enter_city": "✏️ Введите название города одним сообщением:",
        "city_saved": "✅ Город сохранён: {city}",
        "enter_time": "⏰ Введите время в формате ЧЧ:ММ (например 08:00):",
        "time_saved": "✅ Время оповещений: {time}",
        "time_bad": "❌ Неверный формат. Пример: 08:00",
        "fav_enter_add": "➕ Введите город для добавления в избранное:",
        "fav_enter_del": "🗑 Введите город для удаления из избранного:",
        "fav_added": "✅ Город добавлен в избранное!",
        "fav_add_fail": "❌ Не удалось добавить (лимит 50 или дубликат).",
        "fav_del_ok": "✅ Город удалён из избранного.",
        "fav_del_fail": "❌ Такого города нет в избранном.",
        "no_city": "Нажмите '🏙 Город' и введите название.",
        "weather_err": "❌ Не удалось получить погоду. Попробуйте позже.",
        "unknown": "Не знаю такой команды. Нажмите '❓ Помощь'.",
        "main_menu": "🏠 Главное меню:",
        "choose_lang": "🌐 Выберите язык:",
        "lang_set": "✅ Язык переключён на русский.",
        "back": "⬅ Назад",
        "time_btn": "⏰ Время",
        "status_btn": "🔔 Статус: {st}",
        "help": ("🌤 WeatherTomBot для ВКонтакте\n\n"
                 "🌤 Погода сейчас — текущая погода\n"
                 "📅 Прогноз 5 дней — прогноз по дням\n"
                 "⭐ Избранное — ваши города (добавить/удалить)\n"
                 "🏙 Город — установить город (следующим сообщением)\n"
                 "🔔 Оповещения — статус, время и тумблеры\n"
                 "🌐 Язык — выбор языка интерфейса\n"
                 "❓ Помощь — это сообщение"),
        "fields": {"rain": "💧 Дождь", "wind": "💨 Ветер", "frost": "❄️ Мороз", "heat": "🔥 Жара"},
        "btn": {"weather": "🌤 Погода сейчас", "forecast": "📅 Прогноз 5 дней",
                "favorites": "⭐ Избранное", "city": "🏙 Город",
                "notifications": "🔔 Оповещения", "lang": "🌐 Язык", "help": "❓ Помощь"},
    },
    "en": {
        "enter_city": "✏️ Enter the city name in one message:",
        "city_saved": "✅ City saved: {city}",
        "enter_time": "⏰ Enter time as HH:MM (e.g. 08:00):",
        "time_saved": "✅ Notification time: {time}",
        "time_bad": "❌ Wrong format. Example: 08:00",
        "fav_enter_add": "➕ Enter a city to add to favorites:",
        "fav_enter_del": "🗑 Enter a city to remove from favorites:",
        "fav_added": "✅ City added to favorites!",
        "fav_add_fail": "❌ Could not add (limit 50 or duplicate).",
        "fav_del_ok": "✅ City removed from favorites.",
        "fav_del_fail": "❌ This city is not in favorites.",
        "no_city": "Press '🏙 City' and enter a name.",
        "weather_err": "❌ Could not get weather. Try again later.",
        "unknown": "Unknown command. Press '❓ Help'.",
        "main_menu": "🏠 Main menu:",
        "choose_lang": "🌐 Choose your language:",
        "lang_set": "✅ Language switched to English.",
        "back": "⬅ Back",
        "time_btn": "⏰ Time",
        "status_btn": "🔔 Status: {st}",
        "help": ("🌤 WeatherTomBot for VK\n\n"
                 "🌤 Current weather — weather right now\n"
                 "📅 5-day forecast — day-by-day forecast\n"
                 "⭐ Favorites — your cities (add/remove)\n"
                 "🏙 City — set your city (next message)\n"
                 "🔔 Notifications — status, time and toggles\n"
                 "🌐 Language — choose interface language\n"
                 "❓ Help — this message"),
        "fields": {"rain": "💧 Rain", "wind": "💨 Wind", "frost": "❄️ Frost", "heat": "🔥 Heat"},
        "btn": {"weather": "🌤 Current weather", "forecast": "📅 5-day forecast",
                "favorites": "⭐ Favorites", "city": "🏙 City",
                "notifications": "🔔 Notifications", "lang": "🌐 Language", "help": "❓ Help"},
    },
}

def _m(lang, key, **kw):
    d = MSG.get(lang, MSG["en"])
    s = d.get(key) or MSG["en"].get(key) or MSG["ru"].get(key) or key
    return s.format(**kw) if kw else s

def _mbtn(lang, key):
    d = MSG.get(lang, MSG["en"])["btn"]
    return d.get(key) or MSG["ru"]["btn"].get(key) or key

def _t(lang, key, default, **kw):
    for lg in (lang, "ru"):
        val = TEXTS.get(lg, {}).get(key)
        if val:
            try:
                return val.format(**kw) if kw else val
            except Exception:
                return val
    return default.format(**kw) if kw else default

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

def _btn(label, payload_dict, color="primary"):
    return {"action": {"type": "text", "label": label[:40],
                       "payload": json.dumps(payload_dict, ensure_ascii=False)},
            "color": color}

def vk_menu_keyboard(lang="ru"):
    b = lambda k, c: _btn(_mbtn(lang, k), {"cmd": c})
    return {"one_time": False, "inline": False, "buttons": [
        [b("weather", "weather"), b("forecast", "forecast")],
        [b("favorites", "favorites"), b("city", "city")],
        [b("notifications", "notifications"), b("lang", "lang")],
        [b("help", "help")],
    ]}

def _lang_keyboard():
    rows = []
    codes = [c for c in LANG_NAMES if c in TEXTS] or ["ru", "en"]
    row = []
    for c in codes:
        row.append(_btn(LANG_NAMES[c], {"cmd": "lang_set", "lang": c}))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([_btn(MSG["ru"]["back"], {"cmd": "back"})])
    return {"one_time": False, "inline": False, "buttons": rows}

TZ_LIST = [
    ("Europe/Kaliningrad", "🕐 Калининград"),
    ("Europe/Moscow", "🕐 Москва"),
    ("Europe/Samara", "🕐 Самара"),
    ("Asia/Yekaterinburg", "🕐 Екатеринбург"),
    ("Asia/Novosibirsk", "🕐 Новосибирск"),
    ("Asia/Krasnoyarsk", "🕐 Красноярск"),
    ("Asia/Vladivostok", "🕐 Владивосток"),
    ("UTC", "🕐 UTC"),
]

def _tz_keyboard(lang):
    rows = []
    row = []
    for code, label in TZ_LIST:
        row.append(_btn(label, {"cmd": "tz_set", "zone": code}))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([_btn(_m(lang, "back"), {"cmd": "back"})])
    return {"one_time": False, "inline": False, "buttons": rows}

def _notif_keyboard(uid, lang):
    p = notification_prefs(uid)
    if not isinstance(p, dict):
        p = {}
    on = lambda k: "✅" if p.get(k, True) else "❌"
    f = _m(lang, "fields")
    st = "✅" if p.get("enabled") else "❌"
    return {"one_time": False, "inline": False, "buttons": [
        [_btn(_m(lang, "status_btn", st=st), {"cmd": "notif_toggle"}), _btn(_m(lang, "time_btn"), {"cmd": "notif_time"})],
        [_btn(f"{f['rain']}: {on('rain')}", {"cmd": "notif_rain"}), _btn(f"{f['wind']}: {on('wind')}", {"cmd": "notif_wind"})],
        [_btn(f"{f['frost']}: {on('frost')}", {"cmd": "notif_frost"}), _btn(f"{f['heat']}: {on('heat')}", {"cmd": "notif_heat"})],
        [_btn("🌍 Часовой пояс", {"cmd": "notif_tz"})],
        [_btn(_m(lang, "back"), {"cmd": "back"})],
    ]}

def _fav_keyboard(uid, lang):
    labels = {"ru": ("➕ Добавить", "🗑 Удалить"), "en": ("➕ Add", "🗑 Delete")}
    la, ld = labels.get(lang, labels["ru"])
    favs = favorites(uid)[:8]
    rows = []
    row = []
    for city in favs:
        row.append(_btn(city, {"cmd": "city_pick", "city": city}))
        if len(row) == 2:
            rows.append(row); row = []
    if row:
        rows.append(row)
    rows.append([_btn(la, {"cmd": "fav_add"}), _btn(ld, {"cmd": "fav_del"})])
    rows.append([_btn(_m(lang, "back"), {"cmd": "back"})])
    return {"one_time": False, "inline": False, "buttons": rows}

def _show_weather(uid, peer_id, lang):
    city = get_user_city(uid)
    if not city:
        vk_send(peer_id, vk_strip_md(_t(lang, "cities_empty", "")) + "\n" + _m(lang, "no_city"), vk_menu_keyboard(lang))
        return
    w = get_weather_aggregated(city, lang)
    if not w or "error" in w:
        vk_send(peer_id, _m(lang, "weather_err"), vk_menu_keyboard(lang))
        return
    vk_send(peer_id, vk_strip_md(format_weather_text(uid, w)), vk_menu_keyboard(lang))

def _show_forecast(uid, peer_id, lang):
    city = get_user_city(uid)
    if not city:
        vk_send(peer_id, vk_strip_md(_t(lang, "cities_empty", "")) + "\n" + _m(lang, "no_city"), vk_menu_keyboard(lang))
        return
    f = get_forecast_aggregated(city, 5, lang)
    vk_send(peer_id, vk_strip_md(format_forecast_text(uid, f, city, 5)), vk_menu_keyboard(lang))

def _show_favorites(uid, peer_id, lang):
    favs = favorites(uid)
    listing = "\n".join(f"📍 {x}" for x in favs) if favs else vk_strip_md(_t(lang, "cities_empty", "—"))
    text = vk_strip_md(_t(lang, "cities_title", "⭐ Favorites")) + "\n\n" + listing + "\n\n" + vk_strip_md(_t(lang, "cities_choose", ""))
    vk_send(peer_id, text, _fav_keyboard(uid, lang))

def _show_notifications(uid, peer_id, lang):
    p = notification_prefs(uid)
    if not isinstance(p, dict):
        p = {}
    status = _t(lang, "notification_enabled", "Enabled") if p.get("enabled") else _t(lang, "notification_disabled", "Disabled")
    city = p.get("city") or get_user_city(uid) or "—"
    text = _t(lang, "notification_settings",
              "Notifications: {status}\nTime: {time}\nCity: {city}",
              status=status,
              rain="✅" if p.get("rain", True) else "❌",
              wind="✅" if p.get("wind", True) else "❌",
              frost="✅" if p.get("frost", True) else "❌",
              heat="✅" if p.get("heat", True) else "❌",
              time=p.get("time", "08:00"), city=city)
    vk_send(peer_id, vk_strip_md(text), _notif_keyboard(uid, lang))

def _show_help(uid, peer_id, lang):
    vk_send(peer_id, _m(lang, "help"), vk_menu_keyboard(lang))

def _handle_state(uid, peer_id, lang, text):
    mode = _get_state(uid)
    if not mode:
        return False
    _clear_state(uid)
    try:
        if mode == "city":
            save_user_city(uid, text)
            vk_send(peer_id, _m(lang, "city_saved", city=text), vk_menu_keyboard(lang))
        elif mode == "time":
            m = re.match(r"^(\d{1,2}):(\d{2})$", text.strip())
            if m and 0 <= int(m.group(1)) <= 23 and 0 <= int(m.group(2)) <= 59:
                t = f"{int(m.group(1)):02d}:{int(m.group(2)):02d}"
                set_notification_prefs(uid, time=t)
                p = notification_prefs(uid)
                saved = p.get("time") if isinstance(p, dict) else "?"
                logger.info(f"VK time save: requested={t} stored={saved}")
                vk_send(peer_id, _m(lang, "time_saved", time=saved), _notif_keyboard(uid, lang))
            else:
                vk_send(peer_id, _m(lang, "time_bad"), _notif_keyboard(uid, lang))
        elif mode == "fav_add":
            ok = add_favorite(uid, text.strip())
            vk_send(peer_id, _m(lang, "fav_added") if ok else _m(lang, "fav_add_fail"), _fav_keyboard(uid, lang))
        elif mode == "fav_del":
            ok = remove_favorite(uid, text.strip())
            vk_send(peer_id, _m(lang, "fav_del_ok") if ok else _m(lang, "fav_del_fail"), _fav_keyboard(uid, lang))
        return True
    except Exception as e:
        logger.error(f"VK state error: {e}", exc_info=True)
        vk_send(peer_id, "❌ Техническая ошибка при сохранении. Попробуйте ещё раз.", vk_menu_keyboard(lang))
        return True

def _route(uid, peer_id, lang, cmd, text):
    low = (text or "").strip().lower()
    if cmd == "weather" or low in ("погода", "weather", "current weather"):
        _show_weather(uid, peer_id, lang)
    elif cmd == "forecast" or low in ("прогноз", "forecast", "5-day forecast"):
        _show_forecast(uid, peer_id, lang)
    elif cmd == "favorites" or low in ("избранное", "favorites", "favourites"):
        _show_favorites(uid, peer_id, lang)
    elif cmd == "city" or low in ("город", "city"):
        _set_state(uid, "city")
        vk_send(peer_id, _m(lang, "enter_city"), vk_menu_keyboard(lang))
    elif cmd == "notifications" or low in ("оповещения", "notifications", "alerts"):
        _show_notifications(uid, peer_id, lang)
    elif cmd == "lang" or low in ("язык", "language", "lang"):
        vk_send(peer_id, _m(lang, "choose_lang"), _lang_keyboard())
    elif cmd == "lang_set":
        pass
    elif cmd == "help" or low in ("помощь", "help", "/start", "start", "старт", ""):
        _show_help(uid, peer_id, lang)
    elif cmd == "back":
        vk_send(peer_id, _m(lang, "main_menu"), vk_menu_keyboard(lang))
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
        vk_send(peer_id, _m(lang, "enter_time"), vk_menu_keyboard(lang))
    elif cmd == "notif_tz":
        vk_send(peer_id, "🌍 Выберите часовой пояс:", _tz_keyboard(lang))
    elif cmd == "fav_add":
        _set_state(uid, "fav_add")
        vk_send(peer_id, _m(lang, "fav_enter_add"), vk_menu_keyboard(lang))
    elif cmd == "fav_del":
        _set_state(uid, "fav_del")
        vk_send(peer_id, _m(lang, "fav_enter_del"), vk_menu_keyboard(lang))
    else:
        vk_send(peer_id, _m(lang, "unknown"), vk_menu_keyboard(lang))

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
        extra = {}
        if payload:
            try:
                pd = json.loads(payload)
                cmd = pd.get("cmd")
                extra = pd
            except Exception:
                cmd = None
        if cmd == "lang_set":
            new = extra.get("lang", "ru")
            if new in TEXTS:
                set_user_lang(uid, new)
                vk_send(peer_id, _m(new, "lang_set"), vk_menu_keyboard(new))
            return
        if cmd == "tz_set":
            zone = extra.get("zone")
            if zone:
                set_notification_prefs(uid, timezone=zone)
                vk_send(peer_id, f"✅ Часовой пояс: {zone}", _notif_keyboard(uid, lang))
            return
        if cmd == "city_pick":
            city = extra.get("city")
            if city:
                save_user_city(uid, city)
                vk_send(peer_id, _m(lang, "city_saved", city=city), vk_menu_keyboard(lang))
            return
        if cmd:
            # Нажата кнопка — отменяем режим ожидания ввода
            _clear_state(uid)
            _route(uid, peer_id, lang, cmd, text)
            return
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
