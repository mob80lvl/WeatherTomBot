#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Клавиатуры: главное меню, платежи, города, уведомления (raw dict для Telegram API)."""
from config import *
from texts import T, LANGUAGES
from storage import (get_user_lang, get_user_city, get_notification_status,
                     get_current_plan, get_user_b2b_type, is_user_subscribed)

def get_main_keyboard(chat_id):
    """One consistent menu for every plan. Access is checked on click."""
    lang = get_user_lang(chat_id)
    return {
        "keyboard": [
            [T(lang, "btn_weather"), T(lang, "btn_tomorrow"), T(lang, "btn_sunrise")],
            [T(lang, "btn_f3"), T(lang, "btn_f5"), T(lang, "btn_f10")],
            [T(lang, "btn_rain"), T(lang, "btn_moon")],
            [T(lang, "btn_clothing"), T(lang, "btn_stats")],
            [T(lang, "btn_trip"), T(lang, "btn_notifications")],
            [T(lang, "btn_ai"), T(lang, "btn_favorites")],
            [T(lang, "btn_agro"), T(lang, "btn_construction"), T(lang, "btn_tourism")],
            [T(lang, "btn_autopost"), T(lang, "btn_card")],
            [T(lang, "btn_api"), T(lang, "btn_team"), T(lang, "btn_whitelabel")],
            [T(lang, "btn_analytics")],
            [T(lang, "btn_subscription"), T(lang, "btn_buy")],
            [T(lang, "btn_change_city")],
            [T(lang, "btn_change_lang"), T(lang, "btn_help")]
        ],
        "resize_keyboard": True
    }
def get_payment_keyboard(chat_id):
    lang = get_user_lang(chat_id)
    return {
        "keyboard": [
            [T(lang, "btn_personal")],
            [T(lang, "btn_business_sub")],
            [T(lang, "btn_back")]
        ],
        "resize_keyboard": True
    }
def get_team_main_keyboard(lang):
    return {"inline_keyboard": [
        [{"text": T(lang, "team_btn_list"), "callback_data": "team_list"}],
        [{"text": T(lang, "team_btn_create"), "callback_data": "team_create"}],
        [{"text": T(lang, "team_btn_back"), "callback_data": "team_main_back"}]
    ]}
def get_language_keyboard(chat_id=None):
    lang = get_user_lang(chat_id) if chat_id is not None else "en"
    return {
        "keyboard": [
            ["🇷🇺 Русский", "🇬🇧 English"],
            [T(lang, "btn_back")]
        ],
        "resize_keyboard": True
    }
def get_city_keyboard(chat_id):
    lang = get_user_lang(chat_id)
    favs = advanced_features.favorites(chat_id) if advanced_features else []
    rows = [[str(city)] for city in favs]
    rows += [[T(lang, "btn_add_city"), T(lang, "btn_remove_city")], [T(lang, "btn_back")]]
    return {"keyboard": rows, "resize_keyboard": True}
def get_notification_keyboard(chat_id):
    lang = get_user_lang(chat_id)
    return {"keyboard":[[T(lang,"notification_toggle")],[T(lang,"notification_rain"),T(lang,"notification_wind")],[T(lang,"notification_frost"),T(lang,"notification_heat")],[T(lang,"notification_time"),T(lang,"notification_city")],[T(lang,"notification_frequency")],[T(lang,"threshold_heat"),T(lang,"threshold_frost")],[T(lang,"threshold_wind"),T(lang,"threshold_rain")],[T(lang,"threshold_heavy_rain")],[T(lang,"notification_back")]],"resize_keyboard":True}
def get_white_label_keyboard(chat_id):
    lang = get_user_lang(chat_id)
    return {
        "keyboard": [
            [T(lang, "btn_wl_name"), T(lang, "btn_wl_color")],
            [T(lang, "btn_wl_logo")],
            [T(lang, "btn_card")],
            [T(lang, "btn_back")]
        ],
        "resize_keyboard": True
    }
