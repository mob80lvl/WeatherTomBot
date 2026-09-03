import re

print("🔄 Добавляем переводы для сообщений о погоде...")

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Новые ключи переводов для погоды
weather_translations = {
    'fr': {
        'temp': '🌡 Température : {temp}°C',
        'feels_like': '🤔 Ressenti : {feels}°C',
        'wind': '💨 Vent : {wind} m/s, {direction}',
        'humidity': '💧 Humidité : {humidity}%',
        'pressure': '📊 Pression : {pressure} mm',
        'uv_index': '☀️ Indice UV : {uv} ({level})',
        'uv_index_simple': '☀️ Indice UV : {uv}',
        'updated': '🕐 Mis à jour : {time}',
        'description_clear': 'Dégagé',
        'description_partly_cloudy': 'Partiellement nuageux',
        'description_drizzle': 'Bruine',
        'description_rain': 'Pluie',
        'description_snow': 'Neige',
        'description_shower': 'Averses',
        'description_thunder': 'Orage',
        'description_cloudy': 'Nuageux',
        'description_fog': 'Brouillard'
    }
}

# Находим последнюю строку каждого языка и добавляем новые переводы
for lang_code, translations in weather_translations.items():
    # Ищем 'construction_rec_heat' как последнюю кнопку
    pattern = rf"('{lang_code}':\s*\{{.*?'construction_rec_heat':\s*'[^']*')"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        # Формируем строку с новыми переводами
        new_keys = ",\n"
        for key, value in translations.items():
            escaped_value = value.replace("'", "\\'")
            new_keys += f"        '{key}': '{escaped_value}',\n"
        new_keys = new_keys.rstrip(',\n')
        
        # Вставляем перед закрывающей скобкой словаря
        content = content[:match.end(1)] + new_keys + content[match.end(1):]
        print(f"✅ Добавлены переводы для {lang_code}")
    else:
        print(f"⚠️ Не удалось найти маркер для {lang_code}")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("🎉 Переводы добавлены!")
