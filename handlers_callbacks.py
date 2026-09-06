#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Обработчики inline-кнопок (callback_query): команды, API, автопост, карточки, white-label."""
import logging

from config import *
from texts import T
from storage import (get_user_lang, get_current_plan, _set_user_state,
                     get_user_city)
from utils import send_message, answer_callback_query, _paywall
from keyboards import get_main_keyboard, get_team_main_keyboard
from features import get_autopost_inline_keyboard

try:
    import features as advanced_features
except Exception:
    advanced_features = None

logger = logging.getLogger(__name__)

def handle_callback_query(callback_query):
    """Обрабатывает callback_query. Возвращает ("ok",200)."""
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
