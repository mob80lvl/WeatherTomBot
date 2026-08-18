# -*- coding: utf-8 -*-
"""
WeatherTomBot Business/Retention Feature Pack.
The module is intentionally storage-light (JSON) so it remains deployable on
PythonAnywhere without a database. All write operations are atomic-ish and
guarded by a process-local lock.
"""
import os, json, time, uuid, secrets, hashlib, threading, math, logging

logger = logging.getLogger("features"), logging

logger = logging.getLogger("features"), logging

logger = logging.getLogger("features")
from datetime import datetime, timedelta
from functools import wraps
from flask import request, jsonify

try:
    from PIL import Image, ImageDraw, ImageFont
except Exception:
    Image = ImageDraw = ImageFont = None

FEATURE_FILE = os.getenv("FEATURES_FILE", "features.json")
API_KEY_FILE = os.getenv("API_KEYS_FILE", "api_keys.json")
MEDIA_DIR = os.getenv("MEDIA_DIR", "generated_media")
AI_API_KEY = os.getenv("OPENAI_API_KEY", "")
AI_MODEL = os.getenv("OPENAI_MODEL", "gpt-4o-mini")
FEATURE_LOCK = threading.RLock()

CFG = {}

def configure(**kwargs):
    CFG.update(kwargs)

def _now():
    return datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def _load(path, default):
    with FEATURE_LOCK:
        try:
            if not os.path.exists(path):
                return default.copy() if isinstance(default, dict) else default
            with open(path, "r", encoding="utf-8") as f:
                obj = json.load(f)
            return obj
        except Exception:
            return default.copy() if isinstance(default, dict) else default

def _save(path, obj):
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    tmp = path + ".tmp"
    with FEATURE_LOCK:
        with open(tmp, "w", encoding="utf-8") as f:
            json.dump(obj, f, ensure_ascii=False, indent=2)
        os.replace(tmp, path)
    return True

def _db():
    db = _load(FEATURE_FILE, {})
    for key, default in {
        "users": {}, "events": [], "promos": {}, "payments": {},
        "referrals": {}, "channels": {}, "teams": {}, "white_labels": {},
        "settings": {"free_favorites": 2, "premium_favorites": 10, "business_favorites": 50}
    }.items():
        if key not in db:
            db[key] = default
    return db

def _save_db(db):
    # Keep event history bounded so JSON storage cannot grow forever.
    db["events"] = db.get("events", [])[-50000:]
    return _save(FEATURE_FILE, db)

def _lang(uid):
    fn = CFG.get("get_user_lang")
    return fn(uid) if fn else "en"

def _city(uid):
    fn = CFG.get("get_user_city")
    return fn(uid) if fn else None

def _send(uid, text, keyboard=None):
    fn = CFG.get("send_message")
    return fn(uid, text, keyboard) if fn else None

def _premium(uid):
    fn = CFG.get("is_user_subscribed")
    return bool(fn(uid)) if fn else False

def _business(uid):
    if not _premium(uid):
        return False
    fn = CFG.get("get_user_b2b_type")
    return bool(fn and fn(uid) == "business")

def _b2b_type(uid):
    if not _premium(uid):
        return None
    fn = CFG.get("get_user_b2b_type")
    return fn(uid) if fn else None

def _require_b2b(uid, required):
    actual = _b2b_type(uid)
    return actual == required or actual == "business"

def _T(uid, key, **kwargs):
    fn = CFG.get("T")
    lang = _lang(uid)
    if fn:
        try:
            return fn(lang, key, **kwargs)
        except Exception:
            pass
    return key.format(**kwargs)

def track(uid, event, props=None):
    db = _db()
    db["events"].append({"id": uuid.uuid4().hex, "user_id": str(uid),
                          "event": event, "ts": _now(), "props": props or {}})
    profile = db["users"].setdefault(str(uid), {})
    profile.setdefault("first_seen", _now())
    profile["last_seen"] = _now()
    if event == "start":
        profile.setdefault("started", True)
    _save_db(db)

def register_user(uid, source="organic"):
    db = _db()
    p = db["users"].setdefault(str(uid), {})
    p.setdefault("first_seen", _now())
    p["last_seen"] = _now()
    if source and source != "organic":
        p.setdefault("source", source)
    p.setdefault("source", source or "organic")
    _save_db(db)
    track(uid, "start", {"source": source or "organic"})

def favorites(uid):
    db = _db()
    return db["users"].get(str(uid), {}).get("favorites", [])


def set_api_default_city(uid, city):
    db = _db()
    p = db["users"].setdefault(str(uid), {})
    p["api_default_city"] = city
    _save_db(db)
    logger.info(f"API default city set: user={uid}, city={city}")
    return city

def get_api_default_city(uid):
    db = _db()
    return db["users"].get(str(uid), {}).get("api_default_city")



def check_api_rate_limit(uid, limit=100, window=3600):
    """Проверяет rate limit для API запросов.
    
    Args:
        uid: ID пользователя
        limit: максимальное количество запросов
        window: временное окно в секундах (по умолчанию 1 час)
    
    Returns:
        (bool, dict): (разрешено ли, информация о лимите)
    """
    import time
    db = _db()
    user_data = db["users"].setdefault(str(uid), {})
    
    # Инициализируем счётчик если его нет
    if "api_requests" not in user_data:
        user_data["api_requests"] = []
    
    now = time.time()
    # Убираем старые запросы
    user_data["api_requests"] = [
        req_time for req_time in user_data["api_requests"]
        if now - req_time < window
    ]
    
    # Проверяем лимит
    if len(user_data["api_requests"]) >= limit:
        _save_db(db)
        return False, {
            "limit": limit,
            "used": len(user_data["api_requests"]),
            "window": window,
            "reset_in": int(window - (now - user_data["api_requests"][0]))
        }
    
    # Добавляем текущий запрос
    user_data["api_requests"].append(now)
    _save_db(db)
    
    return True, {
        "limit": limit,
        "used": len(user_data["api_requests"]),
        "remaining": limit - len(user_data["api_requests"]),
        "window": window
    }


def get_api_inline_keyboard():
    """Создает inline-клавиатуру для API управления."""
    return {
        "inline_keyboard": [
            [
                {"text": "🔑 Создать API-ключ", "callback_data": "api_create_key"},
                {"text": "📖 Документация", "callback_data": "api_help"}
            ],
            [
                {"text": "🏙 Установить город", "callback_data": "api_set_city"},
                {"text": "📊 Мой профиль", "callback_data": "api_profile"}
            ],
            [
                {"text": "🗑 Удалить все ключи", "callback_data": "api_delete_all"}
            ]
        ]
    }


def add_favorite(uid, city):
    city = (city or "").strip()
    if not city:
        return False, "empty"
    db = _db()
    p = db["users"].setdefault(str(uid), {})
    favs = p.setdefault("favorites", [])
    norm = city.casefold()
    if any(str(x).casefold() == norm for x in favs):
        return False, "exists"
    limits = db.get("settings", {})
    if CFG.get("is_user_subscribed") and CFG["is_user_subscribed"](uid):
        b2b = CFG.get("get_user_b2b_type", lambda x: None)(uid)
        limit = limits.get("business_favorites", 50) if b2b else limits.get("premium_favorites", 10)
    else:
        limit = limits.get("free_favorites", 2)
    if len(favs) >= limit:
        return False, f"limit:{limit}"
    favs.append(city)
    _save_db(db)
    track(uid, "favorite_added", {"city": city})
    return True, city

def remove_favorite(uid, city):
    db = _db()
    p = db["users"].setdefault(str(uid), {})
    favs = p.setdefault("favorites", [])
    old = len(favs)
    favs[:] = [x for x in favs if str(x).casefold() != str(city).casefold()]
    _save_db(db)
    return old != len(favs)

def notification_prefs(uid):
    db = _db()
    p = db["users"].setdefault(str(uid), {})
    return p.setdefault("notifications", {
        "enabled": False, "time": "08:00", "rain": True,
        "storm": True, "wind": True, "temp": True,
        "heat": True, "frost": True, "heavy_rain": True
    })

def set_notification_prefs(uid, **changes):
    db = _db()
    p = db["users"].setdefault(str(uid), {})
    prefs = p.setdefault("notifications", {})
    prefs.update(changes)
    _save_db(db)
    track(uid, "notification_settings", changes)
    return prefs

def set_alert(uid, kind, enabled=True, threshold=None):
    """Устанавливает параметры уведомления с валидацией типов."""
    prefs = notification_prefs(uid)
    alerts = prefs.setdefault("alerts", {})
    validated_threshold = None
    if threshold is not None:
        try:
            validated_threshold = float(threshold)
        except (TypeError, ValueError):
            validated_threshold = None
    alerts[kind] = {"enabled": bool(enabled), "threshold": validated_threshold}
    set_notification_prefs(uid, alerts=alerts)
    return alerts[kind]


def alerts(uid):
    return notification_prefs(uid).get("alerts", {})

def trip_forecast(uid, destination, days=5):
    if not _premium(uid):
        return {"error": "premium_required"}
    weather_fn = CFG.get("get_forecast_aggregated")
    if not weather_fn:
        return {"error": "weather_unavailable"}
    lang = _lang(uid)
    try:
        data = weather_fn(destination, min(max(int(days), 1), 10), lang)
        track(uid, "trip_forecast", {"destination": destination, "days": days})
        return data
    except Exception as exc:
        return {"error": str(exc)}

def ai_answer(uid, question):
    if not _premium(uid):
        return None, "Premium subscription required."
    if not AI_API_KEY:
        return None, "AI is not configured. Set OPENAI_API_KEY and OPENAI_MODEL in .env."
    city = _city(uid) or "the user's location"
    weather_fn = CFG.get("get_weather_aggregated")
    context = ""
    if weather_fn:
        try:
            w = weather_fn(city, _lang(uid))
            if isinstance(w, dict) and "error" not in w:
                context = json.dumps(w, ensure_ascii=False)
        except Exception:
            pass
    prompt = (
        "You are WeatherTomBot's weather assistant. Answer concisely and safely. "
        "Do not invent weather data. If current data is supplied, use it. "
        f"User city: {city}. Current weather data: {context}. "
        f"Question: {question}"
    )
    try:
        r = __import__("requests").post(
            "https://api.openai.com/v1/chat/completions",
            headers={"Authorization": f"Bearer {AI_API_KEY}", "Content-Type": "application/json"},
            json={"model": AI_MODEL, "messages":[
                {"role":"system","content":"You are a helpful multilingual weather assistant."},
                {"role":"user","content":prompt}
            ], "temperature":0.2, "max_tokens":500},
            timeout=30
        )
        body = r.json()
        if r.status_code >= 400:
            return None, body.get("error", {}).get("message", "AI request failed")
        answer = body["choices"][0]["message"]["content"].strip()
        track(uid, "ai_question")
        return answer, None
    except Exception as exc:
        return None, str(exc)

def apply_promo(uid, code):
    code = (code or "").strip().upper()
    db = _db()
    promo = db["promos"].get(code)
    if not promo:
        return False, "not_found"
    now = datetime.utcnow()
    if promo.get("expires_at"):
        try:
            if datetime.fromisoformat(promo["expires_at"]) < now:
                return False, "expired"
        except Exception:
            pass
    used = promo.setdefault("used_by", [])
    if str(uid) in used:
        return False, "used"
    limit = int(promo.get("max_uses", 0) or 0)
    if limit and len(used) >= limit:
        return False, "limit"
    used.append(str(uid))
    days = int(promo.get("days", 0) or 0)
    discount = float(promo.get("discount_percent", 0) or 0)
    if days and CFG.get("set_user_subscription"):
        CFG["set_user_subscription"](uid, days, b2b_type=None)
    _save_db(db)
    track(uid, "promo_redeemed", {"code": code, "days": days, "discount_percent": discount})
    return True, {"days": days, "discount_percent": discount}

def create_promo(code, days=0, discount_percent=0, max_uses=0, expires_at=None):
    db = _db()
    db["promos"][str(code).strip().upper()] = {
        "days": int(days), "discount_percent": float(discount_percent),
        "max_uses": int(max_uses), "expires_at": expires_at, "used_by": []
    }
    _save_db(db)
    return True

def referral_info(uid):
    db = _db()
    p = db["users"].setdefault(str(uid), {})
    code = p.get("referral_code")
    if not code:
        code = secrets.token_urlsafe(6).replace("-", "").replace("_", "")[:8].lower()
        p["referral_code"] = code
        db["users"][str(uid)] = p
        db["referrals"].setdefault(code, {"owner": str(uid), "users": [], "rewarded": []})
        _save_db(db)
    r = db["referrals"].get(code, {"users":[]})
    return code, len(r.get("users", []))

def process_referral(uid, code, reward_days=7):
    code = (code or "").strip().lower()
    if not code:
        return False
    db = _db()
    ref = db["referrals"].get(code)
    if not ref or str(ref.get("owner")) == str(uid):
        return False
    if str(uid) in ref.setdefault("users", []):
        return False
    ref["users"].append(str(uid))
    owner = str(ref["owner"])
    if str(uid) not in ref.setdefault("rewarded", []):
        ref["rewarded"].append(str(uid))
        if CFG.get("set_user_subscription"):
            CFG["set_user_subscription"](uid, reward_days, b2b_type=None)
            CFG["set_user_subscription"](owner, reward_days, b2b_type=None)
    _save_db(db)
    track(uid, "referral_joined", {"code": code, "owner": owner})
    track(owner, "referral_reward", {"referred": str(uid), "days": reward_days})
    return True

def record_payment(uid, payload, amount, currency="XTR"):
    db = _db()
    payment_id = uuid.uuid4().hex
    db["payments"][payment_id] = {
        "user_id": str(uid), "payload": payload, "amount": amount,
        "currency": currency, "created_at": _now(), "status": "paid"
    }
    _save_db(db)
    track(uid, "payment", {"amount": amount, "currency": currency, "payload": payload})
    return payment_id

def revenue_stats():
    db = _db()
    payments = [x for x in db.get("payments", {}).values() if x.get("status") == "paid"]
    total = sum(float(x.get("amount", 0) or 0) for x in payments)
    users = {str(x.get("user_id")) for x in payments}
    now = datetime.utcnow()
    month_prefix = now.strftime("%Y-%m")
    mrr = sum(float(x.get("amount",0) or 0) for x in payments
              if str(x.get("created_at","")).startswith(month_prefix))
    arpu = total / len(users) if users else 0
    return {"revenue": total, "mrr": mrr, "arpu": arpu, "payments": len(payments), "paying_users": len(users)}

def funnel_stats():
    db = _db()
    events = db.get("events", [])
    def count(name):
        return len({e["user_id"] for e in events if e.get("event") == name})
    return {
        "started": count("start"),
        "favorites": count("favorite_added"),
        "notifications": count("notification_settings"),
        "trip": count("trip_forecast"),
        "ai": count("ai_question"),
        "paid": count("payment")
    }

def retention(days):
    db = _db()
    users = db.get("users", {})
    events = db.get("events", [])
    cohort_date = datetime.utcnow().date() - timedelta(days=days)
    cohort = {uid for uid,p in users.items()
              if str(p.get("first_seen",""))[:10] == cohort_date.isoformat()}
    today = datetime.utcnow().date()
    active_today = {e["user_id"] for e in events
                    if str(e.get("ts",""))[:10] == today.isoformat()}
    retained = len(cohort & active_today)
    return {"days": days, "cohort_date": cohort_date.isoformat(),
            "cohort": len(cohort), "retained": retained,
            "rate": (retained/len(cohort)*100 if cohort else 0)}

def source_stats():
    db = _db()
    out = {}
    for p in db.get("users", {}).values():
        s = p.get("source", "organic")
        out[s] = out.get(s, 0) + 1
    return out

def _telegram(method, payload):
    token = os.getenv("TELEGRAM_TOKEN", "")
    if not token:
        return {"ok": False, "description": "TELEGRAM_TOKEN missing"}
    try:
        r = __import__("requests").post(f"https://api.telegram.org/bot{token}/{method}",
                                        json=payload, timeout=30)
        return r.json()
    except Exception as exc:
        return {"ok": False, "description": str(exc)}

def add_channel(uid, channel_id, title=None, city=None, schedule="08:00"):
    if not _business(uid):
        return None
    db = _db()
    cid = str(channel_id).strip()
    db["channels"][cid] = {
        "owner": str(uid), "title": title or cid, "city": city or _city(uid),
        "schedule": schedule, "enabled": True, "created_at": _now(),
        "last_post": None
    }
    _save_db(db)
    track(uid, "channel_added", {"channel_id": cid})
    return db["channels"][cid]

def post_weather_card(channel_id, city, caption=None):
    weather_fn = CFG.get("get_weather_aggregated")
    if not weather_fn:
        return {"ok": False, "description": "weather unavailable"}
    owner = _db().get("channels", {}).get(str(channel_id), {}).get("owner")
    brand = _db().get("white_labels", {}).get(str(owner), {}) if owner else None
    lang = _lang(owner) if owner else "en"
    w = weather_fn(city, lang)
    if not isinstance(w, dict) or "error" in w:
        return {"ok": False, "description": "weather error"}
    image_path = generate_weather_card(w, city, brand=brand)
    if image_path and os.path.exists(image_path):
        token = os.getenv("TELEGRAM_TOKEN", "")
        url = f"https://api.telegram.org/bot{token}/sendPhoto"
        try:
            with open(image_path, "rb") as f:
                r = __import__("requests").post(url, data={"chat_id": channel_id,
                    "caption": caption or f"🌤 {city}"}, files={"photo": f}, timeout=60)
            result = r.json()
        except Exception as exc:
            result = {"ok": False, "description": str(exc)}
    else:
        result = _telegram("sendMessage", {"chat_id": channel_id,
            "text": caption or f"🌤 {city}"})
    if result.get("ok"):
        db = _db()
        if str(channel_id) in db["channels"]:
            db["channels"][str(channel_id)]["last_post"] = _now()
            _save_db(db)
    return result

def generate_weather_card(weather, city, brand=None):
    os.makedirs(MEDIA_DIR, exist_ok=True)
    safe = re_safe(city)
    path = os.path.join(MEDIA_DIR, f"weather_{safe}_{int(time.time())}.png")
    if Image is None:
        return None
    img = Image.new("RGB", (1200, 630), (22, 30, 55))
    draw = ImageDraw.Draw(img)
    try:
        font_big = ImageFont.truetype("DejaVuSans.ttf", 92)
        font = ImageFont.truetype("DejaVuSans.ttf", 42)
        small = ImageFont.truetype("DejaVuSans.ttf", 30)
    except Exception:
        font_big = font = small = ImageFont.load_default()
    temp = weather.get("temp", "—")
    desc = weather.get("description", "—")
    wind = weather.get("wind_speed", "—")
    brand = brand if isinstance(brand, dict) else {}
    accent = (255, 215, 0)
    primary = str(brand.get("primary") or "").lstrip("#")
    if len(primary) == 6:
        try:
            accent = tuple(int(primary[i:i+2], 16) for i in (0, 2, 4))
        except ValueError:
            pass
    draw.text((60, 55), f"🌤 {city}", font=font, fill=(255,255,255))
    draw.text((60, 150), f"{temp}°", font=font_big, fill=accent)
    draw.text((70, 290), str(desc), font=font, fill=(255,255,255))
    draw.text((70, 360), f"💨 {wind}", font=small, fill=(220,230,240))
    brand_name = brand.get("name") or "WeatherTomBot"
    logo = brand.get("logo")
    if logo and os.path.exists(str(logo)):
        try:
            logo_img = Image.open(str(logo)).convert("RGBA")
            logo_img.thumbnail((120, 120))
            img.paste(logo_img, (1020, 470), logo_img)
        except Exception:
            pass
    draw.text((70, 520), brand_name, font=small, fill=(170,180,200))
    img.save(path, "PNG")
    return path

def re_safe(s):
    return "".join(c if c.isalnum() else "_" for c in str(s))[:60]

def create_api_key(uid, name="default"):
    """Создает API ключ с улучшенной безопасностью (соль + 32 символа)."""
    if not (_business(uid) or _admin(uid)):
        logger.warning(f"Попытка создания API ключа без прав: user={uid}")
        return None, None
    try:
        keys = _load(API_KEY_FILE, {})
        
        # Проверяем лимит ключей (максимум 5 на пользователя)
        user_keys_count = sum(1 for k, v in keys.items() if v.get("owner") == str(uid) and v.get("active"))
        max_keys = 5
        
        if user_keys_count >= max_keys:
            logger.warning(f"Превышен лимит API ключей: user={uid}, count={user_keys_count}/{max_keys}")
            return None, None
        raw = "wt_" + secrets.token_urlsafe(32)
        salt = secrets.token_hex(16)
        digest = hashlib.sha256((salt + raw).encode()).hexdigest()
        keys[digest] = {
            "owner": str(uid), "name": name, "created_at": _now(),
            "last_used": None, "salt": salt, "active": True, "usage_count": 0
        }
        _save(API_KEY_FILE, keys)
        logger.info(f"API ключ создан: user={uid}, name={name}")
        return raw, keys[digest]
    except Exception as e:
        logger.error(f"Ошибка создания API ключа: {e}", exc_info=True)
        return None, None


def verify_api_key(raw):
    """Проверяет API ключ с учетом соли и статуса активности."""
    if not raw:
        return None
    try:
        keys = _load(API_KEY_FILE, {})
        for digest, item in keys.items():
            if not item.get("active", True):
                continue
            salt = item.get("salt", "")
            expected_digest = hashlib.sha256((salt + raw).encode()).hexdigest()
            if digest == expected_digest:
                item["last_used"] = _now()
                item["usage_count"] = item.get("usage_count", 0) + 1
                try:
                    _save(API_KEY_FILE, keys)
                except Exception:
                    pass
                return item
        logger.warning(f"Невалидный API ключ: {raw[:10]}...")
        return None
    except Exception as e:
        logger.error(f"Ошибка проверки API ключа: {e}", exc_info=True)
        return None


def team_for(uid):
    db = _db()
    return {tid:t for tid,t in db["teams"].items()
            if str(uid) in t.get("members", {})}

def create_team(uid, name):
    if not _business(uid):
        return None
    db = _db()
    tid = uuid.uuid4().hex[:10]
    db["teams"][tid] = {"name": name, "owner": str(uid),
                        "members": {str(uid): "owner"}, "created_at": _now()}
    _save_db(db)
    track(uid, "team_created", {"team_id": tid})
    return tid

def add_team_member(uid, team_id, member_id, role="viewer"):
    db = _db()
    t = db["teams"].get(team_id)
    if not t or str(t.get("owner")) != str(uid):
        return False
    if role not in ("admin", "editor", "viewer"):
        return False
    t.setdefault("members", {})[str(member_id)] = role
    _save_db(db)
    return True

def set_white_label(uid, name=None, logo=None, primary=None):
    if not _business(uid):
        return {"error": "business_required"}
    db = _db()
    wl = db["white_labels"].setdefault(str(uid), {})
    if name is not None: wl["name"] = name
    if logo is not None: wl["logo"] = logo
    if primary is not None: wl["primary"] = primary
    wl["updated_at"] = _now()
    _save_db(db)
    return wl

def sync_known_users():
    """Ensure users known by the main bot exist in the feature DB."""
    users_file = CFG.get("users_file", "users_city.json")
    try:
        if not os.path.exists(users_file):
            return 0
        with open(users_file, "r", encoding="utf-8") as f:
            users = json.load(f)
        if not isinstance(users, dict):
            return 0
        db = _db()
        changed = 0
        for uid in users:
            key = str(uid)
            if key not in db["users"]:
                db["users"][key] = {"first_seen": _now(), "last_seen": _now(), "source": "legacy"}
                changed += 1
        if changed:
            _save_db(db)
        return changed
    except Exception:
        return 0

def daily_notification_job():
    """Send scheduled notifications and independent weather alerts.
    Run this endpoint at least once per minute for exact HH:MM schedules.
    """
    sync_known_users()
    db = _db()
    now = datetime.utcnow()
    # DEFAULT_TIMEZONE is optional; when available use zoneinfo for user schedules.
    tz_name = os.getenv("DEFAULT_TIMEZONE", "UTC").strip() or "UTC"
    try:
        from zoneinfo import ZoneInfo
        local_now = datetime.now(ZoneInfo(tz_name))
    except Exception:
        local_now = now
    current_hm = local_now.strftime("%H:%M")
    today = local_now.strftime("%Y-%m-%d")
    sent = 0
    changed = False
    errors_count = 0

    # Rate limiting: максимум 100 пользователей за раз
    users_list = list(db.get("users", {}).items())[:100]

    for uid, profile in users_list:
        prefs = profile.get("notifications", {})
        city = _city(uid)
        if not city:
            continue
        weather_fn = CFG.get("get_weather_aggregated")
        if not weather_fn:
            continue
        try:
            w = weather_fn(city, _lang(uid))
            if not isinstance(w, dict) or "error" in w:
                continue

            # Regular daily notification.
            if (prefs.get("enabled")
                    and prefs.get("time", "08:00") == current_hm
                    and prefs.get("last_sent_date") != today):
                text = (f"🌤 *{city}*\n\n"
                        f"🌡 Температура: *{w.get('temp','—')}°C*\n"
                        f"☁️ {w.get('description','—')}\n"
                        f"💧 Влажность: *{w.get('humidity','—')}%*\n"
                        f"🌬 Ветер: *{w.get('wind_speed','—')} м/с* · *{w.get('wind_direction','—')}*")
                if prefs.get("rain") and float(w.get("rain", 0) or 0) > 0:
                    text += "\n" + _FT(uid, "daily_rain")
                if prefs.get("wind") and float(w.get("wind_speed", 0) or 0) >= 50:
                    text += "\n" + _FT(uid, "daily_wind")
                result = _send(uid, text)
                if result and result.get("ok"):
                    prefs["last_sent_date"] = today
                    sent += 1
                    changed = True

            # Weather notifications are independent from the daily notification.
            alert_prefs = prefs.get("alerts", {})
            if not alert_prefs:
                continue
            fired = set(prefs.get("fired_alerts", []))
            fired = {x for x in fired if x.startswith(today + ":")}
            desc = str(w.get("description", "")).casefold()
            messages = []
            rain_value = float(w.get("rain", 0) or 0)
            wind_value = float(w.get("wind_speed", 0) or 0)
            temp_value = float(w.get("temp")) if w.get("temp") is not None else None
            storm_detected = bool(w.get("storm")) or any(x in desc for x in ("thunder", "storm", "гроза", "tormenta", "orage", "雷暴"))
            heavy_rain_detected = bool(w.get("heavy_rain")) or rain_value >= float(alert_prefs.get("heavy_rain", {}).get("threshold") or 10)

            def enabled(kind):
                return alert_prefs.get(kind, {}).get("enabled", False)
            def threshold(kind, default):
                try: return float(alert_prefs.get(kind, {}).get("threshold"))
                except (TypeError, ValueError): return default

            if enabled("rain") and rain_value >= threshold("rain", 0.1) and f"{today}:rain" not in fired:
                messages.append(_FT(uid, "rain_expected")); fired.add(f"{today}:rain")
            if enabled("storm") and storm_detected and f"{today}:storm" not in fired:
                messages.append(_FT(uid, "storm_possible")); fired.add(f"{today}:storm")
            if enabled("wind") and wind_value >= threshold("wind", 15.0) and f"{today}:wind" not in fired:
                messages.append(_FT(uid, "strong_wind", wind=wind_value)); fired.add(f"{today}:wind")
            if enabled("heat") and temp_value is not None and temp_value >= threshold("heat", 30.0) and f"{today}:heat" not in fired:
                messages.append(_FT(uid, "high_temp", temp=temp_value)); fired.add(f"{today}:heat")
            if enabled("frost") and temp_value is not None and temp_value <= threshold("frost", 0.0) and f"{today}:frost" not in fired:
                messages.append(_FT(uid, "frost_warning", temp=temp_value)); fired.add(f"{today}:frost")
            if enabled("heavy_rain") and heavy_rain_detected and f"{today}:heavy_rain" not in fired:
                messages.append(_FT(uid, "heavy_rain_warning", rain=rain_value)); fired.add(f"{today}:heavy_rain")

            if messages:
                alert_result = _send(uid, "\n".join([_FT(uid, "weather_alert_title"), *messages]))
                if alert_result and alert_result.get("ok"):
                    prefs["fired_alerts"] = sorted(fired)
                    changed = True

        except Exception as exc:
            # Изолируем ошибку для каждого пользователя
            errors_count += 1
            logger.error(f"Ошибка обработки уведомлений для пользователя {uid}: {exc}")
            continue

    if changed:
        _save_db(db)
    if sent > 0 or errors_count > 0:
        logger.info(f"Уведомления: отправлено={sent}, ошибок={errors_count}")
    return sent

def process_due_channels():
    db = _db()
    current_hm = datetime.utcnow().strftime("%H:%M")
    posted = 0
    today = datetime.utcnow().strftime("%Y-%m-%d")
    for cid, ch in db.get("channels", {}).items():
        if not ch.get("enabled") or ch.get("schedule", "08:00") != current_hm:
            continue
        if str(ch.get("last_post", "")).startswith(today):
            continue
        result = post_weather_card(cid, ch.get("city"))
        if result.get("ok"):
            posted += 1
    return posted

def scheduled_job():
    return {"notifications": daily_notification_job(), "channels": process_due_channels()}

def segmented_broadcast(uid, segment, message):
    if not _admin(uid):
        return {"ok": False, "error": "forbidden"}
    users_path = CFG.get("users_file", "users_city.json")
    legacy = _load(users_path, {})
    db = _db()
    candidate = set(str(x) for x in legacy.keys()) | set(str(x) for x in db.get("users", {}).keys())
    subs_fn = CFG.get("is_user_subscribed")
    results = {"sent":0, "failed":0, "skipped":0, "total":len(candidate)}
    for target in candidate:
        profile = db.get("users", {}).get(target, {})
        if segment == "premium" and not (subs_fn and subs_fn(target)):
            results["skipped"] += 1; continue
        if segment == "free" and subs_fn and subs_fn(target):
            results["skipped"] += 1; continue
        if segment.startswith("source:") and profile.get("source") != segment[7:]:
            results["skipped"] += 1; continue
        if segment.startswith("lang:") and _lang(target) != segment[5:]:
            results["skipped"] += 1; continue
        if segment == "inactive7":
            last = profile.get("last_seen","")
            try:
                if datetime.utcnow() - datetime.fromisoformat(last.replace("Z","")) < timedelta(days=7):
                    results["skipped"] += 1; continue
            except Exception:
                results["skipped"] += 1; continue
        result = _send(target, message)
        if result and result.get("ok"): results["sent"] += 1
        else: results["failed"] += 1
    track(uid, "segmented_broadcast", {"segment":segment,"sent":results["sent"]})
    return results

def _admin(uid):
    fn = CFG.get("is_admin")
    return bool(fn and fn(uid))


FEATURE_TEXTS = {
    "ru": {
        "trip_button": "✈️ Откройте раздел «Поездка» и выберите город и срок кнопками.", "ai_button": "🤖 Откройте AI и напишите свой вопрос.",
        "help": "🌟 WeatherTomBot\n\n⭐ Города — сохранённые города\n🔔 Уведомления — погодные предупреждения\n✈️ Поездка — прогноз для поездки\n🤖 AI — погодный помощник\n💳 Тарифы — Free / Premium / Business\n\nВсе основные функции доступны через кнопки меню.",
        "favorites_title": "⭐ Города", "no_saved_cities": "Нет сохранённых городов.", "addcity_hint": "\n\nИспользуйте кнопки «Добавить город» и «Удалить город».",
        "favorite_added": "✅ Город добавлен.", "favorite_add_failed": "❌ Не удалось добавить ({result}).", "favorite_removed": "✅ Город удалён.", "city_not_found": "❌ Город не найден.",
        "alerts_title": "🔔 Уведомления", "alerts_hint": "\n\nВыберите нужное уведомление кнопкой.",
        "premium_alerts": "⭐ Погодные уведомления доступны по Premium.", "threshold_number": "❌ Порог должен быть числом.", "alert_set": "🌧 {kind}: {state}{suffix}",
        "premium_notifications": "⭐ Уведомления доступны по Premium.", "notifications_enabled": "🔔 Уведомления включены.", "notifications_disabled": "🔕 Уведомления выключены.", "notification_time": "⏰ Время уведомлений: {time}", "notification_time_usage": "Время уведомлений настраивается в разделе «Уведомления».",
        "premium_trip": "⭐ Туристические прогнозы доступны по Premium.", "trip_unavailable": "❌ Туристический прогноз недоступен.", "trip_title": "✈️ Прогноз поездки: {destination}",
        "premium_required": "⭐ Для этой функции требуется Premium.", "referral": "👥 Реферальная программа\n\nВаш код: {code}\nПриглашено: {count}\n🎁 Награда: 7 дней Premium\n\n{link}",
        "promo_applied": "🎁 Промокод активирован.", "promo_error": "❌ Ошибка промокода: {result}",
        "plans": "💰 Тарифы\n\n🆓 Free — текущая погода + базовые функции\n⭐ Premium — уведомления, города, поездки и AI\n💼 Business — каналы, API, white-label и команды",
        "broadcast_usage": "Используйте /broadcast_segment premium|free|inactive7|lang:en|source:NAME TEXT", "broadcast_done": "📢 Рассылка: {result}",
        "admin_only": "⛔ Только для администратора.", "channel_usage": "Используйте /channel @channel CITY [HH:MM]", "business_channel": "💼 Для автопубликации каналов требуется Business.", "channel_failed": "❌ Не удалось подключить канал.", "channel_connected": "📢 Канал подключён: {channel}\nГород: {city}\nВремя: {schedule}", "no_channels": "📢 Каналов нет. Используйте /channel @channel CITY 08:00", "channels_title": "📢 Каналы:",
        "card_unavailable": "❌ Генерация карточки недоступна.", "business_api": "💼 Для доступа к API требуется Business.", "api_created": "🔑 API-ключ создан (сохраните его сейчас):\n`{api_key}`", "api_usage": "Используйте /apikey для создания ключа.",
        "teams_title": "👥 Команды", "no_teams": "Нет команд", "team_created": "✅ Команда создана: {team}", "business_teams": "💼 Для команд требуется Business.", "member_added": "✅ Участник добавлен.", "member_failed": "❌ Не удалось добавить участника.",
        "white_label": "🏢 White-label\n{data}", "weather_alert_title": "⚠️ Погодное уведомление", "rain_expected": "☔ Ожидается дождь.", "storm_possible": "⛈ Возможна гроза или шторм.", "strong_wind": "💨 Сильный ветер: {wind}.", "low_temp": "🥶 Температура {temp}° или ниже.", "high_temp": "🔥 Жара: температура {temp}° или выше.", "heavy_rain_warning": "🌧️ Сильные осадки: {rain} мм.", "frost_warning": "❄️ Мороз: температура {temp}° или ниже.", "notification_settings_title": "🔔 Уведомления", "notification_usage": "Выберите нужное уведомление кнопкой.",
        "daily_rain": "☔ Ожидается дождь.", "daily_wind": "💨 Предупреждение о сильном ветре.",
    },
    "en": {
        "trip_button":"✈️ Open “Trip” and choose the city and duration with buttons.", "ai_button":"🤖 Откройте AI и напишите свой вопрос.", "help":"🌟 WeatherTomBot\n\n⭐ Cities — saved cities\n🔔 Notifications — weather warnings\n✈️ Trip — travel forecast\n🤖 AI — weather assistant\n💳 Plans — Free / Premium / Business\n\nUse the buttons in the menu for normal operation.",
        "favorites_title":"⭐ Cities", "no_saved_cities":"No saved cities.", "addcity_hint":"\n\nНажмите «➕ Добавить город», чтобы сохранить город.", "favorite_added":"✅ Added to favorites.", "favorite_add_failed":"❌ Could not add ({result}).", "favorite_removed":"✅ Removed.", "city_not_found":"❌ City not found.", "alerts_title":"🔔 Notifications", "alerts_hint":"\n\nChoose an alert with the buttons.", "premium_alerts":"⭐ Premium subscription required for weather notifications.", "threshold_number":"❌ Threshold must be a number.", "alert_set":"🌧 {kind}: {state}{suffix}", "premium_notifications":"⭐ Premium subscription required for notifications.", "notifications_enabled":"🔔 Notifications enabled.", "notifications_disabled":"🔕 Notifications disabled.", "notification_time":"⏰ Notification time: {time}", "notification_time_usage":"Use HH:MM, e.g. /notify_time 08:00", "premium_trip":"⭐ Premium subscription required for travel forecasts.", "trip_unavailable":"❌ Travel forecast unavailable.", "trip_title":"✈️ Trip forecast: {destination}", "premium_required":"⭐ Premium subscription required for this feature.", "referral":"👥 Referral program\n\nYour code: {code}\nInvited: {count}\n🎁 Reward: 7 days Premium\n\n{link}", "promo_applied":"🎁 Promo applied.", "promo_error":"❌ Promo error: {result}", "plans":"💰 Plans\n\n🆓 Free — current weather + basic features\n⭐ Premium — alerts, favorites, trips and AI\n💼 Business — channels, API, white-label, teams", "broadcast_usage":"Use /broadcast_segment premium|free|inactive7|lang:en|source:NAME TEXT", "broadcast_done":"📢 Broadcast: {result}", "admin_only":"⛔ Admin only.", "channel_usage":"Use /channel @channel CITY [HH:MM]", "business_channel":"💼 Business subscription required for channel auto-posting.", "channel_failed":"❌ Could not connect channel.", "channel_connected":"📢 Channel connected: {channel}\nCity: {city}\nTime: {schedule}", "no_channels":"📢 No channels. Use /channel @channel CITY 08:00", "channels_title":"📢 Channels:", "card_unavailable":"❌ Card generation unavailable.", "business_api":"💼 Business subscription required for API access.", "api_created":"🔑 API key created (store it now):\n`{api_key}`", "api_usage":"Use /apikey to generate a key.", "teams_title":"👥 Teams", "no_teams":"No teams", "team_created":"✅ Team created: {team}", "business_teams":"💼 Business subscription required for teams.", "member_added":"✅ Member added.", "member_failed":"❌ Cannot add member.", "white_label":"🏢 White-label\n{data}", "weather_alert_title":"⚠️ Weather notification", "rain_expected":"☔ Rain is expected.", "storm_possible":"⛈ Storm conditions are possible.", "strong_wind":"💨 Strong wind: {wind}.", "low_temp":"🥶 Temperature is {temp}° or lower.", "high_temp":"🔥 Heat warning: {temp}° or higher.", "heavy_rain_warning":"🌧️ Heavy rain: {rain} mm.", "frost_warning":"❄️ Frost warning: {temp}° or lower.", "notification_settings_title":"🔔 Notifications", "notification_usage":"Choose an alert with the buttons.", "daily_rain":"☔ Rain is expected.", "daily_wind":"💨 Strong wind warning."
    },
    "es": {
        "trip_button":"✈️ Abre «Viaje» y elige la ciudad y la duración con botones.", "ai_button":"🤖 Abre IA y escribe tu pregunta.", "help":"🌟 WeatherTomBot\n\n⭐ Ciudades — ciudades guardadas\n🔔 Notificaciones — alertas meteorológicas\n✈️ Viaje — pronóstico de viaje\n🤖 IA — asistente del tiempo\n💳 Planes — Free / Premium / Business\n\nUsa los botones del menú para operar el bot.",
        "favorites_title":"⭐ Ciudades", "no_saved_cities":"No hay ciudades guardadas.", "addcity_hint":"\n\nНажмите «➕ Добавить город», чтобы сохранить город.", "favorite_added":"✅ Añadida a favoritos.", "favorite_add_failed":"❌ No se pudo añadir ({result}).", "favorite_removed":"✅ Eliminada.", "city_not_found":"❌ Ciudad no encontrada.", "alerts_title":"🔔 Notificaciones", "alerts_hint":"\n\nElige una notificación con los botones.", "premium_alerts":"⭐ Las notificaciones requieren Premium.", "threshold_number":"❌ El umbral debe ser un número.", "alert_set":"🌧 {kind}: {state}{suffix}", "premium_notifications":"⭐ Las notificaciones requieren Premium.", "notifications_enabled":"🔔 Notificaciones activadas.", "notifications_disabled":"🔕 Notificaciones desactivadas.", "notification_time":"⏰ Hora de notificación: {time}", "notification_time_usage":"Usa HH:MM, por ejemplo /notify_time 08:00", "premium_trip":"⭐ Los pronósticos de viaje requieren Premium.", "trip_unavailable":"❌ Pronóstico de viaje no disponible.", "trip_title":"✈️ Pronóstico de viaje: {destination}", "premium_required":"⭐ Esta función requiere Premium.", "referral":"👥 Programa de referidos\n\nTu código: {code}\nInvitados: {count}\n🎁 Recompensa: 7 días Premium\n\n{link}", "promo_applied":"🎁 Promoción aplicada.", "promo_error":"❌ Error de promoción: {result}", "plans":"💰 Planes\n\n🆓 Free — tiempo actual + funciones básicas\n⭐ Premium — alertas, favoritos, viajes e IA\n💼 Business — canales, API, white-label y equipos", "broadcast_usage":"Usa /broadcast_segment premium|free|inactive7|lang:en|source:NAME TEXT", "broadcast_done":"📢 Difusión: {result}", "admin_only":"⛔ Solo para administradores.", "channel_usage":"Usa /channel @channel CITY [HH:MM]", "business_channel":"💼 Se requiere Business para publicar automáticamente en canales.", "channel_failed":"❌ No se pudo conectar el canal.", "channel_connected":"📢 Canal conectado: {channel}\nCiudad: {city}\nHora: {schedule}", "no_channels":"📢 No hay canales. Usa /channel @channel CITY 08:00", "channels_title":"📢 Canales:", "card_unavailable":"❌ Generación de tarjeta no disponible.", "business_api":"💼 Se requiere Business para acceder a la API.", "api_created":"🔑 Clave API creada (guárdala ahora):\n`{api_key}`", "api_usage":"Usa /apikey para generar una clave.", "teams_title":"👥 Equipos", "no_teams":"No hay equipos", "team_created":"✅ Equipo creado: {team}", "business_teams":"💼 Se requiere Business para los equipos.", "member_added":"✅ Miembro añadido.", "member_failed":"❌ No se pudo añadir al miembro.", "white_label":"🏢 White-label\n{data}", "weather_alert_title":"⚠️ Notificación meteorológica", "rain_expected":"☔ Se espera lluvia.", "storm_possible":"⛈ Posibles tormentas.", "strong_wind":"💨 Viento fuerte: {wind}.", "low_temp":"🥶 Aviso de frío: {temp}° o menos.", "high_temp":"🔥 Aviso de calor: {temp}° o más.", "heavy_rain_warning":"🌧️ Lluvia intensa: {rain} mm.", "frost_warning":"❄️ Helada: {temp}° o menos.", "notification_settings_title":"🔔 Notificaciones", "notification_usage":"Elige una notificación con los botones.", "daily_rain":"☔ Se espera lluvia.", "daily_wind":"💨 Aviso de viento fuerte."
    },
    "zh": {
        "trip_button":"✈️ 打开「旅行」，使用按钮选择城市和天数。", "ai_button":"🤖 打开 AI 并输入您的问题。", "help":"🌟 WeatherTomBot\n\n⭐ 城市 — 已保存城市\n🔔 通知 — 天气提醒\n✈️ 旅行 — 旅行预报\n🤖 AI — 天气助手\n💳 套餐 — Free / Premium / Business\n\n请使用菜单按钮操作。",
        "favorites_title":"⭐ 城市", "no_saved_cities":"暂无保存的城市。", "addcity_hint":"\n\nНажмите «➕ Добавить город», чтобы сохранить город.", "favorite_added":"✅ 已添加到收藏。", "favorite_add_failed":"❌ 添加失败（{result}）。", "favorite_removed":"✅ 已删除。", "city_not_found":"❌ 未找到城市。", "alerts_title":"🔔 通知", "alerts_hint":"\n\n请使用下方按钮选择通知。", "premium_alerts":"⭐ 天气通知需要 Premium。", "threshold_number":"❌ 阈值必须是数字。", "alert_set":"🌧 {kind}：{state}{suffix}", "premium_notifications":"⭐ 通知功能需要 Premium。", "notifications_enabled":"🔔 通知已开启。", "notifications_disabled":"🔕 通知已关闭。", "notification_time":"⏰ 通知时间：{time}", "notification_time_usage":"使用 HH:MM，例如 /notify_time 08:00", "premium_trip":"⭐ 旅行预报需要 Premium。", "trip_unavailable":"❌ 旅行预报不可用。", "trip_title":"✈️ 旅行预报：{destination}", "premium_required":"⭐ 此功能需要 Premium。", "referral":"👥 推荐计划\n\n您的代码：{code}\n邀请人数：{count}\n🎁 奖励：7 天 Premium\n\n{link}", "promo_applied":"🎁 优惠码已使用。", "promo_error":"❌ 优惠码错误：{result}", "plans":"💰 套餐\n\n🆓 Free — 当前天气 + 基础功能\n⭐ Premium — 警报、收藏、旅行和 AI\n💼 Business — 频道、API、白标和团队", "broadcast_usage":"使用 /broadcast_segment premium|free|inactive7|lang:en|source:NAME TEXT", "broadcast_done":"📢 群发：{result}", "admin_only":"⛔ 仅管理员可用。", "channel_usage":"使用 /channel @channel CITY [HH:MM]", "business_channel":"💼 频道自动发布需要 Business。", "channel_failed":"❌ 无法连接频道。", "channel_connected":"📢 频道已连接：{channel}\n城市：{city}\n时间：{schedule}", "no_channels":"📢 暂无频道。使用 /channel @channel CITY 08:00", "channels_title":"📢 频道：", "card_unavailable":"❌ 无法生成天气卡片。", "business_api":"💼 API 访问需要 Business。", "api_created":"🔑 API 密钥已创建（请立即保存）：\n`{api_key}`", "api_usage":"使用 /apikey 创建密钥。", "teams_title":"👥 团队", "no_teams":"暂无团队", "team_created":"✅ 团队已创建：{team}", "business_teams":"💼 团队功能需要 Business。", "member_added":"✅ 成员已添加。", "member_failed":"❌ 无法添加成员。", "white_label":"🏢 白标\n{data}", "weather_alert_title":"⚠️ 天气通知", "rain_expected":"☔ 预计有雨。", "storm_possible":"⛈ 可能出现雷暴。", "strong_wind":"💨 强风：{wind}。", "low_temp":"🥶 温度为 {temp}° 或更低。", "high_temp":"🔥 高温警告：{temp}° 或更高。", "heavy_rain_warning":"🌧️ 强降雨：{rain} 毫米。", "frost_warning":"❄️ 霜冻警告：{temp}° 或更低。", "notification_settings_title":"🔔 通知", "notification_usage":"请使用下方按钮选择通知。", "daily_rain":"☔ 预计有雨。", "daily_wind":"💨 强风警告。"
    }
}


FEATURE_TEXTS["ru"]["analytics"] = "📊 Аналитика\nДоход: {revenue:.2f}\nMRR: {mrr:.2f}\nARPU: {arpu:.2f}\nПлатежи: {payments}\nПлатящие пользователи: {paying_users}\n\nВоронка: {funnel}\nУдержание: {retention}\nИсточники: {sources}"
FEATURE_TEXTS["en"]["analytics"] = "📊 Analytics\nRevenue: {revenue:.2f}\nMRR: {mrr:.2f}\nARPU: {arpu:.2f}\nPayments: {payments}\nPaying users: {paying_users}\n\nFunnel: {funnel}\nRetention: {retention}\nSources: {sources}"
FEATURE_TEXTS["es"]["analytics"] = "📊 Analítica\nIngresos: {revenue:.2f}\nMRR: {mrr:.2f}\nARPU: {arpu:.2f}\nPagos: {payments}\nUsuarios de pago: {paying_users}\n\nEmbudo: {funnel}\nRetención: {retention}\nFuentes: {sources}"
FEATURE_TEXTS["zh"]["analytics"] = "📊 分析\n收入：{revenue:.2f}\nMRR：{mrr:.2f}\nARPU：{arpu:.2f}\n支付次数：{payments}\n付费用户：{paying_users}\n\n漏斗：{funnel}\n留存：{retention}\n来源：{sources}"


FEATURE_TEXTS["ru"]["api_menu"] = "🔑 *API Управление*\n\nВыберите действие:"
FEATURE_TEXTS["ru"]["api_key_created"] = "🔑 API-ключ создан:\n`{api_key}`\n\n📖 Документация: /api_help"
FEATURE_TEXTS["ru"]["api_city_set"] = "✅ Город по умолчанию для API: *{city}*"
FEATURE_TEXTS["ru"]["api_city_prompt"] = "🏙 Введите город по умолчанию для API запросов:"

FEATURE_TEXTS["en"]["api_menu"] = "🔑 *API Management*\n\nChoose an action:"
FEATURE_TEXTS["en"]["api_key_created"] = "🔑 API key created:\n`{api_key}`\n\n📖 Docs: /api_help"
FEATURE_TEXTS["en"]["api_city_set"] = "✅ Default API city: *{city}*"
FEATURE_TEXTS["en"]["api_city_prompt"] = "🏙 Enter default city for API requests:"

def _FT(uid, key, **kwargs):
    lang = _lang(uid)
    text = FEATURE_TEXTS.get(lang, FEATURE_TEXTS["en"]).get(key, FEATURE_TEXTS["en"].get(key, key))
    try:
        return text.format(**kwargs)
    except Exception:
        return text


FEATURE_BUTTONS = {
    "ru": {"favorites":"⭐ Города", "alerts":"🔔 Уведомления", "trip":"✈️ Поездка", "ai":"🤖 AI", "plans":"💰 Тарифы"},
    "en": {"favorites":"⭐ Cities", "alerts":"🔔 Notifications", "trip":"✈️ Trip", "ai":"🤖 AI", "plans":"💰 Plans"},
    "es": {"favorites":"⭐ Ciudades", "alerts":"🔔 Notificaciones", "trip":"✈️ Viaje", "ai":"🤖 IA", "plans":"💰 Planes"},
    "zh": {"favorites":"⭐ 城市", "alerts":"🔔 通知", "trip":"✈️ 旅行", "ai":"🤖 AI", "plans":"💰 套餐"},
}
def feature_button_action(uid, text):
    lang = _lang(uid)
    # Favorites/alerts are owned by bot.py's stateful UI. Do not consume
    # their buttons here, otherwise the main handler never sees them.
    for action, label in FEATURE_BUTTONS.get(lang, FEATURE_BUTTONS["en"]).items():
        if text == label:
            if action in ("favorites", "alerts", "trip"):
                return None
            return action
    return None

def _help(uid):
    return _FT(uid, "help")

def handle(uid, text):
    """Return True if this module consumed the incoming text."""
    if not uid or not text:
        return False
    raw = text.strip()
    low = raw.casefold()
    register_user(uid)
    button = feature_button_action(uid, raw)
    if button == "favorites":
        raw = "/favorites"; low = raw
    elif button == "alerts":
        raw = "/alerts"; low = raw
    elif button == "trip":
        return False
    elif button == "ai":
        _send(uid, _FT(uid, "ai_button")); return True
    elif button == "plans":
        raw = "/plans"; low = raw
    if low.startswith("/start"):
        param = raw.split(maxsplit=1)[1] if len(raw.split(maxsplit=1)) > 1 else ""
        if param.startswith("ref_"):
            process_referral(uid, param[4:])
        elif param:
            db = _db()
            db["users"].setdefault(str(uid), {})["source"] = param
            _save_db(db)
        return False

    if low in ("/features", "/menu_features", "🌟 функции"):
        _send(uid, _FT(uid, "help")); return True

    if low == "/favorites":
        favs = favorites(uid)
        _send(uid, _FT(uid, "favorites_title") + ":\n" +
              ("\n".join(f"• {x}" for x in favs) if favs else _FT(uid, "no_saved_cities")) +
              _FT(uid, "addcity_hint")); return True

    if low == "/addcity" or low.startswith("/addcity "):
        city = raw[8:].strip()
        if not city:
            _send(uid, _FT(uid, "addcity_hint")); return True
        ok, result = add_favorite(uid, city)
        _send(uid, _FT(uid, "favorite_added") if ok else _FT(uid, "favorite_add_failed", result=result)); return True

    if low == "/delcity" or low.startswith("/delcity "):
        city = raw[8:].strip()
        if not city:
            _send(uid, _FT(uid, "addcity_hint")); return True
        ok = remove_favorite(uid, city)
        _send(uid, _FT(uid, "favorite_removed") if ok else _FT(uid, "city_not_found")); return True

    if low in ("/alerts", "/notifications"):
        if not _premium(uid):
            _send(uid, _FT(uid, "premium_alerts")); return True
        a = alerts(uid)
        kinds = ("rain", "storm", "wind", "heat", "frost", "heavy_rain")
        lines = [f"• {k}: {'ON' if a.get(k, {}).get('enabled') else 'OFF'}" for k in kinds]
        _send(uid, _FT(uid, "notification_settings_title") + "\n" + "\n".join(lines) + _FT(uid, "alerts_hint")); return True

    if low in ("/alert", "/alert on"):
        if not _premium(uid):
            _send(uid, _FT(uid, "premium_alerts")); return True
        set_notification_prefs(uid, enabled=True)
        _send(uid, _FT(uid, "notifications_enabled") + "\n" + _FT(uid, "notification_usage")); return True

    if low.startswith("/alert "):
        if not _premium(uid):
            _send(uid, _FT(uid, "premium_alerts")); return True
        parts = raw.split()
        if len(parts) < 3:
            _send(uid, _FT(uid, "notification_usage")); return True
        kind = parts[1].lower()
        if kind not in ("rain", "storm", "wind", "heat", "frost", "heavy_rain"):
            _send(uid, _FT(uid, "notification_usage")); return True
        enabled = parts[2].lower() in ("on", "1", "yes", "true")
        threshold = None
        if len(parts) >= 4:
            try:
                threshold = float(parts[3])
            except ValueError:
                _send(uid, _FT(uid, "threshold_number")); return True
        defaults = {"rain": 0.1, "storm": None, "wind": 15.0, "heat": 30.0, "frost": 0.0, "heavy_rain": 10.0}
        set_alert(uid, kind, enabled, defaults[kind] if threshold is None else threshold)
        suffix = f" threshold={defaults[kind] if threshold is None else threshold:g}" if defaults[kind] is not None else ""
        _send(uid, _FT(uid, "alert_set", kind=kind, state="ON" if enabled else "OFF", suffix=suffix)); return True

    if low == "/notify_on":
        if not _premium(uid):
            _send(uid, _FT(uid, "premium_notifications")); return True
        set_notification_prefs(uid, enabled=True); _send(uid, _FT(uid, "notifications_enabled")); return True
    if low == "/notify_off":
        set_notification_prefs(uid, enabled=False); _send(uid, _FT(uid, "notifications_disabled")); return True

    if low.startswith("/notify_time "):
        if not _premium(uid):
            _send(uid, _FT(uid, "premium_notifications")); return True
        tm = raw.split(maxsplit=1)[1].strip()
        try:
            datetime.strptime(tm, "%H:%M")
            set_notification_prefs(uid, time=tm, enabled=True)
            _send(uid, _FT(uid, "notification_time", time=tm))
        except ValueError:
            _send(uid, _FT(uid, "notification_time_usage"))
        return True

    if low == "/trip" or low.startswith("/trip "):
        parts = raw.split()
        if len(parts) < 2:
            _send(uid, _FT(uid, "trip_button")); return True
        destination = parts[1]
        days = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 5
        result = trip_forecast(uid, destination, days)
        if result.get("error") == "premium_required":
            _send(uid, _FT(uid, "premium_trip"))
        elif "error" in result:
            _send(uid, _FT(uid, "trip_unavailable"))
        else:
            _send(uid, _FT(uid, "trip_title", destination=destination) + "\n\n" + json.dumps(result, ensure_ascii=False)[:3500])
        return True

    if low == "/ai" or low.startswith("/ai "):
        question = raw[3:].strip()
        if not question:
            _send(uid, _FT(uid, "ai_button")); return True
        answer, err = ai_answer(uid, question)
        _send(uid, f"🤖 {answer}" if answer else _FT(uid, "trip_unavailable"))
        return True

    if low == "/referral":
        code, count = referral_info(uid)
        bot_username = os.getenv("BOT_USERNAME", "")
        link = f"https://t.me/{bot_username}?start=ref_{code}" if bot_username else f"/start ref_{code}"
        _send(uid, _FT(uid, "referral", code=code, count=count, link=link))
        return True

    if low.startswith("/promo "):
        ok, result = apply_promo(uid, raw.split(maxsplit=1)[1])
        _send(uid, _FT(uid, "promo_applied") if ok else _FT(uid, "promo_error", result=result))
        return True


    if low in ("/api", "/api_help"):
        if not _business(uid):
            _send(uid, _FT(uid, "business_api"))
            return True
        if low == "/api":
            _send(uid, _FT(uid, "api_menu"))
        else:
            default_city = get_api_default_city(uid) or "не установлен"
            msg = "📖 API Документация\n\nGET /weather?city=Город\nGET /forecast?city=Город&days=5\nGET /me\n\nГород по умолчанию: " + default_city
            _send(uid, msg)
        return True

    if low.startswith("/api_city"):
        if not _business(uid):
            _send(uid, _FT(uid, "business_api"))
            return True
        parts = raw.split(maxsplit=1)
        if len(parts) < 2:
            _send(uid, _FT(uid, "api_city_prompt"))
            return True
        city = parts[1].strip()
        set_api_default_city(uid, city)
        _send(uid, _FT(uid, "api_city_set", city=city))
        return True

    if low == "/plans":
        _send(uid, _FT(uid, "plans"))
        return True

    if low.startswith("/broadcast_segment "):
        parts = raw.split(maxsplit=2)
        if len(parts) < 3:
            _send(uid, _FT(uid, "broadcast_usage"))
            return True
        result = segmented_broadcast(uid, parts[1], parts[2])
        _send(uid, _FT(uid, "broadcast_done", result=result))
        return True

    if low == "/analytics":
        if not _admin(uid):
            _send(uid, _FT(uid, "admin_only")); return True
        r = revenue_stats(); f = funnel_stats()
        ret = [retention(x) for x in (1,7,30)]
        src = source_stats()
        _send(uid, _FT(uid, "analytics", revenue=r['revenue'], mrr=r['mrr'], arpu=r['arpu'],
                        payments=r['payments'], paying_users=r['paying_users'], funnel=f,
                        retention=ret, sources=src))
        return True

    if low.startswith("/channel "):
        parts = raw.split()
        if len(parts) < 2:
            _send(uid, _FT(uid, "channel_usage")); return True
        channel_id = parts[1]
        city = parts[2] if len(parts) > 2 else _city(uid)
        schedule = parts[3] if len(parts) > 3 else "08:00"
        if not _business(uid):
            _send(uid, _FT(uid, "business_channel"))
            return True
        result = add_channel(uid, channel_id, channel_id, city, schedule)
        if not result:
            _send(uid, _FT(uid, "channel_failed"))
        else:
            _send(uid, _FT(uid, "channel_connected", channel=channel_id, city=city, schedule=schedule))
        return True

    if low == "/channels":
        if not _business(uid):
            _send(uid, _FT(uid, "business_channel")); return True
        db = _db()
        mine = {k:v for k,v in db["channels"].items() if str(v.get("owner")) == str(uid)}
        if not mine: _send(uid, _FT(uid, "no_channels"))
        else: _send(uid, _FT(uid, "channels_title") + "\n" + "\n".join(f"{k} — {v.get('city')} @ {v.get('schedule')}" for k,v in mine.items()))
        return True

    if low.startswith("/generate_card "):
        if not _business(uid):
            _send(uid, _FT(uid, "business_channel")); return True
        city = raw.split(maxsplit=1)[1]
        fn = CFG.get("get_weather_aggregated")
        w = fn(city, _lang(uid)) if fn else {"error":"weather"}
        path = generate_weather_card(w, city) if "error" not in w else None
        if path:
            # Telegram sendPhoto
            token = os.getenv("TELEGRAM_TOKEN","")
            try:
                with open(path,"rb") as f:
                    __import__("requests").post(f"https://api.telegram.org/bot{token}/sendPhoto",
                        data={"chat_id":uid,"caption":f"🌤 {city}"}, files={"photo":f}, timeout=60)
            except Exception: _send(uid, _FT(uid, "card_unavailable"))
        else: _send(uid, _FT(uid, "card_unavailable"))
        return True

    if low.startswith("/apikey"):
        if low == "/apikey":
            raw_key, key_info = create_api_key(uid)
            key = raw_key
            if not key:
                _send(uid, _FT(uid, "business_api"))
            else:
                _send(uid, _FT(uid, "api_created", api_key=key))
        else:
            _send(uid, _FT(uid, "api_usage"))
        return True

    if low.startswith("/team"):
        if not _business(uid):
            _send(uid, _FT(uid, "business_teams")); return True
        parts = raw.split(maxsplit=2)
        if len(parts) == 1:
            teams = team_for(uid)
            _send(uid, _FT(uid, "teams_title") + "\n" + ("\n".join(f"{k}: {v.get('name')}" for k,v in teams.items()) or _FT(uid, "no_teams")))
        elif parts[1].lower() == "create" and len(parts) == 3:
            tid = create_team(uid, parts[2])
            _send(uid, _FT(uid, "team_created", team=tid) if tid else _FT(uid, "business_teams"))
        elif parts[1].lower() == "add" and len(parts) == 3:
            x = parts[2].split()
            if len(x) >= 2 and add_team_member(uid, x[0], x[1], x[2] if len(x)>2 else "viewer"):
                _send(uid, _FT(uid, "member_added"))
            else: _send(uid, _FT(uid, "member_failed"))
        return True

    if low.startswith("/white_label"):
        if not _business(uid):
            _send(uid, _FT(uid, "business_channel")); return True
        parts = raw.split(maxsplit=1)
        if len(parts) == 1:
            _send(uid, _FT(uid, "white_label", data=json.dumps(_db()["white_labels"].get(str(uid), {}), ensure_ascii=False)))
        else:
            value = parts[1]
            result = set_white_label(uid, name=value)
            _send(uid, json.dumps(result, ensure_ascii=False))
        return True

    return False

def register_routes(app):
    @app.route("/api/v1/weather", methods=["GET"])
    def api_weather():
        item = verify_api_key(request.headers.get("X-API-Key") or request.args.get("api_key"))
        if not item: return jsonify({"ok":False,"error":"invalid_api_key"}), 401
        city = request.args.get("city")
        if not city:
            city = get_api_default_city(item["owner"])
        if not city: return jsonify({"ok":False,"error":"city_required"}), 400
        fn = CFG.get("get_weather_aggregated")
        if not fn: return jsonify({"ok":False,"error":"weather_unavailable"}), 503
        result = fn(city, _lang(item["owner"]))
        return jsonify({"ok":True,"city":city,"weather":result})

    @app.route("/api/v1/forecast", methods=["GET"])
    def api_forecast():
        item = verify_api_key(request.headers.get("X-API-Key") or request.args.get("api_key"))
        if not item: return jsonify({"ok":False,"error":"invalid_api_key"}), 401
        city = request.args.get("city")
        try:
            days = min(max(int(request.args.get("days",5)),1),10)
        except (ValueError, TypeError):
            return jsonify({"ok":False,"error":"invalid_days"}), 400
        fn = CFG.get("get_forecast_aggregated")
        if not city or not fn: return jsonify({"ok":False,"error":"city_required"}), 400
        return jsonify({"ok":True,"city":city,"forecast":fn(city, days, _lang(item["owner"]))})

    @app.route("/api/v1/me", methods=["GET"])
    def api_me():
        item = verify_api_key(request.headers.get("X-API-Key") or request.args.get("api_key"))
        if not item: return jsonify({"ok":False,"error":"invalid_api_key"}), 401
        uid=item["owner"]; db=_db()
        own = [x for x in db.get("payments", {}).values()
               if str(x.get("user_id")) == str(uid) and x.get("status") == "paid"]
        total = sum(float(x.get("amount", 0) or 0) for x in own)
        return jsonify({"ok":True,"user_id":uid,"profile":db["users"].get(uid,{}),
                        "payments":{"count":len(own),"total":total}})

    @app.route("/api/v1/admin/analytics", methods=["GET"])
    def api_admin_analytics():
        item = verify_api_key(request.headers.get("X-API-Key") or request.args.get("api_key"))
        if not item or not _admin(item["owner"]): return jsonify({"ok":False,"error":"forbidden"}), 403
        return jsonify({"ok":True,"revenue":revenue_stats(),"funnel":funnel_stats(),
                        "retention":[retention(x) for x in (1,7,30)],"sources":source_stats()})

    def _dashboard_ok():
        try:
            from flask import session
            return bool(session.get("logged_in"))
        except Exception:
            return False

    @app.route("/dashboard/channels", methods=["GET"])
    def channel_dashboard():
        if not _dashboard_ok():
            return jsonify({"ok":False,"error":"login_required"}), 401
        db = _db()
        channels = db.get("channels", {})
        return jsonify({"ok":True,"channels":channels})

    @app.route("/dashboard/analytics", methods=["GET"])
    def business_dashboard():
        if not _dashboard_ok():
            return jsonify({"ok":False,"error":"login_required"}), 401
        return jsonify({"ok":True,"revenue":revenue_stats(),"funnel":funnel_stats(),
                        "retention":[retention(x) for x in (1,7,30)],
                        "sources":source_stats()})

    @app.route("/dashboard/white-label", methods=["GET","POST"])
    def white_label_dashboard():
        if not _dashboard_ok():
            return jsonify({"ok":False,"error":"login_required"}), 401
        # Admin dashboard manages a selected Business user.
        try:
            from flask import session
            if not _admin(session.get("admin_user_id", "")):
                # Backward-compatible admin session: the legacy login has no user id.
                pass
        except Exception:
            pass
        payload = request.get_json(silent=True) or request.form.to_dict()
        uid = str(request.args.get("user_id") or payload.get("user_id") or "").strip()
        if not uid:
            return jsonify({"ok":False,"error":"user_id_required"}), 400
        if request.method == "GET":
            return jsonify({"ok":True,"white_label":_db().get("white_labels",{}).get(uid,{})})
        if not _business(uid):
            return jsonify({"ok":False,"error":"business_required"}), 403
        return jsonify({"ok":True,"white_label":set_white_label(
            uid, payload.get("name"), payload.get("logo"), payload.get("primary")
        )})

    @app.route("/cron/weather", methods=["GET","POST"])
    def cron_weather():
        secret = os.getenv("CRON_SECRET","").strip()
        provided = request.headers.get("X-Cron-Secret","") or request.args.get("secret","")
        if not secret:
            return jsonify({"ok":False,"error":"cron_secret_not_configured"}), 503
        if not provided or not secrets.compare_digest(provided, secret):
            return jsonify({"ok":False,"error":"forbidden"}), 403
        result=scheduled_job()
        return jsonify({"ok":True,**result})

    @app.route("/admin/features", methods=["GET"])
    def feature_health():
        key = request.headers.get("X-API-Key") or request.args.get("api_key")
        item = verify_api_key(key)
        if not item or not _admin(item["owner"]):
            return jsonify({"ok":False,"error":"forbidden"}), 403
        return jsonify({"ok":True,"features":"retention+monetization+marketing+b2b",
                        "ai_configured":bool(AI_API_KEY),
                        "api":"v1","generated_media":MEDIA_DIR})

def on_successful_payment(uid, payload, amount, currency="XTR"):
    record_payment(uid, payload, amount, currency)
    return True
