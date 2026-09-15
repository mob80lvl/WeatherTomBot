#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""SQLite: подключение и схема базы данных."""
import sqlite3
import logging

from config import DB_FILE

logger = logging.getLogger(__name__)

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    chat_id TEXT PRIMARY KEY,
    city TEXT,
    lang TEXT
);
CREATE TABLE IF NOT EXISTS subscriptions (
    chat_id TEXT PRIMARY KEY,
    plan TEXT,
    expiry TEXT,
    activated_by TEXT,
    activated_at TEXT,
    b2b_type TEXT
);
CREATE TABLE IF NOT EXISTS b2b_users (
    chat_id TEXT PRIMARY KEY,
    type TEXT,
    activated_at TEXT,
    expiry TEXT,
    source TEXT
);
CREATE TABLE IF NOT EXISTS user_states (
    chat_id TEXT PRIMARY KEY,
    state TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS notifications (
    chat_id TEXT PRIMARY KEY,
    enabled INTEGER NOT NULL DEFAULT 0
);
-- ===== таблицы features.py =====
CREATE TABLE IF NOT EXISTS f_users (
    uid TEXT PRIMARY KEY,
    first_seen TEXT,
    last_seen TEXT,
    source TEXT,
    started INTEGER DEFAULT 0,
    notifications INTEGER DEFAULT 0,
    favorites TEXT DEFAULT '[]',
    api_default_city TEXT,
    referral_code TEXT
);
CREATE INDEX IF NOT EXISTS idx_f_users_referral ON f_users(referral_code);
CREATE TABLE IF NOT EXISTS f_teams (
    id TEXT PRIMARY KEY,
    name TEXT,
    owner TEXT,
    created_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_f_teams_owner ON f_teams(owner);
CREATE TABLE IF NOT EXISTS f_team_members (
    team_id TEXT,
    uid TEXT,
    role TEXT,
    PRIMARY KEY (team_id, uid)
);
CREATE INDEX IF NOT EXISTS idx_f_team_members_uid ON f_team_members(uid);
CREATE TABLE IF NOT EXISTS f_channels (
    handle TEXT PRIMARY KEY,
    owner TEXT,
    title TEXT,
    city TEXT,
    schedule TEXT,
    enabled INTEGER DEFAULT 0,
    created_at TEXT,
    last_post TEXT
);
CREATE INDEX IF NOT EXISTS idx_f_channels_owner ON f_channels(owner);
CREATE TABLE IF NOT EXISTS f_card_settings (
    uid TEXT PRIMARY KEY,
    bg_image TEXT,
    text_color TEXT,
    accent_color TEXT,
    style TEXT
);
CREATE TABLE IF NOT EXISTS f_white_labels (
    uid TEXT PRIMARY KEY,
    name TEXT,
    updated_at TEXT,
    logo TEXT,
    extra TEXT
);
CREATE TABLE IF NOT EXISTS f_referrals (
    code TEXT PRIMARY KEY,
    owner TEXT,
    users TEXT DEFAULT '[]',
    rewarded INTEGER DEFAULT 0
);
CREATE TABLE IF NOT EXISTS f_events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id TEXT,
    event TEXT,
    ts TEXT,
    payload TEXT
);
CREATE INDEX IF NOT EXISTS idx_f_events_uid ON f_events(user_id);
CREATE INDEX IF NOT EXISTS idx_f_events_event ON f_events(event);
CREATE INDEX IF NOT EXISTS idx_f_events_ts ON f_events(ts);
CREATE TABLE IF NOT EXISTS f_settings (
    key TEXT PRIMARY KEY,
    value TEXT
);

CREATE TABLE IF NOT EXISTS api_keys (
    digest TEXT PRIMARY KEY,
    owner TEXT NOT NULL,
    name TEXT,
    created_at TEXT,
    created_ts REAL,
    last_used TEXT,
    salt TEXT,
    active INTEGER DEFAULT 1,
    usage_count INTEGER DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_api_keys_owner ON api_keys(owner);
CREATE INDEX IF NOT EXISTS idx_api_keys_active ON api_keys(active);

"""

def get_conn():
    """Новое подключение на каждую операцию (потокобезопасно)."""
    conn = sqlite3.connect(DB_FILE, timeout=30)
    conn.execute("PRAGMA journal_mode=WAL")
    return conn

def init_db():
    conn = get_conn()
    try:
        conn.executescript(SCHEMA)
        conn.commit()
    finally:
        conn.close()
    logger.info("✅ SQLite: схема инициализирована")
