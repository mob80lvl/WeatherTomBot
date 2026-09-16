"""VK Bot адаптер для WeatherTomBot."""
import os, json, threading, requests, logging, time
from flask import request
from dotenv import load_dotenv

load_dotenv()
VK_TOKEN = os.getenv("VK_TOKEN", "")
VK_GROUP_ID = os.getenv("VK_GROUP_ID", "")
VK_SECRET = os.getenv("VK_SECRET", "")
VK_CONFIRM = os.getenv("VK_CONFIRM", "")

logger = logging.getLogger(__name__)

# Импорт функций бота
try:
    from storage import get_user_city, save_user_city, get_user_lang
    from weather import get_weather_aggregated, get_forecast_aggregated, format_weather_text
    from features import favorites, notification_prefs
    logger.info("✅ VK bot: imports loaded")
except Exception as e:
    logger.error(f"VK bot: import error: {e}")

# Защита от дублей
recent_events = set()
MAX_EVENTS = 200

def vk_send(peer_id, message, keyboard=None):
    """Отправка сообщения в VK."""
    if not VK_TOKEN:
        logger.error("VK_TOKEN not set")
        return None
    
    params = {
        "peer_id": peer_id,
        "message": message[:4096],  # VK лимит
        "random_id": int(time.time() * 1000) % 2147483647,
        "access_token": VK_TOKEN,
        "v": "5.199"
    }
    if keyboard:
        params["keyboard"] = json.dumps(keyboard, ensure_ascii=False)
    
    try:
        resp = requests.get("https://api.vk.com/method/messages.send", params=params, timeout=10)
        result = resp.json()
        print(f"[VK DEBUG] send to {peer_id}: {json.dumps(result, ensure_ascii=False)[:500]}", flush=True)
        if "error" in result:
            logger.error(f"VK send error: {result['error']}")
        return result
    except Exception as e:
        logger.error(f"VK send exception: {e}")
        return None

def vk_strip_md(text):
    """Убирает Markdown-разметку для VK."""
    if not text:
        return ""
    return text.replace("*", "").replace("_", "").replace("`", "")

def vk_menu_keyboard():
    """Создаёт главное меню."""
    def btn(label, cmd):
        return {
            "action": {
                "type": "text",
                "label": label,
                "payload": json.dumps({"cmd": cmd}, ensure_ascii=False)
            },
            "color": "primary"
        }
    return {
        "one_time": False,
        "inline": False,
        "buttons": [
            [btn("🌤 Погода сейчас", "weather"), btn("📅 Прогноз 5 дней", "forecast")],
            [btn("⭐ Избранное", "favorites"), btn("🏙 Город", "city")],
            [btn("🔔 Оповещения", "notifications"), btn("❓ Помощь", "help")]
        ]
    }

def vk_process_event(event):
    """Обработка события в фоновом потоке."""
    try:
        event_type = event.get("type")
        obj = event.get("object", {})
        message = obj.get("message", {})
        
        from_id = message.get("from_id", 0)
        peer_id = message.get("peer_id", 0)
        uid = f"vk_{from_id}"
        
        # Получаем текст и payload
        text = message.get("text", "").strip()
        payload = message.get("payload")
        
        cmd = None
        if payload:
            try:
                cmd = json.loads(payload).get("cmd")
            except:
                pass
        
        # Роутер команд
        if cmd == "weather" or text.lower() in ["🌤 погода сейчас", "погода", "weather"]:
            city = get_user_city(uid)
            if not city:
                vk_send(peer_id, "❌ Город не установлен. Нажмите '🏙 Город' и введите название.", vk_menu_keyboard())
                return
            
            lang = get_user_lang(uid) or "ru"
            w = get_weather_aggregated(city, lang)
            if not w or "error" in w:
                vk_send(peer_id, "❌ Не удалось получить погоду. Попробуйте позже.", vk_menu_keyboard())
                return
            
            formatted = format_weather_text(uid, w)
            text_clean = vk_strip_md(formatted)
            vk_send(peer_id, text_clean, vk_menu_keyboard())
        
        elif cmd == "forecast" or text.lower() in ["📅 прогноз 5 дней", "прогноз", "forecast"]:
            city = get_user_city(uid)
            if not city:
                vk_send(peer_id, "❌ Город не установлен.", vk_menu_keyboard())
                return
            
            lang = get_user_lang(uid) or "ru"
            f = get_forecast_aggregated(city, 5, lang)
            if not f or "error" in f:
                vk_send(peer_id, "❌ Не удалось получить прогноз.", vk_menu_keyboard())
                return
            
            # Форматируем прогноз
            text = f"📅 Прогноз на 5 дней для {city}:\n\n"
            for day in f.get("daily", [])[:5]:
                date = day.get("date", "—")
                temp_max = day.get("temp_max", "—")
                temp_min = day.get("temp_min", "—")
                desc = day.get("description", "—")
                text += f"🗓 {date}\n🌡 {temp_min}°...{temp_max}°C\n☁️ {desc}\n\n"
            
            vk_send(peer_id, vk_strip_md(text), vk_menu_keyboard())
        
        elif cmd == "favorites" or text.lower() in ["⭐ избранное", "избранное", "favorites"]:
            favs = favorites(uid)
            if not favs:
                vk_send(peer_id, "📭 Избранное пусто.", vk_menu_keyboard())
                return
            
            text = "⭐ Ваши города:\n\n" + "\n".join(f"📍 {c}" for c in favs)
            vk_send(peer_id, text, vk_menu_keyboard())
        
        elif cmd == "city" or text.lower() in ["🏙 город", "город", "city"]:
            vk_send(peer_id, "✏️ Введите название города (следующим сообщением):", vk_menu_keyboard())
            # В упрощённой версии не реализуем state machine
            # В реальности нужно сохранить состояние "ожидание_города" для uid
        
        elif cmd == "notifications" or text.lower() in ["🔔 оповещения", "оповещения", "notifications"]:
            prefs = notification_prefs(uid)
            enabled = prefs.get("enabled") if isinstance(prefs, dict) else False
            time = prefs.get("time", "08:00") if isinstance(prefs, dict) else "08:00"
            status = "✅ Включены" if enabled else "❌ Выключены"
            text = f"🔔 Оповещения: {status}\n⏰ Время: {time}"
            vk_send(peer_id, text, vk_menu_keyboard())
        
        elif cmd == "help" or text.lower() in ["❓ помощь", "помощь", "help", "/start", "старт", "start"]:
            text = ("🌤 WeatherTomBot для ВКонтакте\n\n"
                   "Доступные команды:\n"
                   "🌤 Погода сейчас — текущая погода\n"
                   "📅 Прогноз 5 дней — прогноз на неделю\n"
                   "⭐ Избранное — ваши города\n"
                   "🏙 Город — установить город\n"
                   "🔔 Оповещения — статус уведомлений\n"
                   "❓ Помощь — это сообщение")
            vk_send(peer_id, text, vk_menu_keyboard())
        
        else:
            # Неизвестная команда или введён город (упрощённо)
            if text and len(text) > 2 and not text.startswith("/"):
                # Попытка сохранить как город (упрощённая логика)
                save_user_city(uid, text)
                vk_send(peer_id, f"✅ Город '{text}' сохранён!", vk_menu_keyboard())
            else:
                vk_send(peer_id, "Неизвестная команда. Нажмите '❓ Помощь'.", vk_menu_keyboard())
    
    except Exception as e:
        logger.error(f"VK process error: {e}", exc_info=True)

def vk_webhook():
    """Flask-маршрут для VK Callback API."""
    data = request.json
    if not data:
        return "no data", 400
    
    # Проверка секрета
    secret = data.get("secret")
    if VK_SECRET and secret != VK_SECRET:
        logger.warning(f"VK: неверный secret от {request.remote_addr}")
        return "forbidden", 403
    
    event_type = data.get("type")
    
    # Confirmation (специальный случай — возвращаем строку сразу)
    if event_type == "confirmation":
        logger.info("VK: confirmation request")
        return VK_CONFIRM
    
    # Антидубль
    event_id = data.get("object", {}).get("id") or data.get("object", {}).get("message", {}).get("id")
    if event_id and event_id in recent_events:
        logger.info(f"VK: дубль события {event_id}")
        return "ok"
    
    if event_id:
        recent_events.add(event_id)
        if len(recent_events) > MAX_EVENTS:
            recent_events.pop()
    
    # Фоновая обработка (возвращаем "ok" мгновенно)
    threading.Thread(target=vk_process_event, args=(data,), daemon=True).start()
    
    return "ok"

def register_vk_routes(app):
    """Регистрация маршрута в Flask."""
    app.add_url_rule("/vk_webhook", "vk_webhook", vk_webhook, methods=["POST"])
    logger.info("✅ VK webhook registered at /vk_webhook")
