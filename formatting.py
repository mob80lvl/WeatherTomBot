#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Форматирование: статус подписки, помощь, прогноз поездки."""
from config import *
from texts import T, b2b_name, b2b_features
from storage import (get_user_lang, get_user_city, get_current_plan,
                     is_user_subscribed, get_user_subscription, get_user_b2b_type)

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
    plan = get_current_plan(chat_id)
    
    if lang == "ru":
        text = "📖 *ПОЛНЫЙ СПРАВОЧНИК*\n\n"
        text += f"📍 Ваш город: *{city}*\n"
        text += f"💼 Тариф: *{plan.upper()}*\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "🆓 *БЕСПЛАТНЫЕ ФУНКЦИИ*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "🌤 *Погода сейчас*\n"
        text += "Текущая температура, ощущается как, описание, ветер, влажность, давление.\n"
        text += "Кнопка: 🌤 Погода или команда /weather\n\n"
        
        text += "🌅 *Восход и закат*\n"
        text += "Время восхода, заката, долгота дня.\n"
        text += "Кнопка: 🌅 Восход/закат или команда /sunrise\n\n"
        
        text += "📅 *Прогнозы на 3, 5, 10 дней*\n"
        text += "Подробный прогноз: температура, осадки, ветер по дням.\n"
        text += "Кнопки: 📅 3 дня, 📅 5 дней, 📅 10 дней\n"
        text += "Команды: /forecast_3, /forecast_5, /forecast_10\n\n"
        
        text += "🌧️ *Будет ли дождь?*\n"
        text += "Проверка осадков на сегодня с вероятностью.\n"
        text += "Кнопка: 🌧️ Дождь или команда /rain\n\n"
        
        text += "🌙 *Фазы Луны*\n"
        text += "Текущая фаза, освещённость, даты новолуния/полнолуния.\n"
        text += "Кнопка: 🌙 Луна или команда /moon\n\n"
        
        text += "👕 *Что надеть?*\n"
        text += "Рекомендации по одежде в зависимости от погоды.\n"
        text += "Кнопка: 👕 Что надеть или команда /clothing\n\n"
        
        text += "📊 *Статистика погоды*\n"
        text += "История изменений температуры за последнюю неделю.\n"
        text += "Кнопка: 📊 Статистика или команда /stats\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "⭐ *PREMIUM (100⭐/мес)*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "🔔 *Умные уведомления*\n"
        text += "Получайте оповещения о:\n"
        text += "• 🌧️ Дожде\n"
        text += "• 💨 Сильном ветре\n"
        text += "• ❄️ Морозе (настраиваемый порог)\n"
        text += "• 🔥 Жаре (настраиваемый порог)\n\n"
        text += "*Настройка:*\n"
        text += "Кнопка: 🔔 Уведомления\n"
        text += "• Вкл/Выкл уведомления\n"
        text += "• Время отправки (08:00)\n"
        text += "• Частота (ежедневно/еженедельно/будни/выходные)\n"
        text += "• Пороги температуры и ветра\n\n"
        
        text += "⭐ *Избранные города*\n"
        text += "Сохраняйте до 10 городов для быстрого доступа.\n"
        text += "Кнопка: ⭐ Избранное или команда /favorites\n"
        text += "Команды: /addcity Город, /delcity Город\n\n"
        
        text += "✈️ *Прогноз для поездок*\n"
        text += "Погода в другом городе на выбранные даты.\n"
        text += "Кнопка: ✈️ Поездка или команда /trip Город\n"
        text += "Пример: /trip Сочи 15.09 20.09\n\n"
        
        text += "🤖 *AI-помощник*\n"
        text += "Задайте любой вопрос о погоде, получите умный ответ.\n"
        text += "Кнопка: 🤖 AI или команда /ai Вопрос\n"
        text += "Пример: /ai Будет ли завтра хорошая погода для пикника?\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "💼 *BUSINESS (400⭐/мес)*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📢 *Автопостинг в каналы*\n"
        text += "Автоматическая публикация погодных карточек в ваши Telegram-каналы.\n\n"
        text += "*Подключение:*\n"
        text += "1. Добавьте бота администратором в канал\n"
        text += "2. Команда: /channel @канал Город ЧЧ:ММ\n"
        text += "Пример: /channel @my_weather Томск 08:00\n\n"
        text += "*Управление:*\n"
        text += "• /channels — список ваших каналов\n"
        text += "• /postnow — опубликовать пост сейчас\n"
        text += "• /channel_remove @канал — отключить канал\n\n"
        text += "Кнопка: 📢 Автопостинг (с inline-управлением)\n\n"
        
        text += "🎨 *Стиль карточек*\n"
        text += "Настройте внешний вид погодных карточек:\n"
        text += "• 🎨 Цвет фона (HEX)\n"
        text += "• 📝 Цвет текста (HEX)\n"
        text += "• 🌡 Цвет акцента (температура)\n"
        text += "• 🖼 Фоновая картинка\n\n"
        text += "*Команды:*\n"
        text += "• /cardstyle — показать настройки\n"
        text += "• /card_bg #1a2a3a — цвет фона\n"
        text += "• /card_text #ffffff — цвет текста\n"
        text += "• /card_accent #ffd700 — цвет акцента\n"
        text += "• /card_bg_image — загрузить фоновую картинку\n"
        text += "• /card_reset — сбросить настройки\n\n"
        
        text += "🏢 *White-Label (свой бренд)*\n"
        text += "Замените логотип и название бота на карточках.\n\n"
        text += "*Настройка через кнопки:*\n"
        text += "Кнопка: 🏢 White-Label\n"
        text += "• ✏️ Название бренда\n"
        text += "• 🎨 Основной цвет (HEX)\n"
        text += "• 🖼 Логотип (загрузите фото)\n\n"
        
        text += "🔑 *API доступ*\n"
        text += "Используйте погоду в ваших приложениях.\n"
        text += "Лимит: 10,000 запросов/месяц\n\n"
        text += "*Получение ключа:*\n"
        text += "Кнопка: 🔑 API\n"
        text += "• 🔑 Создать ключ\n"
        text += "• 📖 Документация\n"
        text += "• 📊 Статистика\n\n"
        text += "*Endpoint:* mob100500lvl.pythonanywhere.com/api/v1\n"
        text += "*Пример:* curl -H \"X-API-Key: ВАШ_КЛЮЧ\" https://.../weather\n\n"
        
        text += "👥 *Команды (доступ для сотрудников)*\n"
        text += "Одна подписка Business — вся компания пользуется.\n\n"
        text += "*Роли:*\n"
        text += "• 👑 owner — владелец (создатель команды)\n"
        text += "• 🛠 admin — полный Business-доступ\n"
        text += "• ✏️ editor — полный Business-доступ\n"
        text += "• 👁 viewer — только Premium-функции\n\n"
        text += "*Команды:*\n"
        text += "• /team — список команд\n"
        text += "• /team create Название — создать команду\n"
        text += "• /team add ID_команды ID_пользователя роль — добавить участника\n"
        text += "Пример: /team add abc123 111222333 editor\n\n"
        text += "Участники получают уведомление и доступ автоматически.\n\n"
        
        text += "📊 *Аналитика*\n"
        text += "Статистика по каналам и публикациям.\n"
        text += "Кнопка: 📊 Аналитика или команда /analytics\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "🌾 *B2B ТАРИФЫ (200⭐/мес)*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "🚜 *Агро*\n"
        text += "Специализированные прогнозы для сельского хозяйства:\n"
        text += "• Условия для посева и уборки\n"
        text += "• Риски заморозков\n"
        text += "• Прогноз влажности почвы\n\n"
        
        text += "🏗 *Стройка*\n"
        text += "Погодные условия для строительных работ:\n"
        text += "• Безопасность работ\n"
        text += "• Прогноз осадков\n"
        text += "• Сила ветра\n\n"
        
        text += "✈️ *Туризм*\n"
        text += "Погода для путешествий:\n"
        text += "• Лучшие дни для поездок\n"
        text += "• Рекомендации по одежде\n"
        text += "• Прогноз на весь период\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "🎁 *ДОПОЛНИТЕЛЬНЫЕ ФУНКЦИИ*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "👥 *Реферальная программа*\n"
        text += "Пригласите друга и получите +7 дней Premium бесплатно!\n"
        text += "Команда: /referral\n"
        text += "Ваша ссылка: генерируется автоматически\n\n"
        
        text += "🎁 *Промокоды*\n"
        text += "Активация промокодов на скидки и бонусы.\n"
        text += "Команда: /promo КОД\n\n"
        
        text += "🌐 *Смена языка*\n"
        text += "Доступно 2 языка: Русский и English\n"
        text += "Кнопка: 🌐 Сменить язык\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "❓ *НУЖНА ПОМОЩЬ?*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "Используйте кнопки главного меню — все функции доступны через них.\n"
        text += "Для продвинутых пользователей доступны команды (начинаются с /).\n\n"
        
        text += "📱 *Бот:* @WeatherTomBot\n"
        text += "🌐 *API:* mob100500lvl.pythonanywhere.com/api/v1\n\n"
        
        text += "Если возникли вопросы — напишите /start и выберите нужную кнопку меню."
    else:
        text = "📖 *COMPLETE GUIDE*\n\n"
        text += f"📍 Your city: *{city}*\n"
        text += f"💼 Plan: *{plan.upper()}*\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "🆓 *FREE FEATURES*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "🌤 *Current weather*\n"
        text += "Current temperature, feels like, description, wind, humidity, pressure.\n"
        text += "Button: 🌤 Weather or command /weather\n\n"
        
        text += "🌅 *Sunrise & sunset*\n"
        text += "Sunrise, sunset times, day length.\n"
        text += "Button: 🌅 Sunrise/sunset or command /sunrise\n\n"
        
        text += "📅 *3, 5, 10-day forecasts*\n"
        text += "Detailed forecast: temperature, precipitation, wind by day.\n"
        text += "Buttons: 📅 3 days, 📅 5 days, 📅 10 days\n"
        text += "Commands: /forecast_3, /forecast_5, /forecast_10\n\n"
        
        text += "🌧️ *Will it rain?*\n"
        text += "Today's precipitation check with probability.\n"
        text += "Button: 🌧️ Rain or command /rain\n\n"
        
        text += "🌙 *Moon phases*\n"
        text += "Current phase, illumination, new/full moon dates.\n"
        text += "Button: 🌙 Moon or command /moon\n\n"
        
        text += "👕 *What to wear?*\n"
        text += "Clothing recommendations based on weather.\n"
        text += "Button: 👕 What to wear or command /clothing\n\n"
        
        text += "📊 *Weather statistics*\n"
        text += "Temperature change history for the past week.\n"
        text += "Button: 📊 Statistics or command /stats\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "⭐ *PREMIUM (100⭐/mo)*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "🔔 *Smart notifications*\n"
        text += "Get alerts for:\n"
        text += "• 🌧️ Rain\n"
        text += "• 💨 Strong wind\n"
        text += "• ❄️ Frost (customizable threshold)\n"
        text += "• 🔥 Heat (customizable threshold)\n\n"
        text += "*Settings:*\n"
        text += "Button: 🔔 Notifications\n"
        text += "• Enable/disable notifications\n"
        text += "• Send time (08:00)\n"
        text += "• Frequency (daily/weekly/weekdays/weekends)\n"
        text += "• Temperature and wind thresholds\n\n"
        
        text += "⭐ *Favorite cities*\n"
        text += "Save up to 10 cities for quick access.\n"
        text += "Button: ⭐ Favorites or command /favorites\n"
        text += "Commands: /addcity City, /delcity City\n\n"
        
        text += "✈️ *Trip forecasts*\n"
        text += "Weather in another city for selected dates.\n"
        text += "Button: ✈️ Trip or command /trip City\n"
        text += "Example: /trip Paris 15.09 20.09\n\n"
        
        text += "🤖 *AI assistant*\n"
        text += "Ask any weather question, get smart answers.\n"
        text += "Button: 🤖 AI or command /ai Question\n"
        text += "Example: /ai Will tomorrow be good for a picnic?\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "💼 *BUSINESS (400⭐/mo)*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "📢 *Channel auto-posting*\n"
        text += "Automatically publish weather cards to your Telegram channels.\n\n"
        text += "*Setup:*\n"
        text += "1. Add bot as channel admin\n"
        text += "2. Command: /channel @channel City HH:MM\n"
        text += "Example: /channel @my_weather London 08:00\n\n"
        text += "*Management:*\n"
        text += "• /channels — list your channels\n"
        text += "• /postnow — publish post now\n"
        text += "• /channel_remove @channel — disable channel\n\n"
        text += "Button: 📢 Auto-posting (with inline controls)\n\n"
        
        text += "🎨 *Card styling*\n"
        text += "Customize weather card appearance:\n"
        text += "• 🎨 Background color (HEX)\n"
        text += "• 📝 Text color (HEX)\n"
        text += "• 🌡 Accent color (temperature)\n"
        text += "• 🖼 Background image\n\n"
        text += "*Commands:*\n"
        text += "• /cardstyle — show settings\n"
        text += "• /card_bg #1a2a3a — background color\n"
        text += "• /card_text #ffffff — text color\n"
        text += "• /card_accent #ffd700 — accent color\n"
        text += "• /card_bg_image — upload background image\n"
        text += "• /card_reset — reset settings\n\n"
        
        text += "🏢 *White-Label (your brand)*\n"
        text += "Replace bot logo and name on cards.\n\n"
        text += "*Settings via buttons:*\n"
        text += "Button: 🏢 White-Label\n"
        text += "• ✏️ Brand name\n"
        text += "• 🎨 Primary color (HEX)\n"
        text += "• 🖼 Logo (upload photo)\n\n"
        
        text += "🔑 *API access*\n"
        text += "Use weather data in your applications.\n"
        text += "Limit: 10,000 requests/month\n\n"
        text += "*Get key:*\n"
        text += "Button: 🔑 API\n"
        text += "• 🔑 Create key\n"
        text += "• 📖 Documentation\n"
        text += "• 📊 Statistics\n\n"
        text += "*Endpoint:* mob100500lvl.pythonanywhere.com/api/v1\n"
        text += "*Example:* curl -H \"X-API-Key: YOUR_KEY\" https://.../weather\n\n"
        
        text += "👥 *Teams (employee access)*\n"
        text += "One Business subscription — whole company uses it.\n\n"
        text += "*Roles:*\n"
        text += "• 👑 owner — owner (team creator)\n"
        text += "• 🛠 admin — full Business access\n"
        text += "• ✏️ editor — full Business access\n"
        text += "• 👁 viewer — Premium features only\n\n"
        text += "*Commands:*\n"
        text += "• /team — list teams\n"
        text += "• /team create Name — create team\n"
        text += "• /team add team_id user_id role — add member\n"
        text += "Example: /team add abc123 111222333 editor\n\n"
        text += "Members receive notification and access automatically.\n\n"
        
        text += "📊 *Analytics*\n"
        text += "Channel and posting statistics.\n"
        text += "Button: 📊 Analytics or command /analytics\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "🌾 *B2B PLANS (200⭐/mo)*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "🚜 *Agriculture*\n"
        text += "Specialized forecasts for farming:\n"
        text += "• Sowing and harvest conditions\n"
        text += "• Frost risks\n"
        text += "• Soil moisture forecast\n\n"
        
        text += "🏗 *Construction*\n"
        text += "Weather conditions for construction work:\n"
        text += "• Work safety\n"
        text += "• Precipitation forecast\n"
        text += "• Wind strength\n\n"
        
        text += "✈️ *Tourism*\n"
        text += "Weather for travel:\n"
        text += "• Best travel days\n"
        text += "• Clothing recommendations\n"
        text += "• Forecast for entire period\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "🎁 *ADDITIONAL FEATURES*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "👥 *Referral program*\n"
        text += "Invite a friend and get +7 days Premium free!\n"
        text += "Command: /referral\n"
        text += "Your link: generated automatically\n\n"
        
        text += "🎁 *Promo codes*\n"
        text += "Activate promo codes for discounts and bonuses.\n"
        text += "Command: /promo CODE\n\n"
        
        text += "🌐 *Change language*\n"
        text += "2 languages available: Russian and English\n"
        text += "Button: 🌐 Change language\n\n"
        
        text += "━━━━━━━━━━━━━━━━━━━━\n"
        text += "❓ *NEED HELP?*\n"
        text += "━━━━━━━━━━━━━━━━━━━━\n\n"
        
        text += "Use main menu buttons — all features are accessible through them.\n"
        text += "Advanced users can use commands (start with /).\n\n"
        
        text += "📱 *Bot:* @WeatherTomBot\n"
        text += "🌐 *API:* mob100500lvl.pythonanywhere.com/api/v1\n\n"
        
        text += "If you have questions — type /start and select the needed menu button."
    
    return text
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
