print("🔄 Обновляем features.py (безопасный метод)...")

with open('features.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Точный маркер конца словаря FEATURE_TEXTS (блок "zh" и финальные скобки)
old_marker = '''        "daily_wind": "💨 强风警告。"
    }
}'''

# Новые языки + корректное закрытие словаря
new_content = '''        "daily_wind": "💨 强风警告。"
    },
    "fr": {
        "trip_button": "✈️ Ouvrez « Voyage » et choisissez la ville et la durée avec les boutons.",
        "ai_button": "🤖 Ouvrez IA et écrivez votre question.",
        "help": "🌟 WeatherTomBot\\n\\n⭐ Villes — villes enregistrées\\n🔔 Notifications — alertes météo\\n✈️ Voyage — prévisions de voyage\\n🤖 IA — assistant météo\\n💳 Forfaits — Free / Premium / Business\\n\\nUtilisez les boutons du menu pour une utilisation normale.",
        "favorites_title": "⭐ Villes", "no_saved_cities": "Aucune ville enregistrée.", "addcity_hint": "\\n\\nAppuyez sur « ➕ Ajouter une ville » pour enregistrer une ville.",
        "favorite_added": "✅ Ajoutée aux favoris.", "favorite_add_failed": "❌ Impossible d'ajouter ({result}).", "favorite_removed": "✅ Supprimée.", "city_not_found": "❌ Ville introuvable.",
        "alerts_title": "🔔 Notifications", "alerts_hint": "\\n\\nChoisissez une alerte avec les boutons.", "premium_alerts": "⭐ Abonnement Premium requis pour les notifications météo.",
        "threshold_number": "❌ Le seuil doit être un nombre.", "alert_set": "🌧 {kind}: {state}{suffix}", "premium_notifications": "⭐ Abonnement Premium requis pour les notifications.",
        "notifications_enabled": "🔔 Notifications activées.", "notifications_disabled": "🔕 Notifications désactivées.", "notification_time": "⏰ Heure de notification : {time}",
        "notification_time_usage": "Utilisez HH:MM, par ex. /notify_time 08:00", "premium_trip": "⭐ Abonnement Premium requis pour les prévisions de voyage.",
        "trip_unavailable": "❌ Prévisions de voyage indisponibles.", "trip_title": "✈️ Prévisions de voyage : {destination}", "premium_required": "⭐ Abonnement Premium requis pour cette fonction.",
        "referral": "👥 Programme de parrainage\\n\\nVotre code : {code}\\nInvités : {count}\\n🎁 Récompense : 7 jours Premium\\n\\n{link}",
        "promo_applied": "🎁 Promo appliquée.", "promo_error": "❌ Erreur de promo : {result}",
        "plans": "💰 Forfaits\\n\\n🆓 Free — météo actuelle + fonctions de base\\n⭐ Premium — alertes, favoris, voyages et IA\\n💼 Business — canaux, API, white-label, équipes",
        "broadcast_usage": "Utilisez /broadcast_segment premium|free|inactive7|lang:fr|source:NOM TEXTE", "broadcast_done": "📢 Diffusion : {result}", "admin_only": "⛔ Admin uniquement.",
        "channel_usage": "Utilisez /channel @channel VILLE [HH:MM]", "business_channel": "💼 Abonnement Business requis pour la publication automatique dans les canaux.",
        "channel_failed": "❌ Impossible de connecter le canal.", "channel_connected": "📢 Canal connecté : {channel}\\nVille : {city}\\nHeure : {schedule}",
        "no_channels": "📢 Aucun canal. Utilisez /channel @channel VILLE 08:00", "channels_title": "📢 Canaux :", "card_unavailable": "❌ Génération de carte indisponible.",
        "business_api": "💼 Abonnement Business requis pour l'accès à l'API.", "api_created": "🔑 Clé API créée (stockez-la maintenant) :\\n{key}", "api_usage": "Utilisez /apikey pour générer une clé.",
        "teams_title": "👥 Équipes", "no_teams": "Aucune équipe", "team_created": "✅ Équipe créée : {team}", "business_teams": "💼 Abonnement Business requis pour les équipes.",
        "member_added": "✅ Membre ajouté.", "member_failed": "❌ Impossible d'ajouter le membre.", "white_label": "🏢 White-label\\n{data}",
        "weather_alert_title": "⚠️ Notification météo", "rain_expected": "☔ Pluie attendue.", "storm_possible": "⛈ Conditions orageuses possibles.",
        "strong_wind": "💨 Vent fort : {wind}.", "low_temp": "🥶 Alerte froid : {temp}° ou moins.", "high_temp": "🔥 Alerte chaleur : {temp}° ou plus.",
        "heavy_rain_warning": "🌧️ Pluie forte : {rain} mm.", "frost_warning": "❄️ Alerte gel : {temp}° ou moins.", "notification_settings_title": "🔔 Notifications",
        "notification_usage": "Choisissez une alerte avec les boutons.", "daily_rain": "☔ Pluie attendue.", "daily_wind": "💨 Alerte vent fort.",
        "analytics": "📊 Analytique\\nRevenus : {revenue:.2f}\\nMRR : {mrr:.2f}\\nARPU : {arpu:.2f}\\nPaiements : {payments}\\nUtilisateurs payants : {paying_users}\\n\\nEntonnoir : {funnel}\\nRétention : {retention}\\nSources : {sources}"
    },
    "de": {
        "trip_button": "✈️ Öffnen Sie „Reise“ und wählen Sie Stadt und Dauer mit den Tasten.",
        "ai_button": "🤖 Öffnen Sie KI und schreiben Sie Ihre Frage.",
        "help": "🌟 WeatherTomBot\\n\\n⭐ Städte — gespeicherte Städte\\n🔔 Benachrichtigungen — Wetterwarnungen\\n✈️ Reise — Reisevorhersage\\n🤖 KI — Wetterassistent\\n💳 Tarife — Free / Premium / Business\\n\\nVerwenden Sie die Menüschaltflächen für den normalen Betrieb.",
        "favorites_title": "⭐ Städte", "no_saved_cities": "Keine gespeicherten Städte.", "addcity_hint": "\\n\\nDrücken Sie „➕ Stadt hinzufügen“, um eine Stadt zu speichern.",
        "favorite_added": "✅ Zu Favoriten hinzugefügt.", "favorite_add_failed": "❌ Hinzufügen fehlgeschlagen ({result}).", "favorite_removed": "✅ Entfernt.", "city_not_found": "❌ Stadt nicht gefunden.",
        "alerts_title": "🔔 Benachrichtigungen", "alerts_hint": "\\n\\nWählen Sie eine Warnung mit den Tasten.", "premium_alerts": "⭐ Premium-Abonnement für Wetterbenachrichtigungen erforderlich.",
        "threshold_number": "❌ Der Schwellenwert muss eine Zahl sein.", "alert_set": "🌧 {kind}: {state}{suffix}", "premium_notifications": "⭐ Premium-Abonnement für Benachrichtigungen erforderlich.",
        "notifications_enabled": "🔔 Benachrichtigungen aktiviert.", "notifications_disabled": "🔕 Benachrichtigungen deaktiviert.", "notification_time": "⏰ Benachrichtigungszeit: {time}",
        "notification_time_usage": "Verwenden Sie HH:MM, z.B. /notify_time 08:00", "premium_trip": "⭐ Premium-Abonnement für Reisevorhersagen erforderlich.",
        "trip_unavailable": "❌ Reisevorhersage nicht verfügbar.", "trip_title": "✈️ Reisevorhersage: {destination}", "premium_required": "⭐ Premium-Abonnement für diese Funktion erforderlich.",
        "referral": "👥 Empfehlungsprogramm\\n\\nIhr Code: {code}\\nEingeladen: {count}\\n🎁 Belohnung: 7 Tage Premium\\n\\n{link}",
        "promo_applied": "🎁 Promo angewendet.", "promo_error": "❌ Promo-Fehler: {result}",
        "plans": "💰 Tarife\\n\\n🆓 Free — aktuelles Wetter + Basisfunktionen\\n⭐ Premium — Warnungen, Favoriten, Reisen und KI\\n💼 Business — Kanäle, API, White-Label, Teams",
        "broadcast_usage": "Verwenden Sie /broadcast_segment premium|free|inactive7|lang:de|source:NAME TEXT", "broadcast_done": "📢 Rundsendung: {result}", "admin_only": "⛔ Nur Admin.",
        "channel_usage": "Verwenden Sie /channel @kanal STADT [HH:MM]", "business_channel": "💼 Business-Abonnement für automatische Kanalveröffentlichung erforderlich.",
        "channel_failed": "❌ Kanal konnte nicht verbunden werden.", "channel_connected": "📢 Kanal verbunden: {channel}\\nStadt: {city}\\nZeit: {schedule}",
        "no_channels": "📢 Keine Kanäle. Verwenden Sie /channel @kanal STADT 08:00", "channels_title": "📢 Kanäle:", "card_unavailable": "❌ Kartengenerierung nicht verfügbar.",
        "business_api": "💼 Business-Abonnement für API-Zugriff erforderlich.", "api_created": "🔑 API-Schlüssel erstellt (jetzt speichern):\\n{key}", "api_usage": "Verwenden Sie /apikey, um einen Schlüssel zu generieren.",
        "teams_title": "👥 Teams", "no_teams": "Keine Teams", "team_created": "✅ Team erstellt: {team}", "business_teams": "💼 Business-Abonnement für Teams erforderlich.",
        "member_added": "✅ Mitglied hinzugefügt.", "member_failed": "❌ Mitglied kann nicht hinzugefügt werden.", "white_label": "🏢 White-Label\\n{data}",
        "weather_alert_title": "⚠️ Wetterbenachrichtigung", "rain_expected": "☔ Regen erwartet.", "storm_possible": "⛈ Gewitter möglich.",
        "strong_wind": "💨 Starker Wind: {wind}.", "low_temp": "🥶 Kältewarnung: {temp}° oder weniger.", "high_temp": "🔥 Hitzewarnung: {temp}° oder mehr.",
        "heavy_rain_warning": "🌧️ Starker Regen: {rain} mm.", "frost_warning": "❄️ Frostwarnung: {temp}° oder weniger.", "notification_settings_title": "🔔 Benachrichtigungen",
        "notification_usage": "Wählen Sie eine Warnung mit den Tasten.", "daily_rain": "☔ Regen erwartet.", "daily_wind": "💨 Warnung vor starkem Wind.",
        "analytics": "📊 Analytik\\nUmsatz: {revenue:.2f}\\nMRR: {mrr:.2f}\\nARPU: {arpu:.2f}\\nZahlungen: {payments}\\nZahlende Nutzer: {paying_users}\\n\\nTrichter: {funnel}\\nBindung: {retention}\\nQuellen: {sources}"
    },
    "ja": {
        "trip_button": "✈️ “旅行” を開き、ボタンで都市と日数を選択してください。",
        "ai_button": "🤖 AI を開いて質問を入力してください。",
        "help": "🌟 WeatherTomBot\\n\\n⭐ 都市 — 保存された都市\\n🔔 通知 — 天気アラート\\n✈️ 旅行 — 旅行予報\\n🤖 AI — 天気アシスタント\\n💰 プラン — Free / Premium / Business\\n\\n通常の操作にはメニューボタンを使用してください。",
        "favorites_title": "⭐ 都市", "no_saved_cities": "保存された都市はありません。", "addcity_hint": "\\n\\n「➕ 都市を追加」を押して都市を保存してください。",
        "favorite_added": "✅ お気に入りに追加されました。", "favorite_add_failed": "❌ 追加に失敗しました ({result})。", "favorite_removed": "✅ 削除されました。", "city_not_found": "❌ 都市が見つかりません。",
        "alerts_title": "🔔 通知", "alerts_hint": "\\n\\nボタンでアラートを選択してください。", "premium_alerts": "⭐ 天気通知には Premium が必要です。",
        "threshold_number": "❌ しきい値は数値である必要があります。", "alert_set": "🌧 {kind}: {state}{suffix}", "premium_notifications": "⭐ 通知には Premium が必要です。",
        "notifications_enabled": "🔔 通知が有効になりました。", "notifications_disabled": "🔕 通知が無効になりました。", "notification_time": "⏰ 通知時間: {time}",
        "notification_time_usage": "HH:MM を使用してください (例: /notify_time 08:00)", "premium_trip": "⭐ 旅行予報には Premium が必要です。",
        "trip_unavailable": "❌ 旅行予報は利用できません。", "trip_title": "✈️ 旅行予報: {destination}", "premium_required": "⭐ この機能には Premium が必要です。",
        "referral": "👥 紹介プログラム\\n\\nあなたのコード: {code}\\n招待数: {count}\\n🎁 報酬: 7 日間の Premium\\n\\n{link}",
        "promo_applied": "🎁 プロモーションが適用されました。", "promo_error": "❌ プロモーションエラー: {result}",
        "plans": "💰 プラン\\n\\n🆓 Free — 現在の天気 + 基本機能\\n⭐ Premium — アラート、お気に入り、旅行、AI\\n💼 Business — チャンネル、API、ホワイトラベル、チーム",
        "broadcast_usage": "/broadcast_segment premium|free|inactive7|lang:ja|source:名前 TEXT を使用してください", "broadcast_done": "📢 配信: {result}", "admin_only": "⛔ 管理者のみ。",
        "channel_usage": "/channel @チャンネル 都市 [HH:MM] を使用してください", "business_channel": "💼 チャンネルへの自動投稿には Business が必要です。",
        "channel_failed": "❌ チャンネルを接続できませんでした。", "channel_connected": "📢 チャンネル接続済み: {channel}\\n都市: {city}\\n時間: {schedule}",
        "no_channels": "📢 チャンネルはありません。/channel @チャンネル 都市 08:00 を使用してください", "channels_title": "📢 チャンネル:", "card_unavailable": "❌ カード生成は利用できません。",
        "business_api": "💼 API アクセスには Business が必要です。", "api_created": "🔑 API キーが作成されました (今すぐ保存してください):\\n{key}", "api_usage": "キーを生成するには /apikey を使用してください。",
        "teams_title": "👥 チーム", "no_teams": "チームはありません", "team_created": "✅ チームが作成されました: {team}", "business_teams": "💼 チーム機能には Business が必要です。",
        "member_added": "✅ メンバーが追加されました。", "member_failed": "❌ メンバーを追加できません。", "white_label": "🏢 ホワイトラベル\\n{data}",
        "weather_alert_title": "⚠️ 天気通知", "rain_expected": "☔ 雨が予想されます。", "storm_possible": "⛈ 雷雨の可能性があります。",
        "strong_wind": "💨 強風: {wind}。", "low_temp": "🥶 寒冷注意報: {temp}° 以下。", "high_temp": "🔥 高温注意報: {temp}° 以上。",
        "heavy_rain_warning": "🌧️ 大雨: {rain} mm。", "frost_warning": "❄️ 霜注意報: {temp}° 以下。", "notification_settings_title": "🔔 通知",
        "notification_usage": "ボタンでアラートを選択してください。", "daily_rain": "☔ 雨が予想されます。", "daily_wind": "💨 強風注意報。",
        "analytics": "📊 アナリティクス\\n収益: {revenue:.2f}\\nMRR: {mrr:.2f}\\nARPU: {arpu:.2f}\\n支払い: {payments}\\n有料ユーザー: {paying_users}\\n\\nファネル: {funnel}\\n保持率: {retention}\\nソース: {sources}"
    },
    "ko": {
        "trip_button": "✈️ “여행”을 열고 버튼으로 도시와 일수를 선택하세요.",
        "ai_button": "🤖 AI를 열고 질문을 입력하세요.",
        "help": "🌟 WeatherTomBot\\n\\n⭐ 도시 — 저장된 도시\\n🔔 알림 — 날씨 경보\\n✈️ 여행 — 여행 예보\\n🤖 AI — 날씨 도우미\\n💰 요금제 — Free / Premium / Business\\n\\n정상적인 작동을 위해 메뉴 버튼을 사용하세요.",
        "favorites_title": "⭐ 도시", "no_saved_cities": "저장된 도시가 없습니다.", "addcity_hint": "\\n\\n도시를 저장하려면 “➕ 도시 추가”를 누르세요.",
        "favorite_added": "✅ 즐겨찾기에 추가되었습니다.", "favorite_add_failed": "❌ 추가 실패 ({result}).", "favorite_removed": "✅ 제거되었습니다.", "city_not_found": "❌ 도시를 찾을 수 없습니다.",
        "alerts_title": "🔔 알림", "alerts_hint": "\\n\\n버튼으로 경보를 선택하세요.", "premium_alerts": "⭐ 날씨 알림에는 Premium이 필요합니다.",
        "threshold_number": "❌ 임계값은 숫자여야 합니다.", "alert_set": "🌧 {kind}: {state}{suffix}", "premium_notifications": "⭐ 알림에는 Premium이 필요합니다.",
        "notifications_enabled": "🔔 알림이 활성화되었습니다.", "notifications_disabled": "🔕 알림이 비활성화되었습니다.", "notification_time": "⏰ 알림 시간: {time}",
        "notification_time_usage": "HH:MM을 사용하세요 (예: /notify_time 08:00)", "premium_trip": "⭐ 여행 예보에는 Premium이 필요합니다.",
        "trip_unavailable": "❌ 여행 예보를 사용할 수 없습니다.", "trip_title": "✈️ 여행 예보: {destination}", "premium_required": "⭐ 이 기능에는 Premium이 필요합니다.",
        "referral": "👥 추천 프로그램\\n\\n내 코드: {code}\\n초대 수: {count}\\n🎁 보상: 7일 Premium\\n\\n{link}",
        "promo_applied": "🎁 프로모션이 적용되었습니다.", "promo_error": "❌ 프로모션 오류: {result}",
        "plans": "💰 요금제\\n\\n🆓 Free — 현재 날씨 + 기본 기능\\n⭐ Premium — 경보, 즐겨찾기, 여행, AI\\n💼 Business — 채널, API, 화이트라벨, 팀",
        "broadcast_usage": "/broadcast_segment premium|free|inactive7|lang:ko|source:이름 TEXT를 사용하세요", "broadcast_done": "📢 방송: {result}", "admin_only": "⛔ 관리자만 가능.",
        "channel_usage": "/channel @채널 도시 [HH:MM]을 사용하세요", "business_channel": "💼 채널 자동 게시에는 Business가 필요합니다.",
        "channel_failed": "❌ 채널을 연결할 수 없습니다.", "channel_connected": "📢 채널 연결됨: {channel}\\n도시: {city}\\n시간: {schedule}",
        "no_channels": "📢 채널이 없습니다. /channel @채널 도시 08:00을 사용하세요", "channels_title": "📢 채널:", "card_unavailable": "❌ 카드 생성을 사용할 수 없습니다.",
        "business_api": "💼 API 액세스에는 Business가 필요합니다.", "api_created": "🔑 API 키가 생성되었습니다 (지금 저장하세요):\\n{key}", "api_usage": "키를 생성하려면 /apikey를 사용하세요.",
        "teams_title": "👥 팀", "no_teams": "팀이 없습니다", "team_created": "✅ 팀이 생성되었습니다: {team}", "business_teams": "💼 팀 기능에는 Business가 필요합니다.",
        "member_added": "✅ 멤버가 추가되었습니다.", "member_failed": "❌ 멤버를 추가할 수 없습니다.", "white_label": "🏢 화이트라벨\\n{data}",
        "weather_alert_title": "⚠️ 날씨 알림", "rain_expected": "☔ 비가 예상됩니다.", "storm_possible": "⛈ 뇌우가 예상됩니다.",
        "strong_wind": "💨 강풍: {wind}.", "low_temp": "🥶 한파 주의보: {temp}° 이하.", "high_temp": "🔥 폭염 주의보: {temp}° 이상.",
        "heavy_rain_warning": "🌧️ 호우: {rain} mm.", "frost_warning": "❄️ 서리 주의보: {temp}° 이하.", "notification_settings_title": "🔔 알림",
        "notification_usage": "버튼으로 경보를 선택하세요.", "daily_rain": "☔ 비가 예상됩니다.", "daily_wind": "💨 강풍 주의보.",
        "analytics": "📊 분석\\n수익: {revenue:.2f}\\nMRR: {mrr:.2f}\\nARPU: {arpu:.2f}\\n결제: {payments}\\n유료 사용자: {paying_users}\\n\\n퍼널: {funnel}\\n유지율: {retention}\\n소스: {sources}"
    },
    "it": {
        "trip_button": "✈️ Apri «Viaggio» e scegli città e durata con i pulsanti.",
        "ai_button": "🤖 Apri IA e scrivi la tua domanda.",
        "help": "🌟 WeatherTomBot\\n\\n⭐ Città — città salvate\\n🔔 Notifiche — avvisi meteo\\n✈️ Viaggio — previsioni di viaggio\\n🤖 IA — assistente meteo\\n💰 Piani — Free / Premium / Business\\n\\nUsa i pulsanti del menu per il normale funzionamento.",
        "favorites_title": "⭐ Città", "no_saved_cities": "Nessuna città salvata.", "addcity_hint": "\\n\\nPremi «➕ Aggiungi città» per salvare una città.",
        "favorite_added": "✅ Aggiunta ai preferiti.", "favorite_add_failed": "❌ Impossibile aggiungere ({result}).", "favorite_removed": "✅ Rimossa.", "city_not_found": "❌ Città non trovata.",
        "alerts_title": "🔔 Notifiche", "alerts_hint": "\\n\\nScegli un avviso con i pulsanti.", "premium_alerts": "⭐ Abbonamento Premium richiesto per le notifiche meteo.",
        "threshold_number": "❌ La soglia deve essere un numero.", "alert_set": "🌧 {kind}: {state}{suffix}", "premium_notifications": "⭐ Abbonamento Premium richiesto per le notifiche.",
        "notifications_enabled": "🔔 Notifiche abilitate.", "notifications_disabled": "🔕 Notifiche disabilitate.", "notification_time": "⏰ Ora di notifica: {time}",
        "notification_time_usage": "Usa HH:MM, es. /notify_time 08:00", "premium_trip": "⭐ Abbonamento Premium richiesto per le previsioni di viaggio.",
        "trip_unavailable": "❌ Previsioni di viaggio non disponibili.", "trip_title": "✈️ Previsioni di viaggio: {destination}", "premium_required": "⭐ Abbonamento Premium richiesto per questa funzione.",
        "referral": "👥 Programma di referral\\n\\nIl tuo codice: {code}\\nInvitati: {count}\\n🎁 Ricompensa: 7 giorni Premium\\n\\n{link}",
        "promo_applied": "🎁 Promo applicata.", "promo_error": "❌ Errore promo: {result}",
        "plans": "💰 Piani\\n\\n🆓 Free — meteo attuale + funzioni base\\n⭐ Premium — avvisi, preferiti, viaggi e IA\\n💼 Business — canali, API, white-label, team",
        "broadcast_usage": "Usa /broadcast_segment premium|free|inactive7|lang:it|source:NOME TESTO", "broadcast_done": "📢 Diffusione: {result}", "admin_only": "⛔ Solo admin.",
        "channel_usage": "Usa /channel @canale CITTÀ [HH:MM]", "business_channel": "💼 Abbonamento Business richiesto per la pubblicazione automatica nei canali.",
        "channel_failed": "❌ Impossibile connettere il canale.", "channel_connected": "📢 Canale connesso: {channel}\\nCittà: {city}\\nOra: {schedule}",
        "no_channels": "📢 Nessun canale. Usa /channel @canale CITTÀ 08:00", "channels_title": "📢 Canali:", "card_unavailable": "❌ Generazione carta non disponibile.",
        "business_api": "💼 Abbonamento Business richiesto per l'accesso API.", "api_created": "🔑 Chiave API creata (salvala ora):\\n{key}", "api_usage": "Usa /apikey per generare una chiave.",
        "teams_title": "👥 Team", "no_teams": "Nessun team", "team_created": "✅ Team creato: {team}", "business_teams": "💼 Abbonamento Business richiesto per i team.",
        "member_added": "✅ Membro aggiunto.", "member_failed": "❌ Impossibile aggiungere il membro.", "white_label": "🏢 White-label\\n{data}",
        "weather_alert_title": "⚠️ Notifica meteo", "rain_expected": "☔ Pioggia prevista.", "storm_possible": "⛈ Possibili temporali.",
        "strong_wind": "💨 Vento forte: {wind}.", "low_temp": "🥶 Avviso freddo: {temp}° o meno.", "high_temp": "🔥 Avviso caldo: {temp}° o più.",
        "heavy_rain_warning": "🌧️ Pioggia forte: {rain} mm.", "frost_warning": "❄️ Avviso gelo: {temp}° o meno.", "notification_settings_title": "🔔 Notifiche",
        "notification_usage": "Scegli un avviso con i pulsanti.", "daily_rain": "☔ Pioggia prevista.", "daily_wind": "💨 Avviso vento forte.",
        "analytics": "📊 Analitica\\nEntrate: {revenue:.2f}\\nMRR: {mrr:.2f}\\nARPU: {arpu:.2f}\\nPagamenti: {payments}\\nUtenti paganti: {paying_users}\\n\\nImbuto: {funnel}\\nRitenzione: {retention}\\nFonti: {sources}"
    },
    "hi": {
        "trip_button": "✈️ “यात्रा” खोलें और बटन से शहर और दिन चुनें।",
        "ai_button": "🤖 AI खोलें और अपना प्रश्न लिखें।",
        "help": "🌟 WeatherTomBot\\n\\n⭐ शहर — सहेजे गए शहर\\n🔔 सूचनाएं — मौसम चेतावनी\\n✈️ यात्रा — यात्रा पूर्वानुमान\\n🤖 AI — मौसम सहायक\\n💰 योजनाएं — Free / Premium / Business\\n\\nसामान्य संचालन के लिए मेनू बटन का उपयोग करें।",
        "favorites_title": "⭐ शहर", "no_saved_cities": "कोई सहेजा गया शहर नहीं है।", "addcity_hint": "\\n\\nशहर सहेजने के लिए “➕ शहर जोड़ें” दबाएं।",
        "favorite_added": "✅ पसंदीदा में जोड़ा गया।", "favorite_add_failed": "❌ जोड़ने में विफल ({result})।", "favorite_removed": "✅ हटा दिया गया।", "city_not_found": "❌ शहर नहीं मिला।",
        "alerts_title": "🔔 सूचनाएं", "alerts_hint": "\\n\\nबटन से चेतावनी चुनें।", "premium_alerts": "⭐ मौसम सूचनाओं के लिए Premium आवश्यक है।",
        "threshold_number": "❌ सीमा एक संख्या होनी चाहिए।", "alert_set": "🌧 {kind}: {state}{suffix}", "premium_notifications": "⭐ सूचनाओं के लिए Premium आवश्यक है।",
        "notifications_enabled": "🔔 सूचनाएं सक्षम की गईं।", "notifications_disabled": "🔕 सूचनाएं अक्षम की गईं।", "notification_time": "⏰ सूचना समय: {time}",
        "notification_time_usage": "HH:MM का उपयोग करें, जैसे /notify_time 08:00", "premium_trip": "⭐ यात्रा पूर्वानुमान के लिए Premium आवश्यक है।",
        "trip_unavailable": "❌ यात्रा पूर्वानुमान अनुपलब्ध है।", "trip_title": "✈️ यात्रा पूर्वानुमान: {destination}", "premium_required": "⭐ इस सुविधा के लिए Premium आवश्यक है।",
        "referral": "👥 रेफरल कार्यक्रम\\n\\nआपका कोड: {code}\\nआमंत्रित: {count}\\n🎁 इनाम: 7 दिन Premium\\n\\n{link}",
        "promo_applied": "🎁 प्रोमो लागू किया गया।", "promo_error": "❌ प्रोमो त्रुटि: {result}",
        "plans": "💰 योजनाएं\\n\\n🆓 Free — वर्तमान मौसम + मूल सुविधाएं\\n⭐ Premium — चेतावनी, पसंदीदा, यात्रा और AI\\n💼 Business — चैनल, API, व्हाइट-लेबल, टीमें",
        "broadcast_usage": "/broadcast_segment premium|free|inactive7|lang:hi|source:नाम TEXT का उपयोग करें", "broadcast_done": "📢 प्रसारण: {result}", "admin_only": "⛔ केवल व्यवस्थापक।",
        "channel_usage": "/channel @चैनल शहर [HH:MM] का उपयोग करें", "business_channel": "💼 चैनल ऑटो-पोस्टिंग के लिए Business आवश्यक है।",
        "channel_failed": "❌ चैनल कनेक्ट नहीं किया जा सका।", "channel_connected": "📢 चैनल कनेक्ट किया गया: {channel}\\nशहर: {city}\\nसमय: {schedule}",
        "no_channels": "📢 कोई चैनल नहीं। /channel @चैनल शहर 08:00 का उपयोग करें", "channels_title": "📢 चैनल:", "card_unavailable": "❌ कार्ड जनरेशन अनुपलब्ध है।",
        "business_api": "💼 API एक्सेस के लिए Business आवश्यक है।", "api_created": "🔑 API कुंजी बनाई गई (अभी सहेजें):\\n{key}", "api_usage": "कुंजी बनाने के लिए /apikey का उपयोग करें।",
        "teams_title": "👥 टीमें", "no_teams": "कोई टीम नहीं", "team_created": "✅ टीम बनाई गई: {team}", "business_teams": "💼 टीम सुविधा के लिए Business आवश्यक है।",
        "member_added": "✅ सदस्य जोड़ा गया।", "member_failed": "❌ सदस्य नहीं जोड़ा जा सका।", "white_label": "🏢 व्हाइट-लेबल\\n{data}",
        "weather_alert_title": "⚠️ मौसम सूचना", "rain_expected": "☔ बारिश की संभावना है।", "storm_possible": "⛈ तूफान की संभावना है।",
        "strong_wind": "💨 तेज हवा: {wind}।", "low_temp": "🥶 ठंड की चेतावनी: {temp}° या कम।", "high_temp": "🔥 गर्मी की चेतावनी: {temp}° या अधिक।",
        "heavy_rain_warning": "🌧️ भारी बारिश: {rain} mm।", "frost_warning": "❄️ पाला चेतावनी: {temp}° या कम।", "notification_settings_title": "🔔 सूचनाएं",
        "notification_usage": "बटन से चेतावनी चुनें।", "daily_rain": "☔ बारिश की संभावना है।", "daily_wind": "💨 तेज हवा की चेतावनी।",
        "analytics": "📊 विश्लेषण\\nराजस्व: {revenue:.2f}\\nMRR: {mrr:.2f}\\nARPU: {arpu:.2f}\\nभुगतान: {payments}\\nभुगतान करने वाले उपयोगकर्ता: {paying_users}\\n\\nफ़नल: {funnel}\\nप्रतिधारण: {retention}\\nस्रोत: {sources}"
    },
    "ar": {
        "trip_button": "✈️ افتح «رحلة» واختر المدينة والمدة باستخدام الأزرار.",
        "ai_button": "🤖 افتح الذكاء الاصطناعي واكتب سؤالك.",
        "help": "🌟 WeatherTomBot\\n\\n⭐ مدن — المدن المحفوظة\\n🔔 إشعارات — تحذيرات الطقس\\n✈️ رحلة — توقعات السفر\\n🤖 ذكاء اصطناعي — مساعد الطقس\\n💰 خطط — Free / Premium / Business\\n\\nاستخدم أزرار القائمة للتشغيل العادي.",
        "favorites_title": "⭐ مدن", "no_saved_cities": "لا توجد مدن محفوظة.", "addcity_hint": "\\n\\nاضغط على «➕ إضافة مدينة» لحفظ مدينة.",
        "favorite_added": "✅ تمت الإضافة إلى المفضلة.", "favorite_add_failed": "❌ تعذرت الإضافة ({result}).", "favorite_removed": "✅ تمت الإزالة.", "city_not_found": "❌ لم يتم العثور على المدينة.",
        "alerts_title": "🔔 إشعارات", "alerts_hint": "\\n\\nاختر تنبيهاً باستخدام الأزرار.", "premium_alerts": "⭐ اشتراك Premium مطلوب لإشعارات الطقس.",
        "threshold_number": "❌ يجب أن تكون العتبة رقماً.", "alert_set": "🌧 {kind}: {state}{suffix}", "premium_notifications": "⭐ اشتراك Premium مطلوب للإشعارات.",
        "notifications_enabled": "🔔 تم تمكين الإشعارات.", "notifications_disabled": "🔕 تم تعطيل الإشعارات.", "notification_time": "⏰ وقت الإشعار: {time}",
        "notification_time_usage": "استخدم HH:MM، مثال: /notify_time 08:00", "premium_trip": "⭐ اشتراك Premium مطلوب لتوقعات السفر.",
        "trip_unavailable": "❌ توقعات السفر غير متاحة.", "trip_title": "✈️ توقعات السفر: {destination}", "premium_required": "⭐ اشتراك Premium مطلوب لهذه الميزة.",
        "referral": "👥 برنامج الإحالة\\n\\nرمزك: {code}\\nالمدعوون: {count}\\n🎁 المكافأة: 7 أيام Premium\\n\\n{link}",
        "promo_applied": "🎁 تم تطبيق العرض الترويجي.", "promo_error": "❌ خطأ في العرض: {result}",
        "plans": "💰 خطط\\n\\n🆓 Free — الطقس الحالي + الميزات الأساسية\\n⭐ Premium — تنبيهات، مفضلة، سفر وذكاء اصطناعي\\n💼 Business — قنوات، API، علامة بيضاء، فرق",
        "broadcast_usage": "استخدم /broadcast_segment premium|free|inactive7|lang:ar|source:اسم TEXT", "broadcast_done": "📢 بث: {result}", "admin_only": "⛔ للمسؤولين فقط.",
        "channel_usage": "استخدم /channel @قناة مدينة [HH:MM]", "business_channel": "💼 اشتراك Business مطلوب للنشر التلقائي في القنوات.",
        "channel_failed": "❌ تعذر توصيل القناة.", "channel_connected": "📢 تم توصيل القناة: {channel}\\nالمدينة: {city}\\nالوقت: {schedule}",
        "no_channels": "📢 لا توجد قنوات. استخدم /channel @قناة مدينة 08:00", "channels_title": "📢 قنوات:", "card_unavailable": "❌ إنشاء البطاقة غير متاح.",
        "business_api": "💼 اشتراك Business مطلوب للوصول إلى API.", "api_created": "🔑 تم إنشاء مفتاح API (احفظه الآن):\\n{key}", "api_usage": "استخدم /apikey لإنشاء مفتاح.",
        "teams_title": "👥 فرق", "no_teams": "لا توجد فرق", "team_created": "✅ تم إنشاء الفريق: {team}", "business_teams": "💼 اشتراك Business مطلوب للفرق.",
        "member_added": "✅ تمت إضافة العضو.", "member_failed": "❌ تعذرت إضافة العضو.", "white_label": "🏢 علامة بيضاء\\n{data}",
        "weather_alert_title": "⚠️ إشعار طقس", "rain_expected": "☔ من المتوقع هطول أمطار.", "storm_possible": "⛈ عواصف رعدية محتملة.",
        "strong_wind": "💨 رياح قوية: {wind}.", "low_temp": "🥶 تحذير من البرد: {temp}° أو أقل.", "high_temp": "🔥 تحذير من الحرارة: {temp}° أو أكثر.",
        "heavy_rain_warning": "🌧️ أمطار غزيرة: {rain} مم.", "frost_warning": "❄️ تحذير من الصقيع: {temp}° أو أقل.", "notification_settings_title": "🔔 إشعارات",
        "notification_usage": "اختر تنبيهاً باستخدام الأزرار.", "daily_rain": "☔ من المتوقع هطول أمطار.", "daily_wind": "💨 تحذير من رياح قوية.",
        "analytics": "📊 تحليلات\\nالإيرادات: {revenue:.2f}\\nMRR: {mrr:.2f}\\nARPU: {arpu:.2f}\\nالمدفوعات: {payments}\\nالمستخدمون المدفوعون: {paying_users}\\n\\nقمع: {funnel}\\nالاحتفاظ: {retention}\\nالمصادر: {sources}"
    }
}'''

if old_marker in content:
    content = content.replace(old_marker, new_content)
    with open('features.py', 'w', encoding='utf-8') as f:
        f.write(content)
    print("✅ features.py успешно обновлен!")
else:
    print("❌ Маркер не найден. Показываю последние строки блока 'zh':")
    # Ищем последние 5 строк перед закрывающей скобкой FEATURE_TEXTS
    import re
    m = re.search(r'"daily_wind".*?\n\s*\}\n\}', content, re.DOTALL)
    if m:
        print(m.group(0))
    else:
        print("Не удалось найти блок.")
