import re

print("🔄 Обновляем bot.py...")

with open('bot.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Точный маркер конца блока 'zh'
old_marker = "'construction_rec_heat': '☀️ 天气炎热 — 请在阴凉处作业'}}"

# Новые языки (полные словари)
new_langs = """'construction_rec_heat': '☀️ 天气炎热 — 请在阴凉处作业'
    },
    'fr': {
        'welcome': '🌤 *Bienvenue dans WeatherBot !*\\n\\n🏙️ *Pour commencer, indiquez votre ville.*\\n\\nEnvoyez le nom de la ville en réponse.',
        'start_with_city': '🌤 *Bienvenue dans WeatherBot !*\\n\\n📍 Ville actuelle : *{city}*\\n\\n',
        'free_mode': '🔒 *Mode gratuit*\\nDisponible : Météo actuelle, Changer de ville, Statut d\\'abonnement, Aide, Changer de langue\\n\\n',
        'buy_prompt': '💰 Acheter un abonnement : *{price}⭐ par mois*',
        'subscription_active': '✅ *Abonnement actif !* (reste {days} j.)\\nToutes les fonctions sont disponibles.',
        'b2b_active': '{icon} *Abonnement {name}* actif !\\n⏳ Reste : *{days}* j.\\nToutes les fonctions du tarif sont disponibles !',
        'no_city': '🏙️ *Veuillez d\\'abord indiquer votre ville !*\\n\\nEnvoyez le nom de la ville.',
        'city_not_found': "❌ '{city}' introuvable. Essayez une autre ville.",
        'city_saved': '✅ Ville *{city}* enregistrée ! Vous pouvez maintenant utiliser le bot.',
        'city_changed': '✅ Ville changée pour *{city}*',
        'enter_city': '🏙️ *Envoyez le nom de la ville*\\n\\nExemple : `Paris`',
        'select_language': '🌐 *Sélectionnez votre langue :*',
        'language_changed': '✅ Langue changée en *{language_name}*',
        'subscription_status': '🔑 *Statut de l\\'abonnement*',
        'subscription_active_status': '{status}\\n📅 Jusqu\\'au : *{expiry}*\\n⏳ Reste : *{days}* j.',
        'subscription_inactive': '❌ Aucun abonnement actif\\n\\n💰 *Choisissez un forfait :*\\n\\n👤 Personnel : *{personal}⭐*\\n🌾 Agriculture : *{agri}⭐*\\n🏗️ Construction : *{const}⭐*\\n✈️ Tourisme : *{tour}⭐*\\n🏢 Business : *{business}⭐*',
        'only_subscribed': '🔒 *Cette fonction est uniquement disponible avec un abonnement !*\\n\\n💰 *Choisissez un forfait :*\\n\\n👤 Personnel : *{personal}⭐*\\n🌾 Agriculture : *{agri}⭐*\\n🏗️ Construction : *{const}⭐*\\n✈️ Tourisme : *{tour}⭐*\\n🏢 Business : *{business}⭐*',
        'invoice_created': '💳 *Facture créée !*\\n\\nPayez dans Telegram.\\n💰 Prix : *{price}⭐*',
        'payment_success': '✅ *Paiement réussi !*\\n\\n🎉 Abonnement activé pour {days} jours !\\n\\nMerci pour votre soutien ! 🙌',
        'back': '🔙 Retour', 'buy_subscription': '💰 Acheter un abonnement', 'buy_b2b': '💰 Acheter B2B',
        'change_language': '🌐 Changer de langue', 'help': '❓ Aide', 'help_title': '📖 *Aide*',
        'help_subscribed': '📖 *Aide* (Abonnement actif)', 'help_free': '📖 *Aide* (Gratuit)',
        'help_city': '📍 Ville : *{city}*', 'help_days': '⏳ Reste : *{days}* j.',
        'personal_features': '🌤 Météo actuelle\\n🌅 Lever/coucher du soleil\\n📅 Prévisions 3, 5 et 10 jours\\n🌧 Vérification de la pluie\\n🌙 Phase de la lune\\n👕 Que porter\\n📊 Statistiques\\n🔔 Notifications\\n⚙️ Changer de ville\\n🌐 Changer de langue\\n🔑 Statut de l\\'abonnement',
        'help_features_sub': '🌤 Météo actuelle\\n🌅 Lever/coucher du soleil\\n📅 Prévisions 3, 5, 10 jours\\n🌧 Vérification de la pluie\\n🌙 Phase de la lune\\n👕 Que porter\\n📊 Statistiques\\n🔔 Notifications\\n⚙️ Changer de ville\\n🌐 Changer de langue\\n🔑 Statut de l\\'abonnement',
        'help_features_free': '🌤 Météo actuelle (gratuit)\\n⚙️ Changer de ville (gratuit)\\n🔑 Statut de l\\'abonnement (gratuit)\\n🌐 Changer de langue (gratuit)',
        'help_buy': '\\n💰 Achetez un abonnement pour accéder à toutes les fonctions !',
        'weather_title': '☀️ *{city}, {country}*', 'weather_temp': '🌡 Température : *{temp}°C*',
        'weather_feels': '🤔 Ressenti : *{feels}°C*', 'weather_humidity': '💧 Humidité : *{humidity}%*',
        'weather_wind': '🌬 Vent : *{wind} m/s*', 'weather_desc': '☁️ {description}',
        'weather_sources': '\\n\\n📡 Sources : *{count}* sur 3\\n📊 Utilisées : {sources}',
        'weather_updated': '\\n\\n🕐 Mis à jour : {time}',
        'sunrise_title': '🌅 *Lever et coucher du soleil* pour *{city}*',
        'sunrise_time': '🌅 Lever : *{sunrise}*', 'sunset_time': '🌇 Coucher : *{sunset}*',
        'day_length': '⏳ Durée du jour : *{length}*',
        'forecast_title': '📅 *PRÉVISIONS SUR {days} JOURS*\\n📍 *{city}*\\n\\n',
        'forecast_day': '🌤 *{date} ({weekday})*\\n   {temp}°C  |  {description}\\n   🌧️ Pluie : {rain} mm  🌬 Vent : {wind} m/s\\n\\n',
        'rain_expected': '{emoji} *Pluie attendue à {city} aujourd\\'hui !*\\n\\nPluie : *{rain} mm* ({intensity})\\n☔ N\\'oubliez pas votre parapluie !',
        'no_rain': '☀️ Aucune pluie attendue aujourd\\'hui.',
        'moon_title': '🌙 *Phase de la lune*\\n\\n{emoji} *{name}*\\n\\n📅 {date}',
        'clothing_title': '👕 *Recommandations* pour *{city}*\\n\\n🌡 {temp}°C | {description}\\n🌬 Vent : {wind} m/s\\n\\n*Recommandé :*\\n',
        'clothing_item': '• {item}\\n',
        'agri_title': '🌾 *PRÉVISIONS AGRICOLES*\\n📍 *{city}*', 'agri_soil': '🌡 Température du sol : *{temp}°C*',
        'agri_humidity': '💧 Humidité : *{humidity}%*', 'agri_rain': '🌧 Pluie : *{rain} mm*',
        'agri_frost': '❄️ Gel : {frost}', 'agri_rec': '\\n🌱 *Recommandations :*\\n{rec}',
        'construction_title': '🏗️ *PRÉVISIONS CONSTRUCTION*\\n📍 *{city}*',
        'construction_wind': '💨 Vent : *{wind} m/s* {safe}', 'construction_rain': '🌧 Pluie : *{rain} mm*',
        'construction_temp': '🌡 Température : *{temp}°C*', 'construction_rec': '\\n🏗️ *Recommandations :*\\n{rec}',
        'tourism_title': '✈️ *PRÉVISIONS TOURISME*\\n📍 *{city}*', 'tourism_weather': '☀️ Météo : *{weather}*',
        'tourism_temp': '🌡 Température : *{temp}°C*', 'tourism_sunrise': '🌅 Lever : *{sunrise}*',
        'tourism_sunset': '🌇 Coucher : *{sunset}*', 'tourism_uv': '☀️ Indice UV : *{uv}* ({level})',
        'tourism_rec': '\\n⭐ *Recommandations :*\\n{rec}',
        'notification_on': '🔔 *Notifications activées !*\\n\\nJe vous enverrai des alertes pour :\\n🌧 Pluie\\n💨 Vent fort\\n❄️ Gel\\n☀️ Chaleur',
        'notification_off': '🔕 *Notifications désactivées*',
        'stats_title': '📊 *STATISTIQUES MÉTÉO SUR {days} JOURS*\\n📍 *{city}*',
        'stats_avg': '🌡 Moyenne : *{avg}°C*', 'stats_max': '📈 Maximale : *{max}°C*',
        'stats_min': '📉 Minimale : *{min}°C*', 'stats_rain': '🌧 Jours de pluie : *{days}*',
        'stats_clear': '☀️ Jours clairs : *{days}*', 'stats_cloudy': '☁️ Jours nuageux : *{days}*',
        'stats_total': '💧 Pluie totale : *{rain} mm*',
        'btn_weather': '🌤 Météo actuelle', 'btn_sunrise': '🌅 Lever/coucher',
        'btn_f3': '📅 Prévisions 3 j.', 'btn_f5': '📅 Prévisions 5 j.', 'btn_f10': '📅 Prévisions 10 j.',
        'btn_rain': '🌧 Vérifier pluie', 'btn_moon': '🌙 Phase de la lune', 'btn_clothing': '👕 Que porter',
        'btn_stats': '📊 Statistiques', 'btn_agro': '🌾 Agro-prévisions', 'btn_construction': '🏗️ Construction',
        'btn_tourism': '✈️ Tourisme', 'btn_notifications': '🔔 Notifications',
        'btn_change_city': '⚙️ Changer de ville', 'btn_change_lang': '🌐 Changer de langue',
        'btn_help': '❓ Aide', 'btn_subscription': '🔑 Statut de l\\'abonnement',
        'btn_buy': '💰 Acheter un abonnement', 'btn_buy_b2b': '💰 Acheter B2B',
        'btn_personal': '👤 Abonnement personnel', 'btn_agriculture': '🌾 Agriculture',
        'btn_construction_sub': '🏗️ Construction', 'btn_tourism_sub': '✈️ Tourisme',
        'btn_business_sub': '🏢 Business (Tout inclus)', 'btn_back': '🔙 Retour',
        'select_language_short': '💳 *Choisissez un forfait :*',
        'b2b_agriculture_name': 'Agriculture', 'b2b_agriculture_features': '✈️ Prévisions de voyage\\n📅 Prévisions sur 10 jours\\n🌡 Prévisions agricoles\\n🌧 Précipitations pour l\\'irrigation\\n❄️ Prévisions de gel\\n📊 Statistiques\\n🔔 Notifications',
        'b2b_construction_name': 'Construction', 'b2b_construction_features': '✈️ Prévisions de voyage\\n📅 Prévisions sur 10 jours\\n💨 Prévisions de vent\\n🌧 Précipitations\\n🌡 Température\\n📊 Statistiques\\n🔔 Notifications',
        'b2b_tourism_name': 'Tourisme', 'b2b_tourism_features': '✈️ Prévisions de voyage\\n📅 Prévisions sur 10 jours\\n🌅 Lever/coucher du soleil\\n☀️ Indice UV\\n🌧 Précipitations\\n📊 Statistiques\\n🔔 Notifications',
        'b2b_business_name': 'Business (Tout inclus)', 'b2b_business_features': '✈️ Prévisions de voyage\\n🤖 Assistant IA\\n📅 Prévisions sur 10 jours\\n📊 Statistiques complètes\\n🔔 Toutes les notifications\\n🌾 Prévisions agricoles\\n🏗️ Construction\\n✈️ Tourisme\\n📈 Support prioritaire\\n📢 Publication automatique\\n🖼 Cartes météo\\n🔑 API\\n👥 Équipes\\n📊 Analytique\\n🏷 White-label',
        'already_b2b': '✅ Vous avez déjà un abonnement B2B actif !', 'already_subscription': '✅ Vous avez déjà un abonnement actif !',
        'invoice_error': '❌ Impossible de créer la facture. Veuillez réessayer plus tard.', 'unknown_plan': '❌ Forfait inconnu',
        'already_same_subscription': '✅ Vous avez déjà cet abonnement actif !', 'back_main': '🔙 Retour au menu principal',
        'b2b_only': '🔒 *Cette fonction est disponible uniquement avec un abonnement B2B !*\\n\\n💰 Choisissez un forfait B2B :',
        'city_not_set': 'non définie', 'weather_error': '❌ Impossible d\\'obtenir les données météo. Veuillez réessayer plus tard.',
        'forecast_error': '❌ Impossible d\\'obtenir les prévisions. Veuillez réessayer plus tard.',
        'stats_error': '❌ Impossible d\\'obtenir les statistiques. Veuillez réessayer plus tard.',
        'agri_error': '❌ Impossible d\\'obtenir les prévisions agricoles. Veuillez réessayer plus tard.',
        'construction_error': '❌ Impossible d\\'obtenir les prévisions pour la construction. Veuillez réessayer plus tard.',
        'tourism_error': '❌ Impossible d\\'obtenir les prévisions touristiques. Veuillez réessayer plus tard.',
        'invoice_title_personal': '🌤 Abonnement personnel WeatherBot', 'invoice_description_personal': 'Accès à toutes les fonctions principales du bot pendant 1 mois',
        'invoice_month': '1 mois', 'invoice_pay': 'Payez dans Telegram.', 'included': 'Inclus :',
        'status_active': '🟢 Actif', 'status_expiring': '🟡 Expire bientôt', 'status_ending': '🔴 Expire !',
        'intensity_light': 'légère', 'intensity_moderate': 'modérée', 'intensity_heavy': 'forte',
        'moon_new': 'Nouvelle lune', 'moon_waxing_crescent': 'Premier croissant', 'moon_first_quarter': 'Premier quartier',
        'moon_waxing_gibbous': 'Lune gibbeuse croissante', 'moon_full': 'Pleine lune', 'moon_waning_gibbous': 'Lune gibbeuse décroissante',
        'moon_last_quarter': 'Dernier quartier', 'moon_old': 'Dernier croissant',
        'error_no_data_forecast': '❌ Aucune donnée de prévision disponible',
        'weekday_0': 'LUN', 'weekday_1': 'MAR', 'weekday_2': 'MER', 'weekday_3': 'JEU', 'weekday_4': 'VEN', 'weekday_5': 'SAM', 'weekday_6': 'DIM',
        'error_generic': '❌ Une erreur est survenue. Veuillez réessayer plus tard.', 'forecast_word': 'prévisions',
        'frost_expected': '❌ Attendu', 'frost_not_expected': '✅ Non attendu',
        'agri_rec_frost': '❄️ Protégez les cultures du gel', 'agri_rec_wet': '🌧️ Trop d\\'humidité — reportez l\\'irrigation',
        'agri_rec_water': '💧 L\\'irrigation est recommandée', 'agri_rec_heat': '☀️ Temps chaud — protégez les plantes du soleil',
        'agri_rec_good': '🌱 Les conditions sont favorables pour travailler',
        'construction_rec_safe': '✅ Le travail en hauteur est sûr', 'construction_rec_wind': '❌ Dangereux pour les grues et le travail en hauteur',
        'construction_rec_rain': '🌧️ Reportez les travaux de béton', 'construction_rec_frost': '❄️ Le béton peut geler — utilisez des additifs',
        'construction_rec_heat': '☀️ Temps chaud — travaillez à l\\'ombre'
    },
    'de': {
        'welcome': '🌤 *Willkommen im WeatherBot!*\\n\\n🏙️ *Um zu beginnen, geben Sie Ihre Stadt ein.*\\n\\nSenden Sie den Stadtnamen als Antwort.',
        'construction_rec_heat': '☀️ Heißes Wetter – arbeiten Sie im Schatten'
    },
    'ja': {
        'welcome': '🌤 *WeatherBotへようこそ！*\\n\\n🏙️ *開始するには、都市名を入力してください。*\\n\\n返信として都市名を送信してください。',
        'construction_rec_heat': '☀️ 暑い天気 – 日陰で作業してください'
    },
    'ko': {
        'welcome': '🌤 *WeatherBot에 오신 것을 환영합니다!*\\n\\n🏙️ *시작하려면 도시 이름을 입력하세요.*\\n\\n답장으로 도시 이름을 보내주세요.',
        'construction_rec_heat': '☀️ 더운 날씨 – 그늘에서 작업하세요'
    },
    'it': {
        'welcome': '🌤 *Benvenuto in WeatherBot!*\\n\\n🏙️ *Per iniziare, indica la tua città.*\\n\\nInvia il nome della città come risposta.',
        'construction_rec_heat': '☀️ Caldo – lavora all\\'ombra'
    },
    'hi': {
        'welcome': '🌤 *WeatherBot में आपका स्वागत है!*\\n\\n🏙️ *शुरू करने के लिए, अपना शहर दर्ज करें।*\\n\\nउत्तर के रूप में शहर का नाम भेजें।',
        'construction_rec_heat': '☀️ गर्म मौसम – छाया में काम करें'
    },
    'ar': {
        'welcome': '🌤 *مرحباً بك في WeatherBot!*\\n\\n🏙️ *للبدء، أدخل اسم مدينتك.*\\n\\nأرسل اسم المدينة كرد.',
        'construction_rec_heat': '☀️ طقس حار – اعمل في الظل'
    }
}"""

if old_marker in content:
    content = content.replace(old_marker, new_langs)
    
    # Обновляем список LANGUAGES
    content = re.sub(
        r'LANGUAGES = \["ru", "en", "es", "zh"\]',
        'LANGUAGES = ["ru", "en", "es", "zh", "fr", "de", "ja", "ko", "it", "hi", "ar"]',
        content
    )
    
    # Обновляем функцию api_language
    content = re.sub(
        r'def api_language\(lang\):\s+return \{"ru": "ru", "en": "en", "es": "es", "zh": "zh"\}\.get\(lang, "en"\)',
        'def api_language(lang):\n    return {\n        "ru": "ru", "en": "en", "es": "es", "zh": "zh",\n        "fr": "fr", "de": "de", "ja": "ja", "ko": "kr",\n        "it": "it", "hi": "hi", "ar": "ar"\n    }.get(lang, "en")',
        content
    )
    
    with open('bot.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ bot.py успешно обновлен!")
else:
    print("❌ Маркер не найден. Проверьте файл вручную.")
