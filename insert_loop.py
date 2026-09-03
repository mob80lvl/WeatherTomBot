RU = "\U0001F1F7\U0001F1FA Русский"
EN = "\U0001F1EC\U0001F1E7 English"

with open('bot.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
inserted = False
for line in lines:
    # Вставляем цикл перед строкой с display (которая имеет 8 пробелов отступа)
    if (not inserted) and line.strip().startswith('display = "block" if lang_code'):
        new_lines.append('    for lang_code, lang_name in [("ru", "' + RU + '"), ("en", "' + EN + '")]:\n')
        inserted = True
        print("✅ Вставлена строка цикла for")
    new_lines.append(line)

if not inserted:
    print("⚠️ Не удалось вставить цикл")

with open('bot.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print("🎉 Готово!")
