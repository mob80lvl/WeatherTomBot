import os

# ============================================================
#  НАСТРОЙКИ
# ============================================================

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN", "")
OPENWEATHER_API_KEY = os.getenv("OPENWEATHER_API_KEY", "")
WEATHERAPI_KEY = os.getenv("WEATHERAPI_KEY", "")
ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "")
SECRET_KEY = os.getenv("SECRET_KEY", "change-me")
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "")
ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_IDS", "").split(",") if x.strip().isdigit()]
LOG_FILE = os.getenv("LOG_FILE", "bot.log")

PRICE_PERSONAL = 100
PRICE_PREMIUM = 100
PRICE_BUSINESS = 400
PRICE_B2B_AGRICULTURE = 200
PRICE_B2B_CONSTRUCTION = 200
PRICE_B2B_TOURISM = 200
PRICE_B2B_BUSINESS = 400
SUBSCRIPTION_DAYS = 30

USERS_FILE = "users_city.json"
SUBSCRIPTIONS_FILE = "subscriptions.json"
TEXTS_FILE = "bot_texts.json"
B2B_FILE = "b2b_users.json"
NOTIFICATIONS_FILE = "notifications.json"
USER_STATES_FILE = "user_states.json"

# Advanced feature module (B2B, AI, channels, API, teams, white-label, referrals, analytics)
try:
    import features as advanced_features
except Exception:
    advanced_features = None

B2B_TYPES = {
    "agriculture": {"name_key": "b2b_agriculture_name", "features_key": "b2b_agriculture_features", "icon": "🌾", "price": PRICE_B2B_AGRICULTURE},
    "construction": {"name_key": "b2b_construction_name", "features_key": "b2b_construction_features", "icon": "🏗️", "price": PRICE_B2B_CONSTRUCTION},
    "tourism": {"name_key": "b2b_tourism_name", "features_key": "b2b_tourism_features", "icon": "✈️", "price": PRICE_B2B_TOURISM},
    "business": {"name_key": "b2b_business_name", "features_key": "b2b_business_features", "icon": "🏢", "price": PRICE_B2B_BUSINESS}
}

