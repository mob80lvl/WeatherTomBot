# 🌤 WeatherTomBot — Умный погодный Telegram-бот

Профессиональный погодный бот с подпиской, B2B-клиентами, автопостингом и white-label брендингом.

## ✨ Возможности

### Для пользователей
- 🌤 **Погода сейчас** — точный прогноз для любого города мира
- 📅 **Прогноз на 5 дней** — детальный прогноз с почасовой разбивкой
- ⭐ **Избранное** — быстрые города (до 50 в бизнес-подписке)
- 🖼 **Погодные карточки** — красивые изображения с погодой (4 стиля)
- 🌍 **Мультиязычность** — русский, английский, испанский, китайский
- 👥 **Команды** — создание команд с ролями (owner/admin/viewer)
- 🔗 **Реферальная программа** — приглашение друзей с бонусами

### Для бизнеса (B2B)
- 🌾 **Сельское хозяйство** — агрометеорологические данные
- 🏗 **Строительство** — прогноз для планирования работ
- ✈️ **Туризм** — погода для туристических маршрутов
- 🏢 **Бизнес** — расширенная аналитика и API-доступ

### Администрирование
- 🔐 **Веб-админка** — управление пользователями, подписками, B2B
- 📊 **Аналитика** — события, статистика использования
- 📢 **Broadcast** — рассылка сообщений всем пользователям
- 🏷 **White-label** — брендинг под вашу компанию
- 📢 **Автопостинг** — публикация погоды в каналы
- 🔔 **Уведомления** — cron-задачи для оповещений

## 🛠 Технологии

- **Python 3.10+**
- **python-telegram-bot** — Telegram API
- **Flask** — веб-интерфейс и админка
- **SQLite** — база данных (15 таблиц)
- **OpenWeatherMap API** — погодные данные

## 🚀 Установка

### 1. Клонирование репозитория

    git clone https://github.com/yourusername/WeatherTomBot.git
    cd WeatherTomBot

### 2. Установка зависимостей

    pip install -r requirements.txt

### 3. Настройка окружения

    cp .env.example .env
    nano .env

**Обязательные параметры:**
- `TELEGRAM_TOKEN` — токен от [@BotFather](https://t.me/BotFather)
- `OPENWEATHER_API_KEY` — ключ [OpenWeatherMap](https://openweathermap.org/api)
- `ADMIN_TELEGRAM_ID` — ваш Telegram ID ([@userinfobot](https://t.me/userinfobot))
- `WEB_SECRET` — случайная строка для безопасности
- `WEBHOOK_HOST` — домен вашего сервера

### 4. Запуск бота

    python3 bot.py

База `bot.db` (15 таблиц) создаётся автоматически при первом запуске.

## 📊 База данных (15 таблиц)

**Основные данные:**
- `users` — города и языки пользователей
- `subscriptions` — подписки (план, срок, активатор)
- `b2b_users` — B2B-клиенты
- `user_states` — состояния диалогов
- `notifications` — уведомления

**Функции:**
- `f_users`, `f_teams`, `f_team_members` — профили и команды
- `f_channels` — автопостинг
- `f_card_settings` — погодные карточки
- `f_white_labels` — брендинг
- `f_referrals` — рефералы
- `f_events` — аналитика (до 50 000 событий)
- `api_keys` — API-ключи (SHA-256 + salt)

## 🔄 Бэкапы

Автоматический ежедневный бэкап в 3:00 ночи:

    python3 backup_db.py     # ручной запуск
    ls -lh backups/          # просмотр (хранится 7 последних)

## 🌐 Развёртывание на PythonAnywhere

1. Создайте виртуальное окружение:

       mkvirtualenv --python=/usr/bin/python3.10 weathertom
       pip install -r requirements.txt

2. Настройте Web app:
   - Source code: `/home/username/WeatherTomBot`
   - Working directory: `/home/username/WeatherTomBot/WeatherTomBot`
   - Virtualenv: `/home/username/.virtualenvs/weathertom`

3. WSGI файл:

       import sys
       path = '/home/username/WeatherTomBot/WeatherTomBot'
       if path not in sys.path:
           sys.path.insert(0, path)
       from app import app as application

4. Установите webhook:

       python3 -c "from bot import set_webhook; set_webhook()"

## 🔐 Безопасность

- Секреты в `.env` (не коммитится)
- База исключена из git
- Веб-админка защищена паролем
- API-ключи хранятся в хеше SHA-256 + salt

## 📈 Масштабируемость

Легко мигрирует на PostgreSQL:
- Стандартизированный SQL
- Схема переносится через `pgloader`

## 📄 Лицензия

MIT License

---
**Версия:** 3.0 (B2B + Multi-language)  
**Дата:** 2026-09-15
