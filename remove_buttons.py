print("🔄 Удаляем кнопки новых языков...")

with open('bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Удаляем строки с кнопками новых языков (2162-2165)
# Но номера строк могут сместиться, поэтому ищем по содержимому
new_lines = []
skip_patterns = [
    '["🇫🇷 Français", "🇩🇪 Deutsch"],',
    '["🇯 日本語", "🇰🇷 한국어"],',
    '["🇮 Italiano", "🇮 हिन्दी"],',
    '["🇸🇦 العربية"],',
]

for line in lines:
    if any(p in line for p in skip_patterns):
        print(f"Удалена строка: {line.strip()}")
        continue
    new_lines.append(line)

content = ''.join(new_lines)

# Обновляем обработчик выбора языка (строка 2947)
content = content.replace(
    'elif text in ["🇷 Русский", "🇬 English", "🇫🇷 Français", "🇩🇪 Deutsch", "🇯🇵 日本語", "🇰 한국어", "🇮 Italiano", "🇮🇳 हिन्दी", "🇸🇦 العربية"]:',
    'elif text in ["🇷🇺 Русский", "🇬 English"]:'
)
print("✅ Обновлен обработчик выбора языка")

# Удаляем лишние строки из lang_map
for lang_line in [
    '"🇫🇷 Français": "fr",\n',
    '"🇩 Deutsch": "de",\n',
    '"🇯🇵 日本語": "ja",\n',
    '"🇰🇷 한국어": "ko",\n',
    '"🇮 Italiano": "it",\n',
    '"🇮🇳 हिन्दी": "hi",\n',
    '"🇸🇦 العربية": "ar"\n',
]:
    content = content.replace(lang_line, '')
print("✅ Обновлен lang_map")

# Обновляем language_names
content = content.replace(
    'language_names = {"ru": "Русский", "en": "English", "fr": "Français", "de": "Deutsch", "ja": "日本語", "ko": "한국어", "it": "Italiano", "hi": "हिन्दी", "ar": "العربية"}',
    'language_names = {"ru": "Русский", "en": "English"}'
)
print("✅ Обновлен language_names")

# Удаляем лишние опции из админ-панели
for opt in [
    '<option value="fr">🇫🇷 Français</option>\n',
    '<option value="de">🇩🇪 Deutsch</option>\n',
    '<option value="ja">🇯🇵 日本語</option>\n',
    '<option value="ko">🇰🇷 한국어</option>\n',
    '<option value="it">🇮 Italiano</option>\n',
    '<option value="hi">🇮 हिन्दी</option>\n',
    '<option value="ar">🇸🇦 العربية</option>\n',
]:
    content = content.replace(opt, '')
print("✅ Обновлен выпадающий список в админ-панели")

# Обновляем цикл в админ-панели
content = content.replace(
    'for lang_code, lang_name in [("ru", "🇷 Русский"), ("en", "🇧 English"), ("fr", "🇫🇷 Français"), ("de", "🇩 Deutsch"), ("ja", "🇯🇵 日本語"), ("ko", "🇰🇷 한국어"), ("it", "🇮 Italiano"), ("hi", "🇳 हिन्दी"), ("ar", "🇸🇦 العربية")]:',
    'for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English")]:'
)
print("✅ Обновлен цикл в админ-панели")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("🎉 Готово! Кнопки новых языков удалены.")
