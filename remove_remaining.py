print("🔄 Удаляем оставшиеся строки...")

with open('bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
removed = 0
for line in lines:
    # Удаляем строки с кнопками новых языков
    if '["🇯' in line and '日本語' in line:
        print(f"Удалена: {line.strip()}")
        removed += 1
        continue
    if '["🇮' in line and 'Italiano' in line and 'हिन्दी' in line:
        print(f"Удалена: {line.strip()}")
        removed += 1
        continue
    # Удаляем строки из lang_map
    if '"🇩' in line and '"de"' in line and ':' in line and 'elif' not in line:
        print(f"Удалена: {line.strip()}")
        removed += 1
        continue
    if '"🇮' in line and '"it"' in line:
        print(f"Удалена: {line.strip()}")
        removed += 1
        continue
    # Удаляем опции из админ-панели
    if '<option value="it">' in line:
        print(f"Удалена: {line.strip()}")
        removed += 1
        continue
    if '<option value="hi">' in line:
        print(f"Удалена: {line.strip()}")
        removed += 1
        continue
    new_lines.append(line)

content = ''.join(new_lines)

# Обновляем обработчик выбора языка (строка 2945)
content = content.replace(
    'elif text in ["🇷🇺 Русский", "🇬 English", "🇫 Français", "🇩🇪 Deutsch", "🇯 日本語", "🇰🇷 한국어", "🇮 Italiano", "🇮🇳 हिन्दी", "🇸🇦 العربية"]:',
    'elif text in ["🇷🇺 Русский", "🇬🇧 English"]:'
)
print("✅ Обновлен обработчик выбора языка")

# Обновляем цикл в админ-панели (строка 3543)
content = content.replace(
    'for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English"), ("fr", "🇫 Français"), ("de", "🇩🇪 Deutsch"), ("ja", "🇯🇵 日本語"), ("ko", "🇰🇷 한국어"), ("it", "🇮 Italiano"), ("hi", "🇳 हिन्दी"), ("ar", "🇸🇦 العربية")]:',
    'for lang_code, lang_name in [("ru", "🇷 Русский"), ("en", "🇧 English")]:'
)
print("✅ Обновлен цикл в админ-панели")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print(f"🎉 Готово! Удалено строк: {removed}")
