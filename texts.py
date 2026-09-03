LANGUAGES = ["ru", "en"]
TEXTS = {'ru': {'welcome': '🌤 *Привет! Я — твой персональный метеоролог в Telegram.*\n\n'
                   'Знаешь ли ты, какая погода будет завтра? А через 10 дней? А во время твоей поездки в Сочи?\n\n'
                   '*Я знаю всё.*\n\n'
                   '━━━━━━━━━━━━━━━━━━━━\n\n'
                   '✨ *Что я умею:*\n\n'
                   '🌤 Точная погода прямо сейчас\n'
                   '📅 Прогнозы на 3, 5 и 10 дней\n'
                   '🌧️ Скажу, будет ли дождь\n'
                   '👕 Подскажу, что надеть\n'
                   '🌙 Покажу фазы Луны\n'
                   '🔔 Предупрежу о заморозках и жаре\n'
                   '✈️ Подготовлю прогноз для поездки\n'
                   '🤖 Отвечу на любой вопрос о погоде (AI)\n'
                   '📢 Буду публиковать погоду в твоём Telegram-канале\n'
                   '🎨 Сделаю красивые карточки с твоим дизайном\n\n'
                   '━━━━━━━━━━━━━━━━━━━━\n\n'
                   '🏙️ *Давай начнём!*\n'
                   'Напиши мне название твоего города — и я сразу покажу, какая там погода сейчас 🌍\n\n'
                   '_Например: Москва, Санкт-Петербург, Новосибирск_',
        'start_with_city': '👋 *С возвращением!*\n\n'
                   '📍 Твой город: *{city}*\n\n'
                   'Я снова готов помочь тебе с погодой 🌤\n\n'
                   '━━━━━━━━━━━━━━━━━━━━\n\n'
                   '🔥 *Быстрые действия:*\n\n'
                   '• 🌤 Узнать погоду сейчас\n'
                   '• 📅 Посмотреть прогноз на 5 дней\n'
                   '• 🌧️ Проверить, будет ли дождь\n'
                   '• 👕 Решить, что надеть\n'
                   '• 🔔 Настроить уведомления\n\n'
                   'Используй кнопки ниже — всё под рукой!\n\n'
                   '💡 *Совет:* нажми «❓ Помощь» — там полный справочник по всем функциям.\n\n'
                   '━━━━━━━━━━━━━━━━━━━━\n',
        'free_mode': '🔒 *Бесплатный режим*\n'
                     'Доступны: Погода сейчас, Смена города, Статус подписки, Помощь, Смена языка\n'
                     '\n',
        'buy_prompt': '💰 Купите подписку: *{price}⭐ в месяц*',
        'subscription_active': '✅ *Подписка активна!* (осталось {days} дн.)\nДоступны все функции бота.',
        'b2b_active': '{icon} *{name}* подписка активна!\n⏳ Осталось: *{days}* дн.\nДоступны все функции тарифа!',
        'no_city': '🏙️ *Сначала укажите ваш населённый пункт!*\n\nНапишите название города.',
        'city_not_found': "❌ '{city}' не найден. Попробуйте другой город.",
        'city_saved': '✅ Город *{city}* сохранён! Теперь вы можете пользоваться ботом.',
        'city_changed': '✅ Город изменён на *{city}*',
        'enter_city': '🏙️ *Напишите название города*\n\nНапример: `Москва`',
        'select_language': '🌐 *Выберите язык:*',
        'language_changed': '✅ Язык изменён на *{language_name}*',
        'subscription_status': '🔑 *Статус подписки*',
        'subscription_active_status': '{status}\n📅 До: *{expiry}*\n⏳ Осталось: *{days}* дн.',
        'subscription_inactive': '❌ Подписка неактивна\n'
                                 '\n'
                                 '💰 *Выберите тариф:*\n'
                                 '\n'
                                 '👤 Личная: *{personal}⭐*\n'
                                 '🌾 Сельское хозяйство: *{agri}⭐*\n'
                                 '🏗️ Строительство: *{const}⭐*\n'
                                 '✈️ Туризм: *{tour}⭐*\n'
                                 '🏢 Бизнес: *{business}⭐*',
        'only_subscribed': '🔒 *Эта функция доступна только по подписке!*\n'
                           '\n'
                           '💰 *Выберите тариф:*\n'
                           '\n'
                           '👤 Личная: *{personal}⭐*\n'
                           '🌾 Сельское хозяйство: *{agri}⭐*\n'
                           '🏗️ Строительство: *{const}⭐*\n'
                           '✈️ Туризм: *{tour}⭐*\n'
                           '🏢 Бизнес: *{business}⭐*',
        'invoice_created': '💳 *Счёт создан!*\n\nОплатите в Telegram.\n💰 Цена: *{price}⭐*',
        'payment_success': '✅ *Оплата прошла успешно!*\n'
                           '\n'
                           '🎉 Подписка активирована на {days} дней!\n'
                           '\n'
                           'Спасибо за поддержку! 🙌',
        'back': '🔙 Назад',
        'buy_subscription': '💰 Купить подписку',
        'buy_b2b': '💰 Купить B2B',
        'change_language': '🌐 Сменить язык',
        'help': '❓ Помощь',
        'help_title': '📖 *Помощь*',
        'help_subscribed': '📖 *Помощь* (Подписка активна)',
        'help_free': '📖 *Помощь* (Бесплатно)',
        'help_city': '📍 Город: *{city}*',
        'help_days': '⏳ Осталось: *{days}* дн.',
        'personal_features': '🌤 Погода сейчас\n'
                             '🌅 Восход/закат\n'
                             '📅 Прогнозы 3, 5 и 10 дней\n'
                             '🌧 Проверка дождя\n'
                             '🌙 Фаза луны\n'
                             '👕 Что надеть\n'
                             '📊 Статистика\n'
                             '🔔 Уведомления\n'
                             '⚙️ Смена города\n'
                             '🌐 Смена языка\n'
                             '🔑 Статус подписки',
        'help_features_sub': '🌤 Погода сейчас\n'
                             '🌅 Восход/закат\n'
                             '📅 Прогноз 3, 5, 10 дней\n'
                             '🌧 Проверить дождь\n'
                             '🌙 Фаза луны\n'
                             '👕 Что надеть\n'
                             '📊 Статистика\n'
                             '🔔 Уведомления\n'
                             '⚙️ Сменить город\n'
                             '🌐 Сменить язык\n'
                             '🔑 Статус подписки',
        'help_features_free': '🌤 Погода сейчас (бесплатно)\n'
                              '⚙️ Сменить город (бесплатно)\n'
                              '🔑 Статус подписки (бесплатно)\n'
                              '🌐 Сменить язык (бесплатно)',
        'help_buy': '\n💰 Купите подписку для доступа ко всем функциям!',
        'weather_title': '☀️ *{city}, {country}*',
        'weather_temp': '🌡 Температура: *{temp}°C*',
        'weather_feels': '🤔 Ощущается как: *{feels}°C*',
        'weather_humidity': '💧 Влажность: *{humidity}%*',
        'weather_wind': '🌬 Ветер: *{wind} м/с*',
        'weather_desc': '☁️ {description}',
        'weather_sources': '\n\n📡 Источников: *{count}* из 3\n📊 Использованы: {sources}',
        'weather_updated': '\n\n🕐 Обновлено: {time}',
        'sunrise_title': '🌅 *Восход и закат* для *{city}*',
        'sunrise_time': '🌅 Восход: *{sunrise}*',
        'sunset_time': '🌇 Закат: *{sunset}*',
        'day_length': '⏳ Длина дня: *{length}*',
        'forecast_title': '📅 *ПРОГНОЗ НА {days} ДНЕЙ*\n📍 *{city}*\n\n',
        'forecast_day': '🌤 *{date} ({weekday})*\n'
                        '   {temp}°C  |  {description}\n'
                        '   🌧️ Осадки: {rain} мм  🌬 Ветер: {wind} м/с\n'
                        '\n',
        'rain_expected': '{emoji} *В {city} сегодня будет дождь!*\n'
                         '\n'
                         'Осадки: *{rain} мм* ({intensity})\n'
                         '☔ Не забудьте зонт!',
        'no_rain': '☀️ Сегодня дождя не ожидается.',
        'moon_title': '🌙 *Фаза луны*\n\n{emoji} *{name}*\n\n📅 {date}',
        'clothing_title': '👕 *Рекомендации* для *{city}*\n'
                          '\n'
                          '🌡 {temp}°C | {description}\n'
                          '🌬 Ветер: {wind} м/с\n'
                          '\n'
                          '*Рекомендуется:*\n',
        'clothing_item': '• {item}\n',
        'agri_title': '🌾 *АГРО-ПРОГНОЗ*\n📍 *{city}*',
        'agri_soil': '🌡 Температура почвы: *{temp}°C*',
        'agri_humidity': '💧 Влажность: *{humidity}%*',
        'agri_rain': '🌧 Осадки: *{rain} мм*',
        'agri_frost': '❄️ Заморозки: {frost}',
        'agri_rec': '\n🌱 *Рекомендации:*\n{rec}',
        'construction_title': '🏗️ *СТРОИТЕЛЬНЫЙ ПРОГНОЗ*\n📍 *{city}*',
        'construction_wind': '💨 Ветер: *{wind} м/с* {safe}',
        'construction_rain': '🌧 Осадки: *{rain} мм*',
        'construction_temp': '🌡 Температура: *{temp}°C*',
        'construction_rec': '\n🏗️ *Рекомендации:*\n{rec}',
        'tourism_title': '✈️ *ТУРИСТИЧЕСКИЙ ПРОГНОЗ*\n📍 *{city}*',
        'tourism_weather': '☀️ Погода: *{weather}*',
        'tourism_temp': '🌡 Температура: *{temp}°C*',
        'tourism_sunrise': '🌅 Восход: *{sunrise}*',
        'tourism_sunset': '🌇 Закат: *{sunset}*',
        'tourism_uv': '☀️ UV-индекс: *{uv}* ({level})',
        'tourism_rec': '\n⭐ *Рекомендации:*\n{rec}',
        'notification_on': '🔔 *Уведомления включены!*\n'
                           '\n'
                           'Я буду присылать вам уведомления о:\n'
                           '🌧 Дожде\n'
                           '💨 Сильном ветре\n'
                           '❄️ Морозе\n'
                           '☀️ Жаре',
        'notification_off': '🔕 *Уведомления выключены*',
        'stats_title': '📊 *СТАТИСТИКА ПОГОДЫ ЗА {days} ДНЕЙ*\n📍 *{city}*',
        'stats_avg': '🌡 Средняя: *{avg}°C*',
        'stats_max': '📈 Максимальная: *{max}°C*',
        'stats_min': '📉 Минимальная: *{min}°C*',
        'stats_rain': '🌧 Дождливых дней: *{days}*',
        'stats_clear': '☀️ Ясных дней: *{days}*',
        'stats_cloudy': '☁️ Пасмурных дней: *{days}*',
        'stats_total': '💧 Всего осадков: *{rain} мм*',
        'btn_weather': '🌤 Погода сейчас',
        'btn_sunrise': '🌅 Восход/закат',
        'btn_f3': '📅 Прогноз 3 дня',
        'btn_f5': '📅 Прогноз 5 дней',
        'btn_f10': '📅 Прогноз 10 дней',
        'btn_rain': '🌧 Проверить дождь',
        'btn_moon': '🌙 Фаза луны',
        'btn_clothing': '👕 Что надеть',
        'btn_stats': '📊 Статистика',
        'btn_agro': '🌾 Агро-прогноз',
        'btn_construction': '🏗️ Строительный',
        'btn_tourism': '✈️ Туристический',
        'btn_notifications': '🔔 Уведомления',
        'btn_change_city': '⚙️ Сменить город',
        'btn_change_lang': '🌐 Сменить язык',
        'btn_help': '❓ Помощь',
        'btn_subscription': '🔑 Статус подписки',
        'btn_buy': '💰 Купить подписку',
        'btn_buy_b2b': '💰 Купить B2B',
        'btn_personal': '👤 Личная подписка',
        'btn_agriculture': '🌾 Сельское хозяйство',
        'btn_construction_sub': '🏗️ Строительство',
        'btn_tourism_sub': '✈️ Туризм',
        'btn_business_sub': '🏢 Бизнес (Все включено)',
        'btn_back': '🔙 Назад',
        'select_language_short': '💳 *Выберите тариф:*',
        'b2b_agriculture_name': 'Сельское хозяйство',
        'b2b_agriculture_features': '✈️ Поездки\n'
                                    '📅 Прогноз на 10 дней\n'
                                    '🌡 Агро-прогноз\n'
                                    '🌧 Осадки для полива\n'
                                    '❄️ Прогноз заморозков\n'
                                    '📊 Статистика\n'
                                    '🔔 Уведомления',
        'b2b_construction_name': 'Строительство',
        'b2b_construction_features': '✈️ Поездки\n'
                                     '📅 Прогноз на 10 дней\n'
                                     '💨 Прогноз ветра\n'
                                     '🌧 Осадки\n'
                                     '🌡 Температура\n'
                                     '📊 Статистика\n'
                                     '🔔 Уведомления',
        'b2b_tourism_name': 'Туризм',
        'b2b_tourism_features': '✈️ Поездки\n'
                                '📅 Прогноз на 10 дней\n'
                                '🌅 Восход/закат\n'
                                '☀️ UV-индекс\n'
                                '🌧 Осадки\n'
                                '📊 Статистика\n'
                                '🔔 Уведомления',
        'b2b_business_name': 'Бизнес (Все включено)',
        'b2b_business_features': '✈️ Поездки\n'
                                '🤖 AI-помощник\n'
                                '📅 Прогноз на 10 дней\n'
                                 '📊 Полная статистика\n'
                                 '🔔 Все уведомления\n'
                                 '🌾 Агро-прогноз\n'
                                 '🏗️ Строительный\n'
                                 '✈️ Туристический\n'
                                 '📈 Приоритетная поддержка\n📢 Автопостинг\n🖼 Погодные карточки\n🔑 API\n👥 Команды\n📊 Аналитика\n🏷 White-label',
        'already_b2b': '✅ У вас уже есть активная B2B подписка!',
        'already_subscription': '✅ У вас уже есть активная подписка!',
        'invoice_error': '❌ Ошибка создания счёта. Попробуйте позже.',
        'unknown_plan': '❌ Неизвестный тариф',
        'already_same_subscription': '✅ У вас уже есть активная эта подписка!',
        'back_main': '🔙 Возврат в главное меню',
        'b2b_only': '🔒 *Эта функция доступна только по B2B подписке!*\n\n💰 Выберите B2B тариф:',
        'city_not_set': 'не указан',
        'weather_error': '❌ Не удалось получить данные о погоде. Попробуйте позже.',
        'forecast_error': '❌ Не удалось получить прогноз. Попробуйте позже.',
        'stats_error': '❌ Не удалось получить статистику. Попробуйте позже.',
        'agri_error': '❌ Не удалось получить агропрогноз. Попробуйте позже.',
        'construction_error': '❌ Не удалось получить прогноз для строительства. Попробуйте позже.',
        'tourism_error': '❌ Не удалось получить туристический прогноз. Попробуйте позже.',
        'invoice_title_personal': '🌤 Личная подписка на МетеоБот',
        'invoice_description_personal': 'Доступ ко всем основным функциям бота на 1 месяц',
        'invoice_month': '1 месяц',
        'invoice_pay': 'Оплатите в Telegram.',
        'included': 'Включено:',
        'status_active': '🟢 Активна',
        'status_expiring': '🟡 Скоро закончится',
        'status_ending': '🔴 Заканчивается!',
        'intensity_light': 'лёгкий',
        'intensity_moderate': 'умеренный',
        'intensity_heavy': 'сильный',
        'moon_new': 'Новолуние',
        'moon_waxing_crescent': 'Молодая луна',
        'moon_first_quarter': 'Первая четверть',
        'moon_waxing_gibbous': 'Прибывающая луна',
        'moon_full': 'Полнолуние',
        'moon_waning_gibbous': 'Убывающая луна',
        'moon_last_quarter': 'Последняя четверть',
        'moon_old': 'Старая луна',
        'error_no_data_forecast': '❌ Нет данных прогноза',
        'weekday_0': 'ПН',
        'weekday_1': 'ВТ',
        'weekday_2': 'СР',
        'weekday_3': 'ЧТ',
        'weekday_4': 'ПТ',
        'weekday_5': 'СБ',
        'weekday_6': 'ВС',
        'error_generic': '❌ Произошла ошибка. Попробуйте позже.',
        'forecast_word': 'прогноз',
        'frost_expected': '❌ Ожидаются',
        'frost_not_expected': '✅ Не ожидаются',
        'agri_rec_frost': '❄️ Защитите посевы от заморозков',
        'agri_rec_wet': '🌧️ Избыток влаги — отложите полив',
        'agri_rec_water': '💧 Рекомендуется полив',
        'agri_rec_heat': '☀️ Жарко — защитите растения от солнца',
        'agri_rec_good': '🌱 Условия благоприятные для работ',
        'construction_rec_safe': '✅ Работа на высоте безопасна',
        'construction_rec_wind': '❌ Опасно для кранов и высотных работ',
        'construction_rec_rain': '🌧️ Отложите бетонные работы',
        'construction_rec_frost': '❄️ Бетон замерзает — используйте добавки',
        'construction_rec_heat': '☀️ Жарко — работайте в тени'},
 'en': {'welcome': '🌤 *Hey! I\'m your personal meteorologist in Telegram.*\n\n'
                   'Do you know what the weather will be tomorrow? In 10 days? During your trip to Paris?\n\n'
                   '*I know everything.*\n\n'
                   '━━━━━━━━━━━━━━━━━━━━\n\n'
                   '✨ *What I can do:*\n\n'
                   '🌤 Accurate weather right now\n'
                   '📅 3, 5 and 10-day forecasts\n'
                   '🌧️ Tell you if it will rain\n'
                   '👕 Suggest what to wear\n'
                   '🌙 Show moon phases\n'
                   '🔔 Alert you about frost and heat\n'
                   '✈️ Prepare forecast for your trip\n'
                   '🤖 Answer any weather question (AI)\n'
                   '📢 Publish weather to your Telegram channel\n'
                   '🎨 Create beautiful cards with your design\n\n'
                   '━━━━━━━━━━━━━━━━━━━━\n\n'
                   '🏙️ *Let\'s get started!*\n'
                   'Send me your city name — and I\'ll show you the current weather instantly 🌍\n\n'
                   '_For example: London, New York, Tokyo_',
        'start_with_city': '👋 *Welcome back!*\n\n'
                   '📍 Your city: *{city}*\n\n'
                   'I\'m ready to help you with the weather again 🌤\n\n'
                   '━━━━━━━━━━━━━━━━━━━━\n\n'
                   '🔥 *Quick actions:*\n\n'
                   '• 🌤 Get current weather\n'
                   '• 📅 See 5-day forecast\n'
                   '• 🌧️ Check if it will rain\n'
                   '• 👕 Decide what to wear\n'
                   '• 🔔 Set up notifications\n\n'
                   'Use the buttons below — everything at hand!\n\n'
                   '💡 *Tip:* tap "❓ Help" — there\'s a complete guide to all features.\n\n'
                   '━━━━━━━━━━━━━━━━━━━━\n',
        'free_mode': '🔒 *Free mode*\n'
                     'Available: Current weather, Change city, Subscription status, Help, Change language\n'
                     '\n',
        'buy_prompt': '💰 Buy subscription: *{price}⭐ per month*',
        'subscription_active': '✅ *Subscription active!* ({days} days left)\nAll features available.',
        'b2b_active': '{icon} *{name}* subscription active!\n⏳ Left: *{days}* days.\nAll tariff features available!',
        'no_city': '🏙️ *Please specify your city first!*\n\nSend the city name.',
        'city_not_found': "❌ '{city}' not found. Try another city.",
        'city_saved': '✅ City *{city}* saved! Now you can use the bot.',
        'city_changed': '✅ City changed to *{city}*',
        'enter_city': '🏙️ *Send the city name*\n\nExample: `London`',
        'select_language': '🌐 *Select your language:*',
        'language_changed': '✅ Language changed to *{language_name}*',
        'subscription_status': '🔑 *Subscription status*',
        'subscription_active_status': '{status}\n📅 Until: *{expiry}*\n⏳ Left: *{days}* days',
        'subscription_inactive': '❌ No active subscription\n'
                                 '\n'
                                 '💰 *Choose a plan:*\n'
                                 '\n'
                                 '👤 Personal: *{personal}⭐*\n'
                                 '🌾 Agriculture: *{agri}⭐*\n'
                                 '🏗️ Construction: *{const}⭐*\n'
                                 '✈️ Tourism: *{tour}⭐*\n'
                                 '🏢 Business: *{business}⭐*',
        'only_subscribed': '🔒 *This feature is only available with subscription!*\n'
                           '\n'
                           '💰 *Choose a plan:*\n'
                           '\n'
                           '👤 Personal: *{personal}⭐*\n'
                           '🌾 Agriculture: *{agri}⭐*\n'
                           '🏗️ Construction: *{const}⭐*\n'
                           '✈️ Tourism: *{tour}⭐*\n'
                           '🏢 Business: *{business}⭐*',
        'invoice_created': '💳 *Invoice created!*\n\nPay in Telegram.\n💰 Price: *{price}⭐*',
        'payment_success': '✅ *Payment successful!*\n'
                           '\n'
                           '🎉 Subscription activated for {days} days!\n'
                           '\n'
                           'Thank you for your support! 🙌',
        'back': '🔙 Back',
        'buy_subscription': '💰 Buy subscription',
        'buy_b2b': '💰 Buy B2B',
        'change_language': '🌐 Change language',
        'help': '❓ Help',
        'help_title': '📖 *Help*',
        'help_subscribed': '📖 *Help* (Subscription active)',
        'help_free': '📖 *Help* (Free)',
        'help_city': '📍 City: *{city}*',
        'help_days': '⏳ Left: *{days}* days',
        'personal_features': '🌤 Current weather\n'
                             '🌅 Sunrise/sunset\n'
                             '📅 3, 5 and 10-day forecasts\n'
                             '🌧 Rain check\n'
                             '🌙 Moon phase\n'
                             '👕 What to wear\n'
                             '📊 Statistics\n'
                             '🔔 Notifications\n'
                             '⚙️ Change city\n'
                             '🌐 Change language\n'
                             '🔑 Subscription status',
        'help_features_sub': '🌤 Current weather\n'
                             '🌅 Sunrise/Sunset\n'
                             '📅 3, 5, 10 day forecast\n'
                             '🌧 Rain check\n'
                             '🌙 Moon phase\n'
                             '👕 What to wear\n'
                             '📊 Statistics\n'
                             '🔔 Notifications\n'
                             '⚙️ Change city\n'
                             '🌐 Change language\n'
                             '🔑 Subscription status',
        'help_features_free': '🌤 Current weather (free)\n'
                              '⚙️ Change city (free)\n'
                              '🔑 Subscription status (free)\n'
                              '🌐 Change language (free)',
        'help_buy': '\n💰 Buy subscription to access all features!',
        'weather_title': '☀️ *{city}, {country}*',
        'weather_temp': '🌡 Temperature: *{temp}°C*',
        'weather_feels': '🤔 Feels like: *{feels}°C*',
        'weather_humidity': '💧 Humidity: *{humidity}%*',
        'weather_wind': '🌬 Wind: *{wind} m/s*',
        'weather_desc': '☁️ {description}',
        'weather_sources': '\n\n📡 Sources: *{count}* of 3\n📊 Used: {sources}',
        'weather_updated': '\n\n🕐 Updated: {time}',
        'sunrise_title': '🌅 *Sunrise and sunset* for *{city}*',
        'sunrise_time': '🌅 Sunrise: *{sunrise}*',
        'sunset_time': '🌇 Sunset: *{sunset}*',
        'day_length': '⏳ Day length: *{length}*',
        'forecast_title': '📅 *{days}-DAY FORECAST*\n📍 *{city}*\n\n',
        'forecast_day': '🌤 *{date} ({weekday})*\n'
                        '   {temp}°C  |  {description}\n'
                        '   🌧️ Rain: {rain} mm  🌬 Wind: {wind} m/s\n'
                        '\n',
        'rain_expected': '{emoji} *Rain expected in {city} today!*\n'
                         '\n'
                         'Rain: *{rain} mm* ({intensity})\n'
                         "☔ Don't forget your umbrella!",
        'no_rain': '☀️ No rain expected today.',
        'moon_title': '🌙 *Moon phase*\n\n{emoji} *{name}*\n\n📅 {date}',
        'clothing_title': '👕 *Recommendations* for *{city}*\n'
                          '\n'
                          '🌡 {temp}°C | {description}\n'
                          '🌬 Wind: {wind} m/s\n'
                          '\n'
                          '*Recommended:*\n',
        'clothing_item': '• {item}\n',
        'agri_title': '🌾 *AGRO-FORECAST*\n📍 *{city}*',
        'agri_soil': '🌡 Soil temperature: *{temp}°C*',
        'agri_humidity': '💧 Humidity: *{humidity}%*',
        'agri_rain': '🌧 Rain: *{rain} mm*',
        'agri_frost': '❄️ Frost: {frost}',
        'agri_rec': '\n🌱 *Recommendations:*\n{rec}',
        'construction_title': '🏗️ *CONSTRUCTION FORECAST*\n📍 *{city}*',
        'construction_wind': '💨 Wind: *{wind} m/s* {safe}',
        'construction_rain': '🌧 Rain: *{rain} mm*',
        'construction_temp': '🌡 Temperature: *{temp}°C*',
        'construction_rec': '\n🏗️ *Recommendations:*\n{rec}',
        'tourism_title': '✈️ *TOURISM FORECAST*\n📍 *{city}*',
        'tourism_weather': '☀️ Weather: *{weather}*',
        'tourism_temp': '🌡 Temperature: *{temp}°C*',
        'tourism_sunrise': '🌅 Sunrise: *{sunrise}*',
        'tourism_sunset': '🌇 Sunset: *{sunset}*',
        'tourism_uv': '☀️ UV index: *{uv}* ({level})',
        'tourism_rec': '\n⭐ *Recommendations:*\n{rec}',
        'notification_on': '🔔 *Notifications enabled!*\n'
                           '\n'
                           'I will send alerts about:\n'
                           '🌧 Rain\n'
                           '💨 Strong wind\n'
                           '❄️ Frost\n'
                           '☀️ Heat',
        'notification_off': '🔕 *Notifications disabled*',
        'stats_title': '📊 *WEATHER STATISTICS FOR {days} DAYS*\n📍 *{city}*',
        'stats_avg': '🌡 Average: *{avg}°C*',
        'stats_max': '📈 Maximum: *{max}°C*',
        'stats_min': '📉 Minimum: *{min}°C*',
        'stats_rain': '🌧 Rainy days: *{days}*',
        'stats_clear': '☀️ Clear days: *{days}*',
        'stats_cloudy': '☁️ Cloudy days: *{days}*',
        'stats_total': '💧 Total rain: *{rain} mm*',
        'btn_weather': '🌤 Current weather',
        'btn_sunrise': '🌅 Sunrise/Sunset',
        'btn_f3': '📅 Forecast 3 days',
        'btn_f5': '📅 Forecast 5 days',
        'btn_f10': '📅 Forecast 10 days',
        'btn_rain': '🌧 Rain check',
        'btn_moon': '🌙 Moon phase',
        'btn_clothing': '👕 What to wear',
        'btn_stats': '📊 Statistics',
        'btn_agro': '🌾 Agro-forecast',
        'btn_construction': '🏗️ Construction',
        'btn_tourism': '✈️ Tourism',
        'btn_notifications': '🔔 Notifications',
        'btn_change_city': '⚙️ Change city',
        'btn_change_lang': '🌐 Change language',
        'btn_help': '❓ Help',
        'btn_subscription': '🔑 Subscription status',
        'btn_buy': '💰 Buy subscription',
        'btn_buy_b2b': '💰 Buy B2B',
        'btn_personal': '👤 Personal subscription',
        'btn_agriculture': '🌾 Agriculture',
        'btn_construction_sub': '🏗️ Construction',
        'btn_tourism_sub': '✈️ Tourism',
        'btn_business_sub': '🏢 Business (All included)',
        'btn_back': '🔙 Back',
        'select_language_short': '💳 *Choose a plan:*',
        'b2b_agriculture_name': 'Agriculture',
        'b2b_agriculture_features': '✈️ Trip forecasts\n'
                                    '📅 10-day forecast\n'
                                    '🌡 Agriculture forecast\n'
                                    '🌧 Irrigation precipitation\n'
                                    '❄️ Frost forecast\n'
                                    '📊 Statistics\n'
                                    '🔔 Notifications',
        'b2b_construction_name': 'Construction',
        'b2b_construction_features': '✈️ Trip forecasts\n'
                                     '📅 10-day forecast\n'
                                     '💨 Wind forecast\n'
                                     '🌧 Precipitation\n'
                                     '🌡 Temperature\n'
                                     '📊 Statistics\n'
                                     '🔔 Notifications',
        'b2b_tourism_name': 'Tourism',
        'b2b_tourism_features': '✈️ Trip forecasts\n'
                                '📅 10-day forecast\n'
                                '🌅 Sunrise/sunset\n'
                                '☀️ UV index\n'
                                '🌧 Precipitation\n'
                                '📊 Statistics\n'
                                '🔔 Notifications',
        'b2b_business_name': 'Business (All included)',
        'b2b_business_features': '✈️ Trip forecasts\n'
                                '🤖 AI assistant\n'
                                '📅 10-day forecast\n'
                                 '📊 Full statistics\n'
                                 '🔔 All notifications\n'
                                 '🌾 Agriculture forecast\n'
                                 '🏗️ Construction\n'
                                 '✈️ Tourism\n'
                                 '📈 Priority support\n📢 Auto-posting\n🖼 Weather cards\n🔑 API\n👥 Teams\n📊 Analytics\n🏷 White-label',
        'already_b2b': '✅ You already have an active B2B subscription!',
        'already_subscription': '✅ You already have an active subscription!',
        'invoice_error': '❌ Could not create the invoice. Please try again later.',
        'unknown_plan': '❌ Unknown plan',
        'already_same_subscription': '✅ You already have this subscription active!',
        'back_main': '🔙 Back to main menu',
        'b2b_only': '🔒 *This feature is available only with a B2B subscription!*\n\n💰 Choose a B2B plan:',
        'city_not_set': 'not set',
        'weather_error': '❌ Could not get weather data. Please try again later.',
        'forecast_error': '❌ Could not get the forecast. Please try again later.',
        'temp': '🌡 Temperature: {temp}°C',
        'feels_like': '🤔 Feels like: {feels}°C',
        'wind_full': '💨 Wind: {wind} m/s, {direction}',
        'humidity': '💧 Humidity: {humidity}%',
        'pressure_mm': '📊 Pressure: {pressure} mmHg',
        'uv_with_level': '☀️ UV index: {uv} ({level})',
        'uv_simple': '☀️ UV index: {uv}',
        'updated_time': '🕐 Updated: {time}',
        'precip_prob': '🌧 Precipitation probability: {prob}%',
        'sunrise': '🌅 Sunrise: {time}',
        'sunset': '🌇 Sunset: {time}',
        'forecast_title': '📅 *Forecast for {days_text} — {city}*\n\n',
        'forecast_day_line': '🌡 +{min}°...+{max}° (feels +{feels}°)',
        'forecast_wind_line': '💨 {wind} m/s, {dir} | 💧 {hum}%',
        'forecast_pressure': '📊 {pressure} mm',
        'forecast_uv_line': ' | ☀️ UV {uv} ({level})',
        'forecast_precip': '🌧 Precipitation: {prob}% ({mm} mm)',
        'cloudy_default': 'Cloudy',
        'day_1': 'day', 'day_2_4': 'days', 'day_5_plus': 'days',
        'wind_n': 'N', 'wind_nne': 'NNE', 'wind_ne': 'NE', 'wind_ene': 'ENE',
        'wind_e': 'E', 'wind_ese': 'ESE', 'wind_se': 'SE', 'wind_sse': 'SSE',
        'wind_s': 'S', 'wind_ssw': 'SSW', 'wind_sw': 'SW', 'wind_wsw': 'WSW',
        'wind_w': 'W', 'wind_wnw': 'WNW', 'wind_nw': 'NW', 'wind_nnw': 'NNW',
        'uv_low': 'low', 'uv_moderate': 'moderate', 'uv_high': 'high',
        'uv_very_high': 'very high', 'uv_extreme': 'extreme',
        'temp': '🌡 Temperature: {temp}°C',
        'feels_like': '🤔 Feels like: {feels}°C',
        'wind_full': '💨 Wind: {wind} m/s, {direction}',
        'humidity': '💧 Humidity: {humidity}%',
        'pressure_mm': '📊 Pressure: {pressure} mmHg',
        'uv_with_level': '☀️ UV index: {uv} ({level})',
        'uv_simple': '☀️ UV index: {uv}',
        'updated_time': '🕐 Updated: {time}',
        'precip_prob': '🌧 Precipitation probability: {prob}%',
        'sunrise': '🌅 Sunrise: {time}',
        'sunset': '🌇 Sunset: {time}',
        'forecast_title': '📅 *Forecast for {days_text} — {city}*\n\n',
        'forecast_day_line': '🌡 +{min}°...+{max}° (feels +{feels}°)',
        'forecast_wind_line': '💨 {wind} m/s, {dir} | 💧 {hum}%',
        'forecast_pressure': '📊 {pressure} mm',
        'forecast_uv_line': ' | ☀️ UV {uv} ({level})',
        'forecast_precip': '🌧 Precipitation: {prob}% ({mm} mm)',
        'cloudy_default': 'Cloudy',
        'day_1': 'day', 'day_2_4': 'days', 'day_5_plus': 'days',
        'wind_n': 'N', 'wind_nne': 'NNE', 'wind_ne': 'NE', 'wind_ene': 'ENE',
        'wind_e': 'E', 'wind_ese': 'ESE', 'wind_se': 'SE', 'wind_sse': 'SSE',
        'wind_s': 'S', 'wind_ssw': 'SSW', 'wind_sw': 'SW', 'wind_wsw': 'WSW',
        'wind_w': 'W', 'wind_wnw': 'WNW', 'wind_nw': 'NW', 'wind_nnw': 'NNW',
        'uv_low': 'low', 'uv_moderate': 'moderate', 'uv_high': 'high',
        'uv_very_high': 'very high', 'uv_extreme': 'extreme',
        'stats_error': '❌ Could not get statistics. Please try again later.',
        'agri_error': '❌ Could not get the agriculture forecast. Please try again later.',
        'construction_error': '❌ Could not get the construction forecast. Please try again later.',
        'tourism_error': '❌ Could not get the tourism forecast. Please try again later.',
        'invoice_title_personal': '🌤 WeatherBot Personal Subscription',
        'invoice_description_personal': 'Access to all main bot features for 1 month',
        'invoice_month': '1 month',
        'invoice_pay': 'Pay in Telegram.',
        'included': 'Included:',
        'status_active': '🟢 Active',
        'status_expiring': '🟡 Expiring soon',
        'status_ending': '🔴 Expiring!',
        'intensity_light': 'light',
        'intensity_moderate': 'moderate',
        'intensity_heavy': 'heavy',
        'moon_new': 'New moon',
        'moon_waxing_crescent': 'Waxing crescent',
        'moon_first_quarter': 'First quarter',
        'moon_waxing_gibbous': 'Waxing gibbous',
        'moon_full': 'Full moon',
        'moon_waning_gibbous': 'Waning gibbous',
        'moon_last_quarter': 'Last quarter',
        'moon_old': 'Waning crescent',
        'error_no_data_forecast': '❌ No forecast data available',
        'weekday_0': 'MON',
        'weekday_1': 'TUE',
        'weekday_2': 'WED',
        'weekday_3': 'THU',
        'weekday_4': 'FRI',
        'weekday_5': 'SAT',
        'weekday_6': 'SUN',
        'error_generic': '❌ An error occurred. Please try again later.',
        'forecast_word': 'forecast',
        'frost_expected': '❌ Expected',
        'frost_not_expected': '✅ Not expected',
        'agri_rec_frost': '❄️ Protect crops from frost',
        'agri_rec_wet': '🌧️ Too much moisture — postpone irrigation',
        'agri_rec_water': '💧 Irrigation is recommended',
        'agri_rec_heat': '☀️ Hot weather — protect plants from the sun',
        'agri_rec_good': '🌱 Conditions are favorable for work',
        'construction_rec_safe': '✅ Work at height is safe',
        'construction_rec_wind': '❌ Dangerous for cranes and work at height',
        'construction_rec_rain': '🌧️ Postpone concrete work',
        'construction_rec_frost': '❄️ Concrete may freeze — use additives',
        'construction_rec_heat': '☀️ Hot weather — work in the shade'},
}
# New unified tariff / B2B feature labels. Kept here so the legacy bot UI remains
# fully multilingual and all buttons are visible on every plan.
_NEW_TEXTS = {
    "ru": {
        "btn_trip":"✈️ Поездка","btn_tomorrow":"📅 Погода на завтра","btn_ai":"🤖 AI-помощник","btn_favorites":"⭐ Города",
        "btn_autopost":"📢 Автопостинг","btn_card":"🖼 Погодная карточка",
        "btn_api":"🔑 API","btn_team":"👥 Команда","btn_whitelabel":"🏷 White-label",
        "btn_analytics":"📊 Аналитика",
        "premium_required_paywall":"🔒 *Функция доступна в Premium.*\n\nОформите подписку, чтобы открыть поездки, AI, уведомления и расширенные функции.",
        "business_required":"🔒 *Функция доступна в Business.*\n\nBusiness включает все возможности Premium + автопостинг, карточки, API, команды, аналитику и White-label.",
        "trip_city":"✈️ *Поездка*\n\nНапишите город назначения.","trip_days":"📅 На сколько дней нужна поездка? Выберите число от 1 до 10.",
        "trip_result":"✈️ *Прогноз поездки: {city}*\n\n{result}",
        "ai_button":"🤖 *AI-помощник*\n\nНапишите вопрос о погоде, поездке или о том, что лучше сделать сегодня.",
        "notification_menu":"🔔 *Уведомления*\n\nНажмите ещё раз, чтобы включить или выключить погодные уведомления.",
        "whitelabel_menu":"🏷 *White-label*\n\nBusiness: /white_label NAME",
        "analytics_menu":"📊 *Аналитика*\n\nBusiness: статистика подключённых каналов и публикаций.",
        "autopost_menu":"📢 *Автопостинг*\n\nBusiness позволяет автоматически публиковать погоду в Telegram-канале.\n\nКоманды:\n/channel @channel CITY 08:00 — добавить канал\n/channels — мои каналы\n/postnow — отправить пост сейчас\n/cardstyle — настройка стиля карточки",
        "card_menu":"🖼 Погодная карточка\n\nBusiness: /generate_card CITY",
        "api_menu":"🔑 *API*\n\nBusiness: /apikey — создать API-ключ.",
        'api_btn_create': '🔑 Создать API-ключ',
        'api_btn_help': '📖 Документация',
        'api_btn_city': '🏙 Установить город',
        'api_btn_stats': '📊 Статистика',
        'api_btn_profile': '👤 Мой профиль',
        'api_btn_delete': '🗑 Удалить ключи',
        'api_key_created': '🔑 API-ключ создан:\n`{api_key}`',
        'api_key_error': '❌ Ошибка создания ключа. Проверьте подписку Business.',
        'api_key_limit': '❌ Достигнут лимит: 5 API-ключей. Удалите старые через «🗑 Удалить ключи».',
        'api_help_title': '📖 API Документация',
        'api_help_base': '🌍 Базовый URL:',
        'api_help_endpoints': '📍 Эндпоинты:',
        'api_help_ep_weather': '• GET /weather?city=Город',
        'api_help_ep_forecast': '• GET /forecast?city=Город&days=5',
        'api_help_ep_me': '• GET /me',
        'api_help_auth': '🔑 Авторизация:',
        'api_help_header': 'Заголовок: X-API-Key: ваш_ключ',
        'api_help_default': '🏙 Город по умолчанию: {city}',
        'api_help_limits': '📊 Лимиты:',
        'api_help_limit_keys': '• Максимум 5 API ключей',
        'api_help_limit_req': '• 100 запросов в час на ключ',
        'api_help_example': '💡 Пример:',
        'api_set_city_prompt': '🏙 Введите город по умолчанию для API запросов:',
        'api_profile_title': '📊 Ваш API Профиль',
        'api_profile_id': '🆔 User ID: {id}',
        'api_profile_keys': '🔑 API ключей: {count}',
        'api_profile_city': '🏙 Город по умолчанию: {city}',
        'api_profile_first': '📅 Первая активность: {date}',
        'api_stats_empty': '📊 Статистика API\n\nВы ещё не использовали API.',
        'api_stats_title': '📊 Статистика API',
        'api_stats_total': '📈 Всего: {total}',
        'api_stats_24h': '🕐 24ч: {h24}',
        'api_stats_7d': '📅 7 дней: {d7}',
        'api_stats_by_ep': 'По эндпоинтам:',
        'api_deleted': '🗑 Удалено API-ключей: {count}',
        'api_city_not_set': 'не установлен',
        'city_added': '✅ Город добавлен в избранные.',
        'city_add_failed': '❌ Не удалось добавить город: {result}',
        'city_removed': '✅ Город удалён.',
        'city_not_found': '❌ Такой город не найден.',
        'api_enter_city_short': '🏙 Введите город для API:',
        'api_city_set': '✅ Город для API: *{city}*',
        'card_ready': '🖼 Карточка готова.',
        'card_error': '🖼 Не удалось создать карточку',
        'card_error_generic': '❌ Ошибка: {err}',
        'logo_save_error': '❌ Не удалось сохранить логотип.',

        "team_menu":"👥 *Команды*\n\nУправляйте доступом к боту для вашей команды.\n\n*Роли:*\n"
                   "👑 owner — владелец команды\n"
                   "🛠 admin — полный доступ Business\n"
                   "✏️ editor — полный доступ Business\n"
                   "👁 viewer — только Premium-функции\n\n"
                   "Одна подписка Business — вся команда пользуется!",
        "team_list_title":"👥 *Ваши команды*\n\n",
        "team_list_empty":"У вас пока нет созданных команд.\n\nНажмите «➕ Создать команду», чтобы начать.",
        "team_create_prompt":"✏️ *Создание команды*\n\nВведите название команды (например: Моя Компания).",
        "team_create_success":"✅ Команда *«{name}»* создана!\n\nID команды: `{tid}`\n\nТеперь вы можете добавить участников.",
        "team_create_failed":"❌ Не удалось создать команду. Проверьте наличие подписки Business.",
        "team_add_prompt":"➕ *Добавление участника*\n\nВыберите команду:",
        "team_add_user_prompt":"👤 *Добавление в команду «{name}»*\n\nВведите Telegram ID пользователя в формате:\n`ID роль`\n\nПримеры:\n`123456789 admin`\n`987654321 editor`\n`555555555 viewer`\n\n💡 Узнать свой ID: @userinfobot",
        "team_add_success":"✅ Пользователь добавлен в команду *«{name}»* с ролью *{role}*!",
        "team_add_failed":"❌ Не удалось добавить участника. Проверьте данные.",
        "team_info_title":"👥 *Команда «{name}»*\n\n"
                          "🆔 ID: `{tid}`\n"
                          "📅 Создана: {created}\n\n"
                          "👥 *Участники ({count}):*\n{members}",
        "team_role_changed":"✅ Роль пользователя изменена на *{role}*.",
        "team_role_failed":"❌ Не удалось изменить роль.",
        "team_member_removed":"✅ Участник удалён из команды.",
        "team_remove_failed":"❌ Не удалось удалить участника.",
        "team_deleted":"✅ Команда удалена.",
        "team_delete_confirm":"⚠️ *Удалить команду «{name}»?*\n\nВсе участники потеряют доступ. Это действие нельзя отменить.",
        "team_member":"• {icon} `{uid}` — {role}",
        "team_back":"🔙 К командам",
        "team_btn_create":"➕ Создать команду",
        "team_btn_list":"📋 Мои команды",
        "team_btn_add":"➕ Добавить участника",
        "team_btn_remove":"➖ Удалить участника",
        "team_btn_delete":"🗑 Удалить команду",
        "team_btn_change_role":"🔄 Изменить роль",
        "team_btn_back":"🔙 Назад",
        "whitelabel_menu":"🏷 *White-label*\n\nBusiness: /white_label NAME",
        "analytics_menu":"📊 *Аналитика*\n\nBusiness: статистика подключённых каналов и публикаций."
    },
    "en": {
        "btn_trip":"✈️ Trip","btn_tomorrow":"📅 Tomorrow Weather","btn_ai":"🤖 AI Assistant","btn_favorites":"⭐ Cities",
        "btn_autopost":"📢 Auto-posting","btn_card":"🖼 Weather Card",
        "btn_api":"🔑 API","btn_team":"👥 Team","btn_whitelabel":"🏷 White-label",
        "btn_analytics":"📊 Analytics",
        "premium_required_paywall":"🔒 *This feature is available in Premium.*\n\nSubscribe to unlock trips, AI, notifications and advanced features.",
        "business_required":"🔒 *This feature is available in Business.*\n\nBusiness includes all Premium features plus auto-posting, cards, API, teams, analytics and white-label.",
        "trip_city":"✈️ *Trip*\n\nSend the destination city.","trip_days":"📅 How many days? Choose a number from 1 to 10.",
        "trip_result":"✈️ *Trip forecast: {city}*\n\n{result}","ai_button":"🤖 *AI Assistant*\n\nSend a question about the weather, your trip, or what to do today.",
        "autopost_menu":"📢 *Auto-posting*\n\nBusiness can automatically publish weather to Telegram channels.\n\nCommands:\n/channel @channel CITY 08:00 — add a channel\n/channels — my channels\n/postnow — send post now\n/cardstyle — card style settings",
        "card_menu":"🖼 Weather Card\n\nBusiness: /generate_card CITY",
        "api_menu":"🔑 *API*\n\nBusiness: /apikey — create an API key.",
        'api_btn_create': '🔑 Create API Key',
        'api_btn_help': '📖 Documentation',
        'api_btn_city': '🏙 Set City',
        'api_btn_stats': '📊 Statistics',
        'api_btn_profile': '👤 My Profile',
        'api_btn_delete': '🗑 Delete Keys',
        'api_key_created': '🔑 API key created:\n`{api_key}`',
        'api_key_error': '❌ Error creating key. Check Business subscription.',
        'api_key_limit': '❌ Limit reached: 5 API keys. Delete old ones via «🗑 Delete keys».',
        'api_help_title': '📖 API Documentation',
        'api_help_base': '🌍 Base URL:',
        'api_help_endpoints': '📍 Endpoints:',
        'api_help_ep_weather': '• GET /weather?city=City',
        'api_help_ep_forecast': '• GET /forecast?city=City&days=5',
        'api_help_ep_me': '• GET /me',
        'api_help_auth': '🔑 Authorization:',
        'api_help_header': 'Header: X-API-Key: your_key',
        'api_help_default': '🏙 Default city: {city}',
        'api_help_limits': '📊 Limits:',
        'api_help_limit_keys': '• Maximum 5 API keys',
        'api_help_limit_req': '• 100 requests per hour per key',
        'api_help_example': '💡 Example:',
        'api_set_city_prompt': '🏙 Enter default city for API requests:',
        'api_profile_title': '📊 Your API Profile',
        'api_profile_id': '🆔 User ID: {id}',
        'api_profile_keys': '🔑 API keys: {count}',
        'api_profile_city': '🏙 Default city: {city}',
        'api_profile_first': '📅 First activity: {date}',
        'api_stats_empty': '📊 API Statistics\n\nYou have not used the API yet.',
        'api_stats_title': '📊 API Statistics',
        'api_stats_total': '📈 Total: {total}',
        'api_stats_24h': '🕐 24h: {h24}',
        'api_stats_7d': '📅 7 days: {d7}',
        'api_stats_by_ep': 'By endpoints:',
        'api_deleted': '🗑 Deleted API keys: {count}',
        'api_city_not_set': 'not set',
        'city_added': '✅ City added to favorites.',
        'city_add_failed': '❌ Failed to add city: {result}',
        'city_removed': '✅ City removed.',
        'city_not_found': '❌ City not found.',
        'api_enter_city_short': '🏙 Enter city for API:',
        'api_city_set': '✅ City for API: *{city}*',
        'card_ready': '🖼 Card is ready.',
        'card_error': '🖼 Failed to create card',
        'card_error_generic': '❌ Error: {err}',
        'logo_save_error': '❌ Failed to save logo.',

        "team_menu":"👥 *Teams*\n\nManage access to the bot for your team.\n\n*Roles:*\n"
                   "👑 owner — team owner\n"
                   "🛠 admin — full Business access\n"
                   "✏️ editor — full Business access\n"
                   "👁 viewer — Premium features only\n\n"
                   "One Business subscription — whole team uses it!",
        "team_list_title":"👥 *Your teams*\n\n",
        "team_list_empty":"You have no teams yet.\n\nTap '➕ Create team' to get started.",
        "team_create_prompt":"✏️ *Create a team*\n\nEnter the team name (e.g. My Company).",
        "team_create_success":"✅ Team *«{name}»* created!\n\nTeam ID: `{tid}`\n\nYou can now add members.",
        "team_create_failed":"❌ Could not create team. Check your Business subscription.",
        "team_add_prompt":"➕ *Add member*\n\nChoose a team:",
        "team_add_user_prompt":"👤 *Adding to team «{name}»*\n\nEnter Telegram user ID in format:\n`ID role`\n\nExamples:\n`123456789 admin`\n`987654321 editor`\n`555555555 viewer`\n\n💡 Find your ID: @userinfobot",
        "team_add_success":"✅ User added to team *«{name}»* with role *{role}*!",
        "team_add_failed":"❌ Could not add member. Check the data.",
        "team_info_title":"👥 *Team «{name}»*\n\n"
                          "🆔 ID: `{tid}`\n"
                          "📅 Created: {created}\n\n"
                          "👥 *Members ({count}):*\n{members}",
        "team_role_changed":"✅ User role changed to *{role}*.",
        "team_role_failed":"❌ Could not change role.",
        "team_member_removed":"✅ Member removed from team.",
        "team_remove_failed":"❌ Could not remove member.",
        "team_deleted":"✅ Team deleted.",
        "team_delete_confirm":"⚠️ *Delete team «{name}»?*\n\nAll members will lose access. This action cannot be undone.",
        "team_member":"• {icon} `{uid}` — {role}",
        "team_back":"🔙 To teams",
        "team_btn_create":"➕ Create team",
        "team_btn_list":"📋 My teams",
        "team_btn_add":"➕ Add member",
        "team_btn_remove":"➖ Remove member",
        "team_btn_delete":"🗑 Delete team",
        "team_btn_change_role":"🔄 Change role",
        "team_btn_back":"🔙 Back",
        "whitelabel_menu":"🏷 *White-label*\n\nBusiness: /white_label NAME",
        "analytics_menu":"📊 *Analytics*\n\nBusiness: connected-channel and posting statistics."
    },
}
for _lang_key, _items in _NEW_TEXTS.items():
    TEXTS.setdefault(_lang_key, {}).update(_items)
_EXTRA_UI_TEXTS = {
"ru":{"cities_title":"⭐ *Мои города*","cities_empty":"Пока нет сохранённых городов.","cities_choose":"Выберите город:","city_added":"✅ Город *{city}* добавлен.","city_removed":"✅ Город *{city}* удалён.","city_not_in_favorites":"❌ Такой город не найден в списке.","notification_settings":"🔔 *Настройки уведомлений*\n\nСтатус: {status}\n🌧 Дождь: {rain}\n💨 Сильный ветер: {wind}\n❄️ Мороз: {frost}\n☀️ Жара: {heat}\n🕘 Время: *{time}*\n📍 Город: *{city}*","notification_enabled":"✅ Включены","notification_disabled":"🔕 Выключены","notification_city_prompt":"📍 Напишите город, для которого нужны уведомления.","notification_time_prompt":"🕘 Напишите время в формате HH:MM, например 08:00.","notification_time_saved":"✅ Время уведомлений установлено: *{time}*","notification_city_saved":"✅ Город уведомлений установлен: *{city}*","notification_rain":"🌧 Дождь","notification_wind":"💨 Сильный ветер","notification_frost":"❄️ Мороз","notification_heat":"☀️ Жара","notification_time":"🕘 Время","notification_city":"📍 Город","notification_toggle":"🔔 Включить / выключить","notification_back":"🔙 Назад","notification_frequency":"📅 Периодичность","notification_freq_daily":"Ежедневно","notification_freq_weekly":"Еженедельно","notification_freq_weekdays":"Будни","notification_freq_weekends":"Выходные","notification_freq_saved":"✅ Периодичность установлена: *{freq}*",
        'alert_title': '⚠️ *Предупреждения о погоде на завтра*',
        'alert_heat': '🔥 *Жара!* Макс. температура {temp}°C (порог {thr}°C). Пейте больше воды, избегайте солнца.',
        'alert_frost': '❄️ *Мороз!* Мин. температура {temp}°C (порог {thr}°C). Одевайтесь тепло.',
        'alert_wind': '💨 *Сильный ветер!* До {speed} м/с (порог {thr} м/с). Будьте осторожны на улице.',
        'alert_rain': '🌧 *Дождь!* Осадки {mm} мм. Возьмите зонт.',
        'alert_heavy_rain': '⛈ *Сильный дождь!* Осадки {mm} мм (порог {thr} мм). Осторожно, возможны подтопления.',
        'alert_storm': '⛈ *Гроза!* {desc}. Избегайте открытых пространств.',
        'alert_no_city': '❌ Не удалось получить прогноз для уведомлений.',
        'threshold_heat': '🔥 Порог жары',
        'threshold_frost': '❄️ Порог мороза',
        'threshold_wind': '💨 Порог ветра',
        'threshold_rain': '🌧 Порог дождя',
        'threshold_heavy_rain': '⛈ Порог ливня',
        'threshold_current': 'Текущий порог: *{thr}*',
        'threshold_heat_prompt': '🔥 Введите температуру жары (°C):',
        'threshold_frost_prompt': '❄️ Введите температуру мороза (°C):',
        'threshold_wind_prompt': '💨 Введите скорость ветра (м/с):',
        'threshold_rain_prompt': '🌧 Введите количество осадков (мм):',
        'threshold_heavy_rain_prompt': '⛈ Введите количество осадков (мм):',
        'threshold_saved': '✅ Порог установлен: *{thr}*',
        'thresholds_title': '\n\n*Текущие пороги:*',
        'thresholds_line1': '\n🔥 Жара: {heat}°C | ❄️ Мороз: {frost}°C',
        'thresholds_line2': '\n💨 Ветер: {wind} м/с | 🌧 Дождь: {rain} мм',
        'thresholds_line3': '\n⛈ Ливень: {heavy} мм',},
"en":{"cities_title":"⭐ *My cities*","cities_empty":"No saved cities yet.","cities_choose":"Choose a city:","city_added":"✅ City *{city}* added.","city_removed":"✅ City *{city}* removed.","city_not_in_favorites":"❌ This city is not in your list.","notification_settings":"🔔 *Notification settings*\n\nStatus: {status}\n🌧 Rain: {rain}\n💨 Strong wind: {wind}\n❄️ Frost: {frost}\n☀️ Heat: {heat}\n🕘 Time: *{time}*\n📍 City: *{city}*","notification_enabled":"✅ Enabled","notification_disabled":"🔕 Disabled","notification_city_prompt":"📍 Send the city for notifications.","notification_time_prompt":"🕘 Send time in HH:MM format, e.g. 08:00.","notification_time_saved":"✅ Notification time set: *{time}*","notification_city_saved":"✅ Notification city set: *{city}*","notification_rain":"🌧 Rain","notification_wind":"💨 Strong wind","notification_frost":"❄️ Frost","notification_heat":"☀️ Heat","notification_time":"🕘 Time","notification_city":"📍 City","notification_toggle":"🔔 Enable / disable","notification_back":"🔙 Back","notification_frequency":"📅 Frequency","notification_freq_daily":"Daily","notification_freq_weekly":"Weekly","notification_freq_weekdays":"Weekdays","notification_freq_weekends":"Weekends","notification_freq_saved":"✅ Frequency set: *{freq}*",
        'alert_title': '⚠️ *Weather alerts for tomorrow*',
        'alert_heat': '🔥 *Heat!* Max temp {temp}°C (threshold {thr}°C). Drink water, avoid sun.',
        'alert_frost': '❄️ *Frost!* Min temp {temp}°C (threshold {thr}°C). Dress warmly.',
        'alert_wind': '💨 *Strong wind!* Up to {speed} m/s (threshold {thr} m/s). Be careful outside.',
        'alert_rain': '🌧 *Rain!* Precipitation {mm} mm. Take an umbrella.',
        'alert_heavy_rain': '⛈ *Heavy rain!* Precipitation {mm} mm (threshold {thr} mm). Caution, possible flooding.',
        'alert_storm': '⛈ *Storm!* {desc}. Avoid open areas.',
        'alert_no_city': '❌ Failed to get forecast for notifications.',
        'threshold_heat': '🔥 Heat threshold',
        'threshold_frost': '❄️ Frost threshold',
        'threshold_wind': '💨 Wind threshold',
        'threshold_rain': '🌧 Rain threshold',
        'threshold_heavy_rain': '⛈ Heavy rain threshold',
        'threshold_current': 'Current threshold: *{thr}*',
        'threshold_heat_prompt': '🔥 Enter heat temperature (°C):',
        'threshold_frost_prompt': '❄️ Enter frost temperature (°C):',
        'threshold_wind_prompt': '💨 Enter wind speed (m/s):',
        'threshold_rain_prompt': '🌧 Enter precipitation (mm):',
        'threshold_heavy_rain_prompt': '⛈ Enter precipitation (mm):',
        'threshold_saved': '✅ Threshold set: *{thr}*',
        'thresholds_title': '\n\n*Current thresholds:*',
        'thresholds_line1': '\n🔥 Heat: {heat}°C | ❄️ Frost: {frost}°C',
        'thresholds_line2': '\n💨 Wind: {wind} m/s | 🌧 Rain: {rain} mm',
        'thresholds_line3': '\n⛈ Heavy rain: {heavy} mm',},
}
for _lang_key, _items in _EXTRA_UI_TEXTS.items():
    TEXTS.setdefault(_lang_key, {}).update(_items)
# Final product UI: only Premium and Business are public plans.
TEXTS["ru"].update({
    'temp': '🌡 Температура: {temp}°C',
    'feels_like': '🤔 Ощущается как: {feels}°C',
    'wind_full': '💨 Ветер: {wind} м/с, {direction}',
    'humidity': '💧 Влажность: {humidity}%',
    'pressure_mm': '📊 Давление: {pressure} мм рт.ст.',
    'uv_with_level': '☀️ UV-индекс: {uv} ({level})',
    'uv_simple': '☀️ UV-индекс: {uv}',
    'updated_time': '🕐 Обновлено: {time}',
    'precip_prob': '🌧 Вероятность осадков: {prob}%',
    'sunrise': '🌅 Восход: {time}',
    'sunset': '🌇 Закат: {time}',
    'forecast_title': '📅 *Прогноз на {days_text} — {city}*\n\n',
    'forecast_day_line': '🌡 +{min}°...+{max}° (ощущ. +{feels}°)',
    'forecast_wind_line': '💨 {wind} м/с, {dir} | 💧 {hum}%',
    'forecast_pressure': '📊 {pressure} мм',
    'forecast_uv_line': ' | ☀️ UV {uv} ({level})',
    'forecast_precip': '🌧 Осадки: {prob}% ({mm} мм)',
    'cloudy_default': 'Облачно',
    'day_1': 'день', 'day_2_4': 'дня', 'day_5_plus': 'дней',
    'uv_low': 'низкий', 'uv_moderate': 'умеренный', 'uv_high': 'высокий',
    'uv_very_high': 'очень высокий', 'uv_extreme': 'экстремальный',
})
for _lang_code in LANGUAGES:
    _fallback = TEXTS.get(_lang_code, TEXTS["en"])
    _fallback.update({
        "btn_personal": "⭐ Premium",
        "btn_business_sub": "🏢 Business",
        "btn_add_city": {"ru": "➕ Добавить город", "en": "➕ Add city", "es": "➕ Añadir ciudad", "zh": "➕ 添加城市", "fr": "➕ Ajouter une ville", "de": "➕ Stadt hinzufügen", "ja": "➕ 都市を追加", "ko": "➕ 도시 추가", "it": "➕ Aggiungi città", "hi": "➕ शहर जोड़ें", "ar": "➕ إضافة مدينة"}.get(_lang_code, "➕ Add city"),
        "btn_remove_city": {"ru": "➖ Удалить город", "en": "➖ Remove city", "es": "➖ Eliminar ciudad", "zh": "➖ 删除城市", "fr": "➖ Supprimer une ville", "de": "➖ Stadt entfernen", "ja": "➖ 都市を削除", "ko": "➖ 도시 삭제", "it": "➖ Rimuovi città", "hi": "➖ शहर हटाएं", "ar": "➖ إزالة مدينة"}.get(_lang_code, "➖ Remove city"),
        "btn_wl_name": {"ru": "✏️ Название", "en": "✏️ Name", "es": "✏️ Nombre", "zh": "✏️ 名称", "fr": "✏️ Nom", "de": "✏️ Name", "ja": "✏️ 名前", "ko": "✏️ 이름", "it": "✏️ Nome", "hi": "✏️ नाम", "ar": "✏️ الاسم"}.get(_lang_code, "✏️ Name"),
        "btn_wl_color": {"ru": "🎨 Цвет", "en": "🎨 Color", "es": "🎨 Color", "zh": "🎨 颜色", "fr": "🎨 Couleur", "de": "🎨 Farbe", "ja": "🎨 色", "ko": "🎨 색상", "it": "🎨 Colore", "hi": "🎨 रंग", "ar": "🎨 اللون"}.get(_lang_code, "🎨 Color"),
        "btn_wl_logo": {"ru": "🖼 Логотип", "en": "🖼 Logo", "es": "🖼 Logo", "zh": "🖼 标志", "fr": "🖼 Logo", "de": "🖼 Logo", "ja": "🖼 ロゴ", "ko": "🖼 로고", "it": "🖼 Logo", "hi": "🖼 लोगो", "ar": "🖼 الشعار"}.get(_lang_code, "🖼 Logo"),
        "favorites_menu": "⭐ *Мои города*\n\nВыберите действие:" if _lang_code == "ru" else "⭐ *My cities*\n\nChoose an action:",
        "favorite_add_prompt": "➕ Напишите название города для добавления." if _lang_code == "ru" else "➕ Send the city name to add.",
        "favorite_remove_prompt": "➖ Напишите название города для удаления." if _lang_code == "ru" else "➖ Send the city name to remove.",
        "card_ready": "🖼 Карточка готова.",
        "card_prompt_city": "🖼 Отправьте название города для генерации карточки." if _lang_code == "ru" else "🖼 Card is ready.",
        "card_prompt": "🖼 Погодная карточка для текущего города." if _lang_code == "ru" else "🖼 Weather card for the current city.",
        "wl_menu_working": "🏢 *White-label*\n\nНастройте название, цвет и логотип вашего бренда." if _lang_code == "ru" else "🏢 *White-label*\n\nConfigure your brand name, color and logo.",
        "wl_name_prompt": "✏️ Напишите новое название бренда." if _lang_code == "ru" else "✏️ Send the new brand name.",
        "wl_color_prompt": "🎨 Напишите цвет в HEX, например #2563EB." if _lang_code == "ru" else "🎨 Send a HEX color, e.g. #2563EB.",
        "wl_logo_prompt": "🖼 Отправьте изображение логотипа следующим сообщением." if _lang_code == "ru" else "🖼 Send the logo image as the next message.",
        "wl_saved": "✅ Настройки White-label сохранены.",
        "wl_status_none": "📭 Настройки бренда пусты.",
        "wl_status_name": "✏️ Название: *{val}*",
        "wl_status_color": "🎨 Цвет: `{val}`",
        "wl_status_logo": "🖼 Логотип: `{val}`" if _lang_code == "ru" else "✅ White-label settings saved.",
        "invalid_action": "❌ Используйте кнопки меню или команду." if _lang_code == "ru" else "❌ Use the menu buttons or a command.",
        "city_input_only": "🏙️ Сейчас бот ожидает название города. Используйте кнопку «Сменить город» или отмените действие." if _lang_code == "ru" else "🏙️ The bot is waiting for a city name. Use Change city or cancel.",
    })
    # Hide legacy plan names from all user-facing subscription messages.
    _fallback["subscription_inactive"] = "❌ *Подписка неактивна*\n\n⭐ Premium: *{premium}⭐*\n🏢 Business: *{business}⭐*" if _lang_code == "ru" else "❌ *No active subscription*\n\n⭐ Premium: *{premium}⭐*\n🏢 Business: *{business}⭐*"
    _fallback["only_subscribed"] = "🔒 *Функция доступна по подписке.*\n\n⭐ Premium: *{premium}⭐*\n🏢 Business: *{business}⭐*" if _lang_code == "ru" else "🔒 *Subscription required.*\n\n⭐ Premium: *{premium}⭐*\n🏢 Business: *{business}⭐*"
def T(language, key, **kwargs):
    language = language if language in LANGUAGES else "en"
    text = TEXTS.get(language, TEXTS["en"]).get(key, TEXTS["en"].get(key, key))
    try:
        return text.format(**kwargs)
    except Exception:
        return text

# Описания погоды по кодам WMO (RU/EN)
WEATHER_DESC_TEXTS = {
    "ru": {
        'weather_clear': 'Ясно',
        'weather_partly_cloudy': 'Переменная облачность',
        'weather_fog': 'Туман',
        'weather_drizzle': 'Морось',
        'weather_rain': 'Дождь',
        'weather_snow': 'Снег',
        'weather_shower': 'Ливень',
        'weather_snow_shower': 'Снегопад',
        'weather_thunderstorm': 'Гроза',
        'weather_cloudy': 'Облачно',
    },
    "en": {
        'weather_clear': 'Clear',
        'weather_partly_cloudy': 'Partly cloudy',
        'weather_fog': 'Fog',
        'weather_drizzle': 'Drizzle',
        'weather_rain': 'Rain',
        'weather_snow': 'Snow',
        'weather_shower': 'Shower',
        'weather_snow_shower': 'Snow shower',
        'weather_thunderstorm': 'Thunderstorm',
        'weather_cloudy': 'Cloudy',
    },
}
for _lk, _items in WEATHER_DESC_TEXTS.items():
    TEXTS.setdefault(_lk, {}).update(_items)
