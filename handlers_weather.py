#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обработчики кнопок главного меню: погода, прогнозы, подписки, покупки."""
import logging
import os
from datetime import datetime

from config import *
from texts import T
from config import PRICE_BUSINESS, PRICE_PREMIUM
from formatting import format_help_text, format_subscription_status
from keyboards import get_language_keyboard, get_main_keyboard, get_payment_keyboard, get_team_main_keyboard
from storage import _set_user_state, get_current_plan, get_notification_status, set_notification_status, set_user_lang
from utils import _paywall, create_invoice, send_long_text, send_message
from weather import format_forecast_text, format_tomorrow_forecast_text, format_weather_text, get_agri_forecast, get_clothing_recommendations, get_construction_forecast, get_forecast_aggregated, get_moon_phase, get_sunrise_sunset, get_tomorrow_detailed_forecast, get_tourism_forecast, get_weather_aggregated, get_weather_statistics

try:
    import features as advanced_features
except Exception:
    advanced_features = None

logger = logging.getLogger(__name__)

def handle_buttons(chat_id, text, lang, keyboard, current_city, b2b_type=None):
    """Обрабатывает кнопки меню. Возвращает ("ok",200) или None."""
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
