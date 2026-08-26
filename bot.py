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

# ============================================================
#  НАСТРОЙКИ
# ============================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

PRICE_PERSONAL = 100
PRICE_PREMIUM = 100
PRICE_BUSINESS = 400
PRICE_B2B_AGRICULTURE = 200
PRICE_B2B_CONSTRUCTION = 200
PRICE_B2B_TOURISM = 200
PRICE_B2B_BUSINESS = 400
SUBSCRIPTION_DAYS = 30

USERS_FILE = "users_city.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"
TEXTS_FILE = "bot_texts.json"
B2B_FILE = "b2b_users.json"
NOTIFICATIONS_FILE = "notifications.json"
USER_STATES_FILE = "user_states.json"

# Advanced feature module (B2B, AI, channels, API, teams, white-label, referrals, analytics)
try:
    import features as advanced_features
except Exception:
    advanced_features = None

B2B_TYPES = {
    "agriculture": {"name_key": "b2b_agriculture_name", "features_key": "b2b_agriculture_features", "icon": "🌾", "price": PRICE_B2B_AGRICULTURE},
    "construction": {"name_key": "b2b_construction_name", "features_key": "b2b_construction_features", "icon": "🏗️", "price": PRICE_B2B_CONSTRUCTION},
    "tourism": {"name_key": "b2b_tourism_name", "features_key": "b2b_tourism_features", "icon": "✈️", "price": PRICE_B2B_TOURISM},
    "business": {"name_key": "b2b_business_name", "features_key": "b2b_business_features", "icon": "🏢", "price": PRICE_B2B_BUSINESS}
}

def b2b_name(lang, b2b_type):
    info = B2B_TYPES.get(b2b_type, {})
    return T(lang, info.get("name_key", "b2b_business_name"))

def b2b_features(lang, b2b_type):
    info = B2B_TYPES.get(b2b_type, {})
    return T(lang, info.get("features_key", "b2b_business_features")).split("\n")

def api_language(lang):
    return {
        "ru": "ru", "en": "en",
        "fr": "fr", "de": "de", "ja": "ja", "ko": "kr",
        "it": "it", "hi": "hi", "ar": "ar"
    }.get(lang, "en")

LANGUAGES = ["ru", "en"]

# ============================================================
#  ТЕКСТЫ НА ВСЕХ ЯЗЫКАХ
# ============================================================

TEXTS = {'ru': {'welcome': '🌤 *Добро пожаловать в МетеоБот!*\n'
                   '\n'
                   '🏙️ *Для начала работы укажите ваш населённый пункт.*\n'
                   '\n'
                   'Напишите название города в ответном сообщении.',
        'start_with_city': '🌤 *Добро пожаловать в МетеоБот!*\n\n📍 Текущий город: *{city}*\n\n',
        'free_mode': '🔒 *Бесплатный режим*\n'
                     'Доступны: Погода сейчас, Смена города, Статус подписки, Помощь, Смена языка\n'
                     '\n',
        'buy_prompt': '💰 Купите подписку: *{price}⭐ в месяц*',
        'subscription_active': '✅ *Подписка активна!* (осталось {days} дн.)\nДоступны все функции бота.',
        'b2b_active': '{icon} *{name}* подписка активна!\n⏳ Осталось: *{days}* дн.\nДоступны все функции тарифа!',
        'no_city': '🏙️ *Сначала укажите ваш населённый пункт!*\n\nНапишите название города.',
        'city_not_found': "❌ '{city}' не найден. Попробуйте другой город.",
        'city_saved': '✅ Город *{city}* сохранён! Теперь вы можете пользоваться ботом.',
        'city_changed': '✅ Город изменён на *{city}*',
        'enter_city': '🏙️ *Напишите название города*\n\nНапример: `Москва`',
        'select_language': '🌐 *Выберите язык:*',
        'language_changed': '✅ Язык изменён на *{language_name}*',
        'subscription_status': '🔑 *Статус подписки*',
        'subscription_active_status': '{status}\n📅 До: *{expiry}*\n⏳ Осталось: *{days}* дн.',
        'subscription_inactive': '❌ Подписка неактивна\n'
                                 '\n'
                                 '💰 *Выберите тариф:*\n'
                                 '\n'
                                 '👤 Личная: *{personal}⭐*\n'
                                 '🌾 Сельское хозяйство: *{agri}⭐*\n'
                                 '🏗️ Строительство: *{const}⭐*\n'
                                 '✈️ Туризм: *{tour}⭐*\n'
                                 '🏢 Бизнес: *{business}⭐*',
        'only_subscribed': '🔒 *Эта функция доступна только по подписке!*\n'
                           '\n'
                           '💰 *Выберите тариф:*\n'
                           '\n'
                           '👤 Личная: *{personal}⭐*\n'
                           '🌾 Сельское хозяйство: *{agri}⭐*\n'
                           '🏗️ Строительство: *{const}⭐*\n'
                           '✈️ Туризм: *{tour}⭐*\n'
                           '🏢 Бизнес: *{business}⭐*',
        'invoice_created': '💳 *Счёт создан!*\n\nОплатите в Telegram.\n💰 Цена: *{price}⭐*',
        'payment_success': '✅ *Оплата прошла успешно!*\n'
                           '\n'
                           '🎉 Подписка активирована на {days} дней!\n'
                           '\n'
                           'Спасибо за поддержку! 🙌',
        'back': '🔙 Назад',
        'buy_subscription': '💰 Купить подписку',
        'buy_b2b': '💰 Купить B2B',
        'change_language': '🌐 Сменить язык',
        'help': '❓ Помощь',
        'help_title': '📖 *Помощь*',
        'help_subscribed': '📖 *Помощь* (Подписка активна)',
        'help_free': '📖 *Помощь* (Бесплатно)',
        'help_city': '📍 Город: *{city}*',
        'help_days': '⏳ Осталось: *{days}* дн.',
        'personal_features': '🌤 Погода сейчас\n'
                             '🌅 Восход/закат\n'
                             '📅 Прогнозы 3, 5 и 10 дней\n'
                             '🌧 Проверка дождя\n'
                             '🌙 Фаза луны\n'
                             '👕 Что надеть\n'
                             '📊 Статистика\n'
                             '🔔 Уведомления\n'
                             '⚙️ Смена города\n'
                             '🌐 Смена языка\n'
                             '🔑 Статус подписки',
        'help_features_sub': '🌤 Погода сейчас\n'
                             '🌅 Восход/закат\n'
                             '📅 Прогноз 3, 5, 10 дней\n'
                             '🌧 Проверить дождь\n'
                             '🌙 Фаза луны\n'
                             '👕 Что надеть\n'
                             '📊 Статистика\n'
                             '🔔 Уведомления\n'
                             '⚙️ Сменить город\n'
                             '🌐 Сменить язык\n'
                             '🔑 Статус подписки',
        'help_features_free': '🌤 Погода сейчас (бесплатно)\n'
                              '⚙️ Сменить город (бесплатно)\n'
                              '🔑 Статус подписки (бесплатно)\n'
                              '🌐 Сменить язык (бесплатно)',
        'help_buy': '\n💰 Купите подписку для доступа ко всем функциям!',
        'weather_title': '☀️ *{city}, {country}*',
        'weather_temp': '🌡 Температура: *{temp}°C*',
        'weather_feels': '🤔 Ощущается как: *{feels}°C*',
        'weather_humidity': '💧 Влажность: *{humidity}%*',
        'weather_wind': '🌬 Ветер: *{wind} м/с*',
        'weather_desc': '☁️ {description}',
        'weather_sources': '\n\n📡 Источников: *{count}* из 3\n📊 Использованы: {sources}',
        'weather_updated': '\n\n🕐 Обновлено: {time}',
        'sunrise_title': '🌅 *Восход и закат* для *{city}*',
        'sunrise_time': '🌅 Восход: *{sunrise}*',
        'sunset_time': '🌇 Закат: *{sunset}*',
        'day_length': '⏳ Длина дня: *{length}*',
        'forecast_title': '📅 *ПРОГНОЗ НА {days} ДНЕЙ*\n📍 *{city}*\n\n',
        'forecast_day': '🌤 *{date} ({weekday})*\n'
                        '   {temp}°C  |  {description}\n'
                        '   🌧️ Осадки: {rain} мм  🌬 Ветер: {wind} м/с\n'
                        '\n',
        'rain_expected': '{emoji} *В {city} сегодня будет дождь!*\n'
                         '\n'
                         'Осадки: *{rain} мм* ({intensity})\n'
                         '☔ Не забудьте зонт!',
        'no_rain': '☀️ Сегодня дождя не ожидается.',
        'moon_title': '🌙 *Фаза луны*\n\n{emoji} *{name}*\n\n📅 {date}',
        'clothing_title': '👕 *Рекомендации* для *{city}*\n'
                          '\n'
                          '🌡 {temp}°C | {description}\n'
                          '🌬 Ветер: {wind} м/с\n'
                          '\n'
                          '*Рекомендуется:*\n',
        'clothing_item': '• {item}\n',
        'agri_title': '🌾 *АГРО-ПРОГНОЗ*\n📍 *{city}*',
        'agri_soil': '🌡 Температура почвы: *{temp}°C*',
        'agri_humidity': '💧 Влажность: *{humidity}%*',
        'agri_rain': '🌧 Осадки: *{rain} мм*',
        'agri_frost': '❄️ Заморозки: {frost}',
        'agri_rec': '\n🌱 *Рекомендации:*\n{rec}',
        'construction_title': '🏗️ *СТРОИТЕЛЬНЫЙ ПРОГНОЗ*\n📍 *{city}*',
        'construction_wind': '💨 Ветер: *{wind} м/с* {safe}',
        'construction_rain': '🌧 Осадки: *{rain} мм*',
        'construction_temp': '🌡 Температура: *{temp}°C*',
        'construction_rec': '\n🏗️ *Рекомендации:*\n{rec}',
        'tourism_title': '✈️ *ТУРИСТИЧЕСКИЙ ПРОГНОЗ*\n📍 *{city}*',
        'tourism_weather': '☀️ Погода: *{weather}*',
        'tourism_temp': '🌡 Температура: *{temp}°C*',
        'tourism_sunrise': '🌅 Восход: *{sunrise}*',
        'tourism_sunset': '🌇 Закат: *{sunset}*',
        'tourism_uv': '☀️ UV-индекс: *{uv}* ({level})',
        'tourism_rec': '\n⭐ *Рекомендации:*\n{rec}',
        'notification_on': '🔔 *Уведомления включены!*\n'
                           '\n'
                           'Я буду присылать вам уведомления о:\n'
                           '🌧 Дожде\n'
                           '💨 Сильном ветре\n'
                           '❄️ Морозе\n'
                           '☀️ Жаре',
        'notification_off': '🔕 *Уведомления выключены*',
        'stats_title': '📊 *СТАТИСТИКА ПОГОДЫ ЗА {days} ДНЕЙ*\n📍 *{city}*',
        'stats_avg': '🌡 Средняя: *{avg}°C*',
        'stats_max': '📈 Максимальная: *{max}°C*',
        'stats_min': '📉 Минимальная: *{min}°C*',
        'stats_rain': '🌧 Дождливых дней: *{days}*',
        'stats_clear': '☀️ Ясных дней: *{days}*',
        'stats_cloudy': '☁️ Пасмурных дней: *{days}*',
        'stats_total': '💧 Всего осадков: *{rain} мм*',
        'btn_weather': '🌤 Погода сейчас',
        'btn_sunrise': '🌅 Восход/закат',
        'btn_f3': '📅 Прогноз 3 дня',
        'btn_f5': '📅 Прогноз 5 дней',
        'btn_f10': '📅 Прогноз 10 дней',
        'btn_rain': '🌧 Проверить дождь',
        'btn_moon': '🌙 Фаза луны',
        'btn_clothing': '👕 Что надеть',
        'btn_stats': '📊 Статистика',
        'btn_agro': '🌾 Агро-прогноз',
        'btn_construction': '🏗️ Строительный',
        'btn_tourism': '✈️ Туристический',
        'btn_notifications': '🔔 Уведомления',
        'btn_change_city': '⚙️ Сменить город',
        'btn_change_lang': '🌐 Сменить язык',
        'btn_help': '❓ Помощь',
        'btn_subscription': '🔑 Статус подписки',
        'btn_buy': '💰 Купить подписку',
        'btn_buy_b2b': '💰 Купить B2B',
        'btn_personal': '👤 Личная подписка',
        'btn_agriculture': '🌾 Сельское хозяйство',
        'btn_construction_sub': '🏗️ Строительство',
        'btn_tourism_sub': '✈️ Туризм',
        'btn_business_sub': '🏢 Бизнес (Все включено)',
        'btn_back': '🔙 Назад',
        'select_language_short': '💳 *Выберите тариф:*',
        'b2b_agriculture_name': 'Сельское хозяйство',
        'b2b_agriculture_features': '✈️ Поездки\n'
                                    '📅 Прогноз на 10 дней\n'
                                    '🌡 Агро-прогноз\n'
                                    '🌧 Осадки для полива\n'
                                    '❄️ Прогноз заморозков\n'
                                    '📊 Статистика\n'
                                    '🔔 Уведомления',
        'b2b_construction_name': 'Строительство',
        'b2b_construction_features': '✈️ Поездки\n'
                                     '📅 Прогноз на 10 дней\n'
                                     '💨 Прогноз ветра\n'
                                     '🌧 Осадки\n'
                                     '🌡 Температура\n'
                                     '📊 Статистика\n'
                                     '🔔 Уведомления',
        'b2b_tourism_name': 'Туризм',
        'b2b_tourism_features': '✈️ Поездки\n'
                                '📅 Прогноз на 10 дней\n'
                                '🌅 Восход/закат\n'
                                '☀️ UV-индекс\n'
                                '🌧 Осадки\n'
                                '📊 Статистика\n'
                                '🔔 Уведомления',
        'b2b_business_name': 'Бизнес (Все включено)',
        'b2b_business_features': '✈️ Поездки\n'
                                '🤖 AI-помощник\n'
                                '📅 Прогноз на 10 дней\n'
                                 '📊 Полная статистика\n'
                                 '🔔 Все уведомления\n'
                                 '🌾 Агро-прогноз\n'
                                 '🏗️ Строительный\n'
                                 '✈️ Туристический\n'
                                 '📈 Приоритетная поддержка\n📢 Автопостинг\n🖼 Погодные карточки\n🔑 API\n👥 Команды\n📊 Аналитика\n🏷 White-label',
        'already_b2b': '✅ У вас уже есть активная B2B подписка!',
        'already_subscription': '✅ У вас уже есть активная подписка!',
        'invoice_error': '❌ Ошибка создания счёта. Попробуйте позже.',
        'unknown_plan': '❌ Неизвестный тариф',
        'already_same_subscription': '✅ У вас уже есть активная эта подписка!',
        'back_main': '🔙 Возврат в главное меню',
        'b2b_only': '🔒 *Эта функция доступна только по B2B подписке!*\n\n💰 Выберите B2B тариф:',
        'city_not_set': 'не указан',
        'weather_error': '❌ Не удалось получить данные о погоде. Попробуйте позже.',
        'forecast_error': '❌ Не удалось получить прогноз. Попробуйте позже.',
        'stats_error': '❌ Не удалось получить статистику. Попробуйте позже.',
        'agri_error': '❌ Не удалось получить агропрогноз. Попробуйте позже.',
        'construction_error': '❌ Не удалось получить прогноз для строительства. Попробуйте позже.',
        'tourism_error': '❌ Не удалось получить туристический прогноз. Попробуйте позже.',
        'invoice_title_personal': '🌤 Личная подписка на МетеоБот',
        'invoice_description_personal': 'Доступ ко всем основным функциям бота на 1 месяц',
        'invoice_month': '1 месяц',
        'invoice_pay': 'Оплатите в Telegram.',
        'included': 'Включено:',
        'status_active': '🟢 Активна',
        'status_expiring': '🟡 Скоро закончится',
        'status_ending': '🔴 Заканчивается!',
        'intensity_light': 'лёгкий',
        'intensity_moderate': 'умеренный',
        'intensity_heavy': 'сильный',
        'moon_new': 'Новолуние',
        'moon_waxing_crescent': 'Молодая луна',
        'moon_first_quarter': 'Первая четверть',
        'moon_waxing_gibbous': 'Прибывающая луна',
        'moon_full': 'Полнолуние',
        'moon_waning_gibbous': 'Убывающая луна',
        'moon_last_quarter': 'Последняя четверть',
        'moon_old': 'Старая луна',
        'error_no_data_forecast': '❌ Нет данных прогноза',
        'weekday_0': 'ПН',
        'weekday_1': 'ВТ',
        'weekday_2': 'СР',
        'weekday_3': 'ЧТ',
        'weekday_4': 'ПТ',
        'weekday_5': 'СБ',
        'weekday_6': 'ВС',
        'error_generic': '❌ Произошла ошибка. Попробуйте позже.',
        'forecast_word': 'прогноз',
        'frost_expected': '❌ Ожидаются',
        'frost_not_expected': '✅ Не ожидаются',
        'agri_rec_frost': '❄️ Защитите посевы от заморозков',
        'agri_rec_wet': '🌧️ Избыток влаги — отложите полив',
        'agri_rec_water': '💧 Рекомендуется полив',
        'agri_rec_heat': '☀️ Жарко — защитите растения от солнца',
        'agri_rec_good': '🌱 Условия благоприятные для работ',
        'construction_rec_safe': '✅ Работа на высоте безопасна',
        'construction_rec_wind': '❌ Опасно для кранов и высотных работ',
        'construction_rec_rain': '🌧️ Отложите бетонные работы',
        'construction_rec_frost': '❄️ Бетон замерзает — используйте добавки',
        'construction_rec_heat': '☀️ Жарко — работайте в тени'},
 'en': {'welcome': '🌤 *Welcome to WeatherBot!*\n'
                   '\n'
                   '🏙️ *To get started, enter your city.*\n'
                   '\n'
                   'Send the city name in reply.',
        'start_with_city': '🌤 *Welcome to WeatherBot!*\n\n📍 Current city: *{city}*\n\n',
        'free_mode': '🔒 *Free mode*\n'
                     'Available: Current weather, Change city, Subscription status, Help, Change language\n'
                     '\n',
        'buy_prompt': '💰 Buy subscription: *{price}⭐ per month*',
        'subscription_active': '✅ *Subscription active!* ({days} days left)\nAll features available.',
        'b2b_active': '{icon} *{name}* subscription active!\n⏳ Left: *{days}* days.\nAll tariff features available!',
        'no_city': '🏙️ *Please specify your city first!*\n\nSend the city name.',
        'city_not_found': "❌ '{city}' not found. Try another city.",
        'city_saved': '✅ City *{city}* saved! Now you can use the bot.',
        'city_changed': '✅ City changed to *{city}*',
        'enter_city': '🏙️ *Send the city name*\n\nExample: `London`',
        'select_language': '🌐 *Select your language:*',
        'language_changed': '✅ Language changed to *{language_name}*',
        'subscription_status': '🔑 *Subscription status*',
        'subscription_active_status': '{status}\n📅 Until: *{expiry}*\n⏳ Left: *{days}* days',
        'subscription_inactive': '❌ No active subscription\n'
                                 '\n'
                                 '💰 *Choose a plan:*\n'
                                 '\n'
                                 '👤 Personal: *{personal}⭐*\n'
                                 '🌾 Agriculture: *{agri}⭐*\n'
                                 '🏗️ Construction: *{const}⭐*\n'
                                 '✈️ Tourism: *{tour}⭐*\n'
                                 '🏢 Business: *{business}⭐*',
        'only_subscribed': '🔒 *This feature is only available with subscription!*\n'
                           '\n'
                           '💰 *Choose a plan:*\n'
                           '\n'
                           '👤 Personal: *{personal}⭐*\n'
                           '🌾 Agriculture: *{agri}⭐*\n'
                           '🏗️ Construction: *{const}⭐*\n'
                           '✈️ Tourism: *{tour}⭐*\n'
                           '🏢 Business: *{business}⭐*',
        'invoice_created': '💳 *Invoice created!*\n\nPay in Telegram.\n💰 Price: *{price}⭐*',
        'payment_success': '✅ *Payment successful!*\n'
                           '\n'
                           '🎉 Subscription activated for {days} days!\n'
                           '\n'
                           'Thank you for your support! 🙌',
        'back': '🔙 Back',
        'buy_subscription': '💰 Buy subscription',
        'buy_b2b': '💰 Buy B2B',
        'change_language': '🌐 Change language',
        'help': '❓ Help',
        'help_title': '📖 *Help*',
        'help_subscribed': '📖 *Help* (Subscription active)',
        'help_free': '📖 *Help* (Free)',
        'help_city': '📍 City: *{city}*',
        'help_days': '⏳ Left: *{days}* days',
        'personal_features': '🌤 Current weather\n'
                             '🌅 Sunrise/sunset\n'
                             '📅 3, 5 and 10-day forecasts\n'
                             '🌧 Rain check\n'
                             '🌙 Moon phase\n'
                             '👕 What to wear\n'
                             '📊 Statistics\n'
                             '🔔 Notifications\n'
                             '⚙️ Change city\n'
                             '🌐 Change language\n'
                             '🔑 Subscription status',
        'help_features_sub': '🌤 Current weather\n'
                             '🌅 Sunrise/Sunset\n'
                             '📅 3, 5, 10 day forecast\n'
                             '🌧 Rain check\n'
                             '🌙 Moon phase\n'
                             '👕 What to wear\n'
                             '📊 Statistics\n'
                             '🔔 Notifications\n'
                             '⚙️ Change city\n'
                             '🌐 Change language\n'
                             '🔑 Subscription status',
        'help_features_free': '🌤 Current weather (free)\n'
                              '⚙️ Change city (free)\n'
                              '🔑 Subscription status (free)\n'
                              '🌐 Change language (free)',
        'help_buy': '\n💰 Buy subscription to access all features!',
        'weather_title': '☀️ *{city}, {country}*',
        'weather_temp': '🌡 Temperature: *{temp}°C*',
        'weather_feels': '🤔 Feels like: *{feels}°C*',
        'weather_humidity': '💧 Humidity: *{humidity}%*',
        'weather_wind': '🌬 Wind: *{wind} m/s*',
        'weather_desc': '☁️ {description}',
        'weather_sources': '\n\n📡 Sources: *{count}* of 3\n📊 Used: {sources}',
        'weather_updated': '\n\n🕐 Updated: {time}',
        'sunrise_title': '🌅 *Sunrise and sunset* for *{city}*',
        'sunrise_time': '🌅 Sunrise: *{sunrise}*',
        'sunset_time': '🌇 Sunset: *{sunset}*',
        'day_length': '⏳ Day length: *{length}*',
        'forecast_title': '📅 *{days}-DAY FORECAST*\n📍 *{city}*\n\n',
        'forecast_day': '🌤 *{date} ({weekday})*\n'
                        '   {temp}°C  |  {description}\n'
                        '   🌧️ Rain: {rain} mm  🌬 Wind: {wind} m/s\n'
                        '\n',
        'rain_expected': '{emoji} *Rain expected in {city} today!*\n'
                         '\n'
                         'Rain: *{rain} mm* ({intensity})\n'
                         "☔ Don't forget your umbrella!",
        'no_rain': '☀️ No rain expected today.',
        'moon_title': '🌙 *Moon phase*\n\n{emoji} *{name}*\n\n📅 {date}',
        'clothing_title': '👕 *Recommendations* for *{city}*\n'
                          '\n'
                          '🌡 {temp}°C | {description}\n'
                          '🌬 Wind: {wind} m/s\n'
                          '\n'
                          '*Recommended:*\n',
        'clothing_item': '• {item}\n',
        'agri_title': '🌾 *AGRO-FORECAST*\n📍 *{city}*',
        'agri_soil': '🌡 Soil temperature: *{temp}°C*',
        'agri_humidity': '💧 Humidity: *{humidity}%*',
        'agri_rain': '🌧 Rain: *{rain} mm*',
        'agri_frost': '❄️ Frost: {frost}',
        'agri_rec': '\n🌱 *Recommendations:*\n{rec}',
        'construction_title': '🏗️ *CONSTRUCTION FORECAST*\n📍 *{city}*',
        'construction_wind': '💨 Wind: *{wind} m/s* {safe}',
        'construction_rain': '🌧 Rain: *{rain} mm*',
        'construction_temp': '🌡 Temperature: *{temp}°C*',
        'construction_rec': '\n🏗️ *Recommendations:*\n{rec}',
        'tourism_title': '✈️ *TOURISM FORECAST*\n📍 *{city}*',
        'tourism_weather': '☀️ Weather: *{weather}*',
        'tourism_temp': '🌡 Temperature: *{temp}°C*',
        'tourism_sunrise': '🌅 Sunrise: *{sunrise}*',
        'tourism_sunset': '🌇 Sunset: *{sunset}*',
        'tourism_uv': '☀️ UV index: *{uv}* ({level})',
        'tourism_rec': '\n⭐ *Recommendations:*\n{rec}',
        'notification_on': '🔔 *Notifications enabled!*\n'
                           '\n'
                           'I will send alerts about:\n'
                           '🌧 Rain\n'
                           '💨 Strong wind\n'
                           '❄️ Frost\n'
                           '☀️ Heat',
        'notification_off': '🔕 *Notifications disabled*',
        'stats_title': '📊 *WEATHER STATISTICS FOR {days} DAYS*\n📍 *{city}*',
        'stats_avg': '🌡 Average: *{avg}°C*',
        'stats_max': '📈 Maximum: *{max}°C*',
        'stats_min': '📉 Minimum: *{min}°C*',
        'stats_rain': '🌧 Rainy days: *{days}*',
        'stats_clear': '☀️ Clear days: *{days}*',
        'stats_cloudy': '☁️ Cloudy days: *{days}*',
        'stats_total': '💧 Total rain: *{rain} mm*',
        'btn_weather': '🌤 Current weather',
        'btn_sunrise': '🌅 Sunrise/Sunset',
        'btn_f3': '📅 Forecast 3 days',
        'btn_f5': '📅 Forecast 5 days',
        'btn_f10': '📅 Forecast 10 days',
        'btn_rain': '🌧 Rain check',
        'btn_moon': '🌙 Moon phase',
        'btn_clothing': '👕 What to wear',
        'btn_stats': '📊 Statistics',
        'btn_agro': '🌾 Agro-forecast',
        'btn_construction': '🏗️ Construction',
        'btn_tourism': '✈️ Tourism',
        'btn_notifications': '🔔 Notifications',
        'btn_change_city': '⚙️ Change city',
        'btn_change_lang': '🌐 Change language',
        'btn_help': '❓ Help',
        'btn_subscription': '🔑 Subscription status',
        'btn_buy': '💰 Buy subscription',
        'btn_buy_b2b': '💰 Buy B2B',
        'btn_personal': '👤 Personal subscription',
        'btn_agriculture': '🌾 Agriculture',
        'btn_construction_sub': '🏗️ Construction',
        'btn_tourism_sub': '✈️ Tourism',
        'btn_business_sub': '🏢 Business (All included)',
        'btn_back': '🔙 Back',
        'select_language_short': '💳 *Choose a plan:*',
        'b2b_agriculture_name': 'Agriculture',
        'b2b_agriculture_features': '✈️ Trip forecasts\n'
                                    '📅 10-day forecast\n'
                                    '🌡 Agriculture forecast\n'
                                    '🌧 Irrigation precipitation\n'
                                    '❄️ Frost forecast\n'
                                    '📊 Statistics\n'
                                    '🔔 Notifications',
        'b2b_construction_name': 'Construction',
        'b2b_construction_features': '✈️ Trip forecasts\n'
                                     '📅 10-day forecast\n'
                                     '💨 Wind forecast\n'
                                     '🌧 Precipitation\n'
                                     '🌡 Temperature\n'
                                     '📊 Statistics\n'
                                     '🔔 Notifications',
        'b2b_tourism_name': 'Tourism',
        'b2b_tourism_features': '✈️ Trip forecasts\n'
                                '📅 10-day forecast\n'
                                '🌅 Sunrise/sunset\n'
                                '☀️ UV index\n'
                                '🌧 Precipitation\n'
                                '📊 Statistics\n'
                                '🔔 Notifications',
        'b2b_business_name': 'Business (All included)',
        'b2b_business_features': '✈️ Trip forecasts\n'
                                '🤖 AI assistant\n'
                                '📅 10-day forecast\n'
                                 '📊 Full statistics\n'
                                 '🔔 All notifications\n'
                                 '🌾 Agriculture forecast\n'
                                 '🏗️ Construction\n'
                                 '✈️ Tourism\n'
                                 '📈 Priority support\n📢 Auto-posting\n🖼 Weather cards\n🔑 API\n👥 Teams\n📊 Analytics\n🏷 White-label',
        'already_b2b': '✅ You already have an active B2B subscription!',
        'already_subscription': '✅ You already have an active subscription!',
        'invoice_error': '❌ Could not create the invoice. Please try again later.',
        'unknown_plan': '❌ Unknown plan',
        'already_same_subscription': '✅ You already have this subscription active!',
        'back_main': '🔙 Back to main menu',
        'b2b_only': '🔒 *This feature is available only with a B2B subscription!*\n\n💰 Choose a B2B plan:',
        'city_not_set': 'not set',
        'weather_error': '❌ Could not get weather data. Please try again later.',
        'forecast_error': '❌ Could not get the forecast. Please try again later.',
        'temp': '🌡 Temperature: {temp}°C',
        'feels_like': '🤔 Feels like: {feels}°C',
        'wind_full': '💨 Wind: {wind} m/s, {direction}',
        'humidity': '💧 Humidity: {humidity}%',
        'pressure_mm': '📊 Pressure: {pressure} mmHg',
        'uv_with_level': '☀️ UV index: {uv} ({level})',
        'uv_simple': '☀️ UV index: {uv}',
        'updated_time': '🕐 Updated: {time}',
        'precip_prob': '🌧 Precipitation probability: {prob}%',
        'sunrise': '🌅 Sunrise: {time}',
        'sunset': '🌇 Sunset: {time}',
        'forecast_title': '📅 *Forecast for {days_text} — {city}*\n\n',
        'forecast_day_line': '🌡 +{min}°...+{max}° (feels +{feels}°)',
        'forecast_wind_line': '💨 {wind} m/s, {dir} | 💧 {hum}%',
        'forecast_pressure': '📊 {pressure} mm',
        'forecast_uv_line': ' | ☀️ UV {uv} ({level})',
        'forecast_precip': '🌧 Precipitation: {prob}% ({mm} mm)',
        'cloudy_default': 'Cloudy',
        'day_1': 'day', 'day_2_4': 'days', 'day_5_plus': 'days',
        'wind_n': 'N', 'wind_nne': 'NNE', 'wind_ne': 'NE', 'wind_ene': 'ENE',
        'wind_e': 'E', 'wind_ese': 'ESE', 'wind_se': 'SE', 'wind_sse': 'SSE',
        'wind_s': 'S', 'wind_ssw': 'SSW', 'wind_sw': 'SW', 'wind_wsw': 'WSW',
        'wind_w': 'W', 'wind_wnw': 'WNW', 'wind_nw': 'NW', 'wind_nnw': 'NNW',
        'uv_low': 'low', 'uv_moderate': 'moderate', 'uv_high': 'high',
        'uv_very_high': 'very high', 'uv_extreme': 'extreme',
        'temp': '🌡 Temperature: {temp}°C',
        'feels_like': '🤔 Feels like: {feels}°C',
        'wind_full': '💨 Wind: {wind} m/s, {direction}',
        'humidity': '💧 Humidity: {humidity}%',
        'pressure_mm': '📊 Pressure: {pressure} mmHg',
        'uv_with_level': '☀️ UV index: {uv} ({level})',
        'uv_simple': '☀️ UV index: {uv}',
        'updated_time': '🕐 Updated: {time}',
        'precip_prob': '🌧 Precipitation probability: {prob}%',
        'sunrise': '🌅 Sunrise: {time}',
        'sunset': '🌇 Sunset: {time}',
        'forecast_title': '📅 *Forecast for {days_text} — {city}*\n\n',
        'forecast_day_line': '🌡 +{min}°...+{max}° (feels +{feels}°)',
        'forecast_wind_line': '💨 {wind} m/s, {dir} | 💧 {hum}%',
        'forecast_pressure': '📊 {pressure} mm',
        'forecast_uv_line': ' | ☀️ UV {uv} ({level})',
        'forecast_precip': '🌧 Precipitation: {prob}% ({mm} mm)',
        'cloudy_default': 'Cloudy',
        'day_1': 'day', 'day_2_4': 'days', 'day_5_plus': 'days',
        'wind_n': 'N', 'wind_nne': 'NNE', 'wind_ne': 'NE', 'wind_ene': 'ENE',
        'wind_e': 'E', 'wind_ese': 'ESE', 'wind_se': 'SE', 'wind_sse': 'SSE',
        'wind_s': 'S', 'wind_ssw': 'SSW', 'wind_sw': 'SW', 'wind_wsw': 'WSW',
        'wind_w': 'W', 'wind_wnw': 'WNW', 'wind_nw': 'NW', 'wind_nnw': 'NNW',
        'uv_low': 'low', 'uv_moderate': 'moderate', 'uv_high': 'high',
        'uv_very_high': 'very high', 'uv_extreme': 'extreme',
        'stats_error': '❌ Could not get statistics. Please try again later.',
        'agri_error': '❌ Could not get the agriculture forecast. Please try again later.',
        'construction_error': '❌ Could not get the construction forecast. Please try again later.',
        'tourism_error': '❌ Could not get the tourism forecast. Please try again later.',
        'invoice_title_personal': '🌤 WeatherBot Personal Subscription',
        'invoice_description_personal': 'Access to all main bot features for 1 month',
        'invoice_month': '1 month',
        'invoice_pay': 'Pay in Telegram.',
        'included': 'Included:',
        'status_active': '🟢 Active',
        'status_expiring': '🟡 Expiring soon',
        'status_ending': '🔴 Expiring!',
        'intensity_light': 'light',
        'intensity_moderate': 'moderate',
        'intensity_heavy': 'heavy',
        'moon_new': 'New moon',
        'moon_waxing_crescent': 'Waxing crescent',
        'moon_first_quarter': 'First quarter',
        'moon_waxing_gibbous': 'Waxing gibbous',
        'moon_full': 'Full moon',
        'moon_waning_gibbous': 'Waning gibbous',
        'moon_last_quarter': 'Last quarter',
        'moon_old': 'Waning crescent',
        'error_no_data_forecast': '❌ No forecast data available',
        'weekday_0': 'MON',
        'weekday_1': 'TUE',
        'weekday_2': 'WED',
        'weekday_3': 'THU',
        'weekday_4': 'FRI',
        'weekday_5': 'SAT',
        'weekday_6': 'SUN',
        'error_generic': '❌ An error occurred. Please try again later.',
        'forecast_word': 'forecast',
        'frost_expected': '❌ Expected',
        'frost_not_expected': '✅ Not expected',
        'agri_rec_frost': '❄️ Protect crops from frost',
        'agri_rec_wet': '🌧️ Too much moisture — postpone irrigation',
        'agri_rec_water': '💧 Irrigation is recommended',
        'agri_rec_heat': '☀️ Hot weather — protect plants from the sun',
        'agri_rec_good': '🌱 Conditions are favorable for work',
        'construction_rec_safe': '✅ Work at height is safe',
        'construction_rec_wind': '❌ Dangerous for cranes and work at height',
        'construction_rec_rain': '🌧️ Postpone concrete work',
        'construction_rec_frost': '❄️ Concrete may freeze — use additives',
        'construction_rec_heat': '☀️ Hot weather — work in the shade'},
}
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
app.secret_key = SECRET_KEY

# ============================================================
#  ФУНКЦИЯ ДЛЯ ПОЛУЧЕНИЯ ТЕКСТА
# ============================================================


# New unified tariff / B2B feature labels. Kept here so the legacy bot UI remains
# fully multilingual and all buttons are visible on every plan.
_NEW_TEXTS = {
    "ru": {
        "btn_trip":"✈️ Поездка","btn_tomorrow":"📅 Погода на завтра","btn_ai":"🤖 AI-помощник","btn_favorites":"⭐ Города",
        "btn_autopost":"📢 Автопостинг","btn_card":"🖼 Погодная карточка",
        "btn_api":"🔑 API","btn_team":"👥 Команда","btn_whitelabel":"🏷 White-label",
        "btn_analytics":"📊 Аналитика",
        "premium_required_paywall":"🔒 *Функция доступна в Premium.*\n\nОформите подписку, чтобы открыть поездки, AI, уведомления и расширенные функции.",
        "business_required":"🔒 *Функция доступна в Business.*\n\nBusiness включает все возможности Premium + автопостинг, карточки, API, команды, аналитику и White-label.",
        "trip_city":"✈️ *Поездка*\n\nНапишите город назначения.","trip_days":"📅 На сколько дней нужна поездка? Выберите число от 1 до 10.",
        "trip_result":"✈️ *Прогноз поездки: {city}*\n\n{result}",
        "ai_button":"🤖 *AI-помощник*\n\nНапишите вопрос о погоде, поездке или о том, что лучше сделать сегодня.",
        "notification_menu":"🔔 *Уведомления*\n\nНажмите ещё раз, чтобы включить или выключить погодные уведомления.",
        "whitelabel_menu":"🏷 *White-label*\n\nBusiness: /white_label NAME",
        "analytics_menu":"📊 *Аналитика*\n\nBusiness: статистика подключённых каналов и публикаций.",
        "autopost_menu":"📢 *Автопостинг*\n\nBusiness позволяет автоматически публиковать погоду в Telegram-канале.\n\nКоманды:\n/channel @channel CITY 08:00 — добавить канал\n/channels — мои каналы",
        "card_menu":"🖼 Погодная карточка\n\nBusiness: /generate_card CITY",
        "api_menu":"🔑 *API*\n\nBusiness: /apikey — создать API-ключ.",
        'api_btn_create': '🔑 Создать API-ключ',
        'api_btn_help': '📖 Документация',
        'api_btn_city': '🏙 Установить город',
        'api_btn_stats': '📊 Статистика',
        'api_btn_profile': '👤 Мой профиль',
        'api_btn_delete': '🗑 Удалить ключи',
        'api_key_created': '🔑 API-ключ создан:\n`{api_key}`',
        'api_key_error': '❌ Ошибка создания ключа. Проверьте подписку Business.',
        'api_key_limit': '❌ Достигнут лимит: 5 API-ключей. Удалите старые через «🗑 Удалить ключи».',
        'api_help_title': '📖 API Документация',
        'api_help_base': '🌍 Базовый URL:',
        'api_help_endpoints': '📍 Эндпоинты:',
        'api_help_ep_weather': '• GET /weather?city=Город',
        'api_help_ep_forecast': '• GET /forecast?city=Город&days=5',
        'api_help_ep_me': '• GET /me',
        'api_help_auth': '🔑 Авторизация:',
        'api_help_header': 'Заголовок: X-API-Key: ваш_ключ',
        'api_help_default': '🏙 Город по умолчанию: {city}',
        'api_help_limits': '📊 Лимиты:',
        'api_help_limit_keys': '• Максимум 5 API ключей',
        'api_help_limit_req': '• 100 запросов в час на ключ',
        'api_help_example': '💡 Пример:',
        'api_set_city_prompt': '🏙 Введите город по умолчанию для API запросов:',
        'api_profile_title': '📊 Ваш API Профиль',
        'api_profile_id': '🆔 User ID: {id}',
        'api_profile_keys': '🔑 API ключей: {count}',
        'api_profile_city': '🏙 Город по умолчанию: {city}',
        'api_profile_first': '📅 Первая активность: {date}',
        'api_stats_empty': '📊 Статистика API\n\nВы ещё не использовали API.',
        'api_stats_title': '📊 Статистика API',
        'api_stats_total': '📈 Всего: {total}',
        'api_stats_24h': '🕐 24ч: {h24}',
        'api_stats_7d': '📅 7 дней: {d7}',
        'api_stats_by_ep': 'По эндпоинтам:',
        'api_deleted': '🗑 Удалено API-ключей: {count}',
        'api_city_not_set': 'не установлен',
        'city_added': '✅ Город добавлен в избранные.',
        'city_add_failed': '❌ Не удалось добавить город: {result}',
        'city_removed': '✅ Город удалён.',
        'city_not_found': '❌ Такой город не найден.',
        'api_enter_city_short': '🏙 Введите город для API:',
        'api_city_set': '✅ Город для API: *{city}*',
        'card_ready': '🖼 Карточка готова.',
        'card_error': '🖼 Не удалось создать карточку',
        'card_error_generic': '❌ Ошибка: {err}',
        'logo_save_error': '❌ Не удалось сохранить логотип.',

        "team_menu":"👥 *Команда*\n\nBusiness: /team create NAME\n/team add TEAM_ID USER_ID [ROLE]",
        "whitelabel_menu":"🏷 *White-label*\n\nBusiness: /white_label NAME",
        "analytics_menu":"📊 *Аналитика*\n\nBusiness: статистика подключённых каналов и публикаций."
    },
    "en": {
        "btn_trip":"✈️ Trip","btn_tomorrow":"📅 Tomorrow Weather","btn_ai":"🤖 AI Assistant","btn_favorites":"⭐ Cities",
        "btn_autopost":"📢 Auto-posting","btn_card":"🖼 Weather Card",
        "btn_api":"🔑 API","btn_team":"👥 Team","btn_whitelabel":"🏷 White-label",
        "btn_analytics":"📊 Analytics",
        "premium_required_paywall":"🔒 *This feature is available in Premium.*\n\nSubscribe to unlock trips, AI, notifications and advanced features.",
        "business_required":"🔒 *This feature is available in Business.*\n\nBusiness includes all Premium features plus auto-posting, cards, API, teams, analytics and white-label.",
        "trip_city":"✈️ *Trip*\n\nSend the destination city.","trip_days":"📅 How many days? Choose a number from 1 to 10.",
        "trip_result":"✈️ *Trip forecast: {city}*\n\n{result}","ai_button":"🤖 *AI Assistant*\n\nSend a question about the weather, your trip, or what to do today.",
        "autopost_menu":"📢 *Auto-posting*\n\nBusiness can automatically publish weather to Telegram channels.\n\nCommands:\n/channel @channel CITY 08:00 — add a channel\n/channels — my channels",
        "card_menu":"🖼 Weather Card\n\nBusiness: /generate_card CITY",
        "api_menu":"🔑 *API*\n\nBusiness: /apikey — create an API key.",
        'api_btn_create': '🔑 Create API Key',
        'api_btn_help': '📖 Documentation',
        'api_btn_city': '🏙 Set City',
        'api_btn_stats': '📊 Statistics',
        'api_btn_profile': '👤 My Profile',
        'api_btn_delete': '🗑 Delete Keys',
        'api_key_created': '🔑 API key created:\n`{api_key}`',
        'api_key_error': '❌ Error creating key. Check Business subscription.',
        'api_key_limit': '❌ Limit reached: 5 API keys. Delete old ones via «🗑 Delete keys».',
        'api_help_title': '📖 API Documentation',
        'api_help_base': '🌍 Base URL:',
        'api_help_endpoints': '📍 Endpoints:',
        'api_help_ep_weather': '• GET /weather?city=City',
        'api_help_ep_forecast': '• GET /forecast?city=City&days=5',
        'api_help_ep_me': '• GET /me',
        'api_help_auth': '🔑 Authorization:',
        'api_help_header': 'Header: X-API-Key: your_key',
        'api_help_default': '🏙 Default city: {city}',
        'api_help_limits': '📊 Limits:',
        'api_help_limit_keys': '• Maximum 5 API keys',
        'api_help_limit_req': '• 100 requests per hour per key',
        'api_help_example': '💡 Example:',
        'api_set_city_prompt': '🏙 Enter default city for API requests:',
        'api_profile_title': '📊 Your API Profile',
        'api_profile_id': '🆔 User ID: {id}',
        'api_profile_keys': '🔑 API keys: {count}',
        'api_profile_city': '🏙 Default city: {city}',
        'api_profile_first': '📅 First activity: {date}',
        'api_stats_empty': '📊 API Statistics\n\nYou have not used the API yet.',
        'api_stats_title': '📊 API Statistics',
        'api_stats_total': '📈 Total: {total}',
        'api_stats_24h': '🕐 24h: {h24}',
        'api_stats_7d': '📅 7 days: {d7}',
        'api_stats_by_ep': 'By endpoints:',
        'api_deleted': '🗑 Deleted API keys: {count}',
        'api_city_not_set': 'not set',
        'city_added': '✅ City added to favorites.',
        'city_add_failed': '❌ Failed to add city: {result}',
        'city_removed': '✅ City removed.',
        'city_not_found': '❌ City not found.',
        'api_enter_city_short': '🏙 Enter city for API:',
        'api_city_set': '✅ City for API: *{city}*',
        'card_ready': '🖼 Card is ready.',
        'card_error': '🖼 Failed to create card',
        'card_error_generic': '❌ Error: {err}',
        'logo_save_error': '❌ Failed to save logo.',

        "team_menu":"👥 *Team*\n\nBusiness: /team create NAME\n/team add TEAM_ID USER_ID [ROLE]",
        "whitelabel_menu":"🏷 *White-label*\n\nBusiness: /white_label NAME",
        "analytics_menu":"📊 *Analytics*\n\nBusiness: connected-channel and posting statistics."
    },
}
for _lang_key, _items in _NEW_TEXTS.items():
    TEXTS.setdefault(_lang_key, {}).update(_items)
_EXTRA_UI_TEXTS = {
"ru":{"cities_title":"⭐ *Мои города*","cities_empty":"Пока нет сохранённых городов.","cities_choose":"Выберите город:","city_added":"✅ Город *{city}* добавлен.","city_removed":"✅ Город *{city}* удалён.","city_not_in_favorites":"❌ Такой город не найден в списке.","notification_settings":"🔔 *Настройки уведомлений*\n\nСтатус: {status}\n🌧 Дождь: {rain}\n💨 Сильный ветер: {wind}\n❄️ Мороз: {frost}\n☀️ Жара: {heat}\n🕘 Время: *{time}*\n📍 Город: *{city}*","notification_enabled":"✅ Включены","notification_disabled":"🔕 Выключены","notification_city_prompt":"📍 Напишите город, для которого нужны уведомления.","notification_time_prompt":"🕘 Напишите время в формате HH:MM, например 08:00.","notification_time_saved":"✅ Время уведомлений установлено: *{time}*","notification_city_saved":"✅ Город уведомлений установлен: *{city}*","notification_rain":"🌧 Дождь","notification_wind":"💨 Сильный ветер","notification_frost":"❄️ Мороз","notification_heat":"☀️ Жара","notification_time":"🕘 Время","notification_city":"📍 Город","notification_toggle":"🔔 Включить / выключить","notification_back":"🔙 Назад","notification_frequency":"📅 Периодичность","notification_freq_daily":"Ежедневно","notification_freq_weekly":"Еженедельно","notification_freq_weekdays":"Будни","notification_freq_weekends":"Выходные","notification_freq_saved":"✅ Периодичность установлена: *{freq}*",
        'alert_title': '⚠️ *Предупреждения о погоде на завтра*',
        'alert_heat': '🔥 *Жара!* Макс. температура {temp}°C (порог {thr}°C). Пейте больше воды, избегайте солнца.',
        'alert_frost': '❄️ *Мороз!* Мин. температура {temp}°C (порог {thr}°C). Одевайтесь тепло.',
        'alert_wind': '💨 *Сильный ветер!* До {speed} м/с (порог {thr} м/с). Будьте осторожны на улице.',
        'alert_rain': '🌧 *Дождь!* Осадки {mm} мм. Возьмите зонт.',
        'alert_heavy_rain': '⛈ *Сильный дождь!* Осадки {mm} мм (порог {thr} мм). Осторожно, возможны подтопления.',
        'alert_storm': '⛈ *Гроза!* {desc}. Избегайте открытых пространств.',
        'alert_no_city': '❌ Не удалось получить прогноз для уведомлений.',
        'threshold_heat': '🔥 Порог жары',
        'threshold_frost': '❄️ Порог мороза',
        'threshold_wind': '💨 Порог ветра',
        'threshold_rain': '🌧 Порог дождя',
        'threshold_heavy_rain': '⛈ Порог ливня',
        'threshold_current': 'Текущий порог: *{thr}*',
        'threshold_heat_prompt': '🔥 Введите температуру жары (°C):',
        'threshold_frost_prompt': '❄️ Введите температуру мороза (°C):',
        'threshold_wind_prompt': '💨 Введите скорость ветра (м/с):',
        'threshold_rain_prompt': '🌧 Введите количество осадков (мм):',
        'threshold_heavy_rain_prompt': '⛈ Введите количество осадков (мм):',
        'threshold_saved': '✅ Порог установлен: *{thr}*',
        'thresholds_title': '\n\n*Текущие пороги:*',
        'thresholds_line1': '\n🔥 Жара: {heat}°C | ❄️ Мороз: {frost}°C',
        'thresholds_line2': '\n💨 Ветер: {wind} м/с | 🌧 Дождь: {rain} мм',
        'thresholds_line3': '\n⛈ Ливень: {heavy} мм',},
"en":{"cities_title":"⭐ *My cities*","cities_empty":"No saved cities yet.","cities_choose":"Choose a city:","city_added":"✅ City *{city}* added.","city_removed":"✅ City *{city}* removed.","city_not_in_favorites":"❌ This city is not in your list.","notification_settings":"🔔 *Notification settings*\n\nStatus: {status}\n🌧 Rain: {rain}\n💨 Strong wind: {wind}\n❄️ Frost: {frost}\n☀️ Heat: {heat}\n🕘 Time: *{time}*\n📍 City: *{city}*","notification_enabled":"✅ Enabled","notification_disabled":"🔕 Disabled","notification_city_prompt":"📍 Send the city for notifications.","notification_time_prompt":"🕘 Send time in HH:MM format, e.g. 08:00.","notification_time_saved":"✅ Notification time set: *{time}*","notification_city_saved":"✅ Notification city set: *{city}*","notification_rain":"🌧 Rain","notification_wind":"💨 Strong wind","notification_frost":"❄️ Frost","notification_heat":"☀️ Heat","notification_time":"🕘 Time","notification_city":"📍 City","notification_toggle":"🔔 Enable / disable","notification_back":"🔙 Back","notification_frequency":"📅 Frequency","notification_freq_daily":"Daily","notification_freq_weekly":"Weekly","notification_freq_weekdays":"Weekdays","notification_freq_weekends":"Weekends","notification_freq_saved":"✅ Frequency set: *{freq}*",
        'alert_title': '⚠️ *Weather alerts for tomorrow*',
        'alert_heat': '🔥 *Heat!* Max temp {temp}°C (threshold {thr}°C). Drink water, avoid sun.',
        'alert_frost': '❄️ *Frost!* Min temp {temp}°C (threshold {thr}°C). Dress warmly.',
        'alert_wind': '💨 *Strong wind!* Up to {speed} m/s (threshold {thr} m/s). Be careful outside.',
        'alert_rain': '🌧 *Rain!* Precipitation {mm} mm. Take an umbrella.',
        'alert_heavy_rain': '⛈ *Heavy rain!* Precipitation {mm} mm (threshold {thr} mm). Caution, possible flooding.',
        'alert_storm': '⛈ *Storm!* {desc}. Avoid open areas.',
        'alert_no_city': '❌ Failed to get forecast for notifications.',
        'threshold_heat': '🔥 Heat threshold',
        'threshold_frost': '❄️ Frost threshold',
        'threshold_wind': '💨 Wind threshold',
        'threshold_rain': '🌧 Rain threshold',
        'threshold_heavy_rain': '⛈ Heavy rain threshold',
        'threshold_current': 'Current threshold: *{thr}*',
        'threshold_heat_prompt': '🔥 Enter heat temperature (°C):',
        'threshold_frost_prompt': '❄️ Enter frost temperature (°C):',
        'threshold_wind_prompt': '💨 Enter wind speed (m/s):',
        'threshold_rain_prompt': '🌧 Enter precipitation (mm):',
        'threshold_heavy_rain_prompt': '⛈ Enter precipitation (mm):',
        'threshold_saved': '✅ Threshold set: *{thr}*',
        'thresholds_title': '\n\n*Current thresholds:*',
        'thresholds_line1': '\n🔥 Heat: {heat}°C | ❄️ Frost: {frost}°C',
        'thresholds_line2': '\n💨 Wind: {wind} m/s | 🌧 Rain: {rain} mm',
        'thresholds_line3': '\n⛈ Heavy rain: {heavy} mm',},
}
for _lang_key, _items in _EXTRA_UI_TEXTS.items():
    TEXTS.setdefault(_lang_key, {}).update(_items)

# Final product UI: only Premium and Business are public plans.
TEXTS["ru"].update({
    'temp': '🌡 Температура: {temp}°C',
    'feels_like': '🤔 Ощущается как: {feels}°C',
    'wind_full': '💨 Ветер: {wind} м/с, {direction}',
    'humidity': '💧 Влажность: {humidity}%',
    'pressure_mm': '📊 Давление: {pressure} мм рт.ст.',
    'uv_with_level': '☀️ UV-индекс: {uv} ({level})',
    'uv_simple': '☀️ UV-индекс: {uv}',
    'updated_time': '🕐 Обновлено: {time}',
    'precip_prob': '🌧 Вероятность осадков: {prob}%',
    'sunrise': '🌅 Восход: {time}',
    'sunset': '🌇 Закат: {time}',
    'forecast_title': '📅 *Прогноз на {days_text} — {city}*\n\n',
    'forecast_day_line': '🌡 +{min}°...+{max}° (ощущ. +{feels}°)',
    'forecast_wind_line': '💨 {wind} м/с, {dir} | 💧 {hum}%',
    'forecast_pressure': '📊 {pressure} мм',
    'forecast_uv_line': ' | ☀️ UV {uv} ({level})',
    'forecast_precip': '🌧 Осадки: {prob}% ({mm} мм)',
    'cloudy_default': 'Облачно',
    'day_1': 'день', 'day_2_4': 'дня', 'day_5_plus': 'дней',
    'uv_low': 'низкий', 'uv_moderate': 'умеренный', 'uv_high': 'высокий',
    'uv_very_high': 'очень высокий', 'uv_extreme': 'экстремальный',
})

for _lang_code in LANGUAGES:
    _fallback = TEXTS.get(_lang_code, TEXTS["en"])
    _fallback.update({
        "btn_personal": "⭐ Premium",
        "btn_business_sub": "🏢 Business",
        "btn_add_city": {"ru": "➕ Добавить город", "en": "➕ Add city", "es": "➕ Añadir ciudad", "zh": "➕ 添加城市", "fr": "➕ Ajouter une ville", "de": "➕ Stadt hinzufügen", "ja": "➕ 都市を追加", "ko": "➕ 도시 추가", "it": "➕ Aggiungi città", "hi": "➕ शहर जोड़ें", "ar": "➕ إضافة مدينة"}.get(_lang_code, "➕ Add city"),
        "btn_remove_city": {"ru": "➖ Удалить город", "en": "➖ Remove city", "es": "➖ Eliminar ciudad", "zh": "➖ 删除城市", "fr": "➖ Supprimer une ville", "de": "➖ Stadt entfernen", "ja": "➖ 都市を削除", "ko": "➖ 도시 삭제", "it": "➖ Rimuovi città", "hi": "➖ शहर हटाएं", "ar": "➖ إزالة مدينة"}.get(_lang_code, "➖ Remove city"),
        "btn_wl_name": {"ru": "✏️ Название", "en": "✏️ Name", "es": "✏️ Nombre", "zh": "✏️ 名称", "fr": "✏️ Nom", "de": "✏️ Name", "ja": "✏️ 名前", "ko": "✏️ 이름", "it": "✏️ Nome", "hi": "✏️ नाम", "ar": "✏️ الاسم"}.get(_lang_code, "✏️ Name"),
        "btn_wl_color": {"ru": "🎨 Цвет", "en": "🎨 Color", "es": "🎨 Color", "zh": "🎨 颜色", "fr": "🎨 Couleur", "de": "🎨 Farbe", "ja": "🎨 色", "ko": "🎨 색상", "it": "🎨 Colore", "hi": "🎨 रंग", "ar": "🎨 اللون"}.get(_lang_code, "🎨 Color"),
        "btn_wl_logo": {"ru": "🖼 Логотип", "en": "🖼 Logo", "es": "🖼 Logo", "zh": "🖼 标志", "fr": "🖼 Logo", "de": "🖼 Logo", "ja": "🖼 ロゴ", "ko": "🖼 로고", "it": "🖼 Logo", "hi": "🖼 लोगो", "ar": "🖼 الشعار"}.get(_lang_code, "🖼 Logo"),
        "favorites_menu": "⭐ *Мои города*\n\nВыберите действие:" if _lang_code == "ru" else "⭐ *My cities*\n\nChoose an action:",
        "favorite_add_prompt": "➕ Напишите название города для добавления." if _lang_code == "ru" else "➕ Send the city name to add.",
        "favorite_remove_prompt": "➖ Напишите название города для удаления." if _lang_code == "ru" else "➖ Send the city name to remove.",
        "card_ready": "🖼 Карточка готова." if _lang_code == "ru" else "🖼 Card is ready.",
        "card_prompt": "🖼 Погодная карточка для текущего города." if _lang_code == "ru" else "🖼 Weather card for the current city.",
        "wl_menu_working": "🏢 *White-label*\n\nНастройте название, цвет и логотип вашего бренда." if _lang_code == "ru" else "🏢 *White-label*\n\nConfigure your brand name, color and logo.",
        "wl_name_prompt": "✏️ Напишите новое название бренда." if _lang_code == "ru" else "✏️ Send the new brand name.",
        "wl_color_prompt": "🎨 Напишите цвет в HEX, например #2563EB." if _lang_code == "ru" else "🎨 Send a HEX color, e.g. #2563EB.",
        "wl_logo_prompt": "🖼 Отправьте изображение логотипа следующим сообщением." if _lang_code == "ru" else "🖼 Send the logo image as the next message.",
        "wl_saved": "✅ Настройки White-label сохранены." if _lang_code == "ru" else "✅ White-label settings saved.",
        "invalid_action": "❌ Используйте кнопки меню или команду." if _lang_code == "ru" else "❌ Use the menu buttons or a command.",
        "city_input_only": "🏙️ Сейчас бот ожидает название города. Используйте кнопку «Сменить город» или отмените действие." if _lang_code == "ru" else "🏙️ The bot is waiting for a city name. Use Change city or cancel.",
    })
    # Hide legacy plan names from all user-facing subscription messages.
    _fallback["subscription_inactive"] = "❌ *Подписка неактивна*\n\n⭐ Premium: *{premium}⭐*\n🏢 Business: *{business}⭐*" if _lang_code == "ru" else "❌ *No active subscription*\n\n⭐ Premium: *{premium}⭐*\n🏢 Business: *{business}⭐*"
    _fallback["only_subscribed"] = "🔒 *Функция доступна по подписке.*\n\n⭐ Premium: *{premium}⭐*\n🏢 Business: *{business}⭐*" if _lang_code == "ru" else "🔒 *Subscription required.*\n\n⭐ Premium: *{premium}⭐*\n🏢 Business: *{business}⭐*"

def T(language, key, **kwargs):
    language = language if language in LANGUAGES else "en"
    text = TEXTS.get(language, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
    try:
        return text.format(**kwargs)
    except Exception:
        return text

def get_user_lang(chat_id):
    try:
        lang_file = f"user_lang_{chat_id}.json"
        if os.path.exists(lang_file):
            with open(lang_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('lang', 'ru')
    except:
        pass
    return 'ru'

def set_user_lang(chat_id, lang):
    try:
        with open(f"user_lang_{chat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({'lang': lang}, f)
        return True
    except:
        return False

# ============================================================
#  РАБОТА С ПОЛЬЗОВАТЕЛЯМИ (JSON)
# ============================================================

def get_user_city(chat_id):
    """Возвращает город пользователя."""
    try:
        # Пробуем прочитать из users_city.json напрямую
        import json, os
        cities_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users_city.json")
        cities = {}
        if os.path.exists(cities_path):
            with open(cities_path, 'r', encoding='utf-8') as f:
                cities = json.load(f)
        
        # Преобразуем chat_id в строку для поиска
        city = cities.get(str(chat_id))
        if city:
            logger.info(f"get_user_city: found city repr={repr(city)} for chat_id={chat_id}")
            return city
        
        # Если не нашли - проверяем features.json
        features_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "features.json")
        if os.path.exists(features_path):
            with open(features_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
            user = db.get("users", {}).get(str(chat_id), {})
            city = user.get("city")
            if city:
                logger.info(f"get_user_city: found city '{city}' in features.json for chat_id={chat_id}")
                return city
        
        logger.info(f"get_user_city: city not found for chat_id={chat_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка get_user_city: {e}", exc_info=True)
        return None


def save_user_city(chat_id, city):
    try:
        data = {}
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data[str(chat_id)] = city.strip()
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения города: {e}")
        return False

def _load_json_file(path, default=None):
    default = {} if default is None else default
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, type(default)) else default
    except Exception as e:
        logger.error(f"Ошибка чтения {path}: {e}")
    return default

def _save_json_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка записи {path}: {e}")
        return False

def _clear_b2b_entitlement(chat_id):
    key = str(chat_id)
    try:
        data = _load_json_file(B2B_FILE, {})
        if key in data:
            data.pop(key, None)
            _save_json_file(B2B_FILE, data)
    except Exception:
        pass

def get_current_plan(chat_id):
    """Return exactly one active plan: free, premium or business.
    Expired subscriptions are automatically downgraded to free.
    """
    key = str(chat_id)
    data = _load_json_file(SUBSCRIPTIONS_FILE, {})
    sub = data.get(key)
    if not isinstance(sub, dict):
        return "free"
    raw_expiry = sub.get("expiry")
    try:
        expiry = datetime.fromisoformat(raw_expiry) if raw_expiry else None
    except (TypeError, ValueError):
        expiry = None

    if not expiry or expiry <= datetime.now():
        # Automatic expiry cleanup: old B2B rights must not survive.
        changed = False
        if sub.get("plan") != "free" or sub.get("b2b_type"):
            sub["plan"] = "free"
            sub["b2b_type"] = None
            changed = True
        if changed:
            data[key] = sub
            _save_json_file(SUBSCRIPTIONS_FILE, data)
        _clear_b2b_entitlement(chat_id)
        return "free"

    plan = sub.get("plan")
    if plan in ("premium", "business"):
        return plan
    # Backward compatibility with old data.
    if sub.get("b2b_type") == "business":
        return "business"
    if sub.get("b2b_type"):
        return "business"
    return "premium"

def is_user_subscribed(chat_id):
    return get_current_plan(chat_id) != "free"

def get_user_b2b_type(chat_id):
    """Return active B2B type only for the current active subscription."""
    plan = get_current_plan(chat_id)
    if plan != "business":
        return None
    data = _load_json_file(B2B_FILE, {})
    item = data.get(str(chat_id), {})
    if isinstance(item, dict):
        raw_expiry = item.get("expiry")
        try:
            if raw_expiry and datetime.fromisoformat(raw_expiry) > datetime.now():
                return item.get("type")
        except (TypeError, ValueError):
            pass
    sub = _load_json_file(SUBSCRIPTIONS_FILE, {}).get(str(chat_id), {})
    return sub.get("b2b_type") if isinstance(sub, dict) else None

def set_user_subscription(chat_id, days=30, b2b_type=None, plan=None):
    """Set the user's single current entitlement.

    Same-plan purchases extend the existing expiry.
    Switching plans replaces the current entitlement immediately.
    Business/Premium rights are never accumulated.
    """
    try:
        data = _load_json_file(SUBSCRIPTIONS_FILE, {})
        now = datetime.now()
        key = str(chat_id)
        existing = data.get(key, {}) if isinstance(data.get(key, {}), dict) else {}
        old_plan = get_current_plan(chat_id)
        if plan is None:
            plan = "business" if b2b_type else "premium"

        # Same plan = renewal/extension; different plan = immediate switch.
        try:
            existing_expiry = datetime.fromisoformat(existing.get("expiry")) if existing.get("expiry") else None
        except (TypeError, ValueError):
            existing_expiry = None
        if old_plan == plan and existing_expiry and existing_expiry > now:
            base_date = existing_expiry
        else:
            base_date = now

        expiry_date = base_date + timedelta(days=int(days))
        data[key] = {
            "plan": plan,
            "expiry": expiry_date.isoformat(),
            "activated_by": "payment_b2b" if plan == "business" else "payment",
            "activated_at": now.isoformat(),
            "b2b_type": b2b_type if plan == "business" else None,
        }
        _save_json_file(SUBSCRIPTIONS_FILE, data)

        # Keep the legacy B2B registry synchronized with the CURRENT plan only.
        b2b_data = _load_json_file(B2B_FILE, {})
        if plan == "business":
            b2b_data[key] = {
                "type": b2b_type or "business",
                "activated_at": now.isoformat(),
                "expiry": expiry_date.isoformat(),
                "source": "payment",
            }
        else:
            b2b_data.pop(key, None)
        _save_json_file(B2B_FILE, b2b_data)

        # Ensure the user exists in the registry.
        users = _load_json_file(USERS_FILE, {})
        if key not in users:
            users[key] = {"city": None, "registered": now.isoformat(), "source": "payment"}
            _save_json_file(USERS_FILE, users)

        logger.info(
            f"SUBSCRIPTION: user={chat_id} old_plan={old_plan} new_plan={plan} "
            f"expiry={expiry_date.isoformat()} b2b={b2b_type or '-'}"
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка установки подписки для {chat_id}: {e}", exc_info=True)
        return False

def get_user_subscription(chat_id):
    data = _load_json_file(SUBSCRIPTIONS_FILE, {})
    sub = data.get(str(chat_id))
    if isinstance(sub, dict):
        # Calling this also performs expiry synchronization.
        get_current_plan(chat_id)
        return _load_json_file(SUBSCRIPTIONS_FILE, {}).get(str(chat_id))
    return None

def get_notification_status(chat_id):
    try:
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(str(chat_id), {}).get('enabled', False)
    except:
        pass
    return False

def set_notification_status(chat_id, enabled):
    try:
        data = {}
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data[str(chat_id)] = {
            'enabled': enabled,
            'updated_at': datetime.now().isoformat()
        }
        with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения уведомлений: {e}")
        return False

# ============================================================
#  ФУНКЦИИ ПОГОДЫ (СОКРАЩЕННЫЕ)
# ============================================================

def get_uv_level(uv, lang="ru"):
    if uv is None:
        return None
    try:
        uv = float(uv)
    except (TypeError, ValueError):
        return None
    if uv < 3:
        return T(lang, "uv_low")
    elif uv < 6:
        return T(lang, "uv_moderate")
    elif uv < 8:
        return T(lang, "uv_high")
    elif uv < 11:
        return T(lang, "uv_very_high")
    else:
        return T(lang, "uv_extreme")
def convert_pressure_to_mmhg(pressure_hpa):
    """Конвертирует давление из гектопаскалей (hPa) в миллиметры ртутного столба (мм рт.ст.)."""
    if pressure_hpa is None:
        return None
    # 1 hPa = 0.750062 мм рт.ст.
    return round(pressure_hpa * 0.750062, 1)

def get_weather_aggregated(city_name, lang="en"):
    results = []
    errors = []

    try:
        owm_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric&lang={api_language(lang)}"
        resp = requests.get(owm_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results.append({
                "temp": data['main']['temp'],
                "humidity": data['main']['humidity'],
                "wind": data['wind']['speed'],
                "wind_deg": data['wind'].get('deg', 0),
                "pressure": data['main'].get('pressure'),
                "description": data['weather'][0]['description'],
                "weather_id": data['weather'][0].get('id', 0),
                "source": "OpenWeatherMap"
            })
        else:
            errors.append(f"OWM: {resp.status_code}")
    except Exception as e:
        errors.append(f"OWM: {str(e)}")

    try:
        wa_url = f"https://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={city_name}&lang={api_language(lang)}"
        wa_resp = requests.get(wa_url, timeout=10)
        if wa_resp.status_code == 200:
            data = wa_resp.json()
            results.append({
                "temp": data['current']['temp_c'],
                "humidity": data['current']['humidity'],
                "wind": data['current']['wind_kph'] / 3.6,
                "wind_deg": data['current'].get('wind_degree', 0),
                "pressure": data['current'].get('pressure_mb'),
                "uv": data['current'].get('uv'),
                "description": data['current']['condition']['text'],
                "source": "WeatherAPI"
            })
        else:
            errors.append(f"WeatherAPI: {wa_resp.status_code}")
    except Exception as e:
        errors.append(f"WeatherAPI: {str(e)}")

    try:
        geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url, timeout=5)
        if geo_resp.status_code == 200:
            geo = geo_resp.json()
            lat, lon = geo['coord']['lat'], geo['coord']['lon']
            om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            om_resp = requests.get(om_url, timeout=10)
            if om_resp.status_code == 200:
                data = om_resp.json()['current_weather']
                results.append({
                    "temp": data['temperature'],
                    "wind": data['windspeed'],
                    "wind_deg": data.get('winddirection', 0),
                    "weathercode": data.get('weathercode', 0),
                    "source": "Open-Meteo"
                })
            else:
                errors.append(f"Open-Meteo: {om_resp.status_code}")
    except Exception as e:
        errors.append(f"Open-Meteo: {str(e)}")

    if not results:
        error_msg = "; ".join(errors) if errors else "Нет данных от API"
        return {"error": f"Не удалось получить погоду: {error_msg}"}

    avg_temp = sum(r['temp'] for r in results) / len(results)
    humidity_values = [r.get('humidity', 50) for r in results if 'humidity' in r]
    avg_humidity = sum(humidity_values) / len(humidity_values) if humidity_values else 50
    wind_values = [r['wind'] for r in results if 'wind' in r]
    avg_wind = sum(wind_values) / len(wind_values) if wind_values else 0
    
    # Среднее направление ветра
    wind_deg_values = [r.get('wind_deg') for r in results if r.get('wind_deg') is not None]
    avg_wind_deg = sum(wind_deg_values) / len(wind_deg_values) if wind_deg_values else 0
    
    # Среднее давление (конвертируем из hPa в мм рт.ст.)
    pressure_values = [r.get('pressure') for r in results if r.get('pressure')]
    avg_pressure_hpa = sum(pressure_values) / len(pressure_values) if pressure_values else None
    avg_pressure = convert_pressure_to_mmhg(avg_pressure_hpa) if avg_pressure_hpa else None
    
    # UV индекс (берём из WeatherAPI если есть)
    uv_values = [r.get('uv') for r in results if r.get('uv') is not None]
    avg_uv = sum(uv_values) / len(uv_values) if uv_values else None
    descriptions = [r.get('description') for r in results if r.get('description')]
    if descriptions:
        from collections import Counter
        desc_counter = Counter(descriptions)
        description = desc_counter.most_common(1)[0][0]
    else:
        description = T(lang, "weather_unknown")

    return {
        "city": city_name,
        "country": "RU",
        "temp": round(avg_temp, 1),
        "feels_like": round(avg_temp - 1, 1),
        "humidity": round(avg_humidity),
        "description": description,
        "wind_speed": round(avg_wind, 1),
        "wind_deg": round(avg_wind_deg),
        "pressure": round(avg_pressure, 1) if avg_pressure else None,
        "uv": round(avg_uv, 1) if avg_uv else None,
        "weather_id": next((r.get('weather_id') for r in results if r.get('weather_id')), None),
        "source_count": len(results),
        "sources": [r['source'] for r in results]
    }

def get_forecast_aggregated(city_name, days=10, lang="en"):
    daily_data = {}
    lat = lon = None
    daily_min_temps = {}
    daily_max_temps = {}
    daily_weather_codes = {}
    daily_uv_max = {}
    daily_precip_sum = {}

    try:
        owm_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric&lang={api_language(lang)}"
        resp = requests.get(owm_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            _coord = data.get('city', {}).get('coord', {})
            if _coord:
                lat, lon = _coord.get('lat'), _coord.get('lon')
            for item in data['list']:
                date = item['dt_txt'].split()[0]
                if date not in daily_data:
                    daily_data[date] = {"temps": [], "descriptions": [], "rains": [], "winds": [], "wind_degs": [], "humidities": [], "pressures": [], "weather_codes": [], "feels": [], "precip_probs": []}
                daily_data[date]["temps"].append(item['main']['temp'])
                daily_data[date]["descriptions"].append(item['weather'][0]['description'])
                daily_data[date]["rains"].append(item.get('rain', {}).get('3h', 0))
                daily_data[date]["winds"].append(item['wind']['speed'])
                if item.get("wind", {}).get("deg") is not None:
                    daily_data[date]["wind_degs"].append(float(item["wind"]["deg"]))
    except Exception as e:
        logger.error(f"OWM Forecast ошибка: {e}")

    try:
        if lat is None:
            geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
            geo_resp = requests.get(geo_url, timeout=5)
            if geo_resp.status_code == 200:
                geo = geo_resp.json()
                lat, lon = geo['coord']['lat'], geo['coord']['lon']
        if lat is not None:
            om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,precipitation_probability,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,uv_index&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_sum,wind_speed_10m_max&timezone=auto&forecast_days=14"
            om_resp = requests.get(om_url, timeout=10)
            if om_resp.status_code == 200:
                data = om_resp.json()
                for i, time in enumerate(data['hourly']['time']):
                    date = time.split('T')[0]
                    if date not in daily_data:
                        daily_data[date] = {"temps": [], "descriptions": [], "rains": [], "winds": [], "wind_degs": [], "humidities": [], "pressures": [], "weather_codes": [], "feels": [], "precip_probs": []}
                    daily_data[date]["temps"].append(data['hourly']['temperature_2m'][i])
                    daily_data[date]["rains"].append(data['hourly']['precipitation'][i])
                    daily_data[date]["winds"].append(data['hourly']['wind_speed_10m'][i])
                    if data['hourly'].get('wind_direction_10m'):
                        daily_data[date]["wind_degs"].append(float(data['hourly']['wind_direction_10m'][i]))
    except Exception as e:
        logger.error(f"Open-Meteo Forecast ошибка: {e}")

    if not daily_data:
        return {"error": T(lang, "error_no_data_forecast")}

    def _wind_direction(degrees):
        if not degrees:
            return "—"
        import math as _math
        sx = sum(_math.sin(_math.radians(x)) for x in degrees)
        cx = sum(_math.cos(_math.radians(x)) for x in degrees)
        angle = (_math.degrees(_math.atan2(sx, cx)) + 360) % 360
        return wind_deg_to_direction(angle, lang)

    result = {}
    days_list = sorted(daily_data.keys())[:days]
    
    # Инициализируем daily данные (могут быть не заполнены если Open-Meteo недоступен)
    daily_min_temps = {}
    daily_max_temps = {}
    daily_weather_codes = {}
    daily_uv_max = {}
    daily_precip_sum = {}
    
    # Пытаемся получить daily данные из Open-Meteo если они ещё не загружены
    try:
        geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url, timeout=5)
        if geo_resp.status_code == 200:
            geo = geo_resp.json()
            lat, lon = geo['coord']['lat'], geo['coord']['lon']
            om_daily_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weather_code,uv_index_max,precipitation_sum&timezone=auto&forecast_days=14"
            om_daily_resp = requests.get(om_daily_url, timeout=10)
            if om_daily_resp.status_code == 200:
                daily_info = om_daily_resp.json().get('daily', {})
                daily_dates = daily_info.get('time', [])
                daily_min_temps = {d: t for d, t in zip(daily_dates, daily_info.get('temperature_2m_min', []))}
                daily_max_temps = {d: t for d, t in zip(daily_dates, daily_info.get('temperature_2m_max', []))}
                daily_weather_codes = {d: c for d, c in zip(daily_dates, daily_info.get('weather_code', []))}
                daily_uv_max = {d: u for d, u in zip(daily_dates, daily_info.get('uv_index_max', []))}
                daily_precip_sum = {d: p for d, p in zip(daily_dates, daily_info.get('precipitation_sum', []))}
    except Exception as e:
        logger.error(f"Ошибка получения daily данных: {e}")

    for date in days_list:
        data = daily_data[date]
        if data["temps"]:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            
            # Описание погоды
            descriptions = data.get("descriptions", [])
            if descriptions:
                from collections import Counter
                desc_counter = Counter(descriptions)
                description = desc_counter.most_common(1)[0][0]
            else:
                # По коду погоды из Open-Meteo
                weather_codes = data.get("weather_codes", [])
                if weather_codes:
                    wc = max(set(weather_codes), key=weather_codes.count)
                    if wc in (0, 1):
                        description = "Ясно"
                    elif wc in (2, 3):
                        description = "Переменная облачность"
                    elif 51 <= wc <= 57:
                        description = "Морось"
                    elif 61 <= wc <= 67:
                        description = "Дождь"
                    elif 71 <= wc <= 77:
                        description = "Снег"
                    elif 80 <= wc <= 82:
                        description = "Ливень"
                    elif 95 <= wc <= 99:
                        description = "Гроза"
                    else:
                        description = "Облачно"
                else:
                    description = T(lang, "forecast_word")
            
            # Средние значения
            avg_temp = round(sum(data["temps"]) / len(data["temps"]), 1)
            avg_feels = round(sum(data.get("feels", [avg_temp])) / len(data.get("feels", [avg_temp])), 1) if data.get("feels") else avg_temp
            avg_humidity = round(sum(data.get("humidities", [50])) / len(data.get("humidities", [50]))) if data.get("humidities") else 50
            avg_wind = round(sum(data["winds"]) / len(data["winds"]) / 3.6, 1) if data["winds"] else 0
            avg_pressure = round(sum(data.get("pressures", [1013])) / len(data.get("pressures", [1013])) * 0.750062, 1) if data.get("pressures") else 760
            avg_precip_prob = round(sum(data.get("precip_probs", [0])) / len(data.get("precip_probs", [0]))) if data.get("precip_probs") else 0
            
            # Min/Max температура из daily
            temp_min = daily_min_temps.get(date, min(data["temps"]))
            temp_max = daily_max_temps.get(date, max(data["temps"]))
            
            # UV индекс из daily
            uv_max = daily_uv_max.get(date)
            
            # Суммарные осадки из daily
            precip_sum = daily_precip_sum.get(date, sum(data["rains"]))
            
            result[date] = {
                'date_str': date_obj.strftime("%d.%m.%Y"),
                'weekday': T(lang, f"weekday_{date_obj.weekday()}"),
                'temp': avg_temp,
                'temp_min': round(temp_min, 1),
                'temp_max': round(temp_max, 1),
                'feels_like': avg_feels,
                'description': description,
                'rain': round(precip_sum, 1) if precip_sum else 0,
                'precip_prob': avg_precip_prob,
                'wind_speed': avg_wind,
                'wind_direction': _wind_direction(data.get("wind_degs", [])),
                'humidity': avg_humidity,
                'pressure': avg_pressure,
                'uv': round(uv_max, 1) if uv_max else None
            }

    return result



def get_tomorrow_detailed_forecast(city_name, lang="en"):
    """Получает детальный прогноз на завтрашний день."""
    try:
        # Получаем координаты города
        geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url, timeout=10)
        if geo_resp.status_code != 200:
            return {"error": "Не удалось получить координаты города"}
        
        geo = geo_resp.json()
        lat, lon = geo['coord']['lat'], geo['coord']['lon']
        country = geo.get('sys', {}).get('country', '')
        
        # Получаем прогноз от Open-Meteo (есть все нужные данные)
        om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,uv_index&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_sum,wind_speed_10m_max&timezone=auto&forecast_days=2"
        om_resp = requests.get(om_url, timeout=15)
        
        if om_resp.status_code != 200:
            return {"error": "Не удалось получить прогноз"}
        
        data = om_resp.json()
        
        # Берём данные на завтра (индекс 1, т.к. 0 - сегодня)
        if 'daily' not in data or len(data['daily']['time']) < 2:
            return {"error": "Нет данных на завтра"}
        
        tomorrow = {
            'date': data['daily']['time'][1],
            'temp_max': data['daily']['temperature_2m_max'][1],
            'temp_min': data['daily']['temperature_2m_min'][1],
            'weather_code': data['daily']['weather_code'][1],
            'sunrise': data['daily']['sunrise'][1],
            'sunset': data['daily']['sunset'][1],
            'precipitation_sum': data['daily']['precipitation_sum'][1],
            'wind_max': data['daily']['wind_speed_10m_max'][1],
            'uv_max': data['daily']['uv_index_max'][1],
            'country': country,
            'city': city_name
        }
        
        # Средние значения за день из hourly данных
        # Находим индексы часов для завтрашнего дня
        hourly_times = data['hourly']['time']
        tomorrow_date = tomorrow['date']
        
        hourly_data = {
            'temps': [],
            'humidity': [],
            'pressure': [],
            'uv': [],
            'wind_speed': [],
            'wind_deg': [],
            'precip_prob': [],
            'apparent_temp': []
        }
        
        for i, time_str in enumerate(hourly_times):
            if time_str.startswith(tomorrow_date):
                hourly_data['temps'].append(data['hourly']['temperature_2m'][i])
                hourly_data['humidity'].append(data['hourly']['relative_humidity_2m'][i])
                hourly_data['pressure'].append(data['hourly']['pressure_msl'][i])
                hourly_data['uv'].append(data['hourly']['uv_index'][i])
                hourly_data['wind_speed'].append(data['hourly']['wind_speed_10m'][i])
                hourly_data['wind_deg'].append(data['hourly']['wind_direction_10m'][i])
                hourly_data['precip_prob'].append(data['hourly']['precipitation_probability'][i])
                hourly_data['apparent_temp'].append(data['hourly']['apparent_temperature'][i])
        
        # Считаем средние
        tomorrow['avg_temp'] = round(sum(hourly_data['temps']) / len(hourly_data['temps']), 1) if hourly_data['temps'] else 0
        tomorrow['avg_feels'] = round(sum(hourly_data['apparent_temp']) / len(hourly_data['apparent_temp']), 1) if hourly_data['apparent_temp'] else 0
        tomorrow['avg_humidity'] = round(sum(hourly_data['humidity']) / len(hourly_data['humidity'])) if hourly_data['humidity'] else 0
        tomorrow['avg_pressure'] = round(sum(hourly_data['pressure']) / len(hourly_data['pressure']) * 0.750062, 1) if hourly_data['pressure'] else 0
        tomorrow['avg_uv'] = round(sum(hourly_data['uv']) / len(hourly_data['uv']), 1) if hourly_data['uv'] else 0
        tomorrow['avg_wind'] = round(sum(hourly_data['wind_speed']) / len(hourly_data['wind_speed']) / 3.6, 1) if hourly_data['wind_speed'] else 0
        
        # Среднее направление ветра
        if hourly_data['wind_deg']:
            import math
            sx = sum(math.sin(math.radians(d)) for d in hourly_data['wind_deg'] if d is not None)
            cx = sum(math.cos(math.radians(d)) for d in hourly_data['wind_deg'] if d is not None)
            avg_deg = (math.degrees(math.atan2(sx, cx)) + 360) % 360
            tomorrow['wind_deg'] = round(avg_deg)
        else:
            tomorrow['wind_deg'] = 0
        
        # Средняя вероятность осадков
        tomorrow['precip_prob'] = round(sum(hourly_data['precip_prob']) / len(hourly_data['precip_prob'])) if hourly_data['precip_prob'] else 0
        
        # Описание погоды по коду
        weather_code = tomorrow['weather_code']
        if weather_code in (0, 1):
            tomorrow['description'] = "Ясно"
        elif weather_code in (2, 3):
            tomorrow['description'] = "Переменная облачность"
        elif weather_code in (45, 48):
            tomorrow['description'] = "Туман"
        elif 51 <= weather_code <= 57:
            tomorrow['description'] = "Морось"
        elif 61 <= weather_code <= 67:
            tomorrow['description'] = "Дождь"
        elif 71 <= weather_code <= 77:
            tomorrow['description'] = "Снег"
        elif 80 <= weather_code <= 82:
            tomorrow['description'] = "Ливень"
        elif 85 <= weather_code <= 86:
            tomorrow['description'] = "Снегопад"
        elif 95 <= weather_code <= 99:
            tomorrow['description'] = "Гроза"
        else:
            tomorrow['description'] = "Облачно"
        
        return tomorrow
        
    except Exception as e:
        return {"error": f"Ошибка получения прогноза: {str(e)}"}


def format_tomorrow_forecast_text(chat_id, forecast_data):
    if "error" in forecast_data:
        return f"❌ {forecast_data['error']}"
    from datetime import datetime
    date_obj = datetime.strptime(forecast_data['date'], '%Y-%m-%d')
    lang = get_user_lang(chat_id)
    if lang == "ru":
        weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    else:
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = weekdays[date_obj.weekday()]
    weather_code = forecast_data['weather_code']
    if weather_code in (0, 1): icon = "☀️"
    elif weather_code in (2, 3): icon = "⛅"
    elif weather_code in (45, 48): icon = "🌫"
    elif 51 <= weather_code <= 57: icon = "🌦"
    elif 61 <= weather_code <= 67: icon = "🌧"
    elif 71 <= weather_code <= 77: icon = "❄️"
    elif 80 <= weather_code <= 82: icon = "🌧"
    elif 85 <= weather_code <= 86: icon = "❄️"
    elif 95 <= weather_code <= 99: icon = "⛈"
    else: icon = "☁️"
    wind_dir = wind_deg_to_direction(forecast_data.get('wind_deg'), lang)
    uv_level = get_uv_level(forecast_data.get('uv_max'), lang)
    sunrise = forecast_data.get('sunrise', '').split('T')[1] if 'T' in forecast_data.get('sunrise', '') else '—'
    sunset = forecast_data.get('sunset', '').split('T')[1] if 'T' in forecast_data.get('sunset', '') else '—'
    text = f"📅 {icon} {weekday}, {date_obj.strftime('%d.%m.%Y')}\n\n"
    text += f"📍 {forecast_data['city']}, {forecast_data['country']}\n\n"
    text += T(lang, "temp", temp=f"{forecast_data['temp_min']}...{forecast_data['temp_max']}") + "\n"
    text += T(lang, "feels_like", feels=forecast_data['avg_feels']) + "\n"
    text += T(lang, "wind_full", wind=forecast_data['avg_wind'], direction=wind_dir) + "\n"
    text += T(lang, "humidity", humidity=forecast_data['avg_humidity']) + "\n"
    text += T(lang, "pressure_mm", pressure=forecast_data['avg_pressure']) + "\n"
    if uv_level:
        text += T(lang, "uv_with_level", uv=forecast_data['uv_max'], level=uv_level) + "\n"
    text += T(lang, "precip_prob", prob=forecast_data['precip_prob']) + "\n"
    text += T(lang, "sunrise", time=sunrise) + "\n"
    text += T(lang, "sunset", time=sunset) + "\n\n"
    text += f"{forecast_data['description']}\n\n"
    text += T(lang, "updated_time", time=datetime.now().strftime('%H:%M:%S'))
    return text
def get_weather_statistics(city_name, days=14):
    stats = {
        "avg_temp": 0,
        "max_temp": -100,
        "min_temp": 100,
        "avg_humidity": 0,
        "rain_days": 0,
        "clear_days": 0,
        "cloudy_days": 0,
        "total_rain": 0,
        "days": []
    }

    try:
        geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url, timeout=5)
        if geo_resp.status_code != 200:
            return {"error": "Не удалось получить геоданные"}

        geo = geo_resp.json()
        lat, lon = geo['coord']['lat'], geo['coord']['lon']

        om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&forecast_days=14"
        om_resp = requests.get(om_url, timeout=10)
        if om_resp.status_code == 200:
            data = om_resp.json()
            temps = data['hourly']['temperature_2m'][:24*14]
            rains = data['hourly']['precipitation'][:24*14]

            for i in range(0, len(temps), 24):
                day_temps = temps[i:i+24]
                day_rains = rains[i:i+24]
                if day_temps:
                    avg = sum(day_temps) / len(day_temps)
                    max_t = max(day_temps)
                    min_t = min(day_temps)
                    rain_sum = sum(day_rains)

                    stats["days"].append({
                        "avg": avg,
                        "max": max_t,
                        "min": min_t,
                        "rain": rain_sum
                    })

                    stats["avg_temp"] += avg
                    stats["max_temp"] = max(stats["max_temp"], max_t)
                    stats["min_temp"] = min(stats["min_temp"], min_t)
                    stats["total_rain"] += rain_sum
                    if rain_sum > 0:
                        stats["rain_days"] += 1
                    if rain_sum == 0 and max_t > 20:
                        stats["clear_days"] += 1
                    if rain_sum > 0 and max_t < 15:
                        stats["cloudy_days"] += 1

            if stats["days"]:
                stats["avg_temp"] = round(stats["avg_temp"] / len(stats["days"]), 1)
                stats["max_temp"] = round(stats["max_temp"], 1)
                stats["min_temp"] = round(stats["min_temp"], 1)
                stats["total_rain"] = round(stats["total_rain"], 1)
                stats["city"] = city_name
                return stats

    except Exception as e:
        logger.error(f"Статистика ошибка: {e}")

    return {"error": "Не удалось получить статистику"}

def get_sunrise_sunset(city_name, lang="en"):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric&lang={api_language(lang)}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
            sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
            diff = data['sys']['sunset'] - data['sys']['sunrise']
            return {
                "city": data['name'],
                "country": data['sys']['country'],
                "sunrise": sunrise,
                "sunset": sunset,
                "day_length": f"{int(diff//3600)}ч {int((diff%3600)//60)}м"
            }
        return {"error": f"Ошибка API: {resp.status_code}"}
    except Exception as e:
        return {"error": f"Ошибка: {str(e)}"}

def get_moon_phase(lang="en"):
    today = datetime.now()
    phase = (today.year * 12 + today.month + today.day) % 30
    if phase < 2: key, emoji = "moon_new", "🌑"
    elif phase < 7: key, emoji = "moon_waxing_crescent", "🌒"
    elif phase < 10: key, emoji = "moon_first_quarter", "🌓"
    elif phase < 15: key, emoji = "moon_waxing_gibbous", "🌔"
    elif phase < 18: key, emoji = "moon_full", "🌕"
    elif phase < 23: key, emoji = "moon_waning_gibbous", "🌖"
    elif phase < 26: key, emoji = "moon_last_quarter", "🌗"
    else: key, emoji = "moon_old", "🌘"
    return {"name": T(lang, key), "emoji": emoji}

def get_agri_forecast(city_name, lang="en"):
    weather = get_weather_aggregated(city_name, lang)
    if "error" in weather:
        return {"error": weather["error"]}
    soil_temp = weather['temp'] - 2
    frost = T(lang, "frost_expected") if weather['temp'] < 2 else T(lang, "frost_not_expected")
    recommendations = []
    if weather['temp'] < 0: recommendations.append(T(lang, "agri_rec_frost"))
    if weather.get('rain', 0) > 10: recommendations.append(T(lang, "agri_rec_wet"))
    elif weather.get('rain', 0) < 5: recommendations.append(T(lang, "agri_rec_water"))
    if weather['temp'] > 25: recommendations.append(T(lang, "agri_rec_heat"))
    if not recommendations: recommendations.append(T(lang, "agri_rec_good"))
    return {"city": city_name, "soil_temp": round(soil_temp, 1), "humidity": weather['humidity'], "rain": weather.get('rain', 0), "frost": frost, "recommendations": "\n".join(recommendations)}

def get_construction_forecast(city_name, lang="en"):
    weather = get_weather_aggregated(city_name, lang)
    if "error" in weather:
        return {"error": weather["error"]}
    wind_safe = weather['wind_speed'] < 10
    recommendations = []
    if wind_safe: recommendations.append(T(lang, "construction_rec_safe"))
    else: recommendations.append(T(lang, "construction_rec_wind"))
    if weather.get('rain', 0) > 5: recommendations.append(T(lang, "construction_rec_rain"))
    if weather['temp'] < -5: recommendations.append(T(lang, "construction_rec_frost"))
    if weather['temp'] > 30: recommendations.append(T(lang, "construction_rec_heat"))
    return {"city": city_name, "wind": weather['wind_speed'], "rain": weather.get('rain', 0), "temp": weather['temp'], "wind_safe": wind_safe, "recommendations": "\n".join(recommendations)}

def get_tourism_forecast(chat_id, city_name):
    lang = get_user_lang(chat_id)
    weather = get_weather_aggregated(city_name, lang)
    sun_data = get_sunrise_sunset(city_name, lang)

    if "error" in weather:
        return {"error": weather["error"]}

    uv_index = 3
    if weather['temp'] > 25:
        uv_index = 7
    elif weather['temp'] > 20:
        uv_index = 5
    elif weather['temp'] > 15:
        uv_index = 3
    else:
        uv_index = 1

    uv_levels = {
        "ru": {0: "Низкий", 1: "Низкий", 2: "Низкий", 3: "Средний", 4: "Средний", 5: "Средний", 6: "Высокий", 7: "Высокий", 8: "Очень высокий", 9: "Очень высокий", 10: "Экстремальный"},
        "en": {0: "Low", 1: "Low", 2: "Low", 3: "Moderate", 4: "Moderate", 5: "Moderate", 6: "High", 7: "High", 8: "Very high", 9: "Very high", 10: "Extreme"},
        "es": {0: "Bajo", 1: "Bajo", 2: "Bajo", 3: "Medio", 4: "Medio", 5: "Medio", 6: "Alto", 7: "Alto", 8: "Muy alto", 9: "Muy alto", 10: "Extremo"},
        "zh": {0: "低", 1: "低", 2: "低", 3: "中等", 4: "中等", 5: "中等", 6: "高", 7: "高", 8: "非常高", 9: "非常高", 10: "极端"}
    }

    recommendations = []
    if uv_index > 6:
        if lang == "ru":
            recommendations.append("🧴 Используйте солнцезащитный крем")
        elif lang == "en":
            recommendations.append("🧴 Use sunscreen")
        elif lang == "es":
            recommendations.append("🧴 Use protector solar")
        else:
            recommendations.append("🧴 使用防晒霜")

    if weather.get('rain', 0) > 2:
        if lang == "ru":
            recommendations.append("☔ Возьмите зонт")
        elif lang == "en":
            recommendations.append("☔ Take an umbrella")
        elif lang == "es":
            recommendations.append("☔ Lleva paraguas")
        else:
            recommendations.append("☔ 带伞")

    if weather['temp'] > 25:
        if lang == "ru":
            recommendations.append("💧 Пейте больше воды")
        elif lang == "en":
            recommendations.append("💧 Drink more water")
        elif lang == "es":
            recommendations.append("💧 Bebe más agua")
        else:
            recommendations.append("💧 多喝水")

    if weather['temp'] < 5:
        if lang == "ru":
            recommendations.append("🧥 Одевайтесь теплее")
        elif lang == "en":
            recommendations.append("🧥 Dress warmly")
        elif lang == "es":
            recommendations.append("🧥 Vístete abrigado")
        else:
            recommendations.append("🧥 穿暖和些")

    if not recommendations:
        if lang == "ru":
            recommendations.append("⭐ Отличная погода для прогулок")
        elif lang == "en":
            recommendations.append("⭐ Great weather for walks")
        elif lang == "es":
            recommendations.append("⭐ Buen clima para pasear")
        else:
            recommendations.append("⭐ 散步的好天气")

    return {
        "city": city_name,
        "weather": weather['description'],
        "temp": weather['temp'],
        "sunrise": sun_data.get('sunrise', '--:--') if 'error' not in sun_data else '--:--',
        "sunset": sun_data.get('sunset', '--:--') if 'error' not in sun_data else '--:--',
        "uv": uv_index,
        "uv_level": uv_levels.get(lang, uv_levels["en"]).get(uv_index, uv_levels["en"][3]),
        "recommendations": "\n".join(recommendations)
    }

# ============================================================
#  МУЛЬТИЯЗЫЧНЫЕ РЕКОМЕНДАЦИИ ПО ОДЕЖДЕ
# ============================================================

def get_clothing_recommendations(chat_id, temp, description, wind_speed):
    """Рекомендации одежды с разнообразными фразами (рандомный выбор)."""
    import random
    lang = get_user_lang(chat_id)
    recommendations = []
    
    # Пул фраз: [язык][диапазон] = список категорий, каждая = список вариантов
    CLOTHING = {
        "ru": {
            "freezing": [
                ["🧥 Тёплый пуховик", "🧥 Зимняя парка", "🧥 Пуховик с капюшоном", "🧥 Утеплённая куртка с мехом", "🧥 Длинный пуховик"],
                ["🧶 Шерстяной свитер", "🧶 Термобельё + свитер", "🧶 Флисовая кофта", "🧶 Вязаный кардиган"],
                ["🧤 Тёплые перчатки", "🧤 Варежки с мехом", "🧤 Утеплённые перчатки", "🧤 Кожаные перчатки с мехом"],
                ["🧣 Шарф и шапка", "🧣 Тёплый снуд и шапка", "🧣 Шерстяной шарф и ушанка", "🧣 Балаклава и шапка"],
                ["🥾 Тёплые ботинки", "🥾 Зимние сапоги", "🥾 Утеплённая обувь", "🥾 Сапоги с мехом"],
            ],
            "cold": [
                ["🧥 Зимняя куртка", "🧥 Тёплая куртка", "🧥 Пальто с утеплителем", "🧥 Пуховик со свитером"],
                ["🧤 Перчатки", "🧤 Лёгкие перчатки", "🧤 Варежки"],
                ["🧣 Шарф", "🧣 Лёгкий шарф", "🧣 Снуд", "🧢 Тёплая шапка"],
                ["🥾 Утеплённые ботинки", "🥾 Зимняя обувь", "🥾 Ботинки с мехом"],
            ],
            "cool": [
                ["🧥 Осенняя куртка или пальто", "🧥 Демисезонная куртка", "🧥 Тёплый свитер и куртка", "🧥 Ветровка с подкладкой", "🧥 Тренч со свитером"],
                ["🧣 Лёгкий шарф", "🧣 Шарф или снуд", "🧣 Палантин", "🧢 Лёгкая шапка"],
                ["🥾 Демисезонная обувь", "🥾 Ботинки", "🥾 Непромокаемые кроссовки"],
            ],
            "mild": [
                ["👕 Лёгкая куртка или свитер", "👕 Кофта или худи", "👕 Джинсовка с футболкой", "👕 Кардиган", "👕 Свитшот с лёгкой курткой"],
                ["👖 Джинсы", "👖 Лёгкие брюки", "👖 Чиносы"],
                ["👟 Кроссовки", "👟 Лёгкая обувь", "👟 Лоферы"],
            ],
            "warm": [
                ["👕 Футболка с длинным рукавом", "👕 Лёгкая рубашка", "👕 Лонгслив", "👕 Тонкий свитер", "👕 Футболка с лёгкой рубашкой"],
                ["👖 Лёгкие брюки", "👖 Джинсы", "🩳 Шорты днём"],
                ["👟 Кроссовки", "👟 Сандалии", "👟 Мокасины"],
            ],
            "hot": [
                ["👕 Лёгкая одежда", "👕 Футболка и шорты", "👕 Лёгкое платье или рубашка", "👕 Хлопковая одежда", "👕 Льняной костюм", "👕 Светлая свободная одежда"],
                ["🧢 Головной убор", "🧢 Панама", "🧢 Кепка от солнца", "🕶 Солнечные очки"],
                ["🧴 Солнцезащитный крем", "🧴 SPF-защита", "🧴 Крем от загара", "💧 Бутылка воды"],
                ["🩴 Сандалии", "🩴 Шлёпанцы", "🩴 Лёгкие кроссовки"],
            ],
        },
        "en": {
            "freezing": [
                ["🧥 Warm down jacket", "🧥 Winter parka", "🧥 Hooded puffer jacket", "🧥 Insulated coat"],
                ["🧶 Wool sweater", "🧶 Thermal base + sweater", "🧶 Fleece hoodie"],
                ["🧤 Warm gloves", "🧤 Mittens", "🧤 Insulated gloves"],
                ["🧣 Scarf and hat", "🧣 Warm beanie and scarf"],
                ["🥾 Insulated boots", "🥾 Winter boots"],
            ],
            "cold": [
                ["🧥 Winter jacket", "🧥 Warm coat", "🧥 Puffer with sweater"],
                ["🧤 Gloves", "🧤 Light gloves"],
                ["🧣 Scarf", "🧣 Snood", "🧢 Warm hat"],
                ["🥾 Insulated boots", "🥾 Winter shoes"],
            ],
            "cool": [
                ["🧥 Autumn jacket or coat", "🧥 Light jacket", "🧥 Sweater with jacket"],
                ["🧣 Light scarf", "🧣 Scarf"],
                ["🥾 Autumn shoes", "🥾 Boots"],
            ],
            "mild": [["👕 Light jacket or sweater", "👕 Hoodie", "👕 Cardigan", "👕 Denim jacket"], ["👖 Jeans", "👖 Light pants"], ["👟 Sneakers", "👟 Loafers"]],
            "warm": [["👕 Long-sleeved shirt", "👕 Light sweater", "👕 T-shirt with shirt"], ["👖 Light pants", "🩳 Shorts"], ["👟 Sneakers", "👟 Sandals"]],
            "hot": [
                ["👕 Light clothing", "👕 T-shirt and shorts", "👕 Cotton or linen clothes"],
                ["🧢 Headwear", "🧢 Sun hat", "🕶 Sunglasses"],
                ["🧴 Sunscreen", "🧴 SPF protection", "💧 Water bottle"],
                ["🩴 Sandals", "🩴 Flip-flops"],
            ],
        },
        "es": {
            "freezing": [
                ["🧥 Chaqueta abrigada", "🧥 Parka de invierno", "🧥 Abrigo de plumas"],
                ["🧶 Suéter de lana", "🧶 Ropa térmica"],
                ["🧤 Guantes calientes", "🧤 Manoplas"],
                ["🧣 Bufanda y gorro", "🧣 Bufanda y gorro de lana"],
                ["🥾 Botas de invierno", "🥾 Botas aislantes"],
            ],
            "cold": [
                ["🧥 Chaqueta de invierno", "🧥 Abrigo"],
                ["🧤 Guantes", "🧤 Guantes ligeros"],
                ["🧣 Bufanda", "🧣 Bufanda ligera", "🧢 Gorro"],
                ["🥾 Botas", "🥾 Calzado de invierno"],
            ],
            "cool": [
                ["🧥 Chaqueta de otoño o abrigo", "🧥 Chaqueta ligera", "🧥 Suéter con chaqueta"],
                ["🧣 Bufanda ligera", "🧣 Bufanda"],
                ["🥾 Zapatos de otoño", "🥾 Botines"],
            ],
            "mild": [["👕 Chaqueta ligera o suéter", "👕 Suéter", "👕 Cárdigan"], ["👖 Vaqueros", "👖 Pantalones ligeros"], ["👟 Zapatillas"]],
            "warm": [["👕 Camisa de manga larga", "👕 Camisa ligera"], ["👖 Pantalones ligeros", "🩳 Shorts"], ["👟 Zapatillas", "👟 Sandalias"]],
            "hot": [
                ["👕 Ropa ligera", "👕 Camiseta y shorts", "👕 Ropa de algodón"],
                ["🧢 Sombrero", "🧢 Gorra", "🕶 Gafas de sol"],
                ["🧴 Protector solar", "🧴 Crema solar", "💧 Botella de agua"],
                ["🩴 Sandalias", "🩴 Chanclas"],
            ],
        },
        "zh": {
            "freezing": [["🧥 保暖羽绒服", "🧥 冬季派克大衣", "🧥 连帽羽绒服"], ["🧶 羊毛衫", "🧶 保暖内衣+毛衣"], ["🧤 保暖手套", "🧤 连指手套"], ["🧣 围巾和帽子", "🧣 围巾和毛线帽"], ["🥾 保暖靴", "🥾 雪地靴"]],
            "cold": [["🧥 冬季夹克", "🧥 厚外套"], ["🧤 手套", "🧤 薄手套"], ["🧣 围巾", "🧢 帽子"], ["🥾 保暖鞋", "🥾 冬靴"]],
            "cool": [["🧥 秋季夹克或大衣", "🧥 轻便夹克", "🧥 毛衣加外套"], ["🧣 轻便围巾"], ["🥾 秋季鞋", "🥾 靴子"]],
            "mild": [["👕 轻便夹克或毛衣", "👕 卫衣", "👕 开衫"], ["👖 牛仔裤", "👖 轻便裤"], ["👟 运动鞋"]],
            "warm": [["👕 长袖衬衫", "👕 薄毛衣"], ["👖 轻便裤", "🩳 短裤"], ["👟 运动鞋", "👟 凉鞋"]],
            "hot": [["👕 轻便衣物", "👕 T恤和短裤", "👕 棉麻衣物"], ["🧢 帽子", "🕶 太阳镜"], ["🧴 防晒霜", "💧 水瓶"], ["🩴 凉鞋", "🩴 拖鞋"]],
        },
    }
    
    # Определяем диапазон
    if temp < -10:
        range_key = "freezing"
    elif temp < 0:
        range_key = "cold"
    elif temp < 10:
        range_key = "cool"
    elif temp < 20:
        range_key = "mild"
    elif temp < 25:
        range_key = "warm"
    else:
        range_key = "hot"
    
    lang_pools = CLOTHING.get(lang, CLOTHING["ru"])
    for category in lang_pools.get(range_key, []):
        recommendations.append(random.choice(category))
    
    # Дождь
    if any(w in description.lower() for w in ["дождь", "rain", "lluvia", "雨", "морось", "drizzle"]):
        rain_items = {"ru": ["☂️ Зонт", "☂️ Не забудьте зонт", "☂️ Зонт или дождевик"],
                      "en": ["☂️ Umbrella", "☂️ Take an umbrella"],
                      "es": ["☂️ Paraguas", "☂️ Lleva paraguas"],
                      "zh": ["☂️ 雨伞", "☂️ 带伞"]}
        recommendations.append(random.choice(rain_items.get(lang, rain_items["ru"])))
    
    # Сильный ветер
    if wind_speed > 10:
        wind_items = {"ru": ["🌬️ Ветровка", "🌬️ Куртка от ветра", "🌬️ Непродуваемая куртка"],
                      "en": ["🌬️ Windbreaker", "🌬️ Windproof jacket"],
                      "es": ["🌬️ Rompevientos", "🌬️ Chaqueta cortavientos"],
                      "zh": ["🌬️ 防风夹克", "🌬️ 防风外套"]}
        recommendations.append(random.choice(wind_items.get(lang, wind_items["ru"])))
    
    return recommendations

def get_weather_icon(weather_id=None, description=""):
    """Возвращает эмодзи иконки погоды по weather_id или описанию."""
    desc_lower = str(description).lower()
    
    # По weather_id (OpenWeatherMap)
    if weather_id:
        if 200 <= weather_id < 300:  # Гроза
            return "⛈"
        elif 300 <= weather_id < 400:  # Морось
            return "🌦"
        elif 500 <= weather_id < 600:  # Дождь
            return "🌧"
        elif 600 <= weather_id < 700:  # Снег
            return "❄️"
        elif 700 <= weather_id < 800:  # Туман, дымка
            return "🌫"
        elif weather_id == 800:  # Ясно
            return "☀️"
        elif weather_id == 801:  # Малооблачно
            return "🌤"
        elif weather_id == 802:  # Облачно
            return "⛅"
        elif weather_id in (803, 804):  # Пасмурно
            return "☁️"
    
    # По описанию
    if any(word in desc_lower for word in ["гроза", "thunderstorm", "гроза"]):
        return "⛈"
    elif any(word in desc_lower for word in ["дождь", "ливень", "rain", "shower"]):
        return "🌧"
    elif any(word in desc_lower for word in ["снег", "snow"]):
        return "❄️"
    elif any(word in desc_lower for word in ["туман", "дымка", "fog", "mist"]):
        return "🌫"
    elif any(word in desc_lower for word in ["ясно", "солнечно", "clear", "sunny"]):
        return "☀️"
    elif any(word in desc_lower for word in ["малооблачно", "partly cloudy"]):
        return "🌤"
    elif any(word in desc_lower for word in ["облачно", "пасмурно", "cloudy", "overcast"]):
        return "☁️"
    
    return "🌤"  # По умолчанию

def wind_deg_to_direction(deg, lang="ru"):
    dirs_ru = ["С", "ССВ", "СВ", "ВСВ", "В", "ВЮВ", "ЮВ", "ЮЮВ", "Ю", "ЮЮЗ", "ЮЗ", "ЗЮЗ", "З", "ЗСЗ", "СЗ", "ССЗ"]
    dirs_en = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    directions = dirs_ru if lang == "ru" else dirs_en
    if deg is None:
        return "—"
    idx = round(deg / 22.5) % 16
    return directions[idx]
def format_weather_text(chat_id, weather_data):
    lang = get_user_lang(chat_id)
    if "error" in weather_data:
        return T(lang, "weather_error")
    icon = get_weather_icon(weather_id=weather_data.get('weather_id'), description=weather_data.get('description', ''))
    wind_dir = wind_deg_to_direction(weather_data.get('wind_deg'), lang)
    text = f"{icon} {weather_data['city']}, {weather_data['country']}\n\n"
    text += T(lang, "temp", temp=weather_data['temp']) + "\n"
    text += T(lang, "feels_like", feels=weather_data['feels_like']) + "\n"
    text += T(lang, "wind_full", wind=weather_data['wind_speed'], direction=wind_dir) + "\n"
    text += T(lang, "humidity", humidity=weather_data['humidity']) + "\n"
    pressure = weather_data.get('pressure')
    if pressure:
        text += T(lang, "pressure_mm", pressure=pressure) + "\n"
    uv = weather_data.get('uv')
    if uv is not None:
        uv_level = get_uv_level(uv, lang)
        if uv_level:
            text += T(lang, "uv_with_level", uv=uv, level=uv_level) + "\n"
        else:
            text += T(lang, "uv_simple", uv=uv) + "\n"
    text += f"\n{weather_data.get('description', '').capitalize()}\n"
    text += f"\n{T(lang, 'updated_time', time=datetime.now().strftime('%H:%M:%S'))}"
    return text
def format_forecast_text(chat_id, forecast_data, city_name, days):
    from datetime import datetime
    lang = get_user_lang(chat_id)
    if "error" in forecast_data:
        return T(lang, "forecast_error")
    if not forecast_data:
        return T(lang, "error_no_data_forecast")
    if lang == "ru":
        if days == 1:
            day_word = T(lang, "day_1")
        elif days in (2, 3, 4):
            day_word = T(lang, "day_2_4")
        else:
            day_word = T(lang, "day_5_plus")
        title_days = f"{days} {day_word}"
    else:
        title_days = f"{days} {T(lang, 'day_5_plus')}"
    text = T(lang, "forecast_title", days_text=title_days, city=city_name)
    for date, item in list(forecast_data.items())[:days]:
        desc = item.get('description', '').lower()
        if any(w in desc for w in ['ясно', 'солнечно', 'clear', 'sunny']): icon = "☀️"
        elif any(w in desc for w in ['переменная', 'partly']): icon = "⛅"
        elif any(w in desc for w in ['дождь', 'ливень', 'rain', 'shower']): icon = "🌧"
        elif any(w in desc for w in ['снег', 'snow']): icon = "❄️"
        elif any(w in desc for w in ['гроза', 'thunder']): icon = "⛈"
        elif any(w in desc for w in ['туман', 'fog', 'mist']): icon = "🌫"
        elif any(w in desc for w in ['морось', 'drizzle']): icon = "🌦"
        else: icon = "☁️"
        weekday = item.get('weekday', '')[:3]
        date_str = item.get('date_str', '')
        temp_min = item.get('temp_min', item.get('temp', 0))
        temp_max = item.get('temp_max', item.get('temp', 0))
        feels = item.get('feels_like', item.get('temp', 0))
        wind = item.get('wind_speed', 0)
        wind_dir = item.get('wind_direction', '—')
        humidity = item.get('humidity', 50)
        pressure = item.get('pressure', 760)
        uv = item.get('uv')
        uv_level = get_uv_level(uv, lang) if uv else None
        precip = item.get('rain', 0)
        precip_prob = item.get('precip_prob', 0)
        text += f"{icon} *{weekday}, {date_str}*\n"
        text += T(lang, "forecast_day_line", min=temp_min, max=temp_max, feels=feels) + "\n"
        text += T(lang, "forecast_wind_line", wind=wind, dir=wind_dir, hum=humidity) + "\n"
        text += T(lang, "forecast_pressure", pressure=pressure)
        if uv_level:
            text += T(lang, "forecast_uv_line", uv=uv, level=uv_level)
        text += "\n"
        if precip > 0 or precip_prob > 0:
            text += T(lang, "forecast_precip", prob=precip_prob, mm=precip) + "\n"
        desc_text = item.get('description', T(lang, 'cloudy_default'))
        text += f"{desc_text.capitalize()}\n"
        text += "\n"
    text += T(lang, "updated_time", time=datetime.now().strftime('%H:%M'))
    return text
def format_subscription_status(chat_id):
    """Return only the current subscription status; never append a paywall."""
    lang = get_user_lang(chat_id)
    plan = get_current_plan(chat_id)
    if plan == "free":
        return T(lang, "subscription_inactive",
                 premium=PRICE_PREMIUM, business=PRICE_BUSINESS)
    sub = get_user_subscription(chat_id) or {}
    try:
        expiry = datetime.fromisoformat(sub["expiry"])
        days = max(0, (expiry - datetime.now()).days)
        expiry_text = expiry.strftime("%d.%m.%Y %H:%M")
    except Exception:
        days, expiry_text = 0, "—"
    if plan == "business":
        return f"💼 *Business*\n{T(lang, 'status_active')}\n📅 До: *{expiry_text}*\n⏳ Осталось: *{days}* дн.\n\n✅ Доступны все Premium и Business-функции."
    return f"⭐ *Premium*\n{T(lang, 'status_active')}\n📅 До: *{expiry_text}*\n⏳ Осталось: *{days}* дн.\n\n✅ Доступны все Premium-функции."

def format_help_text(chat_id):
    lang = get_user_lang(chat_id)
    city = get_user_city(chat_id) or T(lang, "city_not_set")
    is_subscribed = is_user_subscribed(chat_id)
    b2b_type = get_user_b2b_type(chat_id)

    if is_subscribed:
        sub = get_user_subscription(chat_id)
        days_left = 0
        if sub:
            expiry = datetime.fromisoformat(sub['expiry'])
            days_left = (expiry - datetime.now()).days

        text = T(lang, "help_subscribed") + "\n\n"
        text += T(lang, "help_city", city=city) + "\n"
        text += T(lang, "help_days", days=days_left) + "\n"

        if b2b_type:
            b2b_info = B2B_TYPES.get(b2b_type, {})
            text += f"\n{b2b_info.get('icon', '🏢')} *{b2b_name(lang, b2b_type)}*\n"

        text += "\n" + T(lang, "help_features_sub")
    else:
        text = T(lang, "help_free") + "\n\n"
        text += T(lang, "help_city", city=city) + "\n\n"
        text += T(lang, "help_features_free")
        text += T(lang, "help_buy")
    return text

# ============================================================
#  КЛАВИАТУРА (МУЛЬТИЯЗЫЧНАЯ)
# ============================================================

def _load_user_states():
    return _load_json_file(USER_STATES_FILE, {})

def _get_user_state(chat_id):
    return _load_user_states().get(str(chat_id), {})

def _set_user_state(chat_id, mode, **extra):
    data = _load_user_states()
    item = {"mode": mode, "updated_at": datetime.now().isoformat()}
    item.update(extra)
    data[str(chat_id)] = item
    _save_json_file(USER_STATES_FILE, data)

def _clear_user_state(chat_id):
    data = _load_user_states()
    data.pop(str(chat_id), None)
    _save_json_file(USER_STATES_FILE, data)

def _paywall(chat_id, required_plan="premium"):
    lang = get_user_lang(chat_id)
    if required_plan == "business":
        text = T(lang, "business_required")
        keyboard = {"keyboard": [[T(lang, "btn_business_sub")], [T(lang, "btn_back")]], "resize_keyboard": True}
    else:
        text = T(lang, "premium_required_paywall")
        keyboard = {"keyboard": [[T(lang, "btn_personal"), T(lang, "btn_business_sub")], [T(lang, "btn_back")]], "resize_keyboard": True}
    send_message(chat_id, text, keyboard)

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
            [T(lang, "btn_subscription"), T(lang, "btn_change_city")],
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

def get_language_keyboard(chat_id=None):
    lang = get_user_lang(chat_id) if chat_id is not None else "en"
    return {
        "keyboard": [
            ["🇷🇺 Русский", "🇬🇧 English"],
            [T(lang, "btn_back")]
        ],
        "resize_keyboard": True
    }

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

def get_city_keyboard(chat_id):
    lang = get_user_lang(chat_id)
    favs = advanced_features.favorites(chat_id) if advanced_features else []
    rows = [[str(city)] for city in favs]
    rows += [[T(lang, "btn_add_city"), T(lang, "btn_remove_city")], [T(lang, "btn_back")]]
    return {"keyboard": rows, "resize_keyboard": True}

def get_notification_keyboard(chat_id):
    lang = get_user_lang(chat_id)
    return {"keyboard":[[T(lang,"notification_toggle")],[T(lang,"notification_rain"),T(lang,"notification_wind")],[T(lang,"notification_frost"),T(lang,"notification_heat")],[T(lang,"notification_time"),T(lang,"notification_city")],[T(lang,"notification_frequency")],[T(lang,"threshold_heat"),T(lang,"threshold_frost")],[T(lang,"threshold_wind"),T(lang,"threshold_rain")],[T(lang,"threshold_heavy_rain")],[T(lang,"notification_back")]],"resize_keyboard":True}

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

def get_white_label_keyboard(chat_id):
    lang = get_user_lang(chat_id)
    return {
        "keyboard": [
            [T(lang, "btn_wl_name"), T(lang, "btn_wl_color")],
            [T(lang, "btn_wl_logo")],
            [T(lang, "btn_back")]
        ],
        "resize_keyboard": True
    }

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

def format_trip_forecast_text(lang, city, result):
    """Render trip forecast as a user-friendly message instead of exposing a Python dict."""
    if not isinstance(result, dict):
        return T(lang, "trip_result", city=city, result=str(result))
    rows = []
    for date_key, item in result.items():
        if not isinstance(item, dict):
            continue
        date_text = item.get("date_str") or item.get("date") or date_key
        weekday = item.get("weekday", "")
        temp = item.get("temp", "—")
        desc = item.get("description", "—")
        rain = item.get("rain", 0)
        wind = item.get("wind_speed", item.get("wind", "—"))
        rows.append(
            f"📅 *{date_text} ({weekday})*\n"
            f"🌡 {temp}°C  |  {desc}\n"
            f"🌧️ Осадки: {rain} мм  🌬 Ветер: {wind} м/с {item.get('wind_direction', '—')}"
        )
    if not rows:
        return T(lang, "trip_result", city=city, result="❌ Нет данных прогноза.")
    return T(lang, "trip_result", city=city, result="\n\n".join(rows))

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
                send_message(chat_id, T(lang, "welcome"), keyboard)
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

        # ===== STATEFUL FLOWS =====
        state = _get_user_state(chat_id)
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
        if state.get("mode") in ("initial_city", "change_city"):
            if text.strip().startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_main_keyboard(chat_id))
                return "ok", 200
            city_name = text.strip()
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

        if state.get("mode") == "wl_name":
            if text.strip().startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_white_label_keyboard(chat_id))
                return "ok", 200
            result = advanced_features.set_white_label(chat_id, name=text.strip()) if advanced_features else {"error":"unavailable"}
            _clear_user_state(chat_id)
            send_message(chat_id, T(lang, "wl_saved") + "\n" + json.dumps(result, ensure_ascii=False), get_white_label_keyboard(chat_id))
            return "ok", 200

        if state.get("mode") == "wl_color":
            value = text.strip()
            if not value.startswith("#") or len(value) not in (4, 7):
                send_message(chat_id, T(lang, "wl_color_prompt"), get_white_label_keyboard(chat_id))
                return "ok", 200
            result = advanced_features.set_white_label(chat_id, primary=value) if advanced_features else {"error":"unavailable"}
            _clear_user_state(chat_id)
            send_message(chat_id, T(lang, "wl_saved"), get_white_label_keyboard(chat_id))
            return "ok", 200

        # Logo upload is handled separately below when Telegram sends a photo.

        if state.get("mode") == "ai_question":
            question = text.strip()
            _clear_user_state(chat_id)
            if get_current_plan(chat_id) == "free":
                _paywall(chat_id, "premium")
            elif advanced_features:
                answer, err = advanced_features.ai_answer(chat_id, question)
                send_message(chat_id, f"🤖 {answer}" if answer else f"❌ {err}", keyboard)
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

        if text == T(lang, "btn_card"):
            logger.info(f"CARD: user={chat_id}, plan={get_current_plan(chat_id)}, city={current_city}")
            if get_current_plan(chat_id) == "free":
                logger.info(f"CARD: показываем paywall")
                _paywall(chat_id, "premium")
                return "ok", 200
            if advanced_features:
                try:
                    logger.info(f"CARD: получаем погоду для {current_city}")
                    weather = get_weather_aggregated(current_city, lang)
                    logger.info(f"CARD: погода получена: {weather.get('temp', 'error')}")
                    brand = advanced_features._db().get("white_labels", {}).get(str(chat_id), {})
                    logger.info(f"CARD: генерируем карточку")
                    path = advanced_features.generate_weather_card(weather, current_city, brand=brand)
                    logger.info(f"CARD: карточка создана: {path}")
                    if path:
                        send_photo(chat_id, path, T(lang, "card_ready"))
                    else:
                        send_message(chat_id, T(lang, "card_error"))
                except Exception as e:
                    logger.error(f"CARD: Ошибка: {e}", exc_info=True)
                    send_message(chat_id, T(lang, "card_error_generic", err=str(e)[:100]))
            else:
                logger.error("CARD: advanced_features не загружен")
            return "ok", 200
        if text == T(lang, "btn_whitelabel"):
            if get_current_plan(chat_id) != "business":
                _paywall(chat_id, "business")
                return "ok", 200
            wl = advanced_features._db().get("white_labels", {}).get(str(chat_id), {}) if advanced_features else {}
            send_message(chat_id, T(lang, "wl_menu_working") + "\n\n" + json.dumps(wl, ensure_ascii=False), get_white_label_keyboard(chat_id))
            return "ok", 200

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
                send_message(chat_id, T(lang, "autopost_menu"), keyboard)
            return "ok", 200

        elif action == "card":
            if get_current_plan(chat_id) != "business":
                _paywall(chat_id, "business")
            else:
                send_message(chat_id, T(lang, "card_menu"), keyboard)
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
                send_message(chat_id, T(lang, "team_menu"), keyboard)
            return "ok", 200

        elif action == "whitelabel":
            if get_current_plan(chat_id) != "business":
                _paywall(chat_id, "business")
            else:
                send_message(chat_id, T(lang, "whitelabel_menu"), keyboard)
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
            send_message(chat_id, format_help_text(chat_id), keyboard)
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

