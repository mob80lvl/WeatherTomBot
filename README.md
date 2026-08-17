# WeatherTomBot — Final Clean 2026-08-10

Production-ready Telegram weather bot with RU/EN/ES/ZH localization, Free/Premium/Business access control, weather aggregation, notifications, trip forecasts, favorite cities, weather cards and Business white-label/API/channel features.

## Public plans
- 🆓 Free — basic weather and core functions.
- ⭐ Premium — notifications, favorite cities, trip forecasts, AI and Premium features.
- 🏢 Business — everything in Premium plus channels, weather cards, API, teams, analytics and White-label.

Only **Premium** and **Business** are paid subscription types. Legacy Personal/Agriculture/Construction/Tourism records are normalized automatically on startup without changing their expiry dates.

## Important fixes in this release
- City changes only after an explicit city-input state; arbitrary text and Telegram commands cannot overwrite the city.
- ⭐ Cities has `➕ Add city` / `➖ Remove city` buttons.
- 🔔 Notifications use the `/cron/weather` scheduler endpoint.
- 🖼 Weather cards are generated and sent as Telegram photos.
- ✈️ Trip forecasts include wind direction.
- 🏢 White-label has an interactive Business UI for name, HEX color and logo.
- 💳 Subscription cabinet exposes only Premium and Business.
- 🔄 Legacy subscriptions migrate to the new two-plan model while preserving expiry.

## Files
`bot.py` and `features.py` are the production source files. JSON files shipped in the package are empty runtime stores so no private user data is distributed.

## Configuration
Copy `.env.example` to `.env` and fill in the secrets. Never commit `.env`.

## Run
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
python bot.py
```

## PythonAnywhere
Use `PYTHONANYWHERE.md`. Configure the Flask web app to load `bot.application` and set the webhook to `/webhook`. For notifications, create a PythonAnywhere Scheduled Task that calls `/cron/weather?secret=CRON_SECRET` every 5 minutes.

## Scheduler
`GET /cron/weather?secret=YOUR_CRON_SECRET` processes user weather notifications and scheduled channel posts. The endpoint remains disabled until `CRON_SECRET` is configured.

## Commercial features
- Favorite cities and weather alerts
- Trip forecasts with wind direction
- AI weather assistant
- Telegram Stars subscription activation
- Promo/referral/traffic analytics
- Business channel auto-posting
- Weather image/card generation
- REST API v1
- Teams and roles
- White-label settings

## Security
Do not distribute `.env`, tokens, API keys, logs, generated media or live user JSON data. Rotate any credentials that were previously exposed.
