import re

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

changed = False

# 1. Многострочные блоки в _NEW_TEXTS
for code in ['es', 'zh']:
    pattern = re.compile(r'\n    "' + code + r'": \{.*?\n    \},?', re.S)
    content, n = pattern.subn('', content)
    if n:
        changed = True
        print(f"✅ Удален блок {code} из _NEW_TEXTS")

# 2. Однострочные записи в _EXTRA_UI_TEXTS
lines = content.split('\n')
out = []
for line in lines:
    s = line.strip()
    if s.startswith('"es":{'):
        changed = True
        print("✅ Удалена строка es из _EXTRA_UI_TEXTS")
        continue
    if s.startswith('"zh":{'):
        changed = True
        if s.endswith('}}'):
            out.append('}')
            print("✅ Строка zh заменена на закрывающую скобку")
        else:
            print("✅ Удалена строка zh из _EXTRA_UI_TEXTS")
        continue
    out.append(line)
content = '\n'.join(out)

if changed:
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("🎉 Файл обновлен")
else:
    print("ℹ️ Мёртвых данных не найдено, всё чисто")
