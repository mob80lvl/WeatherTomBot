#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Резервное копирование базы данных bot.db.

Использует нативный SQLite backup API — бэкап консистентен
даже если бот в этот момент пишет в базу.

Запуск вручную:  python3 backup_db.py
Запуск по cron:  Tasks -> Cron jobs в PythonAnywhere
"""
import os
import sys
import sqlite3
import logging
from datetime import datetime

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_FILE = os.path.join(BASE_DIR, "bot.db")
BACKUP_DIR = os.path.join(BASE_DIR, "backups")
KEEP_LAST = 7  # сколько последних бэкапов хранить

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
logger = logging.getLogger("backup")


def create_backup():
    """Создаёт консистентную копию bot.db и проверяет её целостность."""
    if not os.path.exists(DB_FILE):
        logger.error(f"База не найдена: {DB_FILE}")
        return None
    os.makedirs(BACKUP_DIR, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_path = os.path.join(BACKUP_DIR, f"bot_backup_{stamp}.db")

    src = sqlite3.connect(DB_FILE)
    dst = sqlite3.connect(backup_path)
    try:
        src.backup(dst)
        dst.commit()
    finally:
        dst.close()
        src.close()

    # Проверка целостности бэкапа
    check = sqlite3.connect(backup_path)
    try:
        result = check.execute("PRAGMA integrity_check").fetchone()[0]
        tables = check.execute("SELECT COUNT(*) FROM sqlite_master WHERE type='table'").fetchone()[0]
    finally:
        check.close()
    if result != "ok":
        logger.error(f"Бэкап повреждён, удалён: {result}")
        os.remove(backup_path)
        return None

    size_kb = os.path.getsize(backup_path) / 1024
    logger.info(f"Бэкап создан: {os.path.basename(backup_path)} ({size_kb:.1f} КБ, таблиц: {tables}, integrity: ok)")
    return backup_path


def rotate_backups():
    """Хранит только KEEP_LAST последних бэкапов."""
    files = sorted(
        [f for f in os.listdir(BACKUP_DIR) if f.startswith("bot_backup_") and f.endswith(".db")],
        reverse=True,
    )
    removed = 0
    for old in files[KEEP_LAST:]:
        os.remove(os.path.join(BACKUP_DIR, old))
        removed += 1
    if removed:
        logger.info(f"Удалено старых бэкапов: {removed}")


if __name__ == "__main__":
    path = create_backup()
    if path:
        rotate_backups()
        sys.exit(0)
    sys.exit(1)
