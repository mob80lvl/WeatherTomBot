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
    return {"ru": "ru", "en": "en", "es": "es", "zh": "zh"}.get(lang, "en")

LANGUAGES = ["ru", "en", "es", "zh"]

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
 'es': {'welcome': '🌤 *¡Bienvenido a WeatherBot!*\n'
                   '\n'
                   '🏙️ *Para empezar, indique su ciudad.*\n'
                   '\n'
                   'Envíe el nombre de la ciudad en respuesta.',
        'start_with_city': '🌤 *¡Bienvenido a WeatherBot!*\n\n📍 Ciudad actual: *{city}*\n\n',
        'free_mode': '🔒 *Modo gratuito*\n'
                     'Disponible: Clima actual, Cambiar ciudad, Estado de suscripción, Ayuda, Cambiar idioma\n'
                     '\n',
        'buy_prompt': '💰 Comprar suscripción: *{price}⭐ al mes*',
        'subscription_active': '✅ *¡Suscripción activa!* ({days} días restantes)\nTodas las funciones disponibles.',
        'b2b_active': '{icon} *{name}* suscripción activa!\n'
                      '⏳ Restan: *{days}* días.\n'
                      '¡Todas las funciones del tarifa disponibles!',
        'no_city': '🏙️ *¡Primero indique su ciudad!*\n\nEnvíe el nombre de la ciudad.',
        'city_not_found': "❌ '{city}' no encontrada. Pruebe otra ciudad.",
        'city_saved': '✅ Ciudad *{city}* guardada! Ahora puede usar el bot.',
        'city_changed': '✅ Ciudad cambiada a *{city}*',
        'enter_city': '🏙️ *Envíe el nombre de la ciudad*\n\nEjemplo: `Madrid`',
        'select_language': '🌐 *Seleccione su idioma:*',
        'language_changed': '✅ Idioma cambiado a *{language_name}*',
        'subscription_status': '🔑 *Estado de suscripción*',
        'subscription_active_status': '{status}\n📅 Hasta: *{expiry}*\n⏳ Restan: *{days}* días',
        'subscription_inactive': '❌ Sin suscripción activa\n'
                                 '\n'
                                 '💰 *Elija un plan:*\n'
                                 '\n'
                                 '👤 Personal: *{personal}⭐*\n'
                                 '🌾 Agricultura: *{agri}⭐*\n'
                                 '🏗️ Construcción: *{const}⭐*\n'
                                 '✈️ Turismo: *{tour}⭐*\n'
                                 '🏢 Negocios: *{business}⭐*',
        'only_subscribed': '🔒 *¡Esta función solo está disponible con suscripción!*\n'
                           '\n'
                           '💰 *Elija un plan:*\n'
                           '\n'
                           '👤 Personal: *{personal}⭐*\n'
                           '🌾 Agricultura: *{agri}⭐*\n'
                           '🏗️ Construcción: *{const}⭐*\n'
                           '✈️ Turismo: *{tour}⭐*\n'
                           '🏢 Negocios: *{business}⭐*',
        'invoice_created': '💳 *¡Factura creada!*\n\nPague en Telegram.\n💰 Precio: *{price}⭐*',
        'payment_success': '✅ *¡Pago exitoso!*\n\n🎉 Suscripción activada por {days} días!\n\n¡Gracias por su apoyo! 🙌',
        'back': '🔙 Atrás',
        'buy_subscription': '💰 Comprar suscripción',
        'buy_b2b': '💰 Comprar B2B',
        'change_language': '🌐 Cambiar idioma',
        'help': '❓ Ayuda',
        'help_title': '📖 *Ayuda*',
        'help_subscribed': '📖 *Ayuda* (Suscripción activa)',
        'help_free': '📖 *Ayuda* (Gratis)',
        'help_city': '📍 Ciudad: *{city}*',
        'help_days': '⏳ Restan: *{days}* días',
        'personal_features': '🌤 Clima actual\n'
                             '🌅 Amanecer/atardecer\n'
                             '📅 Pronósticos de 3, 5 y 10 días\n'
                             '🌧 Comprobar lluvia\n'
                             '🌙 Fase lunar\n'
                             '👕 Qué ponerse\n'
                             '📊 Estadísticas\n'
                             '🔔 Notificaciones\n'
                             '⚙️ Cambiar ciudad\n'
                             '🌐 Cambiar idioma\n'
                             '🔑 Estado de suscripción',
        'help_features_sub': '🌤 Clima actual\n'
                             '🌅 Amanecer/Atardecer\n'
                             '📅 Pronóstico 3, 5, 10 días\n'
                             '🌧 Verificar lluvia\n'
                             '🌙 Fase lunar\n'
                             '👕 Qué ponerse\n'
                             '📊 Estadísticas\n'
                             '🔔 Notificaciones\n'
                             '⚙️ Cambiar ciudad\n'
                             '🌐 Cambiar idioma\n'
                             '🔑 Estado de suscripción',
        'help_features_free': '🌤 Clima actual (gratis)\n'
                              '⚙️ Cambiar ciudad (gratis)\n'
                              '🔑 Estado de suscripción (gratis)\n'
                              '🌐 Cambiar idioma (gratis)',
        'help_buy': '\n💰 ¡Compre una suscripción para acceder a todas las funciones!',
        'weather_title': '☀️ *{city}, {country}*',
        'weather_temp': '🌡 Temperatura: *{temp}°C*',
        'weather_feels': '🤔 Sensación: *{feels}°C*',
        'weather_humidity': '💧 Humedad: *{humidity}%*',
        'weather_wind': '🌬 Viento: *{wind} m/s*',
        'weather_desc': '☁️ {description}',
        'weather_sources': '\n\n📡 Fuentes: *{count}* de 3\n📊 Usadas: {sources}',
        'weather_updated': '\n\n🕐 Actualizado: {time}',
        'sunrise_title': '🌅 *Amanecer y atardecer* para *{city}*',
        'sunrise_time': '🌅 Amanecer: *{sunrise}*',
        'sunset_time': '🌇 Atardecer: *{sunset}*',
        'day_length': '⏳ Duración del día: *{length}*',
        'forecast_title': '📅 *PRONÓSTICO {days} DÍAS*\n📍 *{city}*\n\n',
        'forecast_day': '🌤 *{date} ({weekday})*\n'
                        '   {temp}°C  |  {description}\n'
                        '   🌧️ Lluvia: {rain} mm  🌬 Viento: {wind} m/s\n'
                        '\n',
        'rain_expected': '{emoji} *¡Se espera lluvia en {city} hoy!*\n'
                         '\n'
                         'Lluvia: *{rain} mm* ({intensity})\n'
                         '☔ ¡No olvide su paraguas!',
        'no_rain': '☀️ No se espera lluvia hoy.',
        'moon_title': '🌙 *Fase lunar*\n\n{emoji} *{name}*\n\n📅 {date}',
        'clothing_title': '👕 *Recomendaciones* para *{city}*\n'
                          '\n'
                          '🌡 {temp}°C | {description}\n'
                          '🌬 Viento: {wind} m/s\n'
                          '\n'
                          '*Recomendado:*\n',
        'clothing_item': '• {item}\n',
        'agri_title': '🌾 *AGRO-PRONÓSTICO*\n📍 *{city}*',
        'agri_soil': '🌡 Temperatura del suelo: *{temp}°C*',
        'agri_humidity': '💧 Humedad: *{humidity}%*',
        'agri_rain': '🌧 Lluvia: *{rain} mm*',
        'agri_frost': '❄️ Heladas: {frost}',
        'agri_rec': '\n🌱 *Recomendaciones:*\n{rec}',
        'construction_title': '🏗️ *PRONÓSTICO CONSTRUCCIÓN*\n📍 *{city}*',
        'construction_wind': '💨 Viento: *{wind} m/s* {safe}',
        'construction_rain': '🌧 Lluvia: *{rain} mm*',
        'construction_temp': '🌡 Temperatura: *{temp}°C*',
        'construction_rec': '\n🏗️ *Recomendaciones:*\n{rec}',
        'tourism_title': '✈️ *PRONÓSTICO TURISMO*\n📍 *{city}*',
        'tourism_weather': '☀️ Clima: *{weather}*',
        'tourism_temp': '🌡 Temperatura: *{temp}°C*',
        'tourism_sunrise': '🌅 Amanecer: *{sunrise}*',
        'tourism_sunset': '🌇 Atardecer: *{sunset}*',
        'tourism_uv': '☀️ Índice UV: *{uv}* ({level})',
        'tourism_rec': '\n⭐ *Recomendaciones:*\n{rec}',
        'notification_on': '🔔 *¡Notificaciones activadas!*\n'
                           '\n'
                           'Le enviaré alertas sobre:\n'
                           '🌧 Lluvia\n'
                           '💨 Viento fuerte\n'
                           '❄️ Heladas\n'
                           '☀️ Calor',
        'notification_off': '🔕 *Notificaciones desactivadas*',
        'stats_title': '📊 *ESTADÍSTICAS DE {days} DÍAS*\n📍 *{city}*',
        'stats_avg': '🌡 Promedio: *{avg}°C*',
        'stats_max': '📈 Máxima: *{max}°C*',
        'stats_min': '📉 Mínima: *{min}°C*',
        'stats_rain': '🌧 Días lluviosos: *{days}*',
        'stats_clear': '☀️ Días despejados: *{days}*',
        'stats_cloudy': '☁️ Días nublados: *{days}*',
        'stats_total': '💧 Lluvia total: *{rain} mm*',
        'btn_weather': '🌤 Clima actual',
        'btn_sunrise': '🌅 Amanecer/Atardecer',
        'btn_f3': '📅 Pronóstico 3 días',
        'btn_f5': '📅 Pronóstico 5 días',
        'btn_f10': '📅 Pronóstico 10 días',
        'btn_rain': '🌧 Verificar lluvia',
        'btn_moon': '🌙 Fase lunar',
        'btn_clothing': '👕 Qué ponerse',
        'btn_stats': '📊 Estadísticas',
        'btn_agro': '🌾 Agro-pronóstico',
        'btn_construction': '🏗️ Construcción',
        'btn_tourism': '✈️ Turismo',
        'btn_notifications': '🔔 Notificaciones',
        'btn_change_city': '⚙️ Cambiar ciudad',
        'btn_change_lang': '🌐 Cambiar idioma',
        'btn_help': '❓ Ayuda',
        'btn_subscription': '🔑 Estado de suscripción',
        'btn_buy': '💰 Comprar suscripción',
        'btn_buy_b2b': '💰 Comprar B2B',
        'btn_personal': '👤 Suscripción personal',
        'btn_agriculture': '🌾 Agricultura',
        'btn_construction_sub': '🏗️ Construcción',
        'btn_tourism_sub': '✈️ Turismo',
        'btn_business_sub': '🏢 Negocios (Todo incluido)',
        'btn_back': '🔙 Atrás',
        'select_language_short': '💳 *Elija un plan:*',
        'b2b_agriculture_name': 'Agricultura',
        'b2b_agriculture_features': '✈️ Pronóstico de viajes\n'
                                    '📅 Pronóstico de 10 días\n'
                                    '🌡 Pronóstico agrícola\n'
                                    '🌧 Precipitación para riego\n'
                                    '❄️ Pronóstico de heladas\n'
                                    '📊 Estadísticas\n'
                                    '🔔 Notificaciones',
        'b2b_construction_name': 'Construcción',
        'b2b_construction_features': '✈️ Pronóstico de viajes\n'
                                     '📅 Pronóstico de 10 días\n'
                                     '💨 Pronóstico de viento\n'
                                     '🌧 Precipitaciones\n'
                                     '🌡 Temperatura\n'
                                     '📊 Estadísticas\n'
                                     '🔔 Notificaciones',
        'b2b_tourism_name': 'Turismo',
        'b2b_tourism_features': '✈️ Pronóstico de viajes\n'
                                '📅 Pronóstico de 10 días\n'
                                '🌅 Amanecer/atardecer\n'
                                '☀️ Índice UV\n'
                                '🌧 Precipitaciones\n'
                                '📊 Estadísticas\n'
                                '🔔 Notificaciones',
        'b2b_business_name': 'Negocios (Todo incluido)',
        'b2b_business_features': '✈️ Pronóstico de viajes\n'
                                '🤖 Asistente AI\n'
                                '📅 Pronóstico de 10 días\n'
                                 '📊 Estadísticas completas\n'
                                 '🔔 Todas las notificaciones\n'
                                 '🌾 Pronóstico agrícola\n'
                                 '🏗️ Construcción\n'
                                 '✈️ Turismo\n'
                                 '📈 Publicación automática\n🖼 Tarjetas meteorológicas\n🔑 API\n👥 Equipos\n📊 Analítica\n🏷 White-label',
        'already_b2b': '✅ Ya tienes una suscripción B2B activa.',
        'already_subscription': '✅ Ya tienes una suscripción activa.',
        'invoice_error': '❌ No se pudo crear la factura. Inténtalo más tarde.',
        'unknown_plan': '❌ Plan desconocido',
        'already_same_subscription': '✅ Ya tienes activa esta suscripción.',
        'back_main': '🔙 Volver al menú principal',
        'b2b_only': '🔒 *¡Esta función solo está disponible con una suscripción B2B!*\n\n💰 Elige un plan B2B:',
        'city_not_set': 'no indicada',
        'weather_error': '❌ No se pudieron obtener los datos meteorológicos. Inténtalo más tarde.',
        'forecast_error': '❌ No se pudo obtener el pronóstico. Inténtalo más tarde.',
        'stats_error': '❌ No se pudieron obtener las estadísticas. Inténtalo más tarde.',
        'agri_error': '❌ No se pudo obtener el pronóstico agrícola. Inténtalo más tarde.',
        'construction_error': '❌ No se pudo obtener el pronóstico para construcción. Inténtalo más tarde.',
        'tourism_error': '❌ No se pudo obtener el pronóstico turístico. Inténtalo más tarde.',
        'invoice_title_personal': '🌤 Suscripción Personal de WeatherBot',
        'invoice_description_personal': 'Acceso a todas las funciones principales del bot durante 1 mes',
        'invoice_month': '1 mes',
        'invoice_pay': 'Paga en Telegram.',
        'included': 'Incluido:',
        'status_active': '🟢 Activa',
        'status_expiring': '🟡 Termina pronto',
        'status_ending': '🔴 ¡Está por terminar!',
        'intensity_light': 'ligero',
        'intensity_moderate': 'moderado',
        'intensity_heavy': 'fuerte',
        'moon_new': 'Luna nueva',
        'moon_waxing_crescent': 'Luna creciente',
        'moon_first_quarter': 'Cuarto creciente',
        'moon_waxing_gibbous': 'Gibosa creciente',
        'moon_full': 'Luna llena',
        'moon_waning_gibbous': 'Gibosa menguante',
        'moon_last_quarter': 'Cuarto menguante',
        'moon_old': 'Creciente menguante',
        'error_no_data_forecast': '❌ No hay datos del pronóstico',
        'weekday_0': 'LUN',
        'weekday_1': 'MAR',
        'weekday_2': 'MIÉ',
        'weekday_3': 'JUE',
        'weekday_4': 'VIE',
        'weekday_5': 'SÁB',
        'weekday_6': 'DOM',
        'error_generic': '❌ Ocurrió un error. Inténtalo más tarde.',
        'forecast_word': 'pronóstico',
        'frost_expected': '❌ Se esperan heladas',
        'frost_not_expected': '✅ No se esperan',
        'agri_rec_frost': '❄️ Proteja los cultivos de las heladas',
        'agri_rec_wet': '🌧️ Exceso de humedad — posponga el riego',
        'agri_rec_water': '💧 Se recomienda regar',
        'agri_rec_heat': '☀️ Hace calor — proteja las plantas del sol',
        'agri_rec_good': '🌱 Las condiciones son favorables para el trabajo',
        'construction_rec_safe': '✅ El trabajo en altura es seguro',
        'construction_rec_wind': '❌ Peligroso para grúas y trabajos en altura',
        'construction_rec_rain': '🌧️ Posponga los trabajos de hormigón',
        'construction_rec_frost': '❄️ El hormigón puede congelarse — use aditivos',
        'construction_rec_heat': '☀️ Hace calor — trabaje a la sombra'},
 'zh': {'welcome': '🌤 *欢迎来到天气机器人！*\n\n🏙️ *开始使用前，请指定您的城市。*\n\n在回复中发送城市名称。',
        'start_with_city': '🌤 *欢迎来到天气机器人！*\n\n📍 当前城市: *{city}*\n\n',
        'free_mode': '🔒 *免费模式*\n可用: 当前天气, 更换城市, 订阅状态, 帮助, 更换语言\n\n',
        'buy_prompt': '💰 购买订阅: *{price}⭐ 每月*',
        'subscription_active': '✅ *订阅已激活！*（剩余 {days} 天）\n所有功能可用。',
        'b2b_active': '{icon} *{name}* 订阅已激活！\n⏳ 剩余: *{days}* 天。\n所有套餐功能可用！',
        'no_city': '🏙️ *请先指定您的城市！*\n\n发送城市名称。',
        'city_not_found': "❌ 未找到 '{city}'。请尝试其他城市。",
        'city_saved': '✅ 城市 *{city}* 已保存！现在您可以使用机器人了。',
        'city_changed': '✅ 城市已更改为 *{city}*',
        'enter_city': '🏙️ *发送城市名称*\n\n例如: `北京`',
        'select_language': '🌐 *选择您的语言:*',
        'language_changed': '✅ 语言已更改为 *{language_name}*',
        'subscription_status': '🔑 *订阅状态*',
        'subscription_active_status': '{status}\n📅 到期: *{expiry}*\n⏳ 剩余: *{days}* 天',
        'subscription_inactive': '❌ 无有效订阅\n'
                                 '\n'
                                 '💰 *选择套餐:*\n'
                                 '\n'
                                 '👤 个人: *{personal}⭐*\n'
                                 '🌾 农业: *{agri}⭐*\n'
                                 '🏗️ 建筑: *{const}⭐*\n'
                                 '✈️ 旅游: *{tour}⭐*\n'
                                 '🏢 企业: *{business}⭐*',
        'only_subscribed': '🔒 *此功能仅限订阅用户使用！*\n'
                           '\n'
                           '💰 *选择套餐:*\n'
                           '\n'
                           '👤 个人: *{personal}⭐*\n'
                           '🌾 农业: *{agri}⭐*\n'
                           '🏗️ 建筑: *{const}⭐*\n'
                           '✈️ 旅游: *{tour}⭐*\n'
                           '🏢 企业: *{business}⭐*',
        'invoice_created': '💳 *账单已创建！*\n\n请在Telegram中支付。\n💰 价格: *{price}⭐*',
        'payment_success': '✅ *支付成功！*\n\n🎉 订阅已激活 {days} 天！\n\n感谢您的支持！🙌',
        'back': '🔙 返回',
        'buy_subscription': '💰 购买订阅',
        'buy_b2b': '💰 购买企业版',
        'change_language': '🌐 更换语言',
        'help': '❓ 帮助',
        'help_title': '📖 *帮助*',
        'help_subscribed': '📖 *帮助*（订阅已激活）',
        'help_free': '📖 *帮助*（免费）',
        'help_city': '📍 城市: *{city}*',
        'help_days': '⏳ 剩余: *{days}* 天',
        'personal_features': '🌤 当前天气\n'
                             '🌅 日出/日落\n'
                             '📅 3、5、10 天天气预报\n'
                             '🌧 降雨检查\n'
                             '🌙 月相\n'
                             '👕 穿衣建议\n'
                             '📊 统计\n'
                             '🔔 通知\n'
                             '⚙️ 更改城市\n'
                             '🌐 更改语言\n'
                             '🔑 订阅状态',
        'help_features_sub': '🌤 当前天气\n'
                             '🌅 日出/日落\n'
                             '📅 3、5、10天预报\n'
                             '🌧 降雨检查\n'
                             '🌙 月相\n'
                             '👕 穿衣建议\n'
                             '📊 统计\n'
                             '🔔 通知\n'
                             '⚙️ 更改城市\n'
                             '🌐 更改语言\n'
                             '🔑 订阅状态',
        'help_features_free': '🌤 当前天气（免费）\n⚙️ 更换城市（免费）\n🔑 订阅状态（免费）\n🌐 更换语言（免费）',
        'help_buy': '\n💰 购买订阅以访问所有功能！',
        'weather_title': '☀️ *{city}, {country}*',
        'weather_temp': '🌡 温度: *{temp}°C*',
        'weather_feels': '🤔 体感温度: *{feels}°C*',
        'weather_humidity': '💧 湿度: *{humidity}%*',
        'weather_wind': '🌬 风速: *{wind} m/s*',
        'weather_desc': '☁️ {description}',
        'weather_sources': '\n\n📡 数据源: *{count}* / 3\n📊 使用: {sources}',
        'weather_updated': '\n\n🕐 更新: {time}',
        'sunrise_title': '🌅 *日出和日落* for *{city}*',
        'sunrise_time': '🌅 日出: *{sunrise}*',
        'sunset_time': '🌇 日落: *{sunset}*',
        'day_length': '⏳ 日照时长: *{length}*',
        'forecast_title': '📅 *{days}天天气预报*\n📍 *{city}*\n\n',
        'forecast_day': '🌤 *{date} ({weekday})*\n'
                        '   {temp}°C  |  {description}\n'
                        '   🌧️ 降雨: {rain} mm  🌬 风速: {wind} m/s\n'
                        '\n',
        'rain_expected': '{emoji} *今天{city}预计有雨！*\n\n降雨量: *{rain} mm* ({intensity})\n☔ 别忘了带伞！',
        'no_rain': '☀️ 今天预计没有雨。',
        'moon_title': '🌙 *月相*\n\n{emoji} *{name}*\n\n📅 {date}',
        'clothing_title': '👕 *穿衣建议* for *{city}*\n\n🌡 {temp}°C | {description}\n🌬 风速: {wind} m/s\n\n*建议:*\n',
        'clothing_item': '• {item}\n',
        'agri_title': '🌾 *农业预报*\n📍 *{city}*',
        'agri_soil': '🌡 地温: *{temp}°C*',
        'agri_humidity': '💧 湿度: *{humidity}%*',
        'agri_rain': '🌧 降雨: *{rain} mm*',
        'agri_frost': '❄️ 霜冻: {frost}',
        'agri_rec': '\n🌱 *建议:*\n{rec}',
        'construction_title': '🏗️ *建筑预报*\n📍 *{city}*',
        'construction_wind': '💨 风速: *{wind} m/s* {safe}',
        'construction_rain': '🌧 降雨: *{rain} mm*',
        'construction_temp': '🌡 温度: *{temp}°C*',
        'construction_rec': '\n🏗️ *建议:*\n{rec}',
        'tourism_title': '✈️ *旅游预报*\n📍 *{city}*',
        'tourism_weather': '☀️ 天气: *{weather}*',
        'tourism_temp': '🌡 温度: *{temp}°C*',
        'tourism_sunrise': '🌅 日出: *{sunrise}*',
        'tourism_sunset': '🌇 日落: *{sunset}*',
        'tourism_uv': '☀️ UV指数: *{uv}* ({level})',
        'tourism_rec': '\n⭐ *建议:*\n{rec}',
        'notification_on': '🔔 *通知已开启！*\n\n我会发送关于以下内容的提醒:\n🌧 下雨\n💨 强风\n❄️ 霜冻\n☀️ 高温',
        'notification_off': '🔕 *通知已关闭*',
        'stats_title': '📊 *{days}天天气统计*\n📍 *{city}*',
        'stats_avg': '🌡 平均: *{avg}°C*',
        'stats_max': '📈 最高: *{max}°C*',
        'stats_min': '📉 最低: *{min}°C*',
        'stats_rain': '🌧 雨天: *{days}*',
        'stats_clear': '☀️ 晴天: *{days}*',
        'stats_cloudy': '☁️ 阴天: *{days}*',
        'stats_total': '💧 总降雨量: *{rain} mm*',
        'btn_weather': '🌤 当前天气',
        'btn_sunrise': '🌅 日出/日落',
        'btn_f3': '📅 3天预报',
        'btn_f5': '📅 5天预报',
        'btn_f10': '📅 10天预报',
        'btn_rain': '🌧 降雨检查',
        'btn_moon': '🌙 月相',
        'btn_clothing': '👕 穿衣建议',
        'btn_stats': '📊 统计',
        'btn_agro': '🌾 农业预报',
        'btn_construction': '🏗️ 建筑',
        'btn_tourism': '✈️ 旅游',
        'btn_notifications': '🔔 通知',
        'btn_change_city': '⚙️ 更换城市',
        'btn_change_lang': '🌐 更换语言',
        'btn_help': '❓ 帮助',
        'btn_subscription': '🔑 订阅状态',
        'btn_buy': '💰 购买订阅',
        'btn_buy_b2b': '💰 购买企业版',
        'btn_personal': '👤 个人订阅',
        'btn_agriculture': '🌾 农业',
        'btn_construction_sub': '🏗️ 建筑',
        'btn_tourism_sub': '✈️ 旅游',
        'btn_business_sub': '🏢 企业（全部包含）',
        'btn_back': '🔙 返回',
        'select_language_short': '💳 *选择套餐:*',
        'b2b_agriculture_name': '农业',
        'b2b_agriculture_features': '✈️ 旅行预报\n📅 10天天气预报\n🌡 农业预报\n🌧 灌溉降水\n❄️ 霜冻预报\n📊 统计\n🔔 通知',
        'b2b_construction_name': '建筑',
        'b2b_construction_features': '✈️ 旅行预报\n📅 10天天气预报\n💨 风力预报\n🌧 降水\n🌡 温度\n📊 统计\n🔔 通知',
        'b2b_tourism_name': '旅游',
        'b2b_tourism_features': '✈️ 旅行预报\n📅 10天天气预报\n🌅 日出/日落\n☀️ UV指数\n🌧 降水\n📊 统计\n🔔 通知',
        'b2b_business_name': '企业（全部功能）',
        'b2b_business_features': '✈️ 旅行预报\n🤖 AI 助手\n📅 10天天气预报\n📊 完整统计\n🔔 全部通知\n🌾 农业预报\n🏗️ 建筑\n✈️ 旅游\n📢 自动发布\n🖼 天气卡片\n🔑 API\n👥 团队\n📊 分析\n🏷 白标',
        'already_b2b': '✅ 你已经拥有有效的 B2B 订阅！',
        'already_subscription': '✅ 你已经拥有有效的订阅！',
        'invoice_error': '❌ 创建账单失败，请稍后重试。',
        'unknown_plan': '❌ 未知套餐',
        'already_same_subscription': '✅ 你已经激活了此订阅！',
        'back_main': '🔙 返回主菜单',
        'b2b_only': '🔒 *此功能仅适用于 B2B 订阅！*\n\n💰 请选择 B2B 套餐：',
        'city_not_set': '未设置',
        'weather_error': '❌ 无法获取天气数据，请稍后重试。',
        'forecast_error': '❌ 无法获取天气预报，请稍后重试。',
        'stats_error': '❌ 无法获取统计数据，请稍后重试。',
        'agri_error': '❌ 无法获取农业预报，请稍后重试。',
        'construction_error': '❌ 无法获取建筑天气预报，请稍后重试。',
        'tourism_error': '❌ 无法获取旅游预报，请稍后重试。',
        'invoice_title_personal': '🌤 WeatherBot 个人订阅',
        'invoice_description_personal': '使用机器人全部主要功能 1 个月',
        'invoice_month': '1个月',
        'invoice_pay': '请在 Telegram 中完成付款。',
        'included': '包含：',
        'status_active': '🟢 已激活',
        'status_expiring': '🟡 即将到期',
        'status_ending': '🔴 即将过期！',
        'intensity_light': '轻',
        'intensity_moderate': '中等',
        'intensity_heavy': '强',
        'moon_new': '新月',
        'moon_waxing_crescent': '蛾眉月',
        'moon_first_quarter': '上弦月',
        'moon_waxing_gibbous': '盈凸月',
        'moon_full': '满月',
        'moon_waning_gibbous': '亏凸月',
        'moon_last_quarter': '下弦月',
        'moon_old': '残月',
        'error_no_data_forecast': '❌ 暂无天气预报数据',
        'weekday_0': '周一',
        'weekday_1': '周二',
        'weekday_2': '周三',
        'weekday_3': '周四',
        'weekday_4': '周五',
        'weekday_5': '周六',
        'weekday_6': '周日',
        'error_generic': '❌ 发生错误，请稍后重试。',
        'forecast_word': '预报',
        'frost_expected': '❌ 预计有霜冻',
        'frost_not_expected': '✅ 无霜冻预期',
        'agri_rec_frost': '❄️ 保护作物免受霜冻',
        'agri_rec_wet': '🌧️ 湿度过高 — 延后灌溉',
        'agri_rec_water': '💧 建议进行灌溉',
        'agri_rec_heat': '☀️ 天气炎热 — 注意防晒保护植物',
        'agri_rec_good': '🌱 适合进行农业作业',
        'construction_rec_safe': '✅ 高空作业安全',
        'construction_rec_wind': '❌ 起重机和高空作业存在危险',
        'construction_rec_rain': '🌧️ 延后混凝土作业',
        'construction_rec_frost': '❄️ 混凝土可能结冰 — 请使用添加剂',
        'construction_rec_heat': '☀️ 天气炎热 — 请在阴凉处作业'}}
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
        "team_menu":"👥 *Team*\n\nBusiness: /team create NAME\n/team add TEAM_ID USER_ID [ROLE]",
        "whitelabel_menu":"🏷 *White-label*\n\nBusiness: /white_label NAME",
        "analytics_menu":"📊 *Analytics*\n\nBusiness: connected-channel and posting statistics."
    },
    "es": {
        "btn_trip":"✈️ Viaje","btn_tomorrow":"📅 Clima de mañana","btn_ai":"🤖 Asistente IA","btn_favorites":"⭐ Ciudades",
        "btn_autopost":"📢 Publicación automática","btn_card":"🖼 Tarjeta meteorológica",
        "btn_api":"🔑 API","btn_team":"👥 Equipo","btn_whitelabel":"🏷 White-label",
        "btn_analytics":"📊 Analítica",
        "premium_required_paywall":"🔒 *Esta función está disponible en Premium.*\n\nSuscríbete para desbloquear viajes, IA, notificaciones y funciones avanzadas.",
        "business_required":"🔒 *Esta función está disponible en Business.*\n\nBusiness incluye todo Premium más publicación automática, tarjetas, API, equipos, analítica y white-label.",
        "trip_city":"✈️ *Viaje*\n\nEscribe la ciudad de destino.","trip_days":"📅 ¿Cuántos días? Elige de 1 a 10.",
        "trip_result":"✈️ *Pronóstico del viaje: {city}*\n\n{result}","ai_button":"🤖 *Asistente IA*\n\nEscribe una pregunta sobre el tiempo, tu viaje o qué hacer hoy.",
        "autopost_menu":"📢 *Publicación automática*\n\nBusiness puede publicar automáticamente el tiempo en canales de Telegram.\n\nComandos:\n/channel @channel CITY 08:00\n/channels",
        "card_menu":"🖼 Tarjeta meteorológica\n\nBusiness: /generate_card CITY",
        "api_menu":"🔑 *API*\n\nBusiness: /apikey",
        "team_menu":"👥 *Equipo*\n\nBusiness: /team create NAME",
        "whitelabel_menu":"🏷 *White-label*\n\nBusiness: /white_label NAME",
        "analytics_menu":"📊 *Analítica*\n\nBusiness: estadísticas de canales y publicaciones."
    },
    "zh": {
        "btn_trip":"✈️ 旅行","btn_tomorrow":"📅 明天天气","btn_ai":"🤖 AI助手","btn_favorites":"⭐ 城市",
        "btn_autopost":"📢 自动发布","btn_card":"🖼 天气卡片",
        "btn_api":"🔑 API","btn_team":"👥 团队","btn_whitelabel":"🏷 白标",
        "btn_analytics":"📊 分析",
        "premium_required_paywall":"🔒 *此功能需要 Premium。*\n\n订阅后可使用旅行、AI、通知和高级功能。",
        "business_required":"🔒 *此功能需要 Business。*\n\nBusiness 包含全部 Premium 功能，以及自动发布、卡片、API、团队、分析和白标。",
        "trip_city":"✈️ *旅行*\n\n请输入目的地城市。","trip_days":"📅 几天？请选择 1 到 10。",
        "trip_result":"✈️ *旅行预报：{city}*\n\n{result}","ai_button":"🤖 *AI助手*\n\n请输入关于天气、旅行或今天活动的问题。",
        "autopost_menu":"📢 *自动发布*\n\nBusiness 可自动将天气发布到 Telegram 频道。\n\n命令：\n/channel @channel CITY 08:00\n/channels",
        "card_menu":"🖼 天气卡片\n\nBusiness：/generate_card CITY",
        "api_menu":"🔑 *API*\n\nBusiness：/apikey",
        "team_menu":"👥 *团队*\n\nBusiness：/team create NAME",
        "whitelabel_menu":"🏷 *白标*\n\nBusiness：/white_label NAME",
        "analytics_menu":"📊 *分析*\n\nBusiness：频道和发布统计。"
    }
}
for _lang_key, _items in _NEW_TEXTS.items():
    TEXTS.setdefault(_lang_key, {}).update(_items)
_EXTRA_UI_TEXTS = {
"ru":{"cities_title":"⭐ *Мои города*","cities_empty":"Пока нет сохранённых городов.","cities_choose":"Выберите город:","city_added":"✅ Город *{city}* добавлен.","city_removed":"✅ Город *{city}* удалён.","city_not_in_favorites":"❌ Такой город не найден в списке.","notification_settings":"🔔 *Настройки уведомлений*\n\nСтатус: {status}\n🌧 Дождь: {rain}\n💨 Сильный ветер: {wind}\n❄️ Мороз: {frost}\n☀️ Жара: {heat}\n🕘 Время: *{time}*\n📍 Город: *{city}*","notification_enabled":"✅ Включены","notification_disabled":"🔕 Выключены","notification_city_prompt":"📍 Напишите город, для которого нужны уведомления.","notification_time_prompt":"🕘 Напишите время в формате HH:MM, например 08:00.","notification_time_saved":"✅ Время уведомлений установлено: *{time}*","notification_city_saved":"✅ Город уведомлений установлен: *{city}*","notification_rain":"🌧 Дождь","notification_wind":"💨 Сильный ветер","notification_frost":"❄️ Мороз","notification_heat":"☀️ Жара","notification_time":"🕘 Время","notification_city":"📍 Город","notification_toggle":"🔔 Включить / выключить","notification_back":"🔙 Назад"},
"en":{"cities_title":"⭐ *My cities*","cities_empty":"No saved cities yet.","cities_choose":"Choose a city:","city_added":"✅ City *{city}* added.","city_removed":"✅ City *{city}* removed.","city_not_in_favorites":"❌ This city is not in your list.","notification_settings":"🔔 *Notification settings*\n\nStatus: {status}\n🌧 Rain: {rain}\n💨 Strong wind: {wind}\n❄️ Frost: {frost}\n☀️ Heat: {heat}\n🕘 Time: *{time}*\n📍 City: *{city}*","notification_enabled":"✅ Enabled","notification_disabled":"🔕 Disabled","notification_city_prompt":"📍 Send the city for notifications.","notification_time_prompt":"🕘 Send time in HH:MM format, e.g. 08:00.","notification_time_saved":"✅ Notification time set: *{time}*","notification_city_saved":"✅ Notification city set: *{city}*","notification_rain":"🌧 Rain","notification_wind":"💨 Strong wind","notification_frost":"❄️ Frost","notification_heat":"☀️ Heat","notification_time":"🕘 Time","notification_city":"📍 City","notification_toggle":"🔔 Enable / disable","notification_back":"🔙 Back"},
"es":{"cities_title":"⭐ *Mis ciudades*","cities_empty":"Aún no hay ciudades guardadas.","cities_choose":"Elige una ciudad:","city_added":"✅ Ciudad *{city}* añadida.","city_removed":"✅ Ciudad *{city}* eliminada.","city_not_in_favorites":"❌ Esta ciudad no está en tu lista.","notification_settings":"🔔 *Ajustes de notificaciones*\n\nEstado: {status}\n🌧 Lluvia: {rain}\n💨 Viento fuerte: {wind}\n❄️ Heladas: {frost}\n☀️ Calor: {heat}\n🕘 Hora: *{time}*\n📍 Ciudad: *{city}*","notification_enabled":"✅ Activadas","notification_disabled":"🔕 Desactivadas","notification_city_prompt":"📍 Envía la ciudad para las notificaciones.","notification_time_prompt":"🕘 Envía la hora en formato HH:MM, por ejemplo 08:00.","notification_time_saved":"✅ Hora de notificación: *{time}*","notification_city_saved":"✅ Ciudad de notificaciones: *{city}*","notification_rain":"🌧 Lluvia","notification_wind":"💨 Viento fuerte","notification_frost":"❄️ Heladas","notification_heat":"☀️ Calor","notification_time":"🕘 Hora","notification_city":"📍 Ciudad","notification_toggle":"🔔 Activar / desactivar","notification_back":"🔙 Atrás"},
"zh":{"cities_title":"⭐ *我的城市*","cities_empty":"暂无保存的城市。","cities_choose":"选择城市：","city_added":"✅ 已添加城市 *{city}*。","city_removed":"✅ 已删除城市 *{city}*。","city_not_in_favorites":"❌ 列表中没有这个城市。","notification_settings":"🔔 *通知设置*\n\n状态：{status}\n🌧 下雨：{rain}\n💨 强风：{wind}\n❄️ 霜冻：{frost}\n☀️ 高温：{heat}\n🕘 时间：*{time}*\n📍 城市：*{city}*","notification_enabled":"✅ 已开启","notification_disabled":"🔕 已关闭","notification_city_prompt":"📍 请输入通知城市。","notification_time_prompt":"🕘 请输入 HH:MM 格式的时间，例如 08:00。","notification_time_saved":"✅ 通知时间已设置：*{time}*","notification_city_saved":"✅ 通知城市已设置：*{city}*","notification_rain":"🌧 下雨","notification_wind":"💨 强风","notification_frost":"❄️ 霜冻","notification_heat":"☀️ 高温","notification_time":"🕘 时间","notification_city":"📍 城市","notification_toggle":"🔔 开启 / 关闭","notification_back":"🔙 返回"}}
for _lang_key, _items in _EXTRA_UI_TEXTS.items():
    TEXTS.setdefault(_lang_key, {}).update(_items)

# Final product UI: only Premium and Business are public plans.
for _lang_code in LANGUAGES:
    _fallback = TEXTS.get(_lang_code, TEXTS["en"])
    _fallback.update({
        "btn_personal": "⭐ Premium",
        "btn_business_sub": "🏢 Business",
        "btn_add_city": "➕ Добавить город" if _lang_code == "ru" else ("➕ Add city" if _lang_code == "en" else "➕ Añadir ciudad" if _lang_code == "es" else "➕ 添加城市"),
        "btn_remove_city": "➖ Удалить город" if _lang_code == "ru" else ("➖ Remove city" if _lang_code == "en" else "➖ Eliminar ciudad" if _lang_code == "es" else "➖ 删除城市"),
        "btn_wl_name": "✏️ Название" if _lang_code == "ru" else ("✏️ Name" if _lang_code == "en" else "✏️ Nombre" if _lang_code == "es" else "✏️ 名称"),
        "btn_wl_color": "🎨 Цвет" if _lang_code == "ru" else ("🎨 Color" if _lang_code == "en" else "🎨 Color" if _lang_code == "es" else "🎨 颜色"),
        "btn_wl_logo": "🖼 Логотип" if _lang_code == "ru" else ("🖼 Logo" if _lang_code == "en" else "🖼 Logo" if _lang_code == "es" else "🖼 标志"),
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

def get_uv_level(uv):
    """Возвращает уровень UV-индекса с описанием."""
    if uv is None:
        return None
    try:
        uv = float(uv)
    except (TypeError, ValueError):
        return None
    
    if uv < 3:
        return "низкий"
    elif uv < 6:
        return "умеренный"
    elif uv < 8:
        return "высокий"
    elif uv < 11:
        return "очень высокий"
    else:
        return "экстремальный"

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
        return wind_deg_to_direction(angle)

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
    """Форматирует детальный прогноз на завтра."""
    if "error" in forecast_data:
        return f"❌ {forecast_data['error']}"
    
    from datetime import datetime
    
    # Дата и день недели
    date_obj = datetime.strptime(forecast_data['date'], '%Y-%m-%d')
    lang = get_user_lang(chat_id)
    
    if lang == "ru":
        weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
        weekday = weekdays[date_obj.weekday()]
    else:
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
        weekday = weekdays[date_obj.weekday()]
    
    # Иконка погоды по коду
    weather_code = forecast_data['weather_code']
    if weather_code in (0, 1):
        icon = "☀️"
    elif weather_code in (2, 3):
        icon = "⛅"
    elif weather_code in (45, 48):
        icon = "🌫"
    elif 51 <= weather_code <= 57:
        icon = "🌦"
    elif 61 <= weather_code <= 67:
        icon = "🌧"
    elif 71 <= weather_code <= 77:
        icon = "❄️"
    elif 80 <= weather_code <= 82:
        icon = "🌧"
    elif 85 <= weather_code <= 86:
        icon = "❄️"
    elif 95 <= weather_code <= 99:
        icon = "⛈"
    else:
        icon = "☁️"
    
    # Направление ветра
    wind_dir = wind_deg_to_direction(forecast_data.get('wind_deg'))
    
    # Уровень UV
    uv_level = get_uv_level(forecast_data.get('uv_max'))
    
    # Форматируем время восхода/заката
    sunrise = forecast_data.get('sunrise', '').split('T')[1] if 'T' in forecast_data.get('sunrise', '') else '—'
    sunset = forecast_data.get('sunset', '').split('T')[1] if 'T' in forecast_data.get('sunset', '') else '—'
    
    # Формируем сообщение
    text = f"📅 {icon} {weekday}, {date_obj.strftime('%d.%m.%Y')}\n\n"
    text += f"📍 {forecast_data['city']}, {forecast_data['country']}\n\n"
    text += f"🌡 Температура: {forecast_data['temp_min']}°C ... {forecast_data['temp_max']}°C\n"
    text += f"🤔 Ощущается как: {forecast_data['avg_feels']}°C\n"
    text += f"💨 Ветер: {forecast_data['avg_wind']} м/с, {wind_dir}\n"
    text += f"💧 Влажность: {forecast_data['avg_humidity']}%\n"
    text += f"📊 Давление: {forecast_data['avg_pressure']} мм рт.ст.\n"
    
    if uv_level:
        text += f"☀️ UV-индекс: {forecast_data['uv_max']} ({uv_level})\n"
    
    text += f"🌧 Вероятность осадков: {forecast_data['precip_prob']}%\n"
    text += f"🌅 Восход: {sunrise}\n"
    text += f"🌇 Закат: {sunset}\n\n"
    text += f"{forecast_data['description']}\n\n"
    text += f"🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
    
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

def wind_deg_to_direction(deg):
    """Преобразует градусы ветра в направление."""
    directions = ["С", "ССВ", "СВ", "ВСВ", "В", "ВЮВ", "ЮВ", "ЮЮВ",
                  "Ю", "ЮЮЗ", "ЮЗ", "ЗЮЗ", "З", "ЗСЗ", "СЗ", "ССЗ"]
    if deg is None:
        return "—"
    idx = round(deg / 22.5) % 16
    return directions[idx]

def format_weather_text(chat_id, weather_data):
    lang = get_user_lang(chat_id)
    if "error" in weather_data:
        return T(lang, "weather_error")

    # Получаем иконку погоды
    icon = get_weather_icon(
        weather_id=weather_data.get('weather_id'),
        description=weather_data.get('description', '')
    )
    
    # Направление ветра
    wind_dir = wind_deg_to_direction(weather_data.get('wind_deg'))
    
    # Формируем красивый вывод
    text = f"{icon} {weather_data['city']}, {weather_data['country']}\n\n"
    text += f"🌡 Температура: {weather_data['temp']}°C\n"
    text += f"🤔 Ощущается как: {weather_data['feels_like']}°C\n"
    text += f"💨 Ветер: {weather_data['wind_speed']} м/с, {wind_dir}\n"
    text += f"💧 Влажность: {weather_data['humidity']}%\n"
    
    # Давление (если есть)
    pressure = weather_data.get('pressure')
    if pressure:
        text += f"📊 Давление: {pressure} мм рт.ст.\n"
    
    # UV индекс с уровнем (если есть)
    uv = weather_data.get('uv')
    if uv is not None:
        uv_level = get_uv_level(uv)
        if uv_level:
            text += f"☀️ UV-индекс: {uv} ({uv_level})\n"
        else:
            text += f"☀️ UV-индекс: {uv}\n"
    
    text += f"\n{weather_data.get('description', '').capitalize()}\n"
    text += f"\n🕐 Обновлено: {datetime.now().strftime('%H:%M:%S')}"
    
    return text

def format_forecast_text(chat_id, forecast_data, city_name, days):
    """Форматирует подробный прогноз на несколько дней."""
    from datetime import datetime
    
    lang = get_user_lang(chat_id)
    if "error" in forecast_data:
        return T(lang, "forecast_error")
    if not forecast_data:
        return T(lang, "error_no_data_forecast")
    
    # Заголовок
    if lang == "ru":
        day_word = "день" if days == 1 else "дня" if days in (2, 3, 4) else "дней"
        title_days = f"{days} {day_word}"
    else:
        title_days = str(days)
    
    text = f"📅 *Прогноз на {title_days} — {city_name}*\n\n"
    
    # Каждый день
    for date, item in list(forecast_data.items())[:days]:
        # Иконка погоды
        desc = item.get('description', '').lower()
        if any(w in desc for w in ['ясно', 'солнечно', 'clear', 'sunny']):
            icon = "☀️"
        elif any(w in desc for w in ['переменная', 'partly']):
            icon = "⛅"
        elif any(w in desc for w in ['дождь', 'ливень', 'rain', 'shower']):
            icon = "🌧"
        elif any(w in desc for w in ['снег', 'snow']):
            icon = "❄️"
        elif any(w in desc for w in ['гроза', 'thunder']):
            icon = "⛈"
        elif any(w in desc for w in ['туман', 'fog', 'mist']):
            icon = "🌫"
        elif any(w in desc for w in ['морось', 'drizzle']):
            icon = "🌦"
        else:
            icon = "☁️"
        
        # Короткий день недели
        weekday = item.get('weekday', '')[:3]
        
        # Дата
        date_str = item.get('date_str', '')
        
        # Min/Max температура
        temp_min = item.get('temp_min', item.get('temp', 0))
        temp_max = item.get('temp_max', item.get('temp', 0))
        feels = item.get('feels_like', item.get('temp', 0))
        
        # Ветер
        wind = item.get('wind_speed', 0)
        wind_dir = item.get('wind_direction', '—')
        
        # Влажность и давление
        humidity = item.get('humidity', 50)
        pressure = item.get('pressure', 760)
        
        # UV индекс
        uv = item.get('uv')
        uv_level = get_uv_level(uv) if uv else None
        
        # Осадки
        precip = item.get('rain', 0)
        precip_prob = item.get('precip_prob', 0)
        
        # Формируем блок дня
        text += f"{icon} *{weekday}, {date_str}*\n"
        text += f"🌡 +{temp_min}°...+{temp_max}° (ощущ. +{feels}°)\n"
        text += f"💨 {wind} м/с, {wind_dir} | 💧 {humidity}%\n"
        text += f"📊 {pressure} мм"
        if uv_level:
            text += f" | ☀️ UV {uv} ({uv_level})"
        text += "\n"
        
        if precip > 0 or precip_prob > 0:
            text += f"🌧 Осадки: {precip_prob}% ({precip} мм)\n"
        
        text += f"{item.get('description', 'Облачно').capitalize()}\n"
        text += "\n"
    
    text += f"🕐 Обновлено: {datetime.now().strftime('%H:%M')}"
    
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
            ["🇪🇸 Español", "🇨🇳 中文"],
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
    return {"keyboard":[[T(lang,"notification_toggle")],[T(lang,"notification_rain"),T(lang,"notification_wind")],[T(lang,"notification_frost"),T(lang,"notification_heat")],[T(lang,"notification_time"),T(lang,"notification_city")],[T(lang,"notification_back")]],"resize_keyboard":True}

def _show_cities(chat_id):
    lang=get_user_lang(chat_id); favs=advanced_features.favorites(chat_id) if advanced_features else []
    listing="\n".join(f"📍 *{x}*" for x in favs) if favs else T(lang,"cities_empty")
    send_message(chat_id,T(lang,"cities_title")+"\n\n"+listing+"\n\n"+T(lang,"cities_choose"),get_city_keyboard(chat_id))

def _show_notification_settings(chat_id):
    lang=get_user_lang(chat_id)
    prefs=advanced_features.notification_prefs(chat_id) if advanced_features else {"enabled":get_notification_status(chat_id),"time":"08:00","rain":True,"wind":True,"frost":True,"heat":True}
    status=T(lang,"notification_enabled") if prefs.get("enabled") else T(lang,"notification_disabled")
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
                        send_message(chat_id, f"🔑 API-ключ создан:\n`{raw_key}`")
                    else:
                        send_message(chat_id, "❌ Ошибка создания ключа. Проверьте подписку Business.")
                return "ok", 200
            
            elif data_str == "api_help":
                if advanced_features:
                    default_city = advanced_features.get_api_default_city(chat_id) or "не установлен"
                    help_text = f"""📖 API Документация

🌍 Базовый URL:
https://mob100500lvl.pythonanywhere.com/api/v1

📍 Эндпоинты:
• GET /weather?city=Город
• GET /forecast?city=Город&days=5
• GET /me

🔑 Авторизация:
Заголовок: X-API-Key: ваш_ключ

🏙 Город по умолчанию: {default_city}

📊 Лимиты:
• Максимум 5 API ключей
• 100 запросов в час на ключ

💡 Пример:
curl -H "X-API-Key: ВАШ_КЛЮЧ" \
"https://mob100500lvl.pythonanywhere.com/api/v1/weather"
"""
                    send_message(chat_id, help_text)
                return "ok", 200
                return "ok", 200
            
            elif data_str == "api_set_city":
                if advanced_features:
                    _set_user_state(chat_id, "api_city_input")
                    send_message(chat_id, "🏙 Введите город по умолчанию для API запросов:")
                return "ok", 200
            
            elif data_str == "api_profile":
                if advanced_features:
                    db = advanced_features._db()
                    profile = db["users"].get(str(chat_id), {})
                    api_keys_file = advanced_features._load(advanced_features.API_KEY_FILE, {})
                    api_keys_count = sum(1 for k, v in api_keys_file.items() if v.get("owner") == str(chat_id))
                    first_seen = profile.get('first_seen', 'N/A')[:10] if profile.get('first_seen') else 'N/A'
                    profile_text = f"📊 Ваш API Профиль\n\n🆔 User ID: {chat_id}\n🔑 API ключей: {api_keys_count}\n🏙 Город по умолчанию: {profile.get('api_default_city', 'не установлен')}\n📅 Первая активность: {first_seen}"
                    send_message(chat_id, profile_text)
                return "ok", 200

            elif data_str == "api_stats":
                if advanced_features:
                    stats = advanced_features.get_api_stats(chat_id)
                    if stats["total_requests"] == 0:
                        send_message(chat_id, "📊 Статистика API\n\nВы ещё не использовали API.")
                    else:
                        stats_text = f"📊 Статистика API\n\n📈 Всего: {stats['total_requests']}\n🕐 24ч: {stats['last_24h']}\n📅 7 дней: {stats['last_7d']}\n\nПо эндпоинтам:\n"
                        for endpoint, count in sorted(stats["by_endpoint"].items(), key=lambda x: x[1], reverse=True):
                            stats_text += f"  • {endpoint}: {count}\n"
                        send_message(chat_id, stats_text)
                return "ok", 200
            
            elif data_str == "api_delete_all":
                if advanced_features:
                    keys = advanced_features._load(advanced_features.API_KEY_FILE, {})
                    deleted = 0
                    for digest, info in list(keys.items()):
                        if info.get("owner") == str(chat_id):
                            del keys[digest]
                            deleted += 1
                    advanced_features._save(advanced_features.API_KEY_FILE, keys)
                    send_message(chat_id, f"🗑 Удалено API-ключей: {deleted}")
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
                    send_message(chat_id, "❌ Не удалось сохранить логотип.", get_white_label_keyboard(chat_id))
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
                send_message(chat_id, "🏙 Введите город для API:", get_main_keyboard(chat_id))
                return "ok", 200
            if advanced_features:
                advanced_features.set_api_default_city(chat_id, city_name)
            _clear_user_state(chat_id)
            send_message(chat_id, f"✅ Город для API: *{city_name}*", get_main_keyboard(chat_id))
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
                send_message(chat_id, "✅ Город добавлен в избранные.", get_city_keyboard(chat_id))
            else:
                send_message(chat_id, f"❌ Не удалось добавить город: {result}", get_city_keyboard(chat_id))
            return "ok", 200

        if state.get("mode") == "favorite_remove":
            if text.strip().startswith("/"):
                _clear_user_state(chat_id)
                send_message(chat_id, T(lang, "invalid_action"), get_city_keyboard(chat_id))
                return "ok", 200
            city_name = text.strip()
            ok = advanced_features.remove_favorite(chat_id, city_name) if advanced_features else False
            _clear_user_state(chat_id)
            send_message(chat_id, "✅ Город удалён." if ok else "❌ Такой город не найден.", get_city_keyboard(chat_id))
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
                        send_photo(chat_id, path, "🖼 Карточка готова.")
                    else:
                        send_message(chat_id, "🖼 Не удалось создать карточку")
                except Exception as e:
                    logger.error(f"CARD: Ошибка: {e}", exc_info=True)
                    send_message(chat_id, f"❌ Ошибка: {str(e)[:100]}")
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
                send_message(chat_id, T(lang, "api_menu"), advanced_features.get_api_inline_keyboard() if advanced_features else None)
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

        elif text in ["🇷🇺 Русский", "🇬🇧 English", "🇪🇸 Español", "🇨🇳 中文"]:
            lang_map = {
                "🇷🇺 Русский": "ru",
                "🇬🇧 English": "en",
                "🇪🇸 Español": "es",
                "🇨🇳 中文": "zh"
            }
            new_lang = lang_map.get(text, "ru")
            set_user_lang(chat_id, new_lang)
            new_keyboard = get_main_keyboard(chat_id)
            language_names = {"ru": "Русский", "en": "English", "es": "Español", "zh": "中文"}
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
                    <option value="es">🇪🇸 Español</option>
                    <option value="zh">🇨🇳 中文</option>
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

    for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English"), ("es", "🇪🇸 Español"), ("zh", "🇨🇳 中文")]:
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

