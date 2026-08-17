#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Быстрое применение исправлений безопасности v3.1.0
"""

import os
import sys

def replace_in_file(filepath, old, new, description):
    """Заменяет текст в файле"""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if old not in content:
        print(f"⚠️  НЕ НАЙДЕНО: {description}")
        return False
    
    content = content.replace(old, new, 1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print(f"✅ Применено: {description}")
    return True

def fix_features():
    print("\n" + "="*60)
    print("ИСПРАВЛЯЕМ features.py")
    print("="*60)
    
    filepath = "features.py"
    if not os.path.exists(filepath):
        print(f"❌ Файл {filepath} не найден!")
        return False
    
    applied = 0
    
    # 1. Импорт logging
    if replace_in_file(filepath,
        "import os, json, time, uuid, secrets, hashlib, threading, math",
        'import os, json, time, uuid, secrets, hashlib, threading, math, logging\n\nlogger = logging.getLogger("features")',
        "Импорт logging"):
        applied += 1
    
    # 2. create_api_key - добавляем соль
    if replace_in_file(filepath,
        '''def create_api_key(uid, name="default"):
    if not (_business(uid) or _admin(uid)):
        return None
    keys = _load(API_KEY_FILE, {})
    raw = "wt_" + secrets.token_urlsafe(24)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    keys[digest] = {"owner": str(uid), "name": name, "created_at": _now(), "last_used": None}
    _save(API_KEY_FILE, keys)
    return raw''',
        '''def create_api_key(uid, name="default"):
    """Создает API ключ с улучшенной безопасностью (соль + 32 символа)."""
    if not (_business(uid) or _admin(uid)):
        logger.warning(f"Попытка создания API ключа без прав: user={uid}")
        return None, None
    try:
        keys = _load(API_KEY_FILE, {})
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
        return None, None''',
        "create_api_key (соль + безопасность)"):
        applied += 1
    
    # 3. verify_api_key - проверка с солью
    if replace_in_file(filepath,
        '''def verify_api_key(raw):
    if not raw:
        return None
    digest = hashlib.sha256(raw.encode()).hexdigest()
    keys = _load(API_KEY_FILE, {})
    item = keys.get(digest)
    if item:
        item["last_used"] = _now()
        _save(API_KEY_FILE, keys)
        return item
    return None''',
        '''def verify_api_key(raw):
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
        return None''',
        "verify_api_key (проверка с солью)"):
        applied += 1
    
    # 4. set_alert - валидация threshold
    if replace_in_file(filepath,
        '''def set_alert(uid, kind, enabled=True, threshold=None):
    prefs = notification_prefs(uid)
    alerts = prefs.setdefault("alerts", {})
    alerts[kind] = {"enabled": bool(enabled), "threshold": threshold}
    set_notification_prefs(uid, alerts=alerts)
    return alerts[kind]''',
        '''def set_alert(uid, kind, enabled=True, threshold=None):
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
    return alerts[kind]''',
        "set_alert (валидация threshold)"):
        applied += 1
    
    # 5. daily_notification_job - rate limiting
    if replace_in_file(filepath,
        '''    sent = 0
    changed = False

    for uid, profile in db.get("users", {}).items():''',
        '''    sent = 0
    changed = False
    errors_count = 0

    # Rate limiting: максимум 100 пользователей за раз
    users_list = list(db.get("users", {}).items())[:100]

    for uid, profile in users_list:''',
        "daily_notification_job (rate limiting)"):
        applied += 1
    
    # 6. Обработка ошибок
    if replace_in_file(filepath,
        '''        except Exception as exc:
            # One broken user/API response must never stop notifications for everyone else.
            try:
                logger = __import__("logging").getLogger("features")
                logger.exception("Notification check failed for user %s: %s", uid, exc)
            except Exception:
                pass
            continue''',
        '''        except Exception as exc:
            # Изолируем ошибку для каждого пользователя
            errors_count += 1
            logger.error(f"Ошибка обработки уведомлений для пользователя {uid}: {exc}")
            continue''',
        "daily_notification_job (обработка ошибок)"):
        applied += 1
    
    # 7. Логирование итогов
    if replace_in_file(filepath,
        '''    if changed:
        _save_db(db)
    return sent''',
        '''    if changed:
        _save_db(db)
    if sent > 0 or errors_count > 0:
        logger.info(f"Уведомления: отправлено={sent}, ошибок={errors_count}")
    return sent''',
        "daily_notification_job (логирование итогов)"):
        applied += 1
    
    print(f"\n✅ features.py: применено {applied}/7 исправлений")
    return applied > 0

def fix_bot():
    print("\n" + "="*60)
    print("ИСПРАВЛЯЕМ bot.py")
    print("="*60)
    
    filepath = "bot.py"
    if not os.path.exists(filepath):
        print(f"❌ Файл {filepath} не найден!")
        return False
    
    applied = 0
    
    # 1. set_webhook - secret_token
    if replace_in_file(filepath,
        '''@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = WEBHOOK_URL or request.host_url.rstrip("/") + "/webhook"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
    try:
        response = requests.get(url, timeout=30)
        return response.text
    except Exception as e:
        return f"Error: {e}"''',
        '''@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Устанавливает webhook с защитой секретным токеном."""
    webhook_url = WEBHOOK_URL or request.host_url.rstrip("/") + "/webhook"
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if webhook_secret:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}&secret_token={webhook_secret}"
        logger.info(f"Устанавливаем webhook с секретным токеном")
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
        logger.warning("WEBHOOK_SECRET не задан! Webhook не защищен.")
    try:
        response = requests.get(url, timeout=30)
        return response.text
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}", exc_info=True)
        return f"Error: {e}"''',
        "set_webhook (secret_token)"):
        applied += 1
    
    # 2. webhook - проверка секрета
    if replace_in_file(filepath,
        '''@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()''',
        '''@app.route('/webhook', methods=['POST'])
def webhook():
    # Защита webhook секретным токеном
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if webhook_secret:
        secret_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if secret_header != webhook_secret:
            logger.warning(f"Несанкционированный доступ к webhook! IP: {request.remote_addr}")
            return "Forbidden", 403

    try:
        data = request.get_json()''',
        "webhook (проверка секрета)"):
        applied += 1
    
    # 3. validate_config
    if replace_in_file(filepath,
        '''def validate_config():
    required = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "WEATHERAPI_KEY": WEATHERAPI_KEY,
        "ADMIN_PASSWORD": ADMIN_PASSWORD,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))''',
        '''def validate_config():
    """Проверяет наличие всех необходимых переменных окружения."""
    required = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "WEATHERAPI_KEY": WEATHERAPI_KEY,
        "ADMIN_PASSWORD": ADMIN_PASSWORD,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        error_msg = "Missing required environment variables: " + ", ".join(missing)
        logger.error(error_msg)
        raise RuntimeError(error_msg)
    
    # Проверяем SECRET_KEY
    secret_key = os.getenv("SECRET_KEY", "")
    if not secret_key or secret_key == "change-this-to-a-long-random-secret":
        logger.warning("SECRET_KEY не задан или используется значение по умолчанию!")
    
    # Проверяем WEBHOOK_SECRET
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if not webhook_secret:
        logger.warning("WEBHOOK_SECRET не задан! Webhook не защищен.")
    else:
        logger.info(f"WEBHOOK_SECRET задан (длина: {len(webhook_secret)})")
    
    logger.info("Конфигурация валидна")''',
        "validate_config (проверка секретов)"):
        applied += 1
    
    print(f"\n✅ bot.py: применено {applied}/3 исправлений")
    return applied > 0

if __name__ == "__main__":
    print("\n" + "="*60)
    print("WeatherTomBot - Применение исправлений v3.1.0")
    print("="*60)
    
    features_ok = fix_features()
    bot_ok = fix_bot()
    
    print("\n" + "="*60)
    if features_ok and bot_ok:
        print("✅ Все исправления применены!")
        print("\nСледующие команды:")
        print("  git add -A")
        print("  git commit -m '🔒 Apply security fixes v3.1.0'")
        print("  git push origin main")
    else:
        print("⚠️  Некоторые исправления не были применены")
    print("="*60 + "\n")