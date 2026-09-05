#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
from datetime import datetime, timedelta
from flask import Flask, request, session, redirect, url_for, flash, render_template_string
from functools import wraps
from dotenv import load_dotenv

load_dotenv()

from config import *




from texts import TEXTS, T, LANGUAGES, b2b_name, b2b_features, api_language

# ============================================================
#  ТЕКСТЫ НА ВСЕХ ЯЗЫКАХ
# ============================================================

# ============================================================
#  НАСТРОЙКА ЛОГГЕРА
# ============================================================

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
# ============================================================
#  ФОНОВЫЙ ПЛАНИРОВЩИК (автопостинг каналов и уведомления)
# ============================================================
import threading as _threading
import time as _time

def _scheduler_loop():
    """Каждую минуту вызывает scheduled_job() для автопостинга и уведомлений."""
    while True:
        try:
            now = datetime.now()
            sleep_sec = 60 - now.second - now.microsecond / 1e6
            _time.sleep(max(sleep_sec, 1) + 0.5)
            if advanced_features:
                result = advanced_features.scheduled_job()
                if result and (result.get("notifications") or result.get("channels")):
                    logger.info(f"SCHEDULER: {result}")
        except Exception as e:
            logger.error(f"SCHEDULER ошибка: {e}")
            _time.sleep(30)

_scheduler_thread = _threading.Thread(target=_scheduler_loop, daemon=True, name="weather-scheduler")
_scheduler_thread.start()
logger.info("✅ Фоновый планировщик запущен")

app.secret_key = SECRET_KEY

# ============================================================
#  ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ТЕКСТА
# ============================================================






from storage import _clear_b2b_entitlement, _clear_user_state, _get_user_state, _load_json_file, _load_user_states, _save_json_file, _set_user_state, _team_plan, get_current_plan, get_notification_status, get_user_b2b_type, get_user_city, get_user_lang, get_user_subscription, is_user_subscribed, save_user_city, set_notification_status, set_user_lang, set_user_subscription


# ============================================================
#  РАБОТА С ПОЛЬЗОВАТЕЛЯМИ (JSON)
# ============================================================















# ============================================================
#  ФУНКЦИИ ПОГОДЫ (СОКРАЩЕННЫЕ)
# ============================================================

from weather import convert_pressure_to_mmhg, format_forecast_text, format_tomorrow_forecast_text, format_weather_text, get_agri_forecast, get_clothing_recommendations, get_construction_forecast, get_forecast_aggregated, get_moon_phase, get_sunrise_sunset, get_tomorrow_detailed_forecast, get_tourism_forecast, get_uv_level, get_weather_aggregated, get_weather_icon, get_weather_statistics, wind_deg_to_direction













# ============================================================
#  МУЛЬТИЯЗЫЧНЫЕ РЕКОМЕНДАЦИИ ПО ОДЕЖДЕ
# ============================================================



from formatting import format_help_text, format_subscription_status, format_trip_forecast_text


# ============================================================
#  КЛАВИАТУРА (МУЛЬТИЯЗЫЧНАЯ)
# ============================================================





def _paywall(chat_id, required_plan="premium"):
    lang = get_user_lang(chat_id)
    if required_plan == "business":
        text = T(lang, "business_required")
        keyboard = {"keyboard": [[T(lang, "btn_business_sub")], [T(lang, "btn_back")]], "resize_keyboard": True}
    else:
        text = T(lang, "premium_required_paywall")
        keyboard = {"keyboard": [[T(lang, "btn_personal"), T(lang, "btn_business_sub")], [T(lang, "btn_back")]], "resize_keyboard": True}
    send_message(chat_id, text, keyboard)

from keyboards import get_city_keyboard, get_language_keyboard, get_main_keyboard, get_notification_keyboard, get_payment_keyboard, get_team_main_keyboard, get_white_label_keyboard


ROLE_ICONS = {"owner": "👑", "admin": "🛠", "editor": "✏️", "viewer": "👁"}


# ============================================================
#  ОТПРАВКА СООБЩЕНИЙ И ПЛАТЕЖИ
# ============================================================

def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return None

def send_photo(chat_id, photo_path, caption=""):
    """Send a local image to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            response = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": photo},
                timeout=60,
            )
        if response.status_code != 200:
            logger.error(f"Ошибка отправки фото: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}", exc_info=True)
        return None

def send_long_text(chat_id, text, keyboard=None):
    """Отправляет длинный текст частями (лимит Telegram 4096)."""
    limit = 4000
    if len(text) <= limit:
        send_message(chat_id, text, keyboard)
        return
    parts = []
    current = ""
    for block in text.split("\n\n"):
        if len(current) + len(block) + 2 > limit:
            if current:
                parts.append(current)
            if len(block) > limit:
                for line in block.split("\n"):
                    if len(current) + len(line) + 1 > limit:
                        if current:
                            parts.append(current)
                        current = line
                    else:
                        current = current + "\n" + line if current else line
            else:
                current = block
        else:
            current = current + "\n\n" + block if current else block
    if current:
        parts.append(current)
    for i, part in enumerate(parts):
        send_message(chat_id, part, keyboard if i == len(parts) - 1 else None)



def _show_cities(chat_id):
    lang=get_user_lang(chat_id); favs=advanced_features.favorites(chat_id) if advanced_features else []
    listing="\n".join(f"📍 *{x}*" for x in favs) if favs else T(lang,"cities_empty")
    send_message(chat_id,T(lang,"cities_title")+"\n\n"+listing+"\n\n"+T(lang,"cities_choose"),get_city_keyboard(chat_id))

def _show_notification_settings(chat_id):
    lang=get_user_lang(chat_id)
    prefs=advanced_features.notification_prefs(chat_id) if advanced_features else {"enabled":get_notification_status(chat_id),"time":"08:00","frequency":"daily","rain":True,"wind":True,"frost":True,"heat":True}
    status=T(lang,"notification_enabled") if prefs.get("enabled") else T(lang,"notification_disabled")
    freq=prefs.get("frequency","daily")
    freq_names={"daily":T(lang,"notification_freq_daily"),"weekly":T(lang,"notification_freq_weekly"),"weekdays":T(lang,"notification_freq_weekdays"),"weekends":T(lang,"notification_freq_weekends")}
    freq_display=freq_names.get(freq,T(lang,"notification_freq_daily"))
    city=prefs.get("city") or get_user_city(chat_id) or "—"
    text=T(lang,"notification_settings",status=status,rain="✅" if prefs.get("rain",True) else "❌",wind="✅" if prefs.get("wind",True) else "❌",frost="✅" if prefs.get("frost",True) else "❌",heat="✅" if prefs.get("heat",True) else "❌",time=prefs.get("time","08:00"),city=city)
    send_message(chat_id,text,get_notification_keyboard(chat_id))


def create_invoice(chat_id, price, b2b_type=None, plan=None):
    lang = get_user_lang(chat_id)
    if b2b_type:
        b2b_info = B2B_TYPES.get(b2b_type, {})
        name = b2b_name(lang, b2b_type)
        title = f"{b2b_info.get('icon', '🏢')} {name}"
        description = f"{name}\n\n" + "\n".join(b2b_features(lang, b2b_type))
        payload = f"b2b_{b2b_type}"
        if plan is None:
            plan = "business"
    else:
        title = T(lang, "invoice_title_personal")
        description = T(lang, "invoice_description_personal")
        payload = "subscription_premium" if plan != "business" else "subscription_business"

    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendInvoice"
    payload_data = {
        "chat_id": chat_id,
        "title": title,
        "description": description,
        "payload": payload,
        "provider_token": "",
        "currency": "XTR",
        "prices": [{"label": T(lang, "invoice_month"), "amount": price}],
        "start_parameter": "subscription"
    }
    try:
        response = requests.post(url, json=payload_data, timeout=30)
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка создания счёта: {e}")
        return None

# ============================================================
#  ВЕБХУК
# ============================================================


def answer_callback_query(callback_query_id, text=None):
    """Отвечает на callback_query чтобы убрать 'часики' у пользователя."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Ошибка answer_callback_query: {e}")


@app.route('/webhook', methods=['POST'])
def webhook():
    # Защита webhook секретным токеном
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if webhook_secret:
        secret_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if secret_header != webhook_secret:
            logger.warning(f"Несанкционированный доступ к webhook! IP: {request.remote_addr}")
            return "Forbidden", 403

    try:
        data = request.get_json()
        if not data:
            return "no data", 400

        logger.info(f"Получено: {json.dumps(data, ensure_ascii=False)[:200]}")

        if data.get('pre_checkout_query'):
            pre_checkout_query = data['pre_checkout_query']
            answer_url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerPreCheckoutQuery"
            payload = pre_checkout_query.get('payload', '')
            b2b_type = None
            if payload.startswith('b2b_'):
                b2b_type = payload.replace('b2b_', '')
            plan = "business" if (b2b_type or payload == "subscription_business") else "premium"
            try:
                requests.post(answer_url, json={
                    "pre_checkout_query_id": pre_checkout_query['id'],
                    "ok": True
                }, timeout=30)
            except Exception as e:
                logger.error(f"Ошибка подтверждения оплаты: {e}")
            return "ok", 200

        if data.get('message', {}).get('successful_payment'):
            chat_id = data['message']['chat']['id']
            lang = get_user_lang(chat_id)
            payload = data['message']['successful_payment'].get('payload', '')
            b2b_type = None
            if payload.startswith('b2b_'):
                b2b_type = payload.replace('b2b_', '')
            plan = "business" if (b2b_type or payload == "subscription_business") else "premium"
            days = SUBSCRIPTION_DAYS
            subscription_ok = set_user_subscription(chat_id, days, b2b_type=b2b_type, plan=plan)
            if not subscription_ok:
                logger.error(f"PAYMENT: subscription activation FAILED user={chat_id} payload={payload!r}")
                return "ok", 200
            keyboard = get_main_keyboard(chat_id)
            if b2b_type or plan == "business":
                plan_info = B2B_TYPES.get(b2b_type or "business", {})
                plan_features = "\n".join(b2b_features(lang, b2b_type))
                success_text = (
                    T(lang, "payment_success", days=days) + "\n\n"
                    f"{plan_info.get('icon', '🏢')} *{b2b_name(lang, b2b_type)}*\n\n"
                    f"{T(lang, 'included')}\n{plan_features}"
                )
            else:
                success_text = (
                    T(lang, "payment_success", days=days) + "\n\n" +
                    T(lang, "included") + "\n" + T(lang, "personal_features") + "\n📢 " + T(lang, "btn_autopost") + "\n🔑 " + T(lang, "btn_api")
                )
            send_message(chat_id, success_text, keyboard)
            return "ok", 200

        # Обработка callback_query (inline-кнопки)
        callback_query = data.get('callback_query')
        if callback_query:
            callback_id = callback_query['id']
            chat_id = callback_query['message']['chat']['id']
            data_str = callback_query['data']
            lang = get_user_lang(chat_id)
            
            # Ответ на callback чтобы убрать "часики"
            answer_callback_query(callback_id)
            
            # ===== КОМАНДЫ (inline-кнопки) =====
            if data_str == "team_list":
                if get_current_plan(chat_id) != "business":
                    _paywall(chat_id, "business")
                else:
                    teams = advanced_features.owned_teams(chat_id) if advanced_features else {}
                    if not teams:
                        kb = {"inline_keyboard": [
                            [{"text": T(lang, "team_btn_create"), "callback_data": "team_create"}],
                            [{"text": T(lang, "team_btn_back"), "callback_data": "team_menu_open"}]]}
                        send_message(chat_id, T(lang, "team_list_empty"), kb)
                    else:
                        rows = [[{"text": f"👥 {t.get('name', tid)} ({len(t.get('members', {}))})", "callback_data": f"team_view_{tid}"}] for tid, t in teams.items()]
                        rows.append([{"text": T(lang, "team_btn_create"), "callback_data": "team_create"}])
                        rows.append([{"text": T(lang, "team_btn_back"), "callback_data": "team_menu_open"}])
                        send_message(chat_id, T(lang, "team_list_title"), {"inline_keyboard": rows})
                return "ok", 200
            elif data_str == "team_menu_open":
                if get_current_plan(chat_id) != "business":
                    _paywall(chat_id, "business")
                else:
                    send_message(chat_id, T(lang, "team_menu"), get_team_main_keyboard(lang))
                return "ok", 200
            elif data_str == "team_create":
                if get_current_plan(chat_id) != "business":
                    _paywall(chat_id, "business")
                else:
                    _set_user_state(chat_id, "team_create")
                    send_message(chat_id, T(lang, "team_create_prompt"))
                return "ok", 200
            elif data_str == "team_main_back":
                send_message(chat_id, T(lang, "back_main"), get_main_keyboard(chat_id))
                return "ok", 200
            elif data_str.startswith("team_view_"):
                tid = data_str[len("team_view_"):]
                t = advanced_features.get_team(tid) if advanced_features else None
                if not t or str(t.get("owner")) != str(chat_id):
                    send_message(chat_id, T(lang, "team_list_empty"))
                else:
                    lines = [T(lang, "team_member", icon=ROLE_ICONS.get(r, "👤"), uid=mid, role=r) for mid, r in t.get("members", {}).items()]
                    text = T(lang, "team_info_title", name=t.get("name"), tid=tid, created=str(t.get("created_at", "-"))[:10], count=len(t.get("members", {})), members="\n".join(lines))
                    kb = {"inline_keyboard": [
                        [{"text": T(lang, "team_btn_add"), "callback_data": f"team_add_{tid}"}],
                        [{"text": T(lang, "team_btn_remove"), "callback_data": f"team_rm_{tid}"}],
                        [{"text": T(lang, "team_btn_delete"), "callback_data": f"team_del_{tid}"}],
                        [{"text": T(lang, "team_back"), "callback_data": "team_list"}]]}
                    send_message(chat_id, text, kb)
                return "ok", 200
            elif data_str.startswith("team_add_"):
                tid = data_str[len("team_add_"):]
                t = advanced_features.get_team(tid) if advanced_features else None
                if not t or str(t.get("owner")) != str(chat_id):
                    send_message(chat_id, T(lang, "team_list_empty"))
                else:
                    _set_user_state(chat_id, "team_add_member", team_id=tid)
                    send_message(chat_id, T(lang, "team_add_user_prompt", name=t.get("name")))
                return "ok", 200
            elif data_str.startswith("team_rm_"):
                rest = data_str[len("team_rm_"):]
                if "_" in rest:
                    tid, mid = rest.split("_", 1)
                    ok = advanced_features.remove_team_member(chat_id, tid, mid) if advanced_features else False
                    kb = {"inline_keyboard": [[{"text": T(lang, "team_back"), "callback_data": f"team_view_{tid}"}]]}
                    send_message(chat_id, T(lang, "team_member_removed") if ok else T(lang, "team_remove_failed"), kb)
                else:
                    tid = rest
                    t = advanced_features.get_team(tid) if advanced_features else None
                    rows = [[{"text": f"{ROLE_ICONS.get(r, '👤')} {mid}", "callback_data": f"team_rm_{tid}_{mid}"}] for mid, r in (t.get("members", {}) if t else {}).items() if mid != str(chat_id)]
                    if not rows:
                        send_message(chat_id, T(lang, "team_remove_failed"))
                    else:
                        rows.append([{"text": T(lang, "team_back"), "callback_data": f"team_view_{tid}"}])
                        send_message(chat_id, T(lang, "team_btn_remove"), {"inline_keyboard": rows})
                return "ok", 200
            elif data_str.startswith("team_del_"):
                rest = data_str[len("team_del_"):]
                if rest.startswith("yes_"):
                    tid = rest[len("yes_"):]
                    ok = advanced_features.delete_team(chat_id, tid) if advanced_features else False
                    send_message(chat_id, T(lang, "team_deleted") if ok else T(lang, "team_remove_failed"))
                else:
                    tid = rest
                    t = advanced_features.get_team(tid) if advanced_features else None
                    if t:
                        yes_txt = "✅ Да, удалить" if lang == "ru" else "✅ Yes, delete"
                        no_txt = "❌ Отмена" if lang == "ru" else "❌ Cancel"
                        kb = {"inline_keyboard": [
                            [{"text": yes_txt, "callback_data": f"team_del_yes_{tid}"}],
                            [{"text": no_txt, "callback_data": f"team_view_{tid}"}]]}
                        send_message(chat_id, T(lang, "team_delete_confirm", name=t.get("name")), kb)
                return "ok", 200

            # Обработка API кнопок
            if data_str == "api_create_key":
                if advanced_features:
                    raw_key, key_info = advanced_features.create_api_key(chat_id)
                    if raw_key:
                        send_message(chat_id, T(lang, "api_key_created", api_key=raw_key))
                    elif key_info == "limit":
                        send_message(chat_id, T(lang, "api_key_limit"))
                    elif key_info == "recent":
                        pass  # ретрай Telegram — ключ уже создан, не дублируем
                    else:
                        send_message(chat_id, T(lang, "api_key_error"))
                return "ok", 200
            
            elif data_str == "api_help":
                if advanced_features:
                    default_city = advanced_features.get_api_default_city(chat_id) or T(lang, "api_city_not_set")
                    help_text = T(lang, "api_help_title") + "\n"
                    help_text += T(lang, "api_help_base") + "\n"
                    help_text += "https://mob100500lvl.pythonanywhere.com/api/v1\n"
                    help_text += T(lang, "api_help_endpoints") + "\n"
                    help_text += T(lang, "api_help_ep_weather") + "\n"
                    help_text += T(lang, "api_help_ep_forecast") + "\n"
                    help_text += T(lang, "api_help_ep_me") + "\n"
                    help_text += T(lang, "api_help_auth") + "\n"
                    help_text += T(lang, "api_help_header") + "\n"
                    help_text += T(lang, "api_help_default", city=default_city) + "\n"
                    help_text += T(lang, "api_help_limits") + "\n"
                    help_text += T(lang, "api_help_limit_keys") + "\n"
                    help_text += T(lang, "api_help_limit_req") + "\n"
                    help_text += T(lang, "api_help_example") + "\n"
                    help_text += ('curl -H "X-API-Key: ВАШ_КЛЮЧ" \\\n' if lang == "ru" else 'curl -H "X-API-Key: YOUR_KEY" \\\n')
                    help_text += '"https://mob100500lvl.pythonanywhere.com/api/v1/weather"\n'
                    send_message(chat_id, help_text)
                return "ok", 200
                return "ok", 200
            
            elif data_str == "api_set_city":
                if advanced_features:
                    _set_user_state(chat_id, "api_city_input")
                    send_message(chat_id, T(lang, "api_set_city_prompt"))
                return "ok", 200
            
            elif data_str == "api_profile":
                if advanced_features:
                    db = advanced_features._db()
                    profile = db["users"].get(str(chat_id), {})
                    api_keys_file = advanced_features._load(advanced_features.API_KEY_FILE, {})
                    api_keys_count = sum(1 for k, v in api_keys_file.items() if v.get("owner") == str(chat_id))
                    first_seen = profile.get('first_seen', 'N/A')[:10] if profile.get('first_seen') else 'N/A'
                    profile_text = T(lang, "api_profile_title") + "\n\n"
                    profile_text += T(lang, "api_profile_id", id=chat_id) + "\n"
                    profile_text += T(lang, "api_profile_keys", count=api_keys_count) + "\n"
                    profile_text += T(lang, "api_profile_city", city=profile.get('api_default_city', T(lang, "api_city_not_set"))) + "\n"
                    profile_text += T(lang, "api_profile_first", date=first_seen)
                    send_message(chat_id, profile_text)
                return "ok", 200

            elif data_str == "api_stats":
                if advanced_features:
                    stats = advanced_features.get_api_stats(chat_id)
                    if stats["total_requests"] == 0:
                        send_message(chat_id, T(lang, "api_stats_empty"))
                    else:
                        stats_text = T(lang, "api_stats_title") + "\n\n"
                        stats_text += T(lang, "api_stats_total", total=stats['total_requests']) + "\n"
                        stats_text += T(lang, "api_stats_24h", h24=stats['last_24h']) + "\n"
                        stats_text += T(lang, "api_stats_7d", d7=stats['last_7d']) + "\n\n"
                        stats_text += T(lang, "api_stats_by_ep") + "\n"
                        for endpoint, count in sorted(stats["by_endpoint"].items(), key=lambda x: x[1], reverse=True):
                            stats_text += f"  • {endpoint}: {count}\n"
                        send_message(chat_id, stats_text)
                return "ok", 200
            
            elif data_str == "autopost_add":
                send_message(chat_id, "➕ Используйте команду:\n`/channel @канал Город ЧЧ:ММ`\n\nНапример:\n`/channel @my_channel Томск 08:00`", get_main_keyboard(chat_id))
                return "ok", 200
            
            elif data_str == "autopost_list":
                if advanced_features:
                    advanced_features.handle(chat_id, "/channels")
                return "ok", 200
            
            elif data_str == "autopost_send":
                if advanced_features:
                    advanced_features.handle(chat_id, "/postnow")
                return "ok", 200
            
            elif data_str == "autopost_remove":
                send_message(chat_id, "🗑 Чтобы удалить канал, напишите:\n`/channel_remove @канал`", get_main_keyboard(chat_id))
                return "ok", 200
            
            elif data_str == "autopost_style":
                if advanced_features:
                    advanced_features.handle(chat_id, "/cardstyle")
                return "ok", 200
            
            elif data_str == "card_bg":
                _set_user_state(chat_id, "card_bg_input")
                send_message(chat_id, "🎨 Пришлите цвет фона в HEX (например #1a2a3a):")
                return "ok", 200
            
            elif data_str == "card_text":
                _set_user_state(chat_id, "card_text_input")
                send_message(chat_id, "📝 Пришлите цвет текста в HEX (например #ffffff):")
                return "ok", 200
            
            elif data_str == "card_accent":
                _set_user_state(chat_id, "card_accent_input")
                send_message(chat_id, "🌡 Пришлите цвет акцента (температуры) в HEX (например #ffd700):")
                return "ok", 200
            
            elif data_str == "card_bg_image":
                _set_user_state(chat_id, "card_bg_image")
                send_message(chat_id, "📸 Отправьте фото для фона карточки:")
                return "ok", 200
            
            elif data_str == "card_reset":
                if advanced_features:
                    with advanced_features.FEATURE_LOCK:
                        db = advanced_features._db()
                        db.get("card_settings", {}).pop(str(chat_id), None)
                        advanced_features._save_db(db)
                    advanced_features.handle(chat_id, "/cardstyle")
                return "ok", 200
            
            elif data_str == "card_back":
                if advanced_features:
                    send_message(chat_id, T(lang, "autopost_menu"), advanced_features.get_autopost_inline_keyboard(lang))
                return "ok", 200
            
            elif data_str == "card_back_main":
                send_message(chat_id, T(lang, "start_with_city", city=get_user_city(chat_id) or "—"), get_main_keyboard(chat_id))
                return "ok", 200
            
            elif data_str == "card_generate":
                _set_user_state(chat_id, "card_city")
                send_message(chat_id, T(lang, "card_prompt_city"))
                return "ok", 200
            
            elif data_str == "card_style":
                if advanced_features:
                    advanced_features.handle(chat_id, "/cardstyle")
                return "ok", 200
            
            elif data_str == "wl_name_btn":
                _set_user_state(chat_id, "wl_name")
                send_message(chat_id, T(lang, "wl_name_prompt"))
                return "ok", 200
            
            elif data_str == "wl_color_btn":
                _set_user_state(chat_id, "wl_color")
                send_message(chat_id, T(lang, "wl_color_prompt"))
                return "ok", 200
            
            elif data_str == "wl_logo_btn":
                _set_user_state(chat_id, "wl_logo")
                send_message(chat_id, T(lang, "wl_logo_prompt"))
                return "ok", 200
            
            elif data_str == "wl_card":
                _set_user_state(chat_id, "card_city")
                send_message(chat_id, T(lang, "card_prompt_city"))
                return "ok", 200
            
            elif data_str == "wl_back":
                send_message(chat_id, T(lang, "start_with_city", city=get_user_city(chat_id) or "—"), get_main_keyboard(chat_id))
                return "ok", 200
            
            elif data_str == "autopost_back":
                send_message(chat_id, T(lang, "welcome", city=get_user_city(chat_id) or ""), get_main_keyboard(chat_id))
                return "ok", 200
            
            elif data_str == "api_delete_all":
                if advanced_features:
                    with advanced_features.FEATURE_LOCK:
                        keys = advanced_features._load(advanced_features.API_KEY_FILE, {})
                        deleted = 0
                        for digest, info in list(keys.items()):
                            if info.get("owner") == str(chat_id):
                                del keys[digest]
                                deleted += 1
                        advanced_features._save(advanced_features.API_KEY_FILE, keys)
                    send_message(chat_id, T(lang, "api_deleted", count=deleted))
                return "ok", 200
            
            # Обработка выбора периодичности уведомлений
            elif data_str == "freq_daily":
                if advanced_features:
                    advanced_features.set_notification_prefs(chat_id, frequency="daily")
                    send_message(chat_id, T(lang, "notification_freq_saved", freq=T(lang, "notification_freq_daily")))
                answer_callback_query(callback_id)
                return "ok", 200
            
            elif data_str == "freq_weekly":
                if advanced_features:
                    advanced_features.set_notification_prefs(chat_id, frequency="weekly")
                    send_message(chat_id, T(lang, "notification_freq_saved", freq=T(lang, "notification_freq_weekly")))
                answer_callback_query(callback_id)
                return "ok", 200
            
            elif data_str == "freq_weekdays":
                if advanced_features:
                    advanced_features.set_notification_prefs(chat_id, frequency="weekdays")
                    send_message(chat_id, T(lang, "notification_freq_saved", freq=T(lang, "notification_freq_weekdays")))
                answer_callback_query(callback_id)
                return "ok", 200
            
            elif data_str == "freq_weekends":
                if advanced_features:
                    advanced_features.set_notification_prefs(chat_id, frequency="weekends")
                    send_message(chat_id, T(lang, "notification_freq_saved", freq=T(lang, "notification_freq_weekends")))
                answer_callback_query(callback_id)
                return "ok", 200
            
            # Для других callback_query просто возвращаем ok
            return "ok", 200

        message = data.get('message', {})
        chat_id = message.get('chat', {}).get('id')
        text = message.get('text', '')

        if not chat_id:
            return "ok", 200

        # Card background image upload
        state_photo = _get_user_state(chat_id)
        if message.get("photo") and state_photo and state_photo.get("mode") == "card_bg_image":
            if advanced_features:
                # Берём фото с наибольшим разрешением
                photo = message.get("photo")[-1]
                file_id = photo.get("file_id")
                # Скачиваем фото
                token = os.getenv("TELEGRAM_TOKEN", "")
                url = f"https://api.telegram.org/bot{token}/getFile"
                try:
                    r = requests.get(url, params={"file_id": file_id}, timeout=30)
                    if r.status_code == 200:
                        file_path = r.json().get("result", {}).get("file_path")
                        if file_path:
                            os.makedirs("media", exist_ok=True)
                            local_path = f"media/card_bg_{chat_id}.jpg"
                            download_url = f"https://api.telegram.org/file/bot{token}/{file_path}"
                            r2 = requests.get(download_url, timeout=30)
                            if r2.status_code == 200:
                                with open(local_path, "wb") as f:
                                    f.write(r2.content)
                                # Сохраняем путь в card_settings
                                with advanced_features.FEATURE_LOCK:
                                    db = advanced_features._db()
                                    if "card_settings" not in db:
                                        db["card_settings"] = {}
                                    if str(chat_id) not in db["card_settings"]:
                                        db["card_settings"][str(chat_id)] = {}
                                    db["card_settings"][str(chat_id)]["bg_image"] = local_path
                                    advanced_features._save_db(db)
                                _clear_user_state(chat_id)
                                send_message(chat_id, "✅ Фоновая картинка установлена!\n\nИспользуйте /postnow для проверки.", get_main_keyboard(chat_id))
                                return "ok", 200
                except Exception as e:
                    logger.error(f"Card bg image error: {e}")
                _clear_user_state(chat_id)
                send_message(chat_id, "❌ Ошибка загрузки картинки", get_main_keyboard(chat_id))
                return "ok", 200
        
        # White-label logo upload.
        if message.get("photo"):
            state_photo = _get_user_state(chat_id)
            if state_photo.get("mode") == "wl_logo" and get_current_plan(chat_id) == "business" and advanced_features:
                try:
                    photo = message["photo"][-1]
                    file_id = photo["file_id"]
                    file_info = requests.get(
                        f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getFile",
                        params={"file_id": file_id}, timeout=30
                    ).json()
                    file_path = file_info["result"]["file_path"]
                    os.makedirs("white_label_media", exist_ok=True)
                    ext = os.path.splitext(file_path)[1] or ".jpg"
                    local = os.path.join("white_label_media", f"{chat_id}{ext}")
                    raw_image = requests.get(
                        f"https://api.telegram.org/file/bot{TELEGRAM_TOKEN}/{file_path}",
                        timeout=60
                    ).content
                    with open(local, "wb") as fh:
                        fh.write(raw_image)
                    advanced_features.set_white_label(chat_id, logo=local)
                    _clear_user_state(chat_id)
                    send_message(chat_id, T(get_user_lang(chat_id), "wl_saved"), get_white_label_keyboard(chat_id))
                except Exception as e:
                    logger.error(f"Ошибка сохранения White-label logo: {e}", exc_info=True)
                    send_message(chat_id, T(lang, "logo_save_error"), get_white_label_keyboard(chat_id))
                return "ok", 200
            return "ok", 200

        lang = get_user_lang(chat_id)
        keyboard = get_main_keyboard(chat_id)
        current_city = get_user_city(chat_id)
        logger.info(f"DEBUG current_city: repr={repr(current_city)}, type={type(current_city).__name__}, len={len(current_city) if current_city else 0}, chat_id={chat_id}")
        is_subscribed = is_user_subscribed(chat_id)
        b2b_type = get_user_b2b_type(chat_id)

        if text == '/start':
            if not current_city:
                _set_user_state(chat_id, "initial_city")
                send_long_text(chat_id, T(lang, "welcome"), keyboard)
                send_message(chat_id, T(lang, "enter_city"), keyboard)
            else:
                msg = T(lang, "start_with_city", city=current_city)
                if not is_subscribed:
                    msg += T(lang, "free_mode")
                    msg += T(lang, "buy_prompt", price=PRICE_PERSONAL)
                else:
                    if b2b_type:
                        b2b_info = B2B_TYPES.get(b2b_type, {})
                        sub = get_user_subscription(chat_id)
                        days_left = 0
                        if sub:
                            expiry = datetime.fromisoformat(sub['expiry'])
                            days_left = (expiry - datetime.now()).days
                        msg += T(lang, "b2b_active", icon=b2b_info.get('icon', '🏢'), name=b2b_name(lang, b2b_type), days=days_left)
                    else:
                        sub = get_user_subscription(chat_id)
                        days_left = 0
                        if sub:
                            expiry = datetime.fromisoformat(sub['expiry'])
                            days_left = (expiry - datetime.now()).days
                        msg += T(lang, "subscription_active", days=days_left)
                send_message(chat_id, msg, keyboard)
            return "ok", 200
        # === КОМАНДА РАССЫЛКИ ДЛЯ АДМИНА ===
        if text.startswith("/broadcast"):
            if chat_id not in ADMIN_IDS:
                send_message(chat_id, "⛔ Только администратор может использовать эту команду.")
                return "ok", 200
            parts = text.split(maxsplit=1)
            if len(parts) < 2 or not parts[1].strip():
                send_message(chat_id, "📢 Использование: /broadcast <текст сообщения>")
                return "ok", 200
            message_text = parts[1].strip()
            # Получаем список всех пользователей из features.json и users_city.json
            all_users = set()
            try:
                feat_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "features.json")
                if os.path.exists(feat_path):
                    with open(feat_path, 'r', encoding='utf-8') as f:
                        feat_data = json.load(f)
                        all_users.update(str(uid) for uid in feat_data.get("users", {}).keys())
            except Exception as e:
                logger.error(f"BROADCAST: ошибка чтения features.json: {e}")
            try:
                city_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users_city.json")
                if os.path.exists(city_path):
                    with open(city_path, 'r', encoding='utf-8') as f:
                        city_data = json.load(f)
                        all_users.update(str(uid) for uid in city_data.keys())
            except Exception as e:
                logger.error(f"BROADCAST: ошибка чтения users_city.json: {e}")
            if not all_users:
                send_message(chat_id, "❌ Список пользователей пуст.")
                return "ok", 200
            all_users.discard(str(chat_id))  # Не отправляем самому себе
            total = len(all_users)
            send_message(chat_id, f"📨 Начинаю рассылку {total} пользователям...")
            success = 0
            failed = 0
            for uid_str in all_users:
                try:
                    uid = int(uid_str)
                    result = send_message(uid, message_text)
                    if result and result.get("ok"):
                        success += 1
                    else:
                        failed += 1
                except Exception as e:
                    failed += 1
                    logger.error(f"BROADCAST: ошибка отправки {uid_str}: {e}")
                import time
                time.sleep(0.05)  # Защита от лимитов Telegram API
            send_message(chat_id, f"✅ Рассылка завершена!\n\n📤 Всего: {total}\n✅ Успешно: {success}\n❌ Ошибок: {failed}")
            return "ok", 200
            return "ok", 200

        # ===== STATEFUL FLOWS =====
        state = _get_user_state(chat_id)
        # Кнопка «Назад» в любом режиме ввода: выходим без сохранения
        if state and state.get("mode") and text.strip() in (T(lang, "btn_back"), T(lang, "back"), "🔙 Назад", "⬅️ Назад"):
            _clear_user_state(chat_id)
            state = {}
        if state.get("mode") == "notification_time":
            import re
            value=text.strip()
            if not re.fullmatch(r"(?:[01]\d|2[0-3]):[0-5]\d",value):
                send_message(chat_id,T(lang,"notification_time_prompt"),get_notification_keyboard(chat_id)); return "ok",200
            if advanced_features: advanced_features.set_notification_prefs(chat_id,time=value)
            _clear_user_state(chat_id); send_message(chat_id,T(lang,"notification_time_saved",time=value),get_notification_keyboard(chat_id)); return "ok",200
        if state.get("mode") == "threshold_heat":
            try:
                value = float(text.strip())
                if advanced_features: advanced_features.set_alert(chat_id, "heat", enabled=True, threshold=value)
                _clear_user_state(chat_id); send_message(chat_id,T(lang,"threshold_saved",thr=value),get_notification_keyboard(chat_id)); return "ok",200
            except:
                send_message(chat_id,"❌ Введите число, например 30",get_notification_keyboard(chat_id)); return "ok",200
        
        if state.get("mode") == "threshold_frost":
            try:
                value = float(text.strip())
                if advanced_features: advanced_features.set_alert(chat_id, "frost", enabled=True, threshold=value)
                _clear_user_state(chat_id); send_message(chat_id,T(lang,"threshold_saved",thr=value),get_notification_keyboard(chat_id)); return "ok",200
            except:
                send_message(chat_id,"❌ Введите число, например 0",get_notification_keyboard(chat_id)); return "ok",200
        
        if state.get("mode") == "threshold_wind":
            try:
                value = float(text.strip())
                if advanced_features: advanced_features.set_alert(chat_id, "wind", enabled=True, threshold=value)
                _clear_user_state(chat_id); send_message(chat_id,T(lang,"threshold_saved",thr=value),get_notification_keyboard(chat_id)); return "ok",200
            except:
                send_message(chat_id,"❌ Введите число, например 15",get_notification_keyboard(chat_id)); return "ok",200
        
        if state.get("mode") == "threshold_rain":
            try:
                value = float(text.strip())
                if advanced_features: advanced_features.set_alert(chat_id, "rain", enabled=True, threshold=value)
                _clear_user_state(chat_id); send_message(chat_id,T(lang,"threshold_saved",thr=value),get_notification_keyboard(chat_id)); return "ok",200
            except:
                send_message(chat_id,"❌ Введите число, например 0.1",get_notification_keyboard(chat_id)); return "ok",200
        
        if state.get("mode") == "threshold_heavy_rain":
            try:
                value = float(text.strip())
                if advanced_features: advanced_features.set_alert(chat_id, "heavy_rain", enabled=True, threshold=value)
                _clear_user_state(chat_id); send_message(chat_id,T(lang,"threshold_saved",thr=value),get_notification_keyboard(chat_id)); return "ok",200
            except:
                send_message(chat_id,"❌ Введите число, например 10",get_notification_keyboard(chat_id)); return "ok",200
        

        if state.get("mode") == "notification_city":
            city_name=text.strip()
            if not city_name or city_name.startswith("/"): send_message(chat_id,T(lang,"notification_city_prompt"),get_notification_keyboard(chat_id)); return "ok",200
            weather=get_weather_aggregated(city_name,lang)
            if "error" in weather: send_message(chat_id,T(lang,"city_not_found",city=city_name),get_notification_keyboard(chat_id)); return "ok",200
            if advanced_features: advanced_features.set_notification_prefs(chat_id,city=city_name)
            _clear_user_state(chat_id); send_message(chat_id,T(lang,"notification_city_saved",city=city_name),get_notification_keyboard(chat_id)); return "ok",200

        # City may be changed ONLY after an explicit city-input action.
        if state.get("mode") == "team_create":
            name = text.strip()
            _clear_user_state(chat_id)
            if not name or name.startswith("/"):
                send_message(chat_id, T(lang, "invalid_action"), get_main_keyboard(chat_id))
                return "ok", 200
            tid = advanced_features.create_team(chat_id, name) if advanced_features else None
            if tid:
                kb = {"inline_keyboard": [
                    [{"text": T(lang, "team_btn_add"), "callback_data": f"team_add_{tid}"}],
                    [{"text": T(lang, "team_back"), "callback_data": "team_list"}]]}
                send_message(chat_id, T(lang, "team_create_success", name=name, tid=tid), kb)
            else:
                send_message(chat_id, T(lang, "team_create_failed"), get_main_keyboard(chat_id))
            return "ok", 200

        if state.get("mode") == "team_add_member":
            tid = state.get("team_id")
            _clear_user_state(chat_id)
            if text.strip().startswith("/"):
                send_message(chat_id, T(lang, "invalid_action"), get_main_keyboard(chat_id))
                return "ok", 200
            parts = text.strip().split()
            member_id = parts[0]
            role = parts[1] if len(parts) > 1 else "viewer"
            ok = advanced_features.add_team_member(chat_id, tid, member_id, role) if advanced_features else False
            if ok:
                t = advanced_features.get_team(tid) if advanced_features else None
                kb = {"inline_keyboard": [[{"text": "👥 " + (T(lang, "team_back")), "callback_data": f"team_view_{tid}"}]]}
                send_message(chat_id, T(lang, "team_add_success", name=t.get("name") if t else tid, role=role), kb)
                try:
                    mem_lang = get_user_lang(int(member_id))
                    send_message(int(member_id), ("👥 Вас добавили в команду! Роль: " + role + "." if mem_lang == "ru" else "👥 You were added to a team! Role: " + role + "."))
                except Exception:
                    pass
            else:
                send_message(chat_id, T(lang, "team_add_failed"), get_main_keyboard(chat_id))
            return "ok", 200

        if state.get("mode") in ("initial_city", "change_city"):
            if text.strip().startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_main_keyboard(chat_id))
                return "ok", 200
            
            # Список всех названий кнопок (на обоих языках)
            button_names = [
                "🌤 Погода", "🌤 Weather",
                "📅 Погода на завтра", "📅 Tomorrow Weather",
                "🌅 Восход", "🌅 Sunrise",
                "📅 3 дня", "📅 3 days",
                "📅 5 дней", "📅 5 days",
                "📅 10 дней", "📅 10 days",
                "🌧️ Дождь", "🌧️ Rain",
                "🌙 Луна", "🌙 Moon",
                "👕 Что надеть", "👕 What to wear",
                "📊 Статистика", "📊 Statistics",
                "✈️ Поездка", "✈️ Trip",
                "🔔 Уведомления", "🔔 Notifications",
                "🤖 AI-помощник", "🤖 AI Assistant",
                "⭐ Города", "⭐ Cities",
                "🌾 Агро", "🌾 Agriculture",
                "🏗️ Стройка", "🏗️ Construction",
                "🏖️ Туризм", "🏖️ Tourism",
                "📢 Автопостинг", "📢 Auto-posting",
                "🖼 Погодная карточка", "🖼 Weather Card",
                "🔑 API",
                "👥 Команда", "👥 Team",
                "🏷 White-label",
                "📊 Аналитика", "📊 Analytics",
                "🔑 Статус подписки", "🔑 Subscription status",
                "⚙️ Сменить город", "⚙️ Change city",
                "🌐 Сменить язык", "🌐 Change language",
                "❓ Помощь", "❓ Help",
                "➕ Добавить город", "➕ Add city",
                "➖ Удалить город", "➖ Remove city",
                "🔙 Назад", "🔙 Back",
                "✏️ Название", "✏️ Name",
                "🎨 Цвет", "🎨 Color",
                "🖼 Логотип", "🖼 Logo"
            ]
            
            text_stripped = text.strip()
            if text_stripped in button_names:
                send_message(chat_id, T(lang, "enter_city"), get_main_keyboard(chat_id))
                return "ok", 200
            
            city_name = text_stripped
            if not city_name:
                send_message(chat_id, T(lang, "enter_city"), get_main_keyboard(chat_id))
                return "ok", 200
            weather = get_weather_aggregated(city_name, lang)
            if "error" in weather:
                send_message(chat_id, T(lang, "city_not_found", city=city_name), get_main_keyboard(chat_id))
                return "ok", 200
            save_user_city(chat_id, city_name)
            _clear_user_state(chat_id)
            send_message(chat_id, T(lang, "city_changed" if state.get("mode") == "change_city" else "city_saved", city=city_name), get_main_keyboard(chat_id))
            send_message(chat_id, format_weather_text(chat_id, weather), get_main_keyboard(chat_id))
            return "ok", 200

        # Обработка ввода города для API
        if state.get("mode") == "api_city_input":
            if text.strip().startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_main_keyboard(chat_id))
                return "ok", 200
            city_name = text.strip()
            if not city_name:
                send_message(chat_id, T(lang, "api_enter_city_short"), get_main_keyboard(chat_id))
                return "ok", 200
            if advanced_features:
                advanced_features.set_api_default_city(chat_id, city_name)
            _clear_user_state(chat_id)
            send_message(chat_id, T(lang, "api_city_set", city=city_name), get_main_keyboard(chat_id))
            return "ok", 200

        # No city yet: prompt only after stateful city input had a chance to run.
        if not current_city:
            send_message(chat_id, T(lang, "enter_city"), get_main_keyboard(chat_id))
            _set_user_state(chat_id, "initial_city")
            return "ok", 200

        if state.get("mode") == "favorite_add":
            if text.strip().startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_city_keyboard(chat_id))
                return "ok", 200
            city_name = text.strip()
            ok, result = advanced_features.add_favorite(chat_id, city_name) if advanced_features else (False, "unavailable")
            _clear_user_state(chat_id)
            if ok:
                send_message(chat_id, T(lang, "city_added"), get_city_keyboard(chat_id))
            else:
                send_message(chat_id, T(lang, "city_add_failed", result=result), get_city_keyboard(chat_id))
            return "ok", 200

        if state.get("mode") == "favorite_remove":
            if text.strip().startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_city_keyboard(chat_id))
                return "ok", 200
            city_name = text.strip()
            ok = advanced_features.remove_favorite(chat_id, city_name) if advanced_features else False
            _clear_user_state(chat_id)
            send_message(chat_id, T(lang, "city_removed") if ok else T(lang, "city_not_found"), get_city_keyboard(chat_id))
            return "ok", 200

        if state.get("mode") == "card_city":
            city_name = text.strip()
            if city_name.startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_main_keyboard(chat_id))
                return "ok", 200
            logger.info(f"CARD_CITY: user={chat_id}, city={city_name}")
            if advanced_features:
                try:
                    weather = get_weather_aggregated(city_name, lang)
                    if "error" in weather:
                        send_message(chat_id, T(lang, "city_not_found"), get_main_keyboard(chat_id))
                        _clear_user_state(chat_id)
                        return "ok", 200
                    brand = advanced_features._db().get("white_labels", {}).get(str(chat_id), {}) if get_current_plan(chat_id) == "business" else {}
                    card_settings = advanced_features._db().get("card_settings", {}).get(str(chat_id), {})
                    path = advanced_features.generate_weather_card(weather, city_name, brand=brand, card_settings=card_settings)
                    if path:
                        send_photo(chat_id, path, T(lang, "card_ready"))
                    else:
                        send_message(chat_id, T(lang, "card_error"), get_main_keyboard(chat_id))
                except Exception as e:
                    logger.error(f"CARD_CITY: Ошибка: {e}", exc_info=True)
                    send_message(chat_id, T(lang, "card_error_generic", err=str(e)[:100]), get_main_keyboard(chat_id))
            else:
                logger.error("CARD_CITY: advanced_features не загружен")
            _clear_user_state(chat_id)
            return "ok", 200

        if state.get("mode") in ("card_bg_input", "card_text_input", "card_accent_input"):
            value = text.strip()
            if not value.startswith("#"):
                value = "#" + value
            if len(value) != 7:
                send_message(chat_id, "❌ Формат HEX: #RRGGBB (например #1a2a3a)")
                return "ok", 200
            key_map = {"card_bg_input": "bg_color", "card_text_input": "text_color", "card_accent_input": "accent_color"}
            name_map = {"bg_color": "фона", "text_color": "текста", "accent_color": "акцента"}
            key = key_map[state.get("mode")]
            if advanced_features:
                with advanced_features.FEATURE_LOCK:
                    db = advanced_features._db()
                    db.setdefault("card_settings", {}).setdefault(str(chat_id), {})[key] = value
                    advanced_features._save_db(db)
            _clear_user_state(chat_id)
            send_message(chat_id, f"✅ Цвет {name_map[key]} изменён на `{value}`", advanced_features.get_card_style_keyboard(lang) if advanced_features else None)
            return "ok", 200
        if state.get("mode") == "wl_name":
            if text.strip().startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_white_label_keyboard(chat_id))
                return "ok", 200
            result = advanced_features.set_white_label(chat_id, name=text.strip()) if advanced_features else {"error":"unavailable"}
            _clear_user_state(chat_id)
            send_message(chat_id, T(lang, "wl_saved"), advanced_features.get_white_label_inline_keyboard(lang) if advanced_features else None)
            return "ok", 200

        if state.get("mode") == "wl_color":
            value = text.strip()
            if not value.startswith("#") or len(value) not in (4, 7):
                send_message(chat_id, T(lang, "wl_color_prompt"), get_white_label_keyboard(chat_id))
                return "ok", 200
            result = advanced_features.set_white_label(chat_id, primary=value) if advanced_features else {"error":"unavailable"}
            _clear_user_state(chat_id)
            send_message(chat_id, T(lang, "wl_saved"), advanced_features.get_white_label_inline_keyboard(lang) if advanced_features else None)
            return "ok", 200

        # Logo upload is handled separately below when Telegram sends a photo.

        if state.get("mode") == "ai_question":
            question = text.strip()
            _clear_user_state(chat_id)
            if get_current_plan(chat_id) == "free":
                _paywall(chat_id, "premium")
            elif advanced_features:
                answer, err = advanced_features.ai_answer(chat_id, question)
                text_to_send = f"🤖 {answer}" if answer else f"❌ {err}"
                # Безопасная отправка AI ответа (ответ может содержать спецсимволы)
                result = send_message(chat_id, text_to_send, keyboard)
                # Если Markdown сломался, отправляем как обычный текст
                if not result or result.get("ok") == False:
                    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
                    payload = {"chat_id": chat_id, "text": text_to_send}
                    if keyboard:
                        payload["reply_markup"] = keyboard
                    try:
                        requests.post(url, json=payload, timeout=30)
                    except Exception:
                        pass
            return "ok", 200
        if state.get("mode") == "trip_city":
            destination = text.strip()
            weather = get_forecast_aggregated(destination, 1, lang)
            if "error" in weather:
                send_message(chat_id, T(lang, "city_not_found", city=destination), keyboard)
                return "ok", 200
            _set_user_state(chat_id, "trip_days", destination=destination)
            send_message(chat_id, T(lang, "trip_days"), keyboard)
            return "ok", 200
        if state.get("mode") == "trip_days":
            if not text.strip().isdigit() or not (1 <= int(text.strip()) <= 10):
                send_message(chat_id, T(lang, "trip_days"), keyboard)
                return "ok", 200
            destination = state.get("destination")
            days = int(text.strip())
            _clear_user_state(chat_id)
            if get_current_plan(chat_id) == "free":
                _paywall(chat_id, "premium")
                return "ok", 200
            result = advanced_features.trip_forecast(chat_id, destination, days) if advanced_features else {"error":"unavailable"}
            if result.get("error") == "premium_required":
                _paywall(chat_id, "premium")
            elif "error" in result:
                send_message(chat_id, T(lang, "forecast_error"), keyboard)
            else:
                send_message(chat_id, format_trip_forecast_text(lang, destination, result), keyboard)
            return "ok", 200

        # /trip is handled by the bot's stateful UI so CITY/DAYS errors cannot corrupt city selection.
        if text.strip().lower() == "/trip":
            if get_current_plan(chat_id) == "free":
                _paywall(chat_id, "premium")
            else:
                _set_user_state(chat_id, "trip_city")
                send_message(chat_id, T(lang, "trip_city"), keyboard)
            return "ok", 200
        if text.strip().lower().startswith("/trip "):
            parts = text.strip().split()
            destination = parts[1]
            if len(parts) >= 3 and parts[2].isdigit():
                days = max(1, min(10, int(parts[2])))
                if get_current_plan(chat_id) == "free":
                    _paywall(chat_id, "premium")
                elif advanced_features:
                    result = advanced_features.trip_forecast(chat_id, destination, days)
                    send_message(chat_id, format_trip_forecast_text(lang, destination, result), keyboard)
                return "ok", 200
            _set_user_state(chat_id, "trip_days", destination=destination)
            send_message(chat_id, T(lang, "trip_days"), keyboard)
            return "ok", 200

        # New product UI actions must be handled by the main bot, not swallowed by
        # the legacy feature command parser.
        if text == T(lang, "btn_favorites"):
            _show_cities(chat_id)
            return "ok", 200

        if text == T(lang, "btn_add_city"):
            _set_user_state(chat_id, "favorite_add")
            send_message(chat_id, T(lang, "favorite_add_prompt"), get_city_keyboard(chat_id))
            return "ok", 200

        if text == T(lang, "btn_remove_city"):
            _set_user_state(chat_id, "favorite_remove")
            send_message(chat_id, T(lang, "favorite_remove_prompt"), get_city_keyboard(chat_id))
            return "ok", 200

        if advanced_features and text in [str(x) for x in advanced_features.favorites(chat_id)]:
            city_name=text.strip(); weather=get_weather_aggregated(city_name,lang)
            if "error" in weather: send_message(chat_id,T(lang,"city_not_found",city=city_name),get_city_keyboard(chat_id))
            else:
                save_user_city(chat_id,city_name); send_message(chat_id,T(lang,"city_changed",city=city_name),get_city_keyboard(chat_id)); send_message(chat_id,format_weather_text(chat_id,weather),get_main_keyboard(chat_id))
            return "ok",200

        if text == T(lang,"btn_notifications"):
            _show_notification_settings(chat_id); return "ok",200
        if text == T(lang,"notification_toggle"):
            if advanced_features:
                prefs=advanced_features.notification_prefs(chat_id); advanced_features.set_notification_prefs(chat_id,enabled=not bool(prefs.get("enabled")))
            else: set_notification_status(chat_id,not get_notification_status(chat_id))
            _show_notification_settings(chat_id); return "ok",200
        for key,pref in (("notification_rain","rain"),("notification_wind","wind"),("notification_frost","frost"),("notification_heat","heat")):
            if text == T(lang,key):
                if advanced_features:
                    prefs=advanced_features.notification_prefs(chat_id); advanced_features.set_notification_prefs(chat_id,**{pref:not bool(prefs.get(pref,True))})
                _show_notification_settings(chat_id); return "ok",200
        if text == T(lang,"notification_frequency"):
            # Показываем inline-клавиатуру с вариантами
            kb = {
                "inline_keyboard": [
                    [{"text": T(lang, "notification_freq_daily"), "callback_data": "freq_daily"}],
                    [{"text": T(lang, "notification_freq_weekly"), "callback_data": "freq_weekly"}],
                    [{"text": T(lang, "notification_freq_weekdays"), "callback_data": "freq_weekdays"}],
                    [{"text": T(lang, "notification_freq_weekends"), "callback_data": "freq_weekends"}],
                ]
            }
            send_message(chat_id, T(lang, "notification_frequency") + ":", kb)
            return "ok",200
        if text == T(lang,"threshold_heat"):
            _set_user_state(chat_id,"threshold_heat"); send_message(chat_id,T(lang,"threshold_heat_prompt"),get_notification_keyboard(chat_id)); return "ok",200
        
        if text == T(lang,"threshold_frost"):
            _set_user_state(chat_id,"threshold_frost"); send_message(chat_id,T(lang,"threshold_frost_prompt"),get_notification_keyboard(chat_id)); return "ok",200
        
        if text == T(lang,"threshold_wind"):
            _set_user_state(chat_id,"threshold_wind"); send_message(chat_id,T(lang,"threshold_wind_prompt"),get_notification_keyboard(chat_id)); return "ok",200
        
        if text == T(lang,"threshold_rain"):
            _set_user_state(chat_id,"threshold_rain"); send_message(chat_id,T(lang,"threshold_rain_prompt"),get_notification_keyboard(chat_id)); return "ok",200
        
        if text == T(lang,"threshold_heavy_rain"):
            _set_user_state(chat_id,"threshold_heavy_rain"); send_message(chat_id,T(lang,"threshold_heavy_rain_prompt"),get_notification_keyboard(chat_id)); return "ok",200
        
        if text == T(lang,"notification_time"):
            _set_user_state(chat_id,"notification_time"); send_message(chat_id,T(lang,"notification_time_prompt"),get_notification_keyboard(chat_id)); return "ok",200
        if text == T(lang,"notification_city"):
            _set_user_state(chat_id,"notification_city"); send_message(chat_id,T(lang,"notification_city_prompt"),get_notification_keyboard(chat_id)); return "ok",200
        if text == T(lang,"notification_back"):
            _clear_user_state(chat_id); send_message(chat_id,T(lang,"btn_back"),get_main_keyboard(chat_id)); return "ok",200


        if text == T(lang, "btn_wl_name"):
            _set_user_state(chat_id, "wl_name")
            send_message(chat_id, T(lang, "wl_name_prompt"), get_white_label_keyboard(chat_id))
            return "ok", 200

        if text == T(lang, "btn_wl_color"):
            _set_user_state(chat_id, "wl_color")
            send_message(chat_id, T(lang, "wl_color_prompt"), get_white_label_keyboard(chat_id))
            return "ok", 200

        if text == T(lang, "btn_wl_logo"):
            _set_user_state(chat_id, "wl_logo")
            send_message(chat_id, T(lang, "wl_logo_prompt"), get_white_label_keyboard(chat_id))
            return "ok", 200

        # Advanced feature module gets first chance for slash commands.
        if advanced_features:
            try:
                if advanced_features.handle(chat_id, text):
                    return "ok", 200
            except Exception as e:
                logger.error(f"Ошибка advanced_features.handle: {e}", exc_info=True)

        # ===== ОБРАБОТКА КНОПОК =====
        btn_map = {
            "btn_weather": "weather",
            "btn_tomorrow": "tomorrow",
            "btn_sunrise": "sunrise",
            "btn_f3": "forecast_3",
            "btn_f5": "forecast_5",
            "btn_f10": "forecast_10",
            "btn_rain": "rain",
            "btn_moon": "moon",
            "btn_clothing": "clothing",
            "btn_stats": "statistics",
            "btn_agro": "agro",
            "btn_construction": "construction",
            "btn_tourism": "tourism",
            "btn_notifications": "notifications",
            "btn_trip": "trip",
            "btn_ai": "ai",
            "btn_favorites": "favorites",
            "btn_autopost": "autopost",
            "btn_card": "card",
            "btn_api": "api",
            "btn_team": "team",
            "btn_whitelabel": "whitelabel",
            "btn_analytics": "analytics",
            "btn_change_city": "change_city",
            "btn_change_lang": "change_lang",
            "btn_help": "help",
            "btn_subscription": "subscription_status",
            "btn_buy": "buy",
            "btn_buy_b2b": "buy_b2b",
            "btn_personal": "personal",
            "btn_agriculture": "agriculture",
            "btn_construction_sub": "construction_sub",
            "btn_tourism_sub": "tourism_sub",
            "btn_business_sub": "business_sub",
            "btn_back": "back"
        }

        action = None
        for key, val in btn_map.items():
            if text == T(lang, key):
                action = val
                break

        if action == "trip":
            if get_current_plan(chat_id) == "free":
                _paywall(chat_id, "premium")
            else:
                _set_user_state(chat_id, "trip_city")
                send_message(chat_id, T(lang, "trip_city"), keyboard)
            return "ok", 200

        elif action == "ai":
            if get_current_plan(chat_id) == "free":
                _paywall(chat_id, "premium")
            else:
                _set_user_state(chat_id, "ai_question")
                send_message(chat_id, T(lang, "ai_button"), keyboard)
            return "ok", 200

        elif action == "favorites":
            if advanced_features:
                advanced_features.handle(chat_id, "/favorites")
            return "ok", 200

        elif action == "autopost":
            if get_current_plan(chat_id) != "business":
                _paywall(chat_id, "business")
            else:
                send_message(chat_id, T(lang, "autopost_menu"), advanced_features.get_autopost_inline_keyboard(lang) if advanced_features else None)
            return "ok", 200

        elif action == "card":
            if get_current_plan(chat_id) == "free":
                _paywall(chat_id, "premium")
            else:
                menu_text = "🖼 *Погодная карточка*\n\nВыберите действие:" if lang == "ru" else "🖼 *Weather card*\n\nChoose an action:"
                send_message(chat_id, menu_text, advanced_features.get_card_menu_keyboard(lang) if advanced_features else None)
            return "ok", 200

        elif action == "api":
            if get_current_plan(chat_id) != "business":
                _paywall(chat_id, "business")
            else:
                send_message(chat_id, T(lang, "api_menu"), advanced_features.get_api_inline_keyboard(lang) if advanced_features else None)
            return "ok", 200

        elif action == "team":
            if get_current_plan(chat_id) != "business":
                _paywall(chat_id, "business")
            else:
                send_message(chat_id, T(lang, "team_menu"), get_team_main_keyboard(lang))
            return "ok", 200

        elif action == "whitelabel":
            if get_current_plan(chat_id) != "business":
                _paywall(chat_id, "business")
            else:
                wl = advanced_features._db().get("white_labels", {}).get(str(chat_id), {}) if advanced_features else {}
                text = T(lang, "wl_menu_working") + "\n\n"
                if not wl or not any(wl.get(k) for k in ("name", "primary", "logo")):
                    text += T(lang, "wl_status_none")
                else:
                    if wl.get("name"):
                        text += T(lang, "wl_status_name", val=wl["name"]) + "\n"
                    if wl.get("primary"):
                        text += T(lang, "wl_status_color", val=wl["primary"]) + "\n"
                    if wl.get("logo"):
                        logo_short = os.path.basename(str(wl["logo"]))
                        text += T(lang, "wl_status_logo", val=logo_short) + "\n"
                send_message(chat_id, text, advanced_features.get_white_label_inline_keyboard(lang) if advanced_features else None)
            return "ok", 200

        elif action == "analytics":
            if get_current_plan(chat_id) != "business":
                _paywall(chat_id, "business")
            elif advanced_features:
                db = advanced_features._db()
                mine = {k:v for k,v in db.get("channels", {}).items() if str(v.get("owner")) == str(chat_id)}
                posts = sum(1 for v in mine.values() if v.get("last_post"))
                send_message(chat_id, T(lang, "analytics_menu") + f"\n\n📢 Каналов: {len(mine)}\n📤 Опубликовано: {posts}", keyboard)
            return "ok", 200

        if action == "weather":
            weather = get_weather_aggregated(current_city, lang)
            send_message(chat_id, format_weather_text(chat_id, weather), keyboard)
            return "ok", 200
        elif action == "tomorrow":
            tomorrow = get_tomorrow_detailed_forecast(current_city, lang)
            send_message(chat_id, format_tomorrow_forecast_text(chat_id, tomorrow), keyboard)
            return "ok", 200

        elif action == "change_city":
            _set_user_state(chat_id, "change_city")
            send_message(chat_id, T(lang, "enter_city"), get_main_keyboard(chat_id))
            return "ok", 200

        elif action == "subscription_status":
            send_message(chat_id, format_subscription_status(chat_id), keyboard)
            return "ok", 200

        elif action == "help":
            send_long_text(chat_id, format_help_text(chat_id), keyboard)
            return "ok", 200

        elif action == "change_lang":
            send_message(chat_id, T(lang, "select_language"), get_language_keyboard(chat_id))
            return "ok", 200

        elif text in ["🇷🇺 Русский", "🇬🇧 English"]:
            lang_map = {
                "🇷🇺 Русский": "ru",
                "🇬🇧 English": "en",
                                            }
            new_lang = lang_map.get(text, "ru")
            set_user_lang(chat_id, new_lang)
            new_keyboard = get_main_keyboard(chat_id)
            language_names = {"ru": "Русский", "en": "English"}
            confirm_text = T(new_lang, "language_changed", language_name=language_names[new_lang])
            send_message(chat_id, confirm_text, new_keyboard)
            return "ok", 200

        elif action == "buy":
            send_message(chat_id, T(lang, "select_language_short"), get_payment_keyboard(chat_id))
            return "ok", 200

        elif action == "buy_b2b":
            if b2b_type:
                send_message(chat_id, T(lang, "already_b2b"), keyboard)
            else:
                send_message(chat_id, T(lang, "select_language_short"), get_payment_keyboard(chat_id))
            return "ok", 200

        elif action == "personal":
            invoice = create_invoice(chat_id, PRICE_PREMIUM, b2b_type=None, plan="premium")
            if invoice and invoice.get('ok'):
                send_message(chat_id, T(lang, "invoice_created", price=PRICE_PREMIUM), keyboard)
            else:
                send_message(chat_id, T(lang, "invoice_error"), keyboard)
            return "ok", 200

        elif action == "business_sub":
            invoice = create_invoice(chat_id, PRICE_BUSINESS, b2b_type=None, plan="business")
            if invoice and invoice.get('ok'):
                send_message(chat_id, T(lang, "invoice_created", price=PRICE_BUSINESS), keyboard)
            else:
                send_message(chat_id, T(lang, "invoice_error"), keyboard)
            return "ok", 200

        elif action == "back":
            send_message(chat_id, T(lang, "back_main"), get_main_keyboard(chat_id))
            return "ok", 200

        # ===== ПЛАТНЫЕ ФУНКЦИИ =====
        elif action in ["sunrise", "forecast_3", "forecast_5", "forecast_10", "rain", "moon", "clothing", "statistics", "agro", "construction", "tourism", "notifications"]:

            if get_current_plan(chat_id) == "free":
                _paywall(chat_id, "premium")
                return "ok", 200

            # Premium gets normal paid weather tools; Business gets everything.
            if action in ["forecast_10", "statistics", "agro", "construction", "tourism"]:
                if get_current_plan(chat_id) != "business":
                    _paywall(chat_id, "business")
                    return "ok", 200

            if action == "sunrise":
                data = get_sunrise_sunset(current_city, lang)
                if "error" in data:
                    send_message(chat_id, T(lang, "forecast_error"), keyboard)
                else:
                    msg = T(lang, "sunrise_title", city=data['city']) + "\n\n"
                    msg += T(lang, "sunrise_time", sunrise=data['sunrise']) + "\n"
                    msg += T(lang, "sunset_time", sunset=data['sunset']) + "\n"
                    msg += T(lang, "day_length", length=data['day_length'])
                    send_message(chat_id, msg, keyboard)

            elif action == "forecast_3":
                forecast = get_forecast_aggregated(current_city, 3, lang)
                send_message(chat_id, format_forecast_text(chat_id, forecast, current_city, 3), keyboard)

            elif action == "forecast_5":
                forecast = get_forecast_aggregated(current_city, 5, lang)
                send_message(chat_id, format_forecast_text(chat_id, forecast, current_city, 5), keyboard)

            elif action == "forecast_10":
                forecast = get_forecast_aggregated(current_city, 10, lang)
                send_message(chat_id, format_forecast_text(chat_id, forecast, current_city, 10), keyboard)

            elif action == "rain":
                today = datetime.now().strftime("%Y-%m-%d")
                forecast = get_forecast_aggregated(current_city, 1, lang)
                if "error" in forecast or today not in forecast:
                    send_message(chat_id, T(lang, "no_rain"), keyboard)
                else:
                    rain = forecast[today].get('rain', 0)
                    if rain > 0:
                        emoji = "🌧️" if rain > 5 else "☔"
                        intensity = T(lang, "intensity_heavy" if rain > 10 else "intensity_moderate" if rain > 5 else "intensity_light")
                        send_message(chat_id, T(lang, "rain_expected", emoji=emoji, city=current_city, rain=rain, intensity=intensity), keyboard)
                    else:
                        send_message(chat_id, T(lang, "no_rain"), keyboard)

            elif action == "moon":
                moon = get_moon_phase(lang)
                send_message(chat_id, T(lang, "moon_title", emoji=moon['emoji'], name=moon['name'], date=datetime.now().strftime('%d.%m.%Y')), keyboard)

            elif action == "clothing":
                weather = get_weather_aggregated(current_city, lang)
                if "error" in weather:
                    send_message(chat_id, T(lang, "weather_error"), keyboard)
                    return "ok", 200

                recommendations = get_clothing_recommendations(
                    chat_id,
                    weather['temp'],
                    weather['description'],
                    weather['wind_speed']
                )

                msg = T(lang, "clothing_title", city=weather['city'], temp=weather['temp'], description=weather['description'], wind=weather['wind_speed'])
                for item in recommendations:
                    msg += T(lang, "clothing_item", item=item)
                send_message(chat_id, msg, keyboard)

            elif action == "statistics":
                stats = get_weather_statistics(current_city, 14)
                if "error" in stats:
                    send_message(chat_id, T(lang, "stats_error"), keyboard)
                else:
                    msg = T(lang, "stats_title", days=len(stats['days']), city=stats['city']) + "\n\n"
                    msg += T(lang, "stats_avg", avg=stats['avg_temp']) + "\n"
                    msg += T(lang, "stats_max", max=stats['max_temp']) + "\n"
                    msg += T(lang, "stats_min", min=stats['min_temp']) + "\n"
                    msg += T(lang, "stats_rain", days=stats['rain_days']) + "\n"
                    msg += T(lang, "stats_clear", days=stats['clear_days']) + "\n"
                    msg += T(lang, "stats_cloudy", days=stats['cloudy_days']) + "\n"
                    msg += T(lang, "stats_total", rain=stats['total_rain'])
                    send_message(chat_id, msg, keyboard)

            elif action == "agro":
                agri_data = get_agri_forecast(current_city, lang)
                if "error" in agri_data:
                    send_message(chat_id, T(lang, "agri_error"), keyboard)
                else:
                    if lang == "ru":
                        frost_text = agri_data['frost']
                    elif lang == "en":
                        frost_text = "❌ Expected" if "❌" in agri_data['frost'] else "✅ Not expected"
                    elif lang == "es":
                        frost_text = "❌ Esperadas" if "❌" in agri_data['frost'] else "✅ No esperadas"
                    else:
                        frost_text = "❌ 预计" if "❌" in agri_data['frost'] else "✅ 无"
                    msg = T(lang, "agri_title", city=agri_data['city']) + "\n\n"
                    msg += T(lang, "agri_soil", temp=agri_data['soil_temp']) + "\n"
                    msg += T(lang, "agri_humidity", humidity=agri_data['humidity']) + "\n"
                    msg += T(lang, "agri_rain", rain=agri_data['rain']) + "\n"
                    msg += T(lang, "agri_frost", frost=frost_text) + "\n"
                    msg += T(lang, "agri_rec", rec=agri_data['recommendations'])
                    send_message(chat_id, msg, keyboard)

            elif action == "construction":
                const_data = get_construction_forecast(current_city, lang)
                if "error" in const_data:
                    send_message(chat_id, T(lang, "construction_error"), keyboard)
                else:
                    if lang == "ru":
                        safe_text = "✅ Безопасно" if const_data['wind_safe'] else "❌ Опасно"
                    elif lang == "en":
                        safe_text = "✅ Safe" if const_data['wind_safe'] else "❌ Dangerous"
                    elif lang == "es":
                        safe_text = "✅ Seguro" if const_data['wind_safe'] else "❌ Peligroso"
                    else:
                        safe_text = "✅ 安全" if const_data['wind_safe'] else "❌ 危险"
                    msg = T(lang, "construction_title", city=const_data['city']) + "\n\n"
                    msg += T(lang, "construction_wind", wind=const_data['wind'], safe=safe_text) + "\n"
                    msg += T(lang, "construction_rain", rain=const_data['rain']) + "\n"
                    msg += T(lang, "construction_temp", temp=const_data['temp']) + "\n"
                    msg += T(lang, "construction_rec", rec=const_data['recommendations'])
                    send_message(chat_id, msg, keyboard)

            elif action == "tourism":
                tour_data = get_tourism_forecast(chat_id, current_city)
                if "error" in tour_data:
                    send_message(chat_id, T(lang, "tourism_error"), keyboard)
                else:
                    msg = T(lang, "tourism_title", city=tour_data['city']) + "\n\n"
                    msg += T(lang, "tourism_weather", weather=tour_data['weather']) + "\n"
                    msg += T(lang, "tourism_temp", temp=tour_data['temp']) + "\n"
                    msg += T(lang, "tourism_sunrise", sunrise=tour_data['sunrise']) + "\n"
                    msg += T(lang, "tourism_sunset", sunset=tour_data['sunset']) + "\n"
                    msg += T(lang, "tourism_uv", uv=tour_data['uv'], level=tour_data['uv_level']) + "\n"
                    msg += T(lang, "tourism_rec", rec=tour_data['recommendations'])
                    send_message(chat_id, msg, keyboard)

            elif action == "notifications":
                if advanced_features:
                    prefs = advanced_features.notification_prefs(chat_id)
                    enabled = bool(prefs.get("enabled"))
                    advanced_features.set_notification_prefs(chat_id, enabled=not enabled)
                    send_message(chat_id, T(lang, "notification_on") if not enabled else T(lang, "notification_off"), keyboard)
                else:
                    current_status = get_notification_status(chat_id)
                    set_notification_status(chat_id, not current_status)
                    send_message(chat_id, T(lang, "notification_on") if not current_status else T(lang, "notification_off"), keyboard)
            return "ok", 200

        else:
            # Arbitrary text is never a city change. City input is accepted only
            # while an explicit initial_city/change_city state is active.
            send_message(chat_id, T(lang, "invalid_action"), keyboard)
            return "ok", 200

        return "ok", 200

    except Exception as e:
        logger.error(f"Ошибка в вебхуке: {e}", exc_info=True)
        return "error", 500

# ============================================================
#  АДМИН-ПАНЕЛЬ (НА АНГЛИЙСКОМ)
# ============================================================

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

@app.route('/api/cron_notifications', methods=['GET'])
def cron_notifications():
    """Веб-хук для отправки уведомлений (cron-job.org вызывает каждый час)."""
    try:
        import sys, os
        sys.path.insert(0, '/home/mob100500lvl/WeatherTomBot/WeatherTomBot')
        from send_notifications import main as send_main
        send_main()
        return "OK", 200
    except Exception as e:
        return f"Error: {str(e)[:200]}", 500

@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Welcome!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head><title>MeteoBot - Login</title>
            <style>body{font-family:Arial;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;display:flex;justify-content:center;align-items:center;height:100vh}.box{background:rgba(255,255,255,0.05);padding:40px;border-radius:20px;width:350px}h1{text-align:center;color:#ffd200}input{width:100%;padding:12px;margin:10px 0;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.2);color:#fff;border-radius:8px}button{width:100%;padding:12px;background:linear-gradient(90deg,#f7971e,#ffd200);border:none;border-radius:8px;font-weight:bold;cursor:pointer}.error{color:#ff6b6b;text-align:center;margin-top:10px}</style>
            </head>
            <body>
                <div class="box">
                    <h1>🌤 MeteoBot</h1>
                    <form method="post">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Login</button>
                    </form>
                    <div class="error">❌ Invalid username or password</div>
                </div>
            </body>
            </html>
            ''')

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>MeteoBot - Login</title>
    <style>body{font-family:Arial;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;display:flex;justify-content:center;align-items:center;height:100vh}.box{background:rgba(255,255,255,0.05);padding:40px;border-radius:20px;width:350px}h1{text-align:center;color:#ffd200}input{width:100%;padding:12px;margin:10px 0;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.2);color:#fff;border-radius:8px}button{width:100%;padding:12px;background:linear-gradient(90deg,#f7971e,#ffd200);border:none;border-radius:8px;font-weight:bold;cursor:pointer}</style>
    </head>
    <body>
        <div class="box">
            <h1>🌤 MeteoBot</h1>
            <form method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    ''')

@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))

@app.route('/admin')
@login_required
def admin_dashboard():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)

    subscriptions = {}
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)

    b2b_users = {}
    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)

    total_users = len(users)
    subscribed_users = len([u for u in users if u in subscriptions])
    b2b_count = len(b2b_users)

    return f'''<!DOCTYPE html>
    <html>
    <head><title>MeteoBot - Admin Panel</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial;background:#0f0c29;color:#fff;padding:20px}}.container{{max-width:1200px;margin:0 auto}}.header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px}}h1{{color:#ffd200}}.menu a{{color:#aaa;text-decoration:none;margin-left:20px}}.menu a:hover{{color:#fff}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:20px;margin-bottom:30px}}.stat-card{{background:rgba(255,255,255,0.05);padding:20px;border-radius:15px;text-align:center}}.stat-number{{font-size:2em;font-weight:bold;color:#ffd200}}.stat-label{{opacity:0.7}}</style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌤 MeteoBot</h1>
                <div class="menu">
                    <a href="/admin">Dashboard</a>
                    <a href="/admin/users">Users</a>
                    <a href="/admin/subscriptions">Subscriptions</a>
                    <a href="/admin/texts">📝 Texts</a>
                    <a href="/admin/logout">Logout</a>
                </div>
            </div>
            <div class="stats">
                <div class="stat-card"><div class="stat-number">{total_users}</div><div class="stat-label">👥 Users</div></div>
                <div class="stat-card"><div class="stat-number">{subscribed_users}</div><div class="stat-label">✅ Subscribed</div></div>
                <div class="stat-card"><div class="stat-number">{b2b_count}</div><div class="stat-label">🏢 B2B</div></div>
                <div class="stat-card"><div class="stat-number">{total_users - subscribed_users}</div><div class="stat-label">🆓 Free</div></div>
            </div>
        </div>
    </body>
    </html>
    '''

@app.route('/admin/users')
@login_required
def admin_users():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)

    subscriptions = {}
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)

    b2b_users = {}
    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)

    html = '''<!DOCTYPE html><html><head><title>MeteoBot - Users</title>
    <style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial;background:#0f0c29;color:#fff;padding:20px}.container{max-width:1200px;margin:0 auto}.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px}h1{color:#ffd200}.menu a{color:#aaa;text-decoration:none;margin-left:20px}.menu a:hover{color:#fff}table{width:100%;border-collapse:collapse;background:rgba(255,255,255,0.05);border-radius:15px;overflow:hidden}th,td{padding:12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05)}th{background:rgba(255,255,255,0.1)}.subscribed{color:#0f0}.free{color:#ff6b6b}.b2b{color:#ffd700}.btn{padding:5px 10px;border-radius:5px;text-decoration:none;margin:2px;display:inline-block}.btn-sub{color:#0f0;border:1px solid #0f0}.btn-b2b{color:#ffd700;border:1px solid #ffd700}.btn-disable{color:#ff6b6b;border:1px solid #ff6b6b}.btn-del{color:#ff6b6b;border:1px solid #ff6b6b}.btn-disable:hover{background:#ff6b6b;color:#fff}.btn-sub:hover{background:#0f0;color:#000}.btn-b2b:hover{background:#ffd700;color:#000}.btn-del:hover{background:#ff6b6b;color:#fff}</style>
    </head><body><div class="container"><div class="header"><h1>👥 Users</h1>
    <div class="menu"><a href="/admin">Dashboard</a><a href="/admin/users">Users</a><a href="/admin/subscriptions">Subscriptions</a><a href="/admin/texts">📝 Texts</a><a href="/admin/logout">Logout</a></div></div>
    <table><thead><tr><th>ID</th><th>City</th><th>Subscription</th><th>Type</th><th>Actions</th></tr></thead><tbody>'''

    for user_id, city in users.items():
        is_sub = user_id in subscriptions
        b2b_info = b2b_users.get(user_id, {})
        b2b_type = b2b_info.get('type')
        status = '✅ Active' if is_sub else '❌ No'
        status_class = 'subscribed' if is_sub else 'free'

        if b2b_type:
            b2b_data = B2B_TYPES.get(b2b_type, {})
            type_label = f"{b2b_data.get('icon', '🏢')} {b2b_data.get('name', 'B2B')}"
            type_class = 'b2b'
        else:
            type_label = '👤 Personal' if is_sub else '-'
            type_class = 'subscribed' if is_sub else 'free'

        html += f'''<tr>
            <td>{user_id}</td>
            <td>{city}</td>
            <td class="{status_class}">{status}</td>
            <td class="{type_class}">{type_label}</td>
            <td>
                <a href="/admin/user/subscribe/{user_id}" class="btn btn-sub" onclick="return confirm('Activate personal subscription?')">👤</a>
                <a href="/admin/user/b2b/{user_id}/agriculture" class="btn btn-b2b" onclick="return confirm('Activate B2B (Agriculture)?')">🌾</a>
                <a href="/admin/user/b2b/{user_id}/construction" class="btn btn-b2b" onclick="return confirm('Activate B2B (Construction)?')">🏗️</a>
                <a href="/admin/user/b2b/{user_id}/tourism" class="btn btn-b2b" onclick="return confirm('Activate B2B (Tourism)?')">✈️</a>
                <a href="/admin/user/b2b/{user_id}/business" class="btn btn-b2b" onclick="return confirm('Activate B2B (Business)?')">🏢</a>
                <a href="/admin/subscription/disable/{user_id}" class="btn btn-disable" onclick="return confirm('Disable subscription?')">🚫</a>
                <a href="/admin/user/delete/{user_id}" class="btn btn-del" onclick="return confirm('Delete user?')">🗑️</a>
            </td>
        </tr>'''

    html += '''</tbody></table></div></body></html>'''
    return html

@app.route('/admin/user/delete/<chat_id>')
@login_required
def admin_user_delete(chat_id):
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        if chat_id in users:
            del users[chat_id]
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
    return redirect(url_for('admin_users'))

@app.route('/admin/user/subscribe/<chat_id>')
@login_required
def admin_user_subscribe(chat_id):
    set_user_subscription(chat_id, 30, b2b_type=None)
    return redirect(url_for('admin_users'))

@app.route('/admin/user/b2b/<chat_id>/<b2b_type>')
@login_required
def admin_user_b2b(chat_id, b2b_type):
    if b2b_type in B2B_TYPES:
        set_user_subscription(chat_id, 30, b2b_type=b2b_type)
    return redirect(url_for('admin_users'))

@app.route('/admin/subscription/disable/<chat_id>')
@login_required
def admin_subscription_disable(chat_id):
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)
        if chat_id in subscriptions:
            del subscriptions[chat_id]
            with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)

    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)
        if chat_id in b2b_users:
            del b2b_users[chat_id]
            with open(B2B_FILE, 'w', encoding='utf-8') as f:
                json.dump(b2b_users, f, ensure_ascii=False, indent=2)

    flash(f'Subscription disabled for user {chat_id}', 'success')
    return redirect(url_for('admin_users'))

@app.route('/admin/subscriptions')
@login_required
def admin_subscriptions():
    subscriptions = {}
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)

    b2b_users = {}
    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)

    html = '''<!DOCTYPE html><html><head><title>MeteoBot - Subscriptions</title>
    <style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial;background:#0f0c29;color:#fff;padding:20px}.container{max-width:1200px;margin:0 auto}.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px}h1{color:#ffd200}.menu a{color:#aaa;text-decoration:none;margin-left:20px}.menu a:hover{color:#fff}table{width:100%;border-collapse:collapse;background:rgba(255,255,255,0.05);border-radius:15px;overflow:hidden}th,td{padding:12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05)}th{background:rgba(255,255,255,0.1)}.active{color:#0f0}.expired{color:#ff6b6b}.b2b{color:#ffd700}.btn{padding:5px 10px;border-radius:5px;text-decoration:none;margin:2px;display:inline-block;color:#ff6b6b;border:1px solid #ff6b6b}</style>
    </head><body><div class="container"><div class="header"><h1>📋 Subscriptions</h1>
    <div class="menu"><a href="/admin">Dashboard</a><a href="/admin/users">Users</a><a href="/admin/subscriptions">Subscriptions</a><a href="/admin/texts">📝 Texts</a><a href="/admin/logout">Logout</a></div></div>
    <table><thead><tr><th>ID</th><th>Type</th><th>Valid until</th><th>Status</th><th>Actions</th></tr></thead><tbody>'''

    now = datetime.now()
    for user_id, sub in subscriptions.items():
        expiry = datetime.fromisoformat(sub['expiry'])
        is_active = expiry > now
        b2b_type = sub.get('b2b_type')
        status = '✅ Active' if is_active else '❌ Expired'
        status_class = 'active' if is_active else 'expired'

        if b2b_type:
            b2b_data = B2B_TYPES.get(b2b_type, {})
            type_label = f"{b2b_data.get('icon', '🏢')} {b2b_data.get('name', 'B2B')}"
            type_class = 'b2b'
        else:
            type_label = '👤 Personal'
            type_class = 'active' if is_active else 'expired'

        html += f'''<tr>
            <td>{user_id}</td>
            <td class="{type_class}">{type_label}</td>
            <td>{expiry.strftime('%d.%m.%Y')}</td>
            <td class="{status_class}">{status}</td>
            <td><a href="/admin/subscription/revoke/{user_id}" class="btn" onclick="return confirm('Revoke subscription?')">🔄 Revoke</a></td>
        </tr>'''

    html += '''</tbody></table></div></body></html>'''
    return html

@app.route('/admin/subscription/revoke/<chat_id>')
@login_required
def admin_subscription_revoke(chat_id):
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)
        if chat_id in subscriptions:
            del subscriptions[chat_id]
            with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)

    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)
        if chat_id in b2b_users:
            del b2b_users[chat_id]
            with open(B2B_FILE, 'w', encoding='utf-8') as f:
                json.dump(b2b_users, f, ensure_ascii=False, indent=2)

    return redirect(url_for('admin_subscriptions'))

# ============================================================
#  УПРАВЛЕНИЕ ТЕКСТАМИ (АДМИН-ПАНЕЛЬ) С ПОДДЕРЖКОЙ ЯЗЫКОВ
# ============================================================

@app.route('/admin/texts', methods=['GET', 'POST'])
@login_required
def admin_texts():
    global TEXTS

    if request.method == 'POST':
        new_texts = {}
        for lang in TEXTS.keys():
            new_texts[lang] = {}
            for key in TEXTS[lang].keys():
                form_key = f"{lang}_{key}"
                new_texts[lang][key] = request.form.get(form_key, '')

        TEXTS = new_texts
        flash('✅ Texts saved successfully!', 'success')
        return redirect(url_for('admin_texts'))

    html = '''<!DOCTYPE html>
    <html>
    <head>
        <title>📝 Manage Texts</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #0f0c29; color: #fff; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap; }
            h1 { color: #ffd200; }
            .menu a { color: #aaa; text-decoration: none; margin-left: 20px; }
            .menu a:hover { color: #fff; }
            .flash { padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .flash-success { background: rgba(0,255,0,0.1); border: 1px solid rgba(0,255,0,0.3); color: #0f0; }
            .flash-error { background: rgba(255,0,0,0.1); border: 1px solid rgba(255,0,0,0.3); color: #ff6b6b; }
            .lang-tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
            .lang-tab { padding: 10px 20px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; cursor: pointer; color: #aaa; }
            .lang-tab.active { background: rgba(255,215,0,0.1); border-color: #ffd200; color: #ffd200; }
            .lang-content { display: none; background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px; }
            .lang-content.active { display: block; }
            .field { margin-bottom: 15px; }
            .field label { display: block; margin-bottom: 5px; font-weight: bold; opacity: 0.8; }
            .field .key { color: #888; font-size: 0.8em; font-family: monospace; display: block; margin-bottom: 5px; }
            .field textarea { width: 100%; padding: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); color: #fff; border-radius: 8px; min-height: 60px; resize: vertical; }
            .field textarea:focus { outline: none; border-color: #ffd200; }
            .btn-save { padding: 12px 40px; background: linear-gradient(90deg, #f7971e, #ffd200); border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 20px; }
            .btn-save:hover { transform: scale(1.02); }
            .lang-select {
                padding: 10px 15px;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.2);
                color: #fff;
                border-radius: 8px;
                font-size: 14px;
                margin-bottom: 20px;
                cursor: pointer;
            }
            .lang-select option { background: #0f0c29; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📝 Manage Texts</h1>
                <div class="menu">
                    <a href="/admin">Dashboard</a>
                    <a href="/admin/users">Users</a>
                    <a href="/admin/subscriptions">Subscriptions</a>
                    <a href="/admin/texts">📝 Texts</a>
                    <a href="/admin/logout">Logout</a>
                </div>
            </div>

            <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 20px; flex-wrap: wrap;">
                <span style="opacity: 0.7;">🌐 Language:</span>
                <select class="lang-select" id="langSelect" onchange="switchLang(this.value)">
                    <option value="ru">🇷🇺 Русский</option>
                    <option value="en" selected>🇬🇧 English</option>
                                    </select>
                <span style="opacity: 0.5; font-size: 12px;">(default: English)</span>
            </div>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="post">
    '''

    for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English")]:
        display = "block" if lang_code == "en" else "none"
        html += f'<div class="lang-content" id="lang_{lang_code}" style="display:{display}">'
        html += f'<h2>{lang_name}</h2>'

        lang_texts = TEXTS.get(lang_code, TEXTS.get('ru', {}))
        for key, value in lang_texts.items():
            html += f'''
                <div class="field">
                    <label for="{lang_code}_{key}">{key}</label>
                    <span class="key">🔑 {lang_code}.{key}</span>
                    <textarea id="{lang_code}_{key}" name="{lang_code}_{key}" rows="2">{value}</textarea>
                </div>
            '''

        html += '</div>'

    html += '''
                <button type="submit" class="btn-save">💾 Save all texts</button>
            </form>
        </div>

        <script>
            function switchLang(lang) {
                document.querySelectorAll('.lang-content').forEach(el => {
                    el.style.display = el.id === 'lang_' + lang ? 'block' : 'none';
                });
                document.getElementById('langSelect').value = lang;
            }
            document.addEventListener('DOMContentLoaded', function() {
                switchLang('en');
            });
        </script>
    </body>
    </html>
    '''

    return render_template_string(html, TEXTS=TEXTS)

# ============================================================
#  ОСНОВНЫЕ МАРШРУТЫ
# ============================================================

@app.route('/')
def index():
    total_users = 0
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            total_users = len(json.load(f))

    return f'''<!DOCTYPE html><html><head><title>MeteoBot</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}}.container{{text-align:center;max-width:600px}}h1{{font-size:3em;color:#ffd200;margin-bottom:20px}}.status{{background:rgba(255,255,255,0.05);padding:20px;border-radius:15px;margin:20px 0}}.status-item{{padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05)}}.status-item:last-child{{border-bottom:none}}.label{{opacity:0.7}}.value{{font-weight:bold;color:#ffd200}}.btn{{display:inline-block;padding:12px 30px;background:linear-gradient(90deg,#f7971e,#ffd200);color:#000;text-decoration:none;border-radius:10px;font-weight:bold;margin-top:20px}}.btn:hover{{transform:scale(1.05)}}.version{{opacity:0.5;font-size:12px;margin-top:20px}}</style>
    </head><body><div class="container"><h1>🌤 MeteoBot</h1><p>Smart weather bot with subscription</p>
    <div class="status"><div class="status-item"><span class="label">Status:</span> <span class="value">🟢 Running</span></div>
    <div class="status-item"><span class="label">Version:</span> <span class="value">3.0 (B2B + Multi-language)</span></div>
    <div class="status-item"><span class="label">Users:</span> <span class="value">{total_users}</span></div>
    <div class="status-item"><span class="label">Time:</span> <span class="value" id="dt"></span></div></div>
    <a href="/admin" class="btn">🔐 Admin Panel</a>
    <div class="version">Running on PythonAnywhere</div></div>
    <script>document.getElementById('dt').textContent = new Date().toLocaleString('ru-RU');</script></body></html>'''

@app.route('/set_webhook', methods=['GET'])
@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Устанавливает webhook с защитой секретным токеном."""
    webhook_url = WEBHOOK_URL or request.host_url.rstrip("/") + "/webhook"
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if webhook_secret:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}&secret_token={webhook_secret}"
        logger.info("Устанавливаем webhook с секретным токеном")
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
        logger.warning("WEBHOOK_SECRET не задан! Webhook не защищен.")
    try:
        response = requests.get(url, timeout=30)
        return response.text
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}", exc_info=True)
        return f"Error: {e}"


def webhook_info():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url, timeout=30)
        return response.json()
    except Exception as e:
        return {'error': str(e)}


# Wire the advanced feature module to the legacy bot functions.
if advanced_features:
    try:
        advanced_features.configure(
            get_user_lang=get_user_lang,
            get_user_city=get_user_city,
            get_weather_aggregated=get_weather_aggregated,
            get_forecast_aggregated=get_forecast_aggregated,
            send_message=send_message,
            T=T,
            is_user_subscribed=is_user_subscribed,
            get_user_b2b_type=get_user_b2b_type,
            is_admin=lambda uid: str(uid) == str(os.getenv("ADMIN_TELEGRAM_ID", "")) and bool(os.getenv("ADMIN_TELEGRAM_ID", "")),
            users_file=USERS_FILE,
            subscriptions_file=SUBSCRIPTIONS_FILE,
        )
        advanced_features.register_routes(app)
    except Exception as e:
        logger.error(f"Ошибка инициализации advanced_features: {e}", exc_info=True)

def migrate_subscriptions_to_new_plans():
    """One-time safe migration: Personal -> Premium, all legacy B2B -> Business.
    Existing expiry dates and active periods are preserved.
    """
    try:
        data = _load_json_file(SUBSCRIPTIONS_FILE, {})
        b2b_data = _load_json_file(B2B_FILE, {})
        changed = False
        for uid, sub in list(data.items()):
            if not isinstance(sub, dict):
                continue
            old = str(sub.get("plan") or "").casefold()
            b2b = str(sub.get("b2b_type") or "").casefold()
            if old in ("personal", "premium", "") and not b2b:
                new_plan = "premium" if old != "free" else "free"
                if sub.get("plan") != new_plan:
                    sub["plan"] = new_plan
                    sub["b2b_type"] = None
                    changed = True
            elif old in ("agriculture", "construction", "tourism", "business") or b2b in ("agriculture", "construction", "tourism", "business"):
                if sub.get("plan") != "business" or sub.get("b2b_type") != "business":
                    sub["plan"] = "business"
                    sub["b2b_type"] = "business"
                    changed = True
            elif old not in ("premium", "business", "free"):
                sub["plan"] = "business" if b2b else "premium"
                sub["b2b_type"] = "business" if b2b else None
                changed = True

            if sub.get("plan") == "business":
                b2b_data[str(uid)] = {
                    "type": "business",
                    "activated_at": b2b_data.get(str(uid), {}).get("activated_at", sub.get("activated_at", datetime.now().isoformat())),
                    "expiry": sub.get("expiry"),
                    "source": b2b_data.get(str(uid), {}).get("source", "migration"),
                }
            else:
                b2b_data.pop(str(uid), None)
            data[uid] = sub

        if changed:
            _save_json_file(SUBSCRIPTIONS_FILE, data)
        _save_json_file(B2B_FILE, b2b_data)

        # Repair the known class of city corruption caused by treating commands as cities.
        users = _load_json_file(USERS_FILE, {})
        repaired = False
        if isinstance(users, dict):
            for uid, city in list(users.items()):
                if isinstance(city, str) and city.strip().startswith("/"):
                    users[uid] = None
                    repaired = True
        if repaired:
            _save_json_file(USERS_FILE, users)

        # Normalize legacy B2B registry entries too.
        for uid, info in list(b2b_data.items()):
            if not isinstance(info, dict):
                b2b_data.pop(uid, None)
                continue
            sub = data.get(str(uid), {})
            if sub.get("plan") == "business":
                info["type"] = "business"
                info["expiry"] = sub.get("expiry")
                b2b_data[str(uid)] = info
            else:
                b2b_data.pop(uid, None)
        _save_json_file(B2B_FILE, b2b_data)

        logger.info("SUBSCRIPTION MIGRATION: completed; public plans=Premium/Business")
    except Exception:
        logger.exception("SUBSCRIPTION MIGRATION failed")

migrate_subscriptions_to_new_plans()

application = app

def validate_config():
    """Проверяет наличие всех необходимых переменных окружения."""
    required = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "WEATHERAPI_KEY": WEATHERAPI_KEY,
        "ADMIN_PASSWORD": ADMIN_PASSWORD,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        error_msg = "Missing required environment variables: " + ", ".join(missing)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Проверяем SECRET_KEY
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key or secret_key == "change-this-to-a-long-random-secret":
        logger.warning("SECRET_KEY не задан или используется значение по умолчанию!")
    
    # Проверяем WEBHOOK_SECRET
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.warning("WEBHOOK_SECRET не задан! Webhook не защищен.")
    else:
        logger.info(f"WEBHOOK_SECRET задан (длина: {len(webhook_secret)})")
    
    logger.info("Конфигурация валидна")

