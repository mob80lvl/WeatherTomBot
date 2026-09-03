import re

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# ============================================
# 1. Добавляем недостающие ключи в словари TEXTS
# ============================================

# Ключи для русского (добавляем перед последней строкой словаря 'ru')
ru_keys = """        'temp': '🌡 Температура: {temp}°C',
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
        'forecast_title': '📅 *Прогноз на {days_text} — {city}*\\n\\n',
        'forecast_day_line': '🌡 +{min}°...+{max}° (ощущ. +{feels}°)',
        'forecast_wind_line': '💨 {wind} м/с, {dir} | 💧 {hum}%',
        'forecast_pressure': '📊 {pressure} мм',
        'forecast_uv_line': ' | ☀️ UV {uv} ({level})',
        'forecast_precip': '🌧 Осадки: {prob}% ({mm} мм)',
        'cloudy_default': 'Облачно',
        'day_1': 'день', 'day_2_4': 'дня', 'day_5_plus': 'дней',
        'wind_n': 'С', 'wind_nne': 'ССВ', 'wind_ne': 'СВ', 'wind_ene': 'ВСВ',
        'wind_e': 'В', 'wind_ese': 'ВЮВ', 'wind_se': 'ЮВ', 'wind_sse': 'ЮЮВ',
        'wind_s': 'Ю', 'wind_ssw': 'ЮЮЗ', 'wind_sw': 'ЮЗ', 'wind_wsw': 'ЗЮЗ',
        'wind_w': 'З', 'wind_wnw': 'ЗСЗ', 'wind_nw': 'СЗ', 'wind_nnw': 'ССЗ',
        'uv_low': 'низкий', 'uv_moderate': 'умеренный', 'uv_high': 'высокий',
        'uv_very_high': 'очень высокий', 'uv_extreme': 'экстремальный',
"""

# Ключи для английского
en_keys = """        'temp': '🌡 Temperature: {temp}°C',
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
        'forecast_title': '📅 *Forecast for {days_text} — {city}*\\n\\n',
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
"""

# Ищем последнюю запись 'forecast_error' или подобную в каждом словаре и добавляем ключи после неё
# Для ru:
ru_marker = "        'forecast_error':"
if ru_marker in content and "'temp':" not in content:
    # Находим индекс и вставляем ключи
    pos = content.find(ru_marker)
    end_pos = content.find('\n', pos) + 1
    content = content[:end_pos] + ru_keys + content[end_pos:]
    print("✅ Добавлены ключи для ru")

en_marker = "        'forecast_error':"
# Ищем вторую встречу (для en)
if en_marker in content:
    # Находим вторую встречу
    pos1 = content.find(en_marker)
    pos2 = content.find(en_marker, pos1 + 1)
    if pos2 > 0:
        end_pos = content.find('\n', pos2) + 1
        content = content[:end_pos] + en_keys + content[end_pos:]
        print("✅ Добавлены ключи для en")

# ============================================
# 2. Перезаписываем get_uv_level
# ============================================
new_uv_func = '''def get_uv_level(uv, lang="ru"):
    """Возвращает уровень UV-индекса с описанием."""
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
        return T(lang, "uv_extreme")'''

content = re.sub(
    r'def get_uv_level\(uv\):.*?return "экстремальный"',
    new_uv_func,
    content,
    flags=re.DOTALL
)
print("✅ Переписана get_uv_level")

# ============================================
# 3. Перезаписываем wind_deg_to_direction
# ============================================
new_wind_func = '''def wind_deg_to_direction(deg, lang="ru"):
    """Преобразует градусы ветра в направление."""
    dirs_ru = ["С", "ССВ", "СВ", "ВСВ", "В", "ВЮВ", "ЮВ", "ЮЮВ",
               "Ю", "ЮЮЗ", "ЮЗ", "ЗЮЗ", "З", "ЗСЗ", "СЗ", "ССЗ"]
    dirs_en = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE",
               "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    directions = dirs_ru if lang == "ru" else dirs_en
    if deg is None:
        return "—"
    idx = round(deg / 22.5) % 16
    return directions[idx]'''

content = re.sub(
    r'def wind_deg_to_direction\(deg\):.*?return directions\[idx\]',
    new_wind_func,
    content,
    flags=re.DOTALL
)
print("✅ Переписана wind_deg_to_direction")

# ============================================
# 4. Перезаписываем format_weather_text
# ============================================
new_format_weather = '''def format_weather_text(chat_id, weather_data):
    lang = get_user_lang(chat_id)
    if "error" in weather_data:
        return T(lang, "weather_error")
    # Получаем иконку погоды
    icon = get_weather_icon(
        weather_id=weather_data.get('weather_id'),
        description=weather_data.get('description', '')
    )
    
    # Направление ветра
    wind_dir = wind_deg_to_direction(weather_data.get('wind_deg'), lang)
    
    # Формируем красивый вывод
    text = f"{icon} {weather_data['city']}, {weather_data['country']}\\n\\n"
    text += T(lang, "temp", temp=weather_data['temp']) + "\\n"
    text += T(lang, "feels_like", feels=weather_data['feels_like']) + "\\n"
    text += T(lang, "wind_full", wind=weather_data['wind_speed'], direction=wind_dir) + "\\n"
    text += T(lang, "humidity", humidity=weather_data['humidity']) + "\\n"
    
    # Давление (если есть)
    pressure = weather_data.get('pressure')
    if pressure:
        text += T(lang, "pressure_mm", pressure=pressure) + "\\n"
    
    # UV индекс с уровнем (если есть)
    uv = weather_data.get('uv')
    if uv is not None:
        uv_level = get_uv_level(uv, lang)
        if uv_level:
            text += T(lang, "uv_with_level", uv=uv, level=uv_level) + "\\n"
        else:
            text += T(lang, "uv_simple", uv=uv) + "\\n"
    
    text += f"\\n{weather_data.get('description', '').capitalize()}\\n"
    text += f"\\n{T(lang, 'updated_time', time=datetime.now().strftime('%H:%M:%S'))}"
    
    return text'''

content = re.sub(
    r'def format_weather_text\(chat_id, weather_data\):.*?return text\ndef format_forecast_text',
    new_format_weather + '\ndef format_forecast_text',
    content,
    flags=re.DOTALL
)
print("✅ Переписана format_weather_text")

# ============================================
# 5. Перезаписываем format_tomorrow_forecast_text
# ============================================
new_tomorrow = '''def format_tomorrow_forecast_text(chat_id, forecast_data):
    """Форматирует детальный прогноз на завтра."""
    if "error" in forecast_data:
        return f"❌ {forecast_data['error']}"
    
    from datetime import datetime
    
    # Дата и день недели
    date_obj = datetime.strptime(forecast_data['date'], '%Y-%m-%d')
    lang = get_user_lang(chat_id)
    
    if lang == "ru":
        weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
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
    wind_dir = wind_deg_to_direction(forecast_data.get('wind_deg'), lang)
    
    # Уровень UV
    uv_level = get_uv_level(forecast_data.get('uv_max'), lang)
    
    # Форматируем время восхода/заката
    sunrise = forecast_data.get('sunrise', '').split('T')[1] if 'T' in forecast_data.get('sunrise', '') else '—'
    sunset = forecast_data.get('sunset', '').split('T')[1] if 'T' in forecast_data.get('sunset', '') else '—'
    
    # Формируем сообщение
    text = f"📅 {icon} {weekday}, {date_obj.strftime('%d.%m.%Y')}\\n\\n"
    text += f"📍 {forecast_data['city']}, {forecast_data['country']}\\n\\n"
    text += T(lang, "temp", temp=f"{forecast_data['temp_min']}...{forecast_data['temp_max']}") + "\\n"
    text += T(lang, "feels_like", feels=forecast_data['avg_feels']) + "\\n"
    text += T(lang, "wind_full", wind=forecast_data['avg_wind'], direction=wind_dir) + "\\n"
    text += T(lang, "humidity", humidity=forecast_data['avg_humidity']) + "\\n"
    text += T(lang, "pressure_mm", pressure=forecast_data['avg_pressure']) + "\\n"
    
    if uv_level:
        text += T(lang, "uv_with_level", uv=forecast_data['uv_max'], level=uv_level) + "\\n"
    
    text += T(lang, "precip_prob", prob=forecast_data['precip_prob']) + "\\n"
    text += T(lang, "sunrise", time=sunrise) + "\\n"
    text += T(lang, "sunset", time=sunset) + "\\n\\n"
    text += f"{forecast_data['description']}\\n\\n"
    text += T(lang, "updated_time", time=datetime.now().strftime('%H:%M:%S'))
    
    return text'''

content = re.sub(
    r'def format_tomorrow_forecast_text\(chat_id, forecast_data\):.*?return text\ndef get_weather_statistics',
    new_tomorrow + '\ndef get_weather_statistics',
    content,
    flags=re.DOTALL
)
print("✅ Переписана format_tomorrow_forecast_text")

# ============================================
# 6. Перезаписываем format_forecast_text
# ============================================
new_forecast = '''def format_forecast_text(chat_id, forecast_data, city_name, days):
    """Форматирует подробный прогноз на несколько дней."""
    from datetime import datetime
    
    lang = get_user_lang(chat_id)
    if "error" in forecast_data:
        return T(lang, "forecast_error")
    if not forecast_data:
        return T(lang, "error_no_data_forecast")
    
    # Заголовок
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
        uv_level = get_uv_level(uv, lang) if uv else None
        
        # Осадки
        precip = item.get('rain', 0)
        precip_prob = item.get('precip_prob', 0)
        
        # Формируем блок дня
        text += f"{icon} *{weekday}, {date_str}*\\n"
        text += T(lang, "forecast_day_line", min=temp_min, max=temp_max, feels=feels) + "\\n"
        text += T(lang, "forecast_wind_line", wind=wind, dir=wind_dir, hum=humidity) + "\\n"
        text += T(lang, "forecast_pressure", pressure=pressure)
        if uv_level:
            text += T(lang, "forecast_uv_line", uv=uv, level=uv_level)
        text += "\\n"
        
        if precip > 0 or precip_prob > 0:
            text += T(lang, "forecast_precip", prob=precip_prob, mm=precip) + "\\n"
        
        desc_text = item.get('description', T(lang, 'cloudy_default'))
        text += f"{desc_text.capitalize()}\\n"
        text += "\\n"
    
    text += T(lang, "updated_time", time=datetime.now().strftime('%H:%M'))
    
    return text'''

content = re.sub(
    r'def format_forecast_text\(chat_id, forecast_data, city_name, days\):.*?return text\n\ndef format_subscription_status',
    new_forecast + '\n\ndef format_subscription_status',
    content,
    flags=re.DOTALL
)
print("✅ Переписана format_forecast_text")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("🎉 Готово! Погодный блок полностью локализован.")
