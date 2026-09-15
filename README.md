**🇬🇧 English** | [🇷🇺 Русский](README_ru.md)

# 🌤 WeatherTomBot — Smart Weather Telegram Bot

Professional weather bot with subscriptions, B2B clients, auto-posting and white-label branding.

## ✨ Features

### For users
- 🌤 **Current weather** — accurate forecast for any city worldwide
- 📅 **5-day forecast** — detailed forecast with hourly breakdown
- ⭐ **Favorites** — quick-access cities (up to 50 on Business plan)
- 🖼 **Weather cards** — beautiful weather images (4 styles)
- 🌍 **Multi-language** — Russian, English, Spanish, Chinese
- 👥 **Teams** — create teams with roles (owner/admin/viewer)
- 🔗 **Referral program** — invite friends and earn bonuses

### For business (B2B)
- 🌾 **Agriculture** — agrometeorological data
- 🏗 **Construction** — forecasts for work planning
- ✈️ **Tourism** — weather for travel routes
- 🏢 **Business** — extended analytics and API access

### Administration
- 🔐 **Web admin panel** — manage users, subscriptions, B2B clients
- 📊 **Analytics** — events and usage statistics
- 📢 **Broadcast** — send messages to all users
- 🏷 **White-label** — rebrand the bot for your company
- 📢 **Auto-posting** — publish weather to channels automatically
- 🔔 **Notifications** — cron tasks for regular alerts

## 🛠 Tech stack

- **Python 3.10+**
- **python-telegram-bot** — Telegram API
- **Flask** — web interface and admin panel
- **SQLite** — database (15 tables)
- **OpenWeatherMap API** — weather data

## 🚀 Installation

### 1. Clone the repository

    git clone https://github.com/yourusername/WeatherTomBot.git
    cd WeatherTomBot

### 2. Install dependencies

    pip install -r requirements.txt

### 3. Configure environment

    cp .env.example .env
    nano .env

**Required parameters:**
- `TELEGRAM_TOKEN` — bot token from [@BotFather](https://t.me/BotFather)
- `OPENWEATHER_API_KEY` — key from [OpenWeatherMap](https://openweathermap.org/api)
- `ADMIN_TELEGRAM_ID` — your Telegram ID ([@userinfobot](https://t.me/userinfobot))
- `WEB_SECRET` — random string for security
- `WEBHOOK_HOST` — your server domain

### 4. Run the bot

    python3 bot.py

The `bot.db` database (15 tables) is created automatically on first run.

## 📊 Database (15 tables)

**Core data:**
- `users` — user cities and languages
- `subscriptions` — subscriptions (plan, expiry, activator)
- `b2b_users` — B2B clients
- `user_states` — dialog states
- `notifications` — notifications

**Features:**
- `f_users`, `f_teams`, `f_team_members` — profiles and teams
- `f_channels` — auto-posting
- `f_card_settings` — weather cards
- `f_white_labels` — branding
- `f_referrals` — referrals
- `f_events` — analytics (up to 50,000 events)
- `api_keys` — API keys (SHA-256 + salt)

## 🔄 Backups

Automatic daily backup at 3:00 AM:

    python3 backup_db.py     # manual run
    ls -lh backups/          # view (last 7 kept)

## 🌐 Deploying to PythonAnywhere

1. Create a virtual environment:

       mkvirtualenv --python=/usr/bin/python3.10 weathertom
       pip install -r requirements.txt

2. Configure the Web app:
   - Source code: `/home/username/WeatherTomBot`
   - Working directory: `/home/username/WeatherTomBot/WeatherTomBot`
   - Virtualenv: `/home/username/.virtualenvs/weathertom`

3. WSGI file:

       import sys
       path = '/home/username/WeatherTomBot/WeatherTomBot'
       if path not in sys.path:
           sys.path.insert(0, path)
       from app import app as application

4. Set up the webhook:

       python3 -c "from bot import set_webhook; set_webhook()"

## 🔐 Security

- Secrets stored in `.env` (not committed)
- Database excluded from git
- Admin panel password-protected
- API keys stored as SHA-256 + salt hashes

## 📈 Scalability

Easily migrates to PostgreSQL:
- Standardized SQL
- Schema transfers via `pgloader`

## 📄 License

MIT License

---
**Version:** 3.0 (B2B + Multi-language)  
**Date:** 2026-09-15
