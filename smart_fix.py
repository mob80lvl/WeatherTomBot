#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Smart Fix - применяет исправления к реальным файлам
"""

import os
import re
import ast

def log(msg, level="INFO"):
    icons = {"INFO": "ℹ️", "OK": "✅", "WARN": "⚠️", "ERROR": "❌"}
    print(f"{icons.get(level, '  ')} {msg}")

def find_function(code, func_name):
    """Находит функцию по имени и возвращает её позицию"""
    pattern = rf'^def\s+{func_name}\s*\([^)]*\)\s*:[^\n]*\n'
    match = re.search(pattern, code, re.MULTILINE)
    return match

def replace_function(code, func_name, new_function_code):
    """Заменяет функцию целиком"""
    # Находим начало функции
    start_pattern = rf'^(def\s+{func_name}\s*\([^)]*\)\s*:[^\n]*\n)'
    start_match = re.search(start_pattern, code, re.MULTILINE)
    
    if not start_match:
        return None
    
    start_pos = start_match.start()
    
    # Находим конец функции (следующая функция или конец файла)
    next_func_pattern = r'\n(?:def\s+\w+|class\s+\w+|#\s*={3,})'
    rest_of_code = code[start_match.end():]
    end_match = re.search(next_func_pattern, rest_of_code, re.MULTILINE)
    
    if end_match:
        end_pos = start_match.end() + end_match.start()
    else:
        end_pos = len(code)
    
    # Заменяем функцию
    new_code = code[:start_pos] + new_function_code + '\n\n' + code[end_pos:]
    return new_code

def fix_features():
    log("=" * 60)
    log("ИСПРАВЛЯЕМ features.py")
    log("=" * 60)
    
    filepath = "features.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    
    original_code = code
    applied = 0
    
    # 1. Добавляем импорт logging
    if "import logging" not in code:
        code = code.replace(
            "import os, json, time, uuid, secrets, hashlib, threading, math",
            "import os, json, time, uuid, secrets, hashlib, threading, math, logging\n\nlogger = logging.getLogger(\"features\")"
        )
        log("Добавлен импорт logging", "OK")
        applied += 1
    
    # 2. Заменяем create_api_key
    new_create_api_key = '''def create_api_key(uid, name="default"):
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
    
    result = replace_function(code, "create_api_key", new_create_api_key)
    if result:
        code = result
        log("Заменена функция create_api_key (соль + безопасность)", "OK")
        applied += 1
    else:
        log("Не найдена функция create_api_key", "WARN")
    
    # 3. Заменяем verify_api_key
    new_verify_api_key = '''def verify_api_key(raw):
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
    
    result = replace_function(code, "verify_api_key", new_verify_api_key)
    if result:
        code = result
        log("Заменена функция verify_api_key (проверка с солью)", "OK")
        applied += 1
    else:
        log("Не найдена функция verify_api_key", "WARN")
    
    # 4. Заменяем set_alert
    new_set_alert = '''def set_alert(uid, kind, enabled=True, threshold=None):
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
    
    result = replace_function(code, "set_alert", new_set_alert)
    if result:
        code = result
        log("Заменена функция set_alert (валидация threshold)", "OK")
        applied += 1
    else:
        log("Не найдена функция set_alert", "WARN")
    
    # 5. Исправляем daily_notification_job - добавляем rate limiting
    old_loop = 'for uid, profile in db.get("users", {}).items():'
    new_loop = '''# Rate limiting: максимум 100 пользователей за раз
    users_list = list(db.get("users", {}).items())[:100]

    for uid, profile in users_list:'''
    
    if old_loop in code:
        code = code.replace(old_loop, new_loop, 1)
        log("Добавлен rate limiting в daily_notification_job", "OK")
        applied += 1
    
    # 6. Исправляем обработку ошибок в daily_notification_job
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
    
    if old_error in code:
        code = code.replace(old_error, new_error, 1)
        log("Улучшена обработка ошибок в daily_notification_job", "OK")
        applied += 1
    
    # 7. Добавляем errors_count в начало функции
    if 'errors_count = 0' not in code and 'sent = 0' in code:
        code = code.replace(
            '    sent = 0\n    changed = False',
            '    sent = 0\n    changed = False\n    errors_count = 0',
            1
        )
        log("Добавлена переменная errors_count", "OK")
        applied += 1
    
    # 8. Добавляем логирование в конец daily_notification_job
    old_return = '    if changed:\n        _save_db(db)\n    return sent'
    new_return = '''    if changed:
        _save_db(db)
    if sent > 0 or errors_count > 0:
        logger.info(f"Уведомления: отправлено={sent}, ошибок={errors_count}")
    return sent'''
    
    if old_return in code:
        code = code.replace(old_return, new_return, 1)
        log("Добавлено логирование итогов", "OK")
        applied += 1
    
    # Проверяем синтаксис
    try:
        ast.parse(code)
        log("Синтаксис features.py корректен", "OK")
    except SyntaxError as e:
        log(f"ОШИБКА СИНТАКСИСА: {e}", "ERROR")
        return False
    
    # Сохраняем
    if code != original_code:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        log(f"features.py: применено {applied} исправлений", "OK")
        return True
    else:
        log("Изменений не было", "WARN")
        return False

def fix_bot():
    log("\n" + "=" * 60)
    log("ИСПРАВЛЯЕМ bot.py")
    log("=" * 60)
    
    filepath = "bot.py"
    with open(filepath, 'r', encoding='utf-8') as f:
        code = f.read()
    
    original_code = code
    applied = 0
    
    # 1. Заменяем set_webhook
    new_set_webhook = '''@app.route('/set_webhook', methods=['GET'])
def set_webhook():
    """Устанавливает webhook с защитой секретным токеном."""
    webhook_url = WEBHOOK_URL or request.host_url.rstrip("/") + "/webhook"
    webhook_secret = os.getenv("WEBHOOK_SECRET", "")
    if webhook_secret:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}&secret_token={webhook_secret}"
        logger.info("Устанавливаем webhook с секретным токеном")
    else:
        url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/setWebhook?url={webhook_url}"
        logger.warning("WEBHOOK_SECRET не задан! Webhook не защищен.")
    try:
        response = requests.get(url, timeout=30)
        return response.text
    except Exception as e:
        logger.error(f"Ошибка установки webhook: {e}", exc_info=True)
        return f"Error: {e}"'''
    
    result = replace_function(code, "set_webhook", new_set_webhook)
    if result:
        code = result
        log("Заменена функция set_webhook (secret_token)", "OK")
        applied += 1
    else:
        log("Не найдена функция set_webhook", "WARN")
    
    # 2. Добавляем проверку секрета в webhook
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
    
    if old_webhook_start in code:
        code = code.replace(old_webhook_start, new_webhook_start, 1)
        log("Добавлена проверка секрета в webhook", "OK")
        applied += 1
    else:
        log("Не найден шаблон webhook", "WARN")
    
    # 3. Заменяем validate_config
    new_validate_config = '''def validate_config():
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
    
    result = replace_function(code, "validate_config", new_validate_config)
    if result:
        code = result
        log("Заменена функция validate_config (проверка секретов)", "OK")
        applied += 1
    else:
        log("Не найдена функция validate_config", "WARN")
    
    # Проверяем синтаксис
    try:
        ast.parse(code)
        log("Синтаксис bot.py корректен", "OK")
    except SyntaxError as e:
        log(f"ОШИБКА СИНТАКСИСА: {e}", "ERROR")
        return False
    
    # Сохраняем
    if code != original_code:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(code)
        log(f"bot.py: применено {applied} исправлений", "OK")
        return True
    else:
        log("Изменений не было", "WARN")
        return False

if __name__ == "__main__":
    print("\n" + "=" * 60)
    print("WeatherTomBot - Smart Fix v3.1.0")
    print("=" * 60 + "\n")
    
    features_ok = fix_features()
    bot_ok = fix_bot()
    
    print("\n" + "=" * 60)
    if features_ok or bot_ok:
        print("✅ Исправления применены!")
        print("\nСледующие команды:")
        print("  git add -A")
        print("  git commit -m '🔒 Apply security fixes v3.1.0'")
        print("  git push origin main")
    else:
        print("⚠️  Изменений не было или произошла ошибка")
    print("=" * 60 + "\n")