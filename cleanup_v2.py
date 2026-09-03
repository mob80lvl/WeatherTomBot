import re

print("🔄 Дочищаем лишние языки...")

# Очищаем bot.py
with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Удаляем блоки для всех лишних языков (включая новые)
for lang_code in ['es', 'zh', 'fr', 'de', 'ja', 'ko', 'it', 'hi', 'ar']:
    # Удаляем блок языка из TEXTS
    pattern = rf"\s*'{lang_code}':\s*\{{.*?'construction_rec_heat':\s*'[^']*'\s*\}}\s*,?"
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    print(f"✅ Удален блок {lang_code} из bot.py")

# Также удаляем блоки, которые могли остаться от новых языков
# Они могут иметь другую структуру, поэтому ищем по началу блока
for lang_code in ['fr', 'de', 'ja', 'ko', 'it', 'hi', 'ar']:
    # Ищем блок от начала языка до следующего языка или конца словаря
    pattern = rf"\s*'{lang_code}':\s*\{{.*?\n    \}},?\s*\n"
    content = re.sub(pattern, '\n', content, flags=re.DOTALL)
    print(f"✅ Дополнительно удален блок {lang_code} из bot.py")

# Обновляем функцию get_language_keyboard если она содержит лишние языки
if '["🇪🇸 Español", "🇨🇳 中文"]' in content:
    content = content.replace('["🇪🇸 Español", "🇨🇳 中文"],\n            ', '')
    print("✅ Удалены лишние кнопки из get_language_keyboard")

# Обновляем обработчик выбора языка если он содержит лишние языки
if '"🇪🇸 Español": "es"' in content:
    content = content.replace('"🇪🇸 Español": "es",\n                ', '')
    content = content.replace('"🇨🇳 中文": "zh"\n', '')
    content = content.replace('"🇪🇸 Español", "🇨🇳 中文", ', '')
    content = content.replace(', "es": "Español", "zh": "中文"', '')
    print("✅ Обновлен обработчик выбора языка")

# Обновляем LANGUAGES если нужно
if 'LANGUAGES = ["ru", "en", "es", "zh"]' in content:
    content = content.replace('LANGUAGES = ["ru", "en", "es", "zh"]', 'LANGUAGES = ["ru", "en"]')
    print("✅ Обновлен LANGUAGES")

# Обновляем api_language если нужно
if '"es": "es", "zh": "zh"' in content:
    content = content.replace('"ru": "ru", "en": "en", "es": "es", "zh": "zh"', '"ru": "ru", "en": "en"')
    print("✅ Обновлен api_language")

# Обновляем админ-панель
if '<option value="es">🇪🇸 Español</option>' in content:
    content = content.replace('<option value="es">🇪🇸 Español</option>\n                    ', '')
    content = content.replace('<option value="zh">🇨🇳 中文</option>\n', '')
    print("✅ Обновлена админ-панель")

if '("es", "🇪🇸 Español"), ("zh", "🇨🇳 中文")' in content:
    content = content.replace('("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English"), ("es", "🇪🇸 Español"), ("zh", "🇨🇳 中文")', 
                              '("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English")')
    print("✅ Обновлен цикл в админ-панели")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("✅ bot.py полностью очищен!")

# Очищаем features.py
with open('features.py', 'r', encoding='utf-8') as f:
    features_content = f.read()

# Ищем и удаляем все следы es и zh
for lang_code in ['es', 'zh', 'fr', 'de', 'ja', 'ko', 'it', 'hi', 'ar']:
    # Удаляем блоки из FEATURE_TEXTS
    pattern = rf',?\s*"{lang_code}":\s*\{{[^}}]*\}}'
    features_content = re.sub(pattern, '', features_content, flags=re.DOTALL)
    print(f"✅ Удален блок {lang_code} из FEATURE_TEXTS")

# Удаляем строки с analytics для лишних языков
for lang_code in ['es', 'zh', 'fr', 'de', 'ja', 'ko', 'it', 'hi', 'ar']:
    pattern = rf'FEATURE_TEXTS\["{lang_code}"\]\["analytics"\] = "[^"]*"\n'
    features_content = re.sub(pattern, '', features_content)
    print(f"✅ Удалена строка analytics для {lang_code}")

# Обновляем FEATURE_BUTTONS если нужно
if '"es":' in features_content or '"zh":' in features_content:
    # Ищем блок FEATURE_BUTTONS и заменяем его
    pattern = r'FEATURE_BUTTONS = \{[^}]*\}'
    new_buttons = '''FEATURE_BUTTONS = {
    "ru": {"favorites":"⭐ Города", "alerts":"🔔 Уведомления", "trip":"✈️ Поездка", "ai":"🤖 AI", "plans":"💰 Тарифы"},
    "en": {"favorites":"⭐ Cities", "alerts":"🔔 Notifications", "trip":"✈️ Trip", "ai":"🤖 AI", "plans":"💰 Plans"}
}'''
    features_content = re.sub(pattern, new_buttons, features_content, flags=re.DOTALL)
    print("✅ Обновлен FEATURE_BUTTONS")

with open('features.py', 'w', encoding='utf-8') as f:
    f.write(features_content)

print("✅ features.py полностью очищен!")
print("\n🎉 Готово! Остались только русский и английский.")
