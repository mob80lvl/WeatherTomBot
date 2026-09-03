import re

print("🔄 Обновляем кнопки выбора языка в bot.py...")

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Обновляем функцию get_language_keyboard
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
            ["🇪🇸 Español", "🇨🇳 中文"],
            ["🇫🇷 Français", "🇩🇪 Deutsch"],
            ["🇯🇵 日本語", "🇰🇷 한국어"],
            ["🇮🇹 Italiano", "🇮🇳 हिन्दी"],
            ["🇸🇦 العربية"],
            [T(lang, "btn_back")]
        ],
        "resize_keyboard": True
    }'''

if old_keyboard in content:
    content = content.replace(old_keyboard, new_keyboard)
    print("✅ Функция get_language_keyboard обновлена")
else:
    print("⚠️ Не удалось найти старую версию get_language_keyboard")

# 2. Обновляем обработчик выбора языка
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

new_handler = '''        elif text in ["🇷🇺 Русский", "🇬🇧 English", "🇪🇸 Español", "🇨🇳 中文", "🇫🇷 Français", "🇩🇪 Deutsch", "🇯🇵 日本語", "🇰🇷 한국어", "🇮🇹 Italiano", "🇮🇳 हिन्दी", "🇸🇦 العربية"]:
            lang_map = {
                "🇷🇺 Русский": "ru",
                "🇬🇧 English": "en",
                "🇪🇸 Español": "es",
                "🇨🇳 中文": "zh",
                "🇫🇷 Français": "fr",
                "🇩🇪 Deutsch": "de",
                "🇯🇵 日本語": "ja",
                "🇰🇷 한국어": "ko",
                "🇮🇹 Italiano": "it",
                "🇮🇳 हिन्दी": "hi",
                "🇸🇦 العربية": "ar"
            }
            new_lang = lang_map.get(text, "ru")
            set_user_lang(chat_id, new_lang)
            new_keyboard = get_main_keyboard(chat_id)
            language_names = {"ru": "Русский", "en": "English", "es": "Español", "zh": "中文", "fr": "Français", "de": "Deutsch", "ja": "日本語", "ko": "한국어", "it": "Italiano", "hi": "हिन्दी", "ar": "العربية"}'''

if old_handler in content:
    content = content.replace(old_handler, new_handler)
    print("✅ Обработчик выбора языка обновлен")
else:
    print("⚠️ Не удалось найти старую версию обработчика")

# 3. Обновляем админ-панель - выпадающий список
old_admin_select = '''                    <option value="ru">🇷🇺 Русский</option>
                    <option value="en" selected>🇬🇧 English</option>
                    <option value="es">🇪🇸 Español</option>
                    <option value="zh">🇨🇳 中文</option>'''

new_admin_select = '''                    <option value="ru">🇷🇺 Русский</option>
                    <option value="en" selected>🇬🇧 English</option>
                    <option value="es">🇪🇸 Español</option>
                    <option value="zh">🇨🇳 中文</option>
                    <option value="fr">🇫🇷 Français</option>
                    <option value="de">🇩🇪 Deutsch</option>
                    <option value="ja">🇯🇵 日本語</option>
                    <option value="ko">🇰🇷 한국어</option>
                    <option value="it">🇮🇹 Italiano</option>
                    <option value="hi">🇮🇳 हिन्दी</option>
                    <option value="ar">🇸🇦 العربية</option>'''

if old_admin_select in content:
    content = content.replace(old_admin_select, new_admin_select)
    print("✅ Выпадающий список в админ-панели обновлен")
else:
    print("⚠️ Не удалось найти старый выпадающий список")

# 4. Обновляем цикл в админ-панели
old_admin_loop = '''    for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English"), ("es", "🇪🇸 Español"), ("zh", "🇨🇳 中文")]:'''

new_admin_loop = '''    for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English"), ("es", "🇪🇸 Español"), ("zh", "🇨🇳 中文"), ("fr", "🇫🇷 Français"), ("de", "🇩🇪 Deutsch"), ("ja", "🇯🇵 日本語"), ("ko", "🇰🇷 한국어"), ("it", "🇮🇹 Italiano"), ("hi", "🇮🇳 हिन्दी"), ("ar", "🇸🇦 العربية")]:'''

if old_admin_loop in content:
    content = content.replace(old_admin_loop, new_admin_loop)
    print("✅ Цикл в админ-панели обновлен")
else:
    print("⚠️ Не удалось найти старый цикл")

# Сохраняем изменения
with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("🎉 Готово! Все кнопки языков обновлены.")
