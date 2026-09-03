import re

print("🔄 Удаляем лишние языки, оставляем только ru и en...")

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Обновляем список LANGUAGES
content = re.sub(
    r'LANGUAGES = \["ru", "en", "es", "zh"\]',
    'LANGUAGES = ["ru", "en"]',
    content
)
print("✅ LANGUAGES обновлен")

# 2. Обновляем функцию api_language
content = re.sub(
    r'def api_language\(lang\):\s+return \{"ru": "ru", "en": "en", "es": "es", "zh": "zh"\}\.get\(lang, "en"\)',
    'def api_language(lang):\n    return {"ru": "ru", "en": "en"}.get(lang, "en")',
    content
)
print("✅ api_language обновлен")

# 3. Удаляем словари для es и zh из TEXTS
# Ищем блоки типа 'es': { ... } или 'zh': { ... } и удаляем их
for lang_code in ['es', 'zh']:
    # Удаляем блок языка из TEXTS (от начала блока до конца)
    pattern = rf"\s*'{lang_code}':\s*\{{.*?'construction_rec_heat':\s*'[^']*'\s*\}}\s*,?"
    content = re.sub(pattern, '', content, flags=re.DOTALL)
    print(f"✅ Удален словарь {lang_code} из TEXTS")

# 4. Обновляем функцию get_language_keyboard
old_keyboard = '''def get_language_keyboard(chat_id=None):
    lang = get_user_lang(chat_id) if chat_id is not None else "en"
    return {
        "keyboard": [
            ["🇷🇺 Русский", "🇬🇧 English"],
            ["🇪🇸 Español", "🇨🇳 中文"],
            [T(lang, "btn_back")]
        ],
        "resize_keyboard": True
    }'''

new_keyboard = '''def get_language_keyboard(chat_id=None):
    lang = get_user_lang(chat_id) if chat_id is not None else "en"
    return {
        "keyboard": [
            ["🇷🇺 Русский", "🇬🇧 English"],
            [T(lang, "btn_back")]
        ],
        "resize_keyboard": True
    }'''

if old_keyboard in content:
    content = content.replace(old_keyboard, new_keyboard)
    print("✅ Функция get_language_keyboard обновлена")
else:
    print("⚠️ Не удалось найти старую версию get_language_keyboard")

# 5. Обновляем обработчик выбора языка
old_handler = '''        elif text in ["🇷🇺 Русский", "🇬🇧 English", "🇪🇸 Español", "🇨🇳 中文"]:
            lang_map = {
                "🇷🇺 Русский": "ru",
                "🇬🇧 English": "en",
                "🇪🇸 Español": "es",
                "🇨🇳 中文": "zh"
            }
            new_lang = lang_map.get(text, "ru")
            set_user_lang(chat_id, new_lang)
            new_keyboard = get_main_keyboard(chat_id)
            language_names = {"ru": "Русский", "en": "English", "es": "Español", "zh": "中文"}'''

new_handler = '''        elif text in ["🇷🇺 Русский", "🇬🇧 English"]:
            lang_map = {
                "🇷🇺 Русский": "ru",
                "🇬🇧 English": "en"
            }
            new_lang = lang_map.get(text, "ru")
            set_user_lang(chat_id, new_lang)
            new_keyboard = get_main_keyboard(chat_id)
            language_names = {"ru": "Русский", "en": "English"}'''

if old_handler in content:
    content = content.replace(old_handler, new_handler)
    print("✅ Обработчик выбора языка обновлен")
else:
    print("⚠️ Не удалось найти старую версию обработчика")

# 6. Обновляем админ-панель - выпадающий список
old_admin_select = '''                    <option value="ru">🇷🇺 Русский</option>
                    <option value="en" selected>🇬🇧 English</option>
                    <option value="es">🇪🇸 Español</option>
                    <option value="zh">🇨🇳 中文</option>'''

new_admin_select = '''                    <option value="ru">🇷🇺 Русский</option>
                    <option value="en" selected>🇬🇧 English</option>'''

if old_admin_select in content:
    content = content.replace(old_admin_select, new_admin_select)
    print("✅ Выпадающий список в админ-панели обновлен")
else:
    print("⚠️ Не удалось найти старый выпадающий список")

# 7. Обновляем цикл в админ-панели
old_admin_loop = '''    for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English"), ("es", "🇪🇸 Español"), ("zh", "🇨🇳 中文")]:'''

new_admin_loop = '''    for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English")]:'''

if old_admin_loop in content:
    content = content.replace(old_admin_loop, new_admin_loop)
    print("✅ Цикл в админ-панели обновлен")
else:
    print("⚠️ Не удалось найти старый цикл")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("\n🎉 bot.py очищен от лишних языков!")

# Теперь обрабатываем features.py
print("\n🔄 Очищаем features.py...")

with open('features.py', 'r', encoding='utf-8') as f:
    features_content = f.read()

# Удаляем словари для лишних языков из FEATURE_TEXTS
for lang_code in ['es', 'zh']:
    # Ищем блок языка и удаляем его
    pattern = rf',?\s*"{lang_code}":\s*\{{.*?"daily_wind":\s*"[^"]*"\s*\}}'
    features_content = re.sub(pattern, '', features_content, flags=re.DOTALL)
    print(f"✅ Удален словарь {lang_code} из FEATURE_TEXTS")

# Удаляем строки с analytics для лишних языков
for lang_code in ['es', 'zh']:
    pattern = rf'FEATURE_TEXTS\["{lang_code}"\]\["analytics"\] = "[^"]*"\n'
    features_content = re.sub(pattern, '', features_content)
    print(f"✅ Удалена строка analytics для {lang_code}")

# Обновляем FEATURE_BUTTONS
old_buttons = '''FEATURE_BUTTONS = {
    "ru": {"favorites": "⭐ Города", "alerts": "🔔 Уведомления", "trip": "✈️ Поездка", "ai": "🤖 AI", "plans": "💰 Тарифы"},
    "en": {"favorites": "⭐ Cities", "alerts": "🔔 Notifications", "trip": "✈️ Trip", "ai": "🤖 AI", "plans": "💰 Plans"},
    "es": {"favorites": "⭐ Ciudades", "alerts": "🔔 Notificaciones", "trip": "✈️ Viaje", "ai": "🤖 IA", "plans": "💰 Planes"},
    "zh": {"favorites": "⭐ 城市", "alerts": "🔔 通知", "trip": "✈️ 旅行", "ai": "🤖 AI", "plans": "💰 套餐"}
}'''

new_buttons = '''FEATURE_BUTTONS = {
    "ru": {"favorites": "⭐ Города", "alerts": "🔔 Уведомления", "trip": "✈️ Поездка", "ai": "🤖 AI", "plans": "💰 Тарифы"},
    "en": {"favorites": "⭐ Cities", "alerts": "🔔 Notifications", "trip": "✈️ Trip", "ai": "🤖 AI", "plans": "💰 Plans"}
}'''

if old_buttons in features_content:
    features_content = features_content.replace(old_buttons, new_buttons)
    print("✅ FEATURE_BUTTONS обновлен")
else:
    print("⚠️ Не удалось найти старый FEATURE_BUTTONS")

with open('features.py', 'w', encoding='utf-8') as f:
    f.write(features_content)

print("\n🎉 features.py очищен от лишних языков!")
print("✅ Готово! Остались только русский и английский.")
