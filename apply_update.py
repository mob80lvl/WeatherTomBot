#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
WeatherTomBot Auto-Updater v3.1.0
==================================
Автоматически применяет все исправления безопасности и багов.

Использование:
    python apply_update.py

Что делает:
    1. Создаёт резервные копии bot.py и features.py
    2. Применяет все исправления
    3. Проверяет синтаксис результата
    4. Выводит отчёт
"""

import os
import sys
import ast
import shutil
from datetime import datetime

# ============================================================
#  КОНФИГУРАЦИЯ
# ============================================================
BOT_FILE = "bot.py"
FEATURES_FILE = "features.py"
BACKUP_SUFFIX = ".backup_" + datetime.now().strftime("%Y%m%d_%H%M%S")

# ============================================================
#  УТИЛИТЫ
# ============================================================
def log(msg, level="INFO"):
    icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌"}
    print(f"{icons.get(level, '  ')} {msg}")

def backup_file(filepath):
    """Создаёт резервную копию файла."""
    if os.path.exists(filepath):
        backup = filepath + BACKUP_SUFFIX
        shutil.copy2(filepath, backup)
        log(f"Резервная копия: {backup}")
        return backup
    return None

def check_syntax(filepath):
    """Проверяет синтаксис Python-файла."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            source = f.read()
        ast.parse(source)
        return True, None
    except SyntaxError as e:
        return False, str(e)

def replace_in_file(filepath, old, new, description):
    """Заменяет текст в файле. Возвращает True если замена успешна."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if old not in content:
        log(f"НЕ НАЙДЕНО: {description}", "WARN")
        return False
    
    content = content.replace(old, new, 1)
    
    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(content)
    
    log(f"Применено: {description}", "OK")
    return True

# ============================================================
#  ИСПРАВЛЕНИЯ ДЛЯ features.py
# ============================================================
def fix_features():
    """Применяет все исправления к features.py."""
    log("=" * 60)
    log("ИСПРАВЛЯЕМ features.py")
    log("=" * 60)
    
    filepath = FEATURES_FILE
    if not os.path.exists(filepath):
        log(f"Файл {filepath} не найден!", "ERROR")
        return False
    
    backup_file(filepath)
    applied = 0
    
    # --- Исправление 1: Импорт логирования ---
    old_import = "import os, json, time, uuid, secrets, hashlib, threading, math"
    new_import = """import os, json, time, uuid, secrets, hashlib, threading, math, logging

logger = logging.getLogger("features")"""
    
    if replace_in_file(filepath, old_import, new_import, "Импорт logging"):
        applied += 1
    
    # --- Исправление 2: create_api_key ---
    old_create = '''def create_api_key(uid, name="default"):
    if not (_business(uid) or _admin(uid)):
        return None
    keys = _load(API_KEY_FILE, {})
    raw = "wt_" + secrets.token_urlsafe(24)
    digest = hashlib.sha256(raw.encode()).hexdigest()
    keys[digest] = {"owner": str(uid), "name": name, "created_at": _now(), "last_used": None}
    _save(API_KEY_FILE, keys)
    return raw'''
    
    new_create = '''def create_api_key(uid, name="default"):
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
        return None, None'''
    
    if replace_in_file(filepath, old_create, new_create, "create_api_key (соль + безопасность)"):
        applied += 1
    
    # --- Исправление 3: verify_api_key ---
    old_verify = '''def verify_api_key(raw):
    if not raw:
        return None
    digest = hashlib.sha256(raw.encode()).hexdigest()
    keys = _load(API_KEY_FILE, {})
    item = keys.get(digest)
    if item:
        item["last_used"] = _now()
        _save(API_KEY_FILE, keys)
        return item
    return None'''
    
    new_verify = '''def verify_api_key(raw):
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
        return None'''
    
    if replace_in_file(filepath, old_verify, new_verify, "verify_api_key (проверка с солью)"):
        applied += 1
    
    # --- Исправление 4: set_alert ---
    old_alert = '''def set_alert(uid, kind, enabled=True, threshold=None):
    prefs = notification_prefs(uid)
    alerts = prefs.setdefault("alerts", {})
    alerts[kind] = {"enabled": bool(enabled), "threshold": threshold}
    set_notification_prefs(uid, alerts=alerts)
    return alerts[kind]'''
    
    new_alert = '''def set_alert(uid, kind, enabled=True, threshold=None):
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
    return alerts[kind]'''
    
    if replace_in_file(filepath, old_alert, new_alert, "set_alert (валидация threshold)"):
        applied += 1
    
    # --- Исправление 5: daily_notification_job (rate limiting) ---
    old_loop_start = '''    sent = 0
    changed = False

    for uid, profile in db.get("users", {}).items():'''
    
    new_loop_start = '''    sent = 0
    changed = False
    errors_count = 0

    # Rate limiting: максимум 100 пользователей за раз
    users_list = list(db.get("users", {}).items())[:100]

    for uid, profile in users_list:'''
    
    if replace_in_file(filepath, old_loop_start, new_loop_start, "daily_notification_job (rate limiting)"):
        applied += 1
    
    # --- Исправление 6: Обработка ошибок в daily_notification_job ---
    old_error = '''        except Exception as exc:
            # One broken user/API response must never stop notifications for everyone else.
            try:
                logger = __import__("logging").getLogger("features")
                logger.exception("Notification check failed for user %s: %s", uid, exc)
            except Exception:
                pass
            continue'''
    
    new_error = '''        except Exception as exc:
            # Изолируем ошибку для каждого пользователя
            errors_count += 1
            logger.error(f"Ошибка обработки уведомлений для пользователя {uid}: {exc}")
            continue'''
    
    if replace_in_file(filepath, old_error, new_error, "daily_notification_job (обработка ошибок)"):
        applied += 1
    
    # --- Исправление 7: Конец daily_notification_job ---
    old_end = '''    if changed:
        _save_db(db)
    return sent'''
    
    new_end = '''    if changed:
        _save_db(db)
    if sent > 0 or errors_count > 0:
        logger.info(f"Уведомления: отправлено={sent}, ошибок={errors_count}")
    return sent'''
    
    if replace_in_file(filepath, old_end, new_end, "daily_notification_job (логирование итогов)"):
        applied += 1
    
    log(f"features.py: применено {applied}/7 исправлений", "OK")
    return applied > 0

# ============================================================
#  ИСПРАВЛЕНИЯ ДЛЯ bot.py
# ============================================================
def fix_bot():
    """Применяет все исправления к bot.py."""
    log("")
    log("=" * 60)
    log("ИСПРАВЛЯЕМ bot.py")
    log("=" * 60)
    
    filepath = BOT_FILE
    if not os.path.exists(filepath):
        log(f"Файл {filepath} не найден!", "ERROR")
        return False
    
    backup_file(filepath)
    applied = 0
    
    # --- Исправление 1: set_webhook ---
    old_webhook_set = '''@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    webhook_url = WEBHOOK_URL or request.host_url.rstrip("/") + "/webhook"
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
    try:
        response = requests.get(url, timeout=30)
        return response.text
    except Exception as e:
        return f"Error: {e}"'''
    
    new_webhook_set = '''@app.route('/set_webhook', methods=['GET'])
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
        return f"Error: {e}"'''
    
    if replace_in_file(filepath, old_webhook_set, new_webhook_set, "set_webhook (secret_token)"):
        applied += 1
    
    # --- Исправление 2: Проверка секрета в webhook ---
    old_webhook_start = '''@app.route('/webhook', methods=['POST'])
def webhook():
    try:
        data = request.get_json()'''
    
    new_webhook_start = '''@app.route('/webhook', methods=['POST'])
def webhook():
    # Защита webhook секретным токеном
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if webhook_secret:
        secret_header = request.headers.get('X-Telegram-Bot-Api-Secret-Token')
        if secret_header != webhook_secret:
            logger.warning(f"Несанкционированный доступ к webhook! IP: {request.remote_addr}")
            return "Forbidden", 403

    try:
        data = request.get_json()'''
    
    if replace_in_file(filepath, old_webhook_start, new_webhook_start, "webhook (проверка секрета)"):
        applied += 1
    
    # --- Исправление 3: validate_config ---
    old_validate = '''def validate_config():
    required = {
        "TELEGRAM_TOKEN": TELEGRAM_TOKEN,
        "OPENWEATHER_API_KEY": OPENWEATHER_API_KEY,
        "WEATHERAPI_KEY": WEATHERAPI_KEY,
        "ADMIN_PASSWORD": ADMIN_PASSWORD,
    }
    missing = [name for name, value in required.items() if not value]
    if missing:
        raise RuntimeError("Missing required environment variables: " + ", ".join(missing))'''
    
    new_validate = '''def validate_config():
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
    
    logger.info("Конфигурация валидна")'''
    
    if replace_in_file(filepath, old_validate, new_validate, "validate_config (проверка секретов)"):
        applied += 1
    
    log(f"bot.py: применено {applied}/3 исправлений", "OK")
    return applied > 0

# ============================================================
#  ОБНОВЛЕНИЕ .env
# ============================================================
def fix_env():
    """Добавляет недостающие переменные в .env."""
    log("")
    log("=" * 60)
    log("ОБНОВЛЯЕМ .env")
    log("=" * 60)
    
    env_file = ".env"
    if not os.path.exists(env_file):
        log("Файл .env не найден! Пропускаем.", "WARN")
        return False
    
    backup_file(env_file)
    
    with open(env_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    changes = []
    
    # Добавляем WEBHOOK_SECRET если его нет
    if "WEBHOOK_SECRET" not in content:
        import secrets
        webhook_secret = secrets.token_hex(32)
        content += f"\nWEBHOOK_SECRET={webhook_secret}\n"
        changes.append(f"WEBHOOK_SECRET добавлен: {webhook_secret[:8]}...")
    
    # Проверяем SECRET_KEY
    if "SECRET_KEY=" in content:
        for line in content.split('\n'):
            if line.startswith("SECRET_KEY="):
                value = line.split("=", 1)[1].strip()
                if not value or value == "change-this-to-a-long-random-secret":
                    import secrets
                    new_secret = secrets.token_hex(32)
                    content = content.replace(line, f"SECRET_KEY={new_secret}")
                    changes.append(f"SECRET_KEY обновлён: {new_secret[:8]}...")
                break
    else:
        import secrets
        new_secret = secrets.token_hex(32)
        content += f"\nSECRET_KEY={new_secret}\n"
        changes.append(f"SECRET_KEY добавлен: {new_secret[:8]}...")
    
    with open(env_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    if changes:
        for c in changes:
            log(c, "OK")
    else:
        log(".env уже содержит все необходимые переменные", "OK")
    
    return True

# ============================================================
#  ГЛАВНАЯ ФУНКЦИЯ
# ============================================================
def main():
    print("")
    print("╔══════════════════════════════════════════════════════════╗")
    print("║     WeatherTomBot Auto-Updater v3.1.0                   ║")
    print("║     Безопасность + Исправление багов                    ║")
    print("╚══════════════════════════════════════════════════════════╝")
    print("")
    
    # Проверяем, что мы в правильной папке
    if not os.path.exists(BOT_FILE):
        log(f"Файл {BOT_FILE} не найден в текущей директории!", "ERROR")
        log("Запустите скрипт в папке проекта WeatherTomBot", "ERROR")
        sys.exit(1)
    
    # Применяем исправления
    features_ok = fix_features()
    bot_ok = fix_bot()
    env_ok = fix_env()
    
    # Проверяем синтаксис
    log("")
    log("=" * 60)
    log("ПРОВЕРКА СИНТАКСИСА")
    log("=" * 60)
    
    all_ok = True
    
    for filepath in [FEATURES_FILE, BOT_FILE]:
        valid, error = check_syntax(filepath)
        if valid:
            log(f"{filepath}: синтаксис корректен", "OK")
        else:
            log(f"{filepath}: ОШИБКА СИНТАКСИСА: {error}", "ERROR")
            all_ok = False
    
    # Итоговый отчёт
    log("")
    log("=" * 60)
    log("ИТОГОВЫЙ ОТЧЁТ")
    log("=" * 60)
    
    if features_ok and bot_ok and all_ok:
        log("Все исправления успешно применены!", "OK")
        log("")
        log("Следующие шаги:", "INFO")
        log("  1. git add -A", "INFO")
        log("  2. git commit -m 'Security update v3.1.0'", "INFO")
        log("  3. git push origin main", "INFO")
        log("  4. Перезапустите бота", "INFO")
        log("  5. Откройте /set_webhook в браузере", "INFO")
    else:
        log("Некоторые исправления не были применены.", "WARN")
        log("Проверьте предупреждения выше.", "WARN")
        log("Резервные копии созданы с суффиксом: " + BACKUP_SUFFIX, "INFO")
    
    print("")

if __name__ == "__main__":
    main()