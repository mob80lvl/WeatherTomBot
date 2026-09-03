print("🔄 Финальные исправления...")

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# 1. Восстанавливаем строку цикла в админ-панели
old_pattern = "    '''\n        display = \"block\" if lang_code == \"en\" else \"none\""
new_pattern = "    '''\n    for lang_code, lang_name in [(\"ru\", \"🇷🇺 Русский\"), (\"en\", \"🇬 English\")]:\n        display = \"block\" if lang_code == \"en\" else \"none\""
if old_pattern in content:
    content = content.replace(old_pattern, new_pattern)
    print("✅ Восстановлен цикл в админ-панели")
else:
    print("⚠️ Не найден паттерн цикла")

# 2. Исправляем обработчик выбора языка
old_handler = 'elif text in ["🇷🇺 Русский", "🇬🇧 English", "🇫🇷 Français", "🇩 Deutsch", "🇯 日本語", "🇷 한국어", "🇹 Italiano", "🇮 हिन्दी", "🇸🇦 العربية"]:'
new_handler = 'elif text in ["🇷 Русский", "🇬 English"]:'
if old_handler in content:
    content = content.replace(old_handler, new_handler)
    print("✅ Исправлен обработчик выбора языка")
else:
    print("⚠️ Не найден обработчик")

# 3. Удаляем лишнюю строку из lang_map
old_zh = '                "🇨🇳 中文": "zh",\n'
if old_zh in content:
    content = content.replace(old_zh, '')
    print("✅ Удалена лишняя строка из lang_map")
else:
    print("⚠️ Не найдена строка zh в lang_map")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("🎉 Готово!")
