#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Сервисные функции: миграция подписок и валидация конфигурации."""
import os
import logging
from datetime import datetime

from config import *
from storage import _load_json_file, _save_json_file

logger = logging.getLogger(__name__)

def migrate_subscriptions_to_new_plans():
    """One-time safe migration: Personal -> Premium, all legacy B2B -> Business.
    Existing expiry dates and active periods are preserved.
    """
    try:
        data = _load_json_file(SUBSCRIPTIONS_FILE, {})
        b2b_data = _load_json_file(B2B_FILE, {})
        changed = False
        for uid, sub in list(data.items()):
            if not isinstance(sub, dict):
                continue
            old = str(sub.get("plan") or "").casefold()
            b2b = str(sub.get("b2b_type") or "").casefold()
            if old in ("personal", "premium", "") and not b2b:
                new_plan = "premium" if old != "free" else "free"
                if sub.get("plan") != new_plan:
                    sub["plan"] = new_plan
                    sub["b2b_type"] = None
                    changed = True
            elif old in ("agriculture", "construction", "tourism", "business") or b2b in ("agriculture", "construction", "tourism", "business"):
                if sub.get("plan") != "business" or sub.get("b2b_type") != "business":
                    sub["plan"] = "business"
                    sub["b2b_type"] = "business"
                    changed = True
            elif old not in ("premium", "business", "free"):
                sub["plan"] = "business" if b2b else "premium"
                sub["b2b_type"] = "business" if b2b else None
                changed = True

            if sub.get("plan") == "business":
                b2b_data[str(uid)] = {
                    "type": "business",
                    "activated_at": b2b_data.get(str(uid), {}).get("activated_at", sub.get("activated_at", datetime.now().isoformat())),
                    "expiry": sub.get("expiry"),
                    "source": b2b_data.get(str(uid), {}).get("source", "migration"),
                }
            else:
                b2b_data.pop(str(uid), None)
            data[uid] = sub

        if changed:
            _save_json_file(SUBSCRIPTIONS_FILE, data)
        _save_json_file(B2B_FILE, b2b_data)

        # Repair the known class of city corruption caused by treating commands as cities.
        users = _load_json_file(USERS_FILE, {})
        repaired = False
        if isinstance(users, dict):
            for uid, city in list(users.items()):
                if isinstance(city, str) and city.strip().startswith("/"):
                    users[uid] = None
                    repaired = True
        if repaired:
            _save_json_file(USERS_FILE, users)

        # Normalize legacy B2B registry entries too.
        for uid, info in list(b2b_data.items()):
            if not isinstance(info, dict):
                b2b_data.pop(uid, None)
                continue
            sub = data.get(str(uid), {})
            if sub.get("plan") == "business":
                info["type"] = "business"
                info["expiry"] = sub.get("expiry")
                b2b_data[str(uid)] = info
            else:
                b2b_data.pop(uid, None)
        _save_json_file(B2B_FILE, b2b_data)

        logger.info("SUBSCRIPTION MIGRATION: completed; public plans=Premium/Business")
    except Exception:
        logger.exception("SUBSCRIPTION MIGRATION failed")

def validate_config():
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
    
    logger.info("Конфигурация валидна")

