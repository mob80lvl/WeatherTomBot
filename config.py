import os
# Автозагрузка .env (не перезаписывает уже заданные переменные окружения)
try:
    _env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), ".env")
    if os.path.exists(_env_path):
        with open(_env_path, encoding="utf-8") as _ef:
            for _ln in _ef:
                _ln = _ln.strip()
                if _ln and not _ln.startswith("#") and "=" in _ln:
                    _k, _v = _ln.split("=", 1)
                    os.environ.setdefault(_k.strip(), _v.strip())
except Exception:
    pass

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
# ЮKassa (RUB, копейки) + USD fallback rate
PRICE_PREMIUM_RUB = 19900  # 199 ₽ в копейках
PRICE_BUSINESS_RUB = 49900  # 499 ₽ в копейках
USD_FALLBACK_RATE = 92.5  # Фолбэк-курс USD/RUB
YOOKASSA_TOKEN = os.getenv("YOOKASSA_TOKEN", "")  # live_xxx... или test_xxx...
PRICE_B2B_AGRICULTURE = 200
PRICE_B2B_CONSTRUCTION = 200
PRICE_B2B_TOURISM = 200
PRICE_B2B_BUSINESS = 400
SUBSCRIPTION_DAYS = 30

TEXTS_FILE = "bot_texts.json"
DB_FILE = os.getenv("DB_FILE", "bot.db")

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

