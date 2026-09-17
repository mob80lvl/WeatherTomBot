#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обработчики состояний: ввод времени, порогов, городов, команд."""
import re
import logging

from config import *
from texts import T
from storage import (get_user_lang, _get_user_state, _clear_user_state,
                     save_user_city)
from weather import get_weather_aggregated, format_weather_text
from utils import send_message
from keyboards import (get_notification_keyboard, get_main_keyboard,
                      get_city_keyboard)

try:
    import features as advanced_features
except Exception:
    advanced_features = None

logger = logging.getLogger(__name__)

def handle_stateful_flows(chat_id, text, lang):
    """Обрабатывает активные состояния. Возвращает ("ok",200) или None."""
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

    return None
