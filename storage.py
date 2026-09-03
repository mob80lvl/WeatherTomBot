#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Хранилище: пользователи, города, подписки, состояния."""
import os
import json
import logging
from datetime import datetime, timedelta

from config import *
from texts import T

try:
    import features as advanced_features
except Exception:
    advanced_features = None

logger = logging.getLogger(__name__)

def get_user_lang(chat_id):
    try:
        lang_file = f"user_lang_{chat_id}.json"
        if os.path.exists(lang_file):
            with open(lang_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get('lang', 'ru')
    except:
        pass
    return 'ru'
def set_user_lang(chat_id, lang):
    try:
        with open(f"user_lang_{chat_id}.json", 'w', encoding='utf-8') as f:
            json.dump({'lang': lang}, f)
        return True
    except:
        return False
def get_user_city(chat_id):
    """Возвращает город пользователя."""
    try:
        # Пробуем прочитать из users_city.json напрямую
        import json, os
        cities_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "users_city.json")
        cities = {}
        if os.path.exists(cities_path):
            with open(cities_path, 'r', encoding='utf-8') as f:
                cities = json.load(f)
        
        # Преобразуем chat_id в строку для поиска
        city = cities.get(str(chat_id))
        if city:
            logger.info(f"get_user_city: found city repr={repr(city)} for chat_id={chat_id}")
            return city
        
        # Если не нашли - проверяем features.json
        features_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "features.json")
        if os.path.exists(features_path):
            with open(features_path, 'r', encoding='utf-8') as f:
                db = json.load(f)
            user = db.get("users", {}).get(str(chat_id), {})
            city = user.get("city")
            if city:
                logger.info(f"get_user_city: found city '{city}' in features.json for chat_id={chat_id}")
                return city
        
        logger.info(f"get_user_city: city not found for chat_id={chat_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка get_user_city: {e}", exc_info=True)
        return None
def save_user_city(chat_id, city):
    try:
        data = {}
        if os.path.exists(USERS_FILE):
            with open(USERS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data[str(chat_id)] = city.strip()
        with open(USERS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения города: {e}")
        return False
def _load_json_file(path, default=None):
    default = {} if default is None else default
    try:
        if os.path.exists(path):
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
                return data if isinstance(data, type(default)) else default
    except Exception as e:
        logger.error(f"Ошибка чтения {path}: {e}")
    return default
def _save_json_file(path, data):
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка записи {path}: {e}")
        return False
def _clear_b2b_entitlement(chat_id):
    key = str(chat_id)
    try:
        data = _load_json_file(B2B_FILE, {})
        if key in data:
            data.pop(key, None)
            _save_json_file(B2B_FILE, data)
    except Exception:
        pass
def _team_plan(chat_id):
    """План через команду: admin/editor бизнес-команды -> business, иначе premium."""
    try:
        if not advanced_features:
            return None
        db = advanced_features._db()
        data = _load_json_file(SUBSCRIPTIONS_FILE, {})
        found_premium = None
        for t in db.get("teams", {}).values():
            members = t.get("members", {})
            if str(chat_id) in members and str(t.get("owner")) != str(chat_id):
                owner = str(t.get("owner"))
                role = members[str(chat_id)]
                osub = data.get(owner)
                if not isinstance(osub, dict):
                    continue
                oexp = osub.get("expiry")
                try:
                    oexpiry = datetime.fromisoformat(oexp) if oexp else None
                except (TypeError, ValueError):
                    oexpiry = None
                if not oexpiry or oexpiry <= datetime.now():
                    continue
                if role in ("admin", "editor") and (osub.get("plan") == "business" or osub.get("b2b_type") == "business"):
                    return "business"
                if osub.get("plan") in ("premium", "business") or osub.get("b2b_type"):
                    found_premium = "premium"
        return found_premium
    except Exception as e:
        logger.error(f"TEAM_PLAN: ошибка: {e}")
        return None
def get_current_plan(chat_id):
    """Return exactly one active plan: free, premium or business.
    Expired subscriptions are automatically downgraded to free.
    """
    key = str(chat_id)
    data = _load_json_file(SUBSCRIPTIONS_FILE, {})
    sub = data.get(key)
    if not isinstance(sub, dict):
        return _team_plan(chat_id) or "free"
    raw_expiry = sub.get("expiry")
    try:
        expiry = datetime.fromisoformat(raw_expiry) if raw_expiry else None
    except (TypeError, ValueError):
        expiry = None

    if not expiry or expiry <= datetime.now():
        # Automatic expiry cleanup: old B2B rights must not survive.
        changed = False
        if sub.get("plan") != "free" or sub.get("b2b_type"):
            sub["plan"] = "free"
            sub["b2b_type"] = None
            changed = True
        if changed:
            data[key] = sub
            _save_json_file(SUBSCRIPTIONS_FILE, data)
        _clear_b2b_entitlement(chat_id)
        return _team_plan(chat_id) or "free"

    plan = sub.get("plan")
    if plan in ("premium", "business"):
        return plan
    # Backward compatibility with old data.
    if sub.get("b2b_type") == "business":
        return "business"
    return _team_plan(chat_id) or "free"
    if sub.get("b2b_type"):
        return "business"
    return "premium"
def is_user_subscribed(chat_id):
    return get_current_plan(chat_id) != "free"
def get_user_b2b_type(chat_id):
    """Return active B2B type only for the current active subscription."""
    plan = get_current_plan(chat_id)
    if plan != "business":
        return None
    data = _load_json_file(B2B_FILE, {})
    item = data.get(str(chat_id), {})
    if isinstance(item, dict):
        raw_expiry = item.get("expiry")
        try:
            if raw_expiry and datetime.fromisoformat(raw_expiry) > datetime.now():
                return item.get("type")
        except (TypeError, ValueError):
            pass
    sub = _load_json_file(SUBSCRIPTIONS_FILE, {}).get(str(chat_id), {})
    return sub.get("b2b_type") if isinstance(sub, dict) else None
def set_user_subscription(chat_id, days=30, b2b_type=None, plan=None):
    """Set the user's single current entitlement.

    Same-plan purchases extend the existing expiry.
    Switching plans replaces the current entitlement immediately.
    Business/Premium rights are never accumulated.
    """
    try:
        data = _load_json_file(SUBSCRIPTIONS_FILE, {})
        now = datetime.now()
        key = str(chat_id)
        existing = data.get(key, {}) if isinstance(data.get(key, {}), dict) else {}
        old_plan = get_current_plan(chat_id)
        if plan is None:
            plan = "business" if b2b_type else "premium"

        # Same plan = renewal/extension; different plan = immediate switch.
        try:
            existing_expiry = datetime.fromisoformat(existing.get("expiry")) if existing.get("expiry") else None
        except (TypeError, ValueError):
            existing_expiry = None
        if old_plan == plan and existing_expiry and existing_expiry > now:
            base_date = existing_expiry
        else:
            base_date = now

        expiry_date = base_date + timedelta(days=int(days))
        data[key] = {
            "plan": plan,
            "expiry": expiry_date.isoformat(),
            "activated_by": "payment_b2b" if plan == "business" else "payment",
            "activated_at": now.isoformat(),
            "b2b_type": b2b_type if plan == "business" else None,
        }
        _save_json_file(SUBSCRIPTIONS_FILE, data)

        # Keep the legacy B2B registry synchronized with the CURRENT plan only.
        b2b_data = _load_json_file(B2B_FILE, {})
        if plan == "business":
            b2b_data[key] = {
                "type": b2b_type or "business",
                "activated_at": now.isoformat(),
                "expiry": expiry_date.isoformat(),
                "source": "payment",
            }
        else:
            b2b_data.pop(key, None)
        _save_json_file(B2B_FILE, b2b_data)

        # Ensure the user exists in the registry.
        users = _load_json_file(USERS_FILE, {})
        if key not in users:
            users[key] = {"city": None, "registered": now.isoformat(), "source": "payment"}
            _save_json_file(USERS_FILE, users)

        logger.info(
            f"SUBSCRIPTION: user={chat_id} old_plan={old_plan} new_plan={plan} "
            f"expiry={expiry_date.isoformat()} b2b={b2b_type or '-'}"
        )
        return True
    except Exception as e:
        logger.error(f"Ошибка установки подписки для {chat_id}: {e}", exc_info=True)
        return False
def get_user_subscription(chat_id):
    data = _load_json_file(SUBSCRIPTIONS_FILE, {})
    sub = data.get(str(chat_id))
    if isinstance(sub, dict):
        # Calling this also performs expiry synchronization.
        get_current_plan(chat_id)
        return _load_json_file(SUBSCRIPTIONS_FILE, {}).get(str(chat_id))
    return None
def get_notification_status(chat_id):
    try:
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return data.get(str(chat_id), {}).get('enabled', False)
    except:
        pass
    return False
def set_notification_status(chat_id, enabled):
    try:
        data = {}
        if os.path.exists(NOTIFICATIONS_FILE):
            with open(NOTIFICATIONS_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
        data[str(chat_id)] = {
            'enabled': enabled,
            'updated_at': datetime.now().isoformat()
        }
        with open(NOTIFICATIONS_FILE, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка сохранения уведомлений: {e}")
        return False
def _load_user_states():
    return _load_json_file(USER_STATES_FILE, {})
def _get_user_state(chat_id):
    return _load_user_states().get(str(chat_id), {})
def _set_user_state(chat_id, mode, **extra):
    data = _load_user_states()
    item = {"mode": mode, "updated_at": datetime.now().isoformat()}
    item.update(extra)
    data[str(chat_id)] = item
    _save_json_file(USER_STATES_FILE, data)
def _clear_user_state(chat_id):
    data = _load_user_states()
    data.pop(str(chat_id), None)
    _save_json_file(USER_STATES_FILE, data)
