import re

print("🔄 Добавляем недостающие переводы кнопок...")

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Переводы недостающих кнопок для новых языков
missing_translations = {
    'fr': {
        'btn_trip': '✈️ Voyage', 'btn_tomorrow': '📅 Demain', 'btn_ai': '🤖 Assistant IA', 'btn_favorites': '⭐ Villes',
        'btn_autopost': '📢 Auto-publication', 'btn_card': '🖼 Carte météo',
        'btn_api': '🔑 API', 'btn_team': '👥 Équipe', 'btn_whitelabel': '🏷 White-label',
        'btn_analytics': '📊 Analytique',
        'btn_add_city': '➕ Ajouter une ville', 'btn_remove_city': '➖ Supprimer une ville',
        'btn_wl_name': '✏️ Nom', 'btn_wl_color': '🎨 Couleur', 'btn_wl_logo': '🖼 Logo'
    },
    'de': {
        'btn_trip': '✈️ Reise', 'btn_tomorrow': '📅 Morgen', 'btn_ai': '🤖 KI-Assistent', 'btn_favorites': '⭐ Städte',
        'btn_autopost': '📢 Auto-Posting', 'btn_card': '🖼 Wetterkarte',
        'btn_api': '🔑 API', 'btn_team': '👥 Team', 'btn_whitelabel': '🏷 White-Label',
        'btn_analytics': '📊 Analytik',
        'btn_add_city': '➕ Stadt hinzufügen', 'btn_remove_city': '➖ Stadt entfernen',
        'btn_wl_name': '✏️ Name', 'btn_wl_color': '🎨 Farbe', 'btn_wl_logo': '🖼 Logo'
    },
    'ja': {
        'btn_trip': '✈️ 旅行', 'btn_tomorrow': '📅 明日', 'btn_ai': '🤖 AIアシスタント', 'btn_favorites': '⭐ 都市',
        'btn_autopost': '📢 自動投稿', 'btn_card': '🖼 天気カード',
        'btn_api': '🔑 API', 'btn_team': '👥 チーム', 'btn_whitelabel': '🏷 ホワイトラベル',
        'btn_analytics': '📊 アナリティクス',
        'btn_add_city': '➕ 都市を追加', 'btn_remove_city': '➖ 都市を削除',
        'btn_wl_name': '✏️ 名前', 'btn_wl_color': '🎨 色', 'btn_wl_logo': '🖼 ロゴ'
    },
    'ko': {
        'btn_trip': '✈️ 여행', 'btn_tomorrow': '📅 내일', 'btn_ai': '🤖 AI 어시스턴트', 'btn_favorites': '⭐ 도시',
        'btn_autopost': '📢 자동 게시', 'btn_card': '🖼 날씨 카드',
        'btn_api': '🔑 API', 'btn_team': '👥 팀', 'btn_whitelabel': '🏷 화이트라벨',
        'btn_analytics': '📊 분석',
        'btn_add_city': '➕ 도시 추가', 'btn_remove_city': '➖ 도시 삭제',
        'btn_wl_name': '✏️ 이름', 'btn_wl_color': '🎨 색상', 'btn_wl_logo': '🖼 로고'
    },
    'it': {
        'btn_trip': '✈️ Viaggio', 'btn_tomorrow': '📅 Domani', 'btn_ai': '🤖 Assistente IA', 'btn_favorites': '⭐ Città',
        'btn_autopost': '📢 Auto-pubblicazione', 'btn_card': '🖼 Carta meteo',
        'btn_api': '🔑 API', 'btn_team': '👥 Team', 'btn_whitelabel': '🏷 White-label',
        'btn_analytics': '📊 Analitica',
        'btn_add_city': '➕ Aggiungi città', 'btn_remove_city': '➖ Rimuovi città',
        'btn_wl_name': '✏️ Nome', 'btn_wl_color': '🎨 Colore', 'btn_wl_logo': '🖼 Logo'
    },
    'hi': {
        'btn_trip': '✈️ यात्रा', 'btn_tomorrow': '📅 कल', 'btn_ai': '🤖 AI सहायक', 'btn_favorites': '⭐ शहर',
        'btn_autopost': '📢 स्वचालित पोस्टिंग', 'btn_card': '🖼 मौसम कार्ड',
        'btn_api': '🔑 API', 'btn_team': '👥 टीम', 'btn_whitelabel': '🏷 व्हाइट-लेबल',
        'btn_analytics': '📊 विश्लेषण',
        'btn_add_city': '➕ शहर जोड़ें', 'btn_remove_city': '➖ शहर हटाएं',
        'btn_wl_name': '✏️ नाम', 'btn_wl_color': '🎨 रंग', 'btn_wl_logo': '🖼 लोगो'
    },
    'ar': {
        'btn_trip': '✈️ رحلة', 'btn_tomorrow': '📅 غداً', 'btn_ai': '🤖 مساعد AI', 'btn_favorites': '⭐ مدن',
        'btn_autopost': '📢 نشر تلقائي', 'btn_card': '🖼 بطاقة الطقس',
        'btn_api': '🔑 API', 'btn_team': '👥 فريق', 'btn_whitelabel': '🏷 علامة بيضاء',
        'btn_analytics': '📊 تحليلات',
        'btn_add_city': '➕ إضافة مدينة', 'btn_remove_city': '➖ إزالة مدينة',
        'btn_wl_name': '✏️ الاسم', 'btn_wl_color': '🎨 اللون', 'btn_wl_logo': '🖼 الشعار'
    }
}

# Добавляем переводы в каждый язык
for lang_code, translations in missing_translations.items():
    # Находим последнюю кнопку в словаре языка и добавляем после неё
    # Ищем 'construction_rec_heat' как последнюю кнопку
    pattern = rf"('{lang_code}':\s*\{{.*?'construction_rec_heat':\s*'[^']*')"
    match = re.search(pattern, content, re.DOTALL)
    if match:
        # Формируем строку с новыми кнопками
        new_buttons = ",\n"
        for key, value in translations.items():
            new_buttons += f"        '{key}': '{value}',\n"
        new_buttons = new_buttons.rstrip(',\n')
        
        # Вставляем перед закрывающей скобкой словаря
        content = content[:match.end(1)] + new_buttons + content[match.end(1):]
        print(f"✅ Добавлены кнопки для {lang_code}")
    else:
        print(f"⚠️ Не удалось найти маркер для {lang_code}")

# Обновляем тернарные операторы для поддержки всех языков
# btn_add_city
content = content.replace(
    '"btn_add_city": "➕ Добавить город" if _lang_code == "ru" else ("➕ Add city" if _lang_code == "en" else "➕ Añadir ciudad" if _lang_code == "es" else "➕ 添加城市")',
    '"btn_add_city": {"ru": "➕ Добавить город", "en": "➕ Add city", "es": "➕ Añadir ciudad", "zh": "➕ 添加城市", "fr": "➕ Ajouter une ville", "de": "➕ Stadt hinzufügen", "ja": "➕ 都市を追加", "ko": "➕ 도시 추가", "it": "➕ Aggiungi città", "hi": "➕ शहर जोड़ें", "ar": "➕ إضافة مدينة"}.get(_lang_code, "➕ Add city")'
)
content = content.replace(
    '"btn_remove_city": "➖ Удалить город" if _lang_code == "ru" else ("➖ Remove city" if _lang_code == "en" else "➖ Eliminar ciudad" if _lang_code == "es" else "➖ 删除城市")',
    '"btn_remove_city": {"ru": "➖ Удалить город", "en": "➖ Remove city", "es": "➖ Eliminar ciudad", "zh": "➖ 删除城市", "fr": "➖ Supprimer une ville", "de": "➖ Stadt entfernen", "ja": "➖ 都市を削除", "ko": "➖ 도시 삭제", "it": "➖ Rimuovi città", "hi": "➖ शहर हटाएं", "ar": "➖ إزالة مدينة"}.get(_lang_code, "➖ Remove city")'
)
content = content.replace(
    '"btn_wl_name": "✏️ Название" if _lang_code == "ru" else ("✏️ Name" if _lang_code == "en" else "✏️ Nombre" if _lang_code == "es" else "✏️ 名称")',
    '"btn_wl_name": {"ru": "✏️ Название", "en": "✏️ Name", "es": "✏️ Nombre", "zh": "✏️ 名称", "fr": "✏️ Nom", "de": "✏️ Name", "ja": "✏️ 名前", "ko": "✏️ 이름", "it": "✏️ Nome", "hi": "✏️ नाम", "ar": "✏️ الاسم"}.get(_lang_code, "✏️ Name")'
)
content = content.replace(
    '"btn_wl_color": "🎨 Цвет" if _lang_code == "ru" else ("🎨 Color" if _lang_code == "en" else "🎨 Color" if _lang_code == "es" else "🎨 颜色")',
    '"btn_wl_color": {"ru": "🎨 Цвет", "en": "🎨 Color", "es": "🎨 Color", "zh": "🎨 颜色", "fr": "🎨 Couleur", "de": "🎨 Farbe", "ja": "🎨 色", "ko": "🎨 색상", "it": "🎨 Colore", "hi": "🎨 रंग", "ar": "🎨 اللون"}.get(_lang_code, "🎨 Color")'
)
content = content.replace(
    '"btn_wl_logo": "🖼 Логотип" if _lang_code == "ru" else ("🖼 Logo" if _lang_code == "en" else "🖼 Logo" if _lang_code == "es" else "🖼 标志")',
    '"btn_wl_logo": {"ru": "🖼 Логотип", "en": "🖼 Logo", "es": "🖼 Logo", "zh": "🖼 标志", "fr": "🖼 Logo", "de": "🖼 Logo", "ja": "🖼 ロゴ", "ko": "🖼 로고", "it": "🖼 Logo", "hi": "🖼 लोगो", "ar": "🖼 الشعار"}.get(_lang_code, "🖼 Logo")'
)

with open('bot.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("🎉 Все недостающие переводы добавлены!")
