#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Хранилище: пользователи, города, подписки, состояния (SQLite)."""
import os
import json
import logging
from datetime import datetime, timedelta
from config import *
from db import get_conn, init_db
try:
    import features as advanced_features
except Exception:
    advanced_features = None
logger = logging.getLogger(__name__)

# Инициализация БД при импорте
init_db()

def get_user_lang(chat_id):
    """Получить язык пользователя."""
    try:
        conn = get_conn()
        try:
            row = conn.execute("SELECT lang FROM users WHERE chat_id=?", (str(chat_id),)).fetchone()
            return row[0] if row and row[0] else 'ru'
        finally:
            conn.close()
    except Exception:
        pass
    return 'ru'

def set_user_lang(chat_id, lang):
    """Установить язык пользователя."""
    try:
        conn = get_conn()
        try:
            conn.execute("INSERT OR IGNORE INTO users(chat_id) VALUES(?)", (str(chat_id),))
            conn.execute("UPDATE users SET lang=? WHERE chat_id=?", (lang, str(chat_id)))
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Ошибка установки языка для {chat_id}: {e}")
        return False

def get_user_city(chat_id):
    """Возвращает город пользователя."""
    try:
        # Пробуем из SQLite
        conn = get_conn()
        try:
            row = conn.execute("SELECT city FROM users WHERE chat_id=?", (str(chat_id),)).fetchone()
            if row and row[0]:
                logger.info(f"get_user_city: found city repr={repr(row[0])} for chat_id={chat_id}")
                return row[0]
        finally:
            conn.close()
        
        logger.info(f"get_user_city: city not found for chat_id={chat_id}")
        return None
    except Exception as e:
        logger.error(f"Ошибка get_user_city: {e}", exc_info=True)
        return None

def save_user_city(chat_id, city):
    """Сохранить город пользователя."""
    try:
        conn = get_conn()
        try:
            conn.execute("INSERT OR IGNORE INTO users(chat_id) VALUES(?)", (str(chat_id),))
            conn.execute("UPDATE users SET city=? WHERE chat_id=?", (city.strip(), str(chat_id)))
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Ошибка сохранения города: {e}")
        return False

def _load_json_file(path, default=None):
    """Утилита чтения JSON (для совместимости с service.py и миграции)."""
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
    """Утилита записи JSON (для совместимости с service.py и миграции)."""
    try:
        with open(path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        logger.error(f"Ошибка записи {path}: {e}")
        return False

def _clear_b2b_entitlement(chat_id):
    """Удалить B2B-права пользователя."""
    key = str(chat_id)
    try:
        conn = get_conn()
        try:
            conn.execute("DELETE FROM b2b_users WHERE chat_id=?", (key,))
            conn.commit()
        finally:
            conn.close()
    except Exception:
        pass

def _team_plan(chat_id):
    """План через команду: admin/editor бизнес-команды -> business, иначе premium."""
    try:
        if not advanced_features:
            return None
        db = advanced_features._db()
        conn = get_conn()
        try:
            found_premium = None
            for t in db.get("teams", {}).values():
                members = t.get("members", {})
                if str(chat_id) in members and str(t.get("owner")) != str(chat_id):
                    owner = str(t.get("owner"))
                    role = members[str(chat_id)]
                    row = conn.execute("SELECT plan, b2b_type, expiry FROM subscriptions WHERE chat_id=?", (owner,)).fetchone()
                    if not row:
                        continue
                    plan, b2b_type, oexp = row
                    try:
                        oexpiry = datetime.fromisoformat(oexp) if oexp else None
                    except (TypeError, ValueError):
                        oexpiry = None
                    if not oexpiry or oexpiry <= datetime.now():
                        continue
                    if role in ("admin", "editor") and (plan == "business" or b2b_type == "business"):
                        return "business"
                    if plan in ("premium", "business") or b2b_type:
                        found_premium = "premium"
            return found_premium
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"TEAM_PLAN: ошибка: {e}")
        return None

def get_current_plan(chat_id):
    try:
        import json as _j, os as _o, time as _t
        _pp = _o.path.join(_o.path.dirname(_o.path.abspath(__file__)), "plans.json")
        with open(_pp, encoding="utf-8") as _f:
            _e = _j.load(_f).get(str(chat_id), {})
        if _e.get("plan") in ("business", "premium") and _e.get("expires", 0) > int(_t.time()):
            return _e["plan"]
    except Exception:
        pass
    """Return exactly one active plan: free, premium or business.
    Expired subscriptions are automatically downgraded to free.
    """
    key = str(chat_id)
    conn = get_conn()
    try:
        row = conn.execute("SELECT plan, expiry, b2b_type FROM subscriptions WHERE chat_id=?", (key,)).fetchone()
        if not row:
            return _team_plan(chat_id) or "free"
        
        plan, raw_expiry, b2b_type = row
        try:
            expiry = datetime.fromisoformat(raw_expiry) if raw_expiry else None
        except (TypeError, ValueError):
            expiry = None

        if not expiry or expiry <= datetime.now():
            # Automatic expiry cleanup
            conn.execute("UPDATE subscriptions SET plan='free', b2b_type=NULL WHERE chat_id=?", (key,))
            conn.execute("DELETE FROM b2b_users WHERE chat_id=?", (key,))
            conn.commit()
            return _team_plan(chat_id) or "free"

        if plan in ("premium", "business"):
            return plan
        if b2b_type == "business":
            return "business"
        return _team_plan(chat_id) or "free"
    finally:
        conn.close()

def is_user_subscribed(chat_id):
    """Проверить, подписан ли пользователь."""
    return get_current_plan(chat_id) != "free"

def get_user_b2b_type(chat_id):
    """Return active B2B type only for the current active subscription."""
    plan = get_current_plan(chat_id)
    if plan != "business":
        return None
    conn = get_conn()
    try:
        row = conn.execute("SELECT expiry, type FROM b2b_users WHERE chat_id=?", (str(chat_id),)).fetchone()
        if row:
            try:
                if row[0] and datetime.fromisoformat(row[0]) > datetime.now():
                    return row[1]
            except (TypeError, ValueError):
                pass
        sub = conn.execute("SELECT b2b_type FROM subscriptions WHERE chat_id=?", (str(chat_id),)).fetchone()
        return sub[0] if sub else None
    finally:
        conn.close()

def set_user_subscription(chat_id, days=30, b2b_type=None, plan=None):
    """Set the user's single current entitlement.

    Same-plan purchases extend the existing expiry.
    Switching plans replaces the current entitlement immediately.
    Business/Premium rights are never accumulated.
    """
    try:
        conn = get_conn()
        try:
            now = datetime.now()
            key = str(chat_id)
            old_plan = get_current_plan(chat_id)
            if plan is None:
                plan = "business" if b2b_type else "premium"

            # Получаем существующую подписку
            row = conn.execute("SELECT plan, expiry FROM subscriptions WHERE chat_id=?", (key,)).fetchone()
            existing_plan = row[0] if row else None
            existing_expiry_str = row[1] if row else None

            try:
                existing_expiry = datetime.fromisoformat(existing_expiry_str) if existing_expiry_str else None
            except (TypeError, ValueError):
                existing_expiry = None

            if old_plan == plan and existing_expiry and existing_expiry > now:
                base_date = existing_expiry
            else:
                base_date = now

            expiry_date = base_date + timedelta(days=int(days))
            
            # Вставляем или обновляем подписку
            conn.execute("""INSERT OR REPLACE INTO subscriptions(chat_id, plan, expiry, activated_by, activated_at, b2b_type) 
                           VALUES(?,?,?,?,?,?)""",
                        (key, plan, expiry_date.isoformat(),
                         "payment_b2b" if plan == "business" else "payment",
                         now.isoformat(),
                         b2b_type if plan == "business" else None))

            # Синхронизируем b2b_users
            if plan == "business":
                conn.execute("""INSERT OR REPLACE INTO b2b_users(chat_id, type, activated_at, expiry, source) 
                               VALUES(?,?,?,?,?)""",
                            (key, b2b_type or "business", now.isoformat(), expiry_date.isoformat(), "payment"))
            else:
                conn.execute("DELETE FROM b2b_users WHERE chat_id=?", (key,))

            # Обеспечиваем существование пользователя
            conn.execute("INSERT OR IGNORE INTO users(chat_id) VALUES(?)", (key,))
            conn.commit()

            logger.info(
                f"SUBSCRIPTION: user={chat_id} old_plan={old_plan} new_plan={plan} "
                f"expiry={expiry_date.isoformat()} b2b={b2b_type or '-'}"
            )
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Ошибка установки подписки для {chat_id}: {e}", exc_info=True)
        return False

def get_user_subscription(chat_id):
    """Получить данные подписки пользователя."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT * FROM subscriptions WHERE chat_id=?", (str(chat_id),)).fetchone()
        if row:
            # Синхронизируем истечение
            get_current_plan(chat_id)
            row2 = conn.execute("SELECT plan, expiry, activated_by, activated_at, b2b_type FROM subscriptions WHERE chat_id=?", (str(chat_id),)).fetchone()
            if row2:
                return {
                    "plan": row2[0],
                    "expiry": row2[1],
                    "activated_by": row2[2],
                    "activated_at": row2[3],
                    "b2b_type": row2[4]
                }
        return None
    finally:
        conn.close()

def get_notification_status(chat_id):
    """Получить статус уведомлений."""
    try:
        conn = get_conn()
        try:
            row = conn.execute("SELECT enabled FROM notifications WHERE chat_id=?", (str(chat_id),)).fetchone()
            return bool(row[0]) if row else False
        finally:
            conn.close()
    except Exception:
        pass
    return False

def set_notification_status(chat_id, enabled):
    """Установить статус уведомлений."""
    try:
        conn = get_conn()
        try:
            conn.execute("INSERT OR REPLACE INTO notifications(chat_id, enabled) VALUES(?,?)",
                        (str(chat_id), 1 if enabled else 0))
            conn.commit()
            return True
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Ошибка сохранения уведомлений: {e}")
        return False

def _load_user_states():
    """Загрузить все состояния (для совместимости)."""
    conn = get_conn()
    try:
        rows = conn.execute("SELECT chat_id, state FROM user_states").fetchall()
        result = {}
        for cid, state_json in rows:
            result[cid] = json.loads(state_json)
        return result
    finally:
        conn.close()

def _get_user_state(chat_id):
    """Получить состояние пользователя."""
    conn = get_conn()
    try:
        row = conn.execute("SELECT state FROM user_states WHERE chat_id=?", (str(chat_id),)).fetchone()
        return json.loads(row[0]) if row else {}
    finally:
        conn.close()

def _set_user_state(chat_id, mode, **extra):
    """Установить состояние пользователя."""
    try:
        conn = get_conn()
        try:
            item = {"mode": mode, "updated_at": datetime.now().isoformat()}
            item.update(extra)
            conn.execute("INSERT OR REPLACE INTO user_states(chat_id, state) VALUES(?,?)",
                        (str(chat_id), json.dumps(item, ensure_ascii=False)))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Ошибка установки состояния для {chat_id}: {e}")

def _clear_user_state(chat_id):
    """Очистить состояние пользователя."""
    try:
        conn = get_conn()
        try:
            conn.execute("DELETE FROM user_states WHERE chat_id=?", (str(chat_id),))
            conn.commit()
        finally:
            conn.close()
    except Exception as e:
        logger.error(f"Ошибка очистки состояния для {chat_id}: {e}")
