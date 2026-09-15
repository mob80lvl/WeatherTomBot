# Installation / Deployment

## PythonAnywhere
1. Upload the contents of this archive into a clean project directory.
2. Create `.env` from `.env.example` and fill in `TELEGRAM_TOKEN`, weather API keys, `SECRET_KEY`, admin credentials and `WEBHOOK_URL`.
3. Install dependencies: `pip install -r requirements.txt`.
4. Configure the Flask web app to use `bot.application`.
5. Set the webhook to `https://YOUR-DOMAIN/webhook`.
6. Configure a Scheduled Task every 5 minutes:
   `curl -fsS "https://YOUR-DOMAIN/cron/weather?secret=YOUR_CRON_SECRET" >/dev/null`
7. Check `/webhook_info` and test `/start`.

## First launch
The application performs an idempotent subscription migration on startup:
- Personal -> Premium
- Agriculture -> Business
- Construction -> Business
- Tourism -> Business
- Business -> Business

Existing `expiry` timestamps are preserved. The distributable archive contains empty runtime JSON stores; when upgrading an existing installation, **do not overwrite your live JSON data**. Replace source/config files first, then restart the application so the migration can run against the existing data.

## Linux / systemd
A sample service is included in `deploy/weathertombot.service`.

## Update of an existing installation
1. Back up the whole current WeatherTomBot directory.
2. Replace `bot.py`, `features.py`, `features.json`, `notify_cron.py` and documentation/config files as needed.
3. Keep the existing live runtime JSON files (`subscriptions.json`, `b2b_users.json`, `users_city.json`, `notifications.json`, `referrals.json`, `api_keys.json`, `user_states.json`).
4. Restart the web application.
5. Verify `/start`, city input, ⭐ Cities, 🔔 Notifications, 🖼 Card, ✈️ Trip, 💳 Plans and 🏢 White-label.

## Security
Never upload `.env`, bot tokens, API keys, logs or private user data to GitHub or to a buyer package.
