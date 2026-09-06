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

from app import app
import admin
# ============================================================
#  ФОНОВЫЙ ПЛАНИРОВЩИК (автопостинг каналов и уведомления)
# ============================================================
import threading as _threading
import time as _time

from cron import _scheduler_loop, cron_notifications

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






from keyboards import get_city_keyboard, get_language_keyboard, get_main_keyboard, get_notification_keyboard, get_payment_keyboard, get_team_main_keyboard, get_white_label_keyboard




# ============================================================
#  ОТПРАВКА СООБЩЕНИЙ И ПЛАТЕЖИ
# ============================================================

from utils import answer_callback_query, send_long_text, send_message, send_photo





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
            return handle_callback_query(callback_query)

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
        _r = handle_stateful_flows(chat_id, text, lang)
        if _r: return _r
        state = _get_user_state(chat_id)

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
        _r = handle_buttons(chat_id, text, lang, keyboard, current_city, b2b_type)
        if _r: return _r

        return "ok", 200

    except Exception as e:
        logger.error(f"Ошибка в вебхуке: {e}", exc_info=True)
        return "error", 500

# ============================================================
#  АДМИН-ПАНЕЛЬ (НА АНГЛИЙСКОМ)
# ============================================================













# ============================================================
#  УПРАВЛЕНИЕ ТЕКСТАМИ (АДМИН-ПАНЕЛЬ) С ПОДДЕРЖКОЙ ЯЗЫКОВ
# ============================================================


# ============================================================
#  ОСНОВНЫЕ МАРШРУТЫ
# ============================================================

from webhooks import index, set_webhook, webhook_info
from handlers import handle_stateful_flows
from handlers_callbacks import handle_callback_query
from handlers_weather import handle_buttons





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

from service import migrate_subscriptions_to_new_plans, validate_config

migrate_subscriptions_to_new_plans()

application = app


