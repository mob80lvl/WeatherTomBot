#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Фоновые задачи: планировщик автопостинга и cron уведомлений."""
import logging
import time as _time
from datetime import datetime

from app import app
from config import *

try:
    import features as advanced_features
except Exception:
    advanced_features = None

logger = logging.getLogger(__name__)

def _scheduler_loop():
    """Каждую минуту вызывает scheduled_job() для автопостинга и уведомлений."""
    while True:
        try:
            now = datetime.now()
            sleep_sec = 60 - now.second - now.microsecond / 1e6
            _time.sleep(max(sleep_sec, 1) + 0.5)
            if advanced_features:
                result = advanced_features.scheduled_job()
                if result and (result.get("notifications") or result.get("channels")):
                    logger.info(f"SCHEDULER: {result}")
        except Exception as e:
            logger.error(f"SCHEDULER ошибка: {e}")
            _time.sleep(30)

@app.route('/api/cron_notifications', methods=['GET'])
def cron_notifications():
    """Веб-хук для отправки уведомлений (cron-job.org вызывает каждый час)."""
    try:
        import sys, os
        sys.path.insert(0, '/home/mob100500lvl/WeatherTomBot/WeatherTomBot')
        from send_notifications import main as send_main
        send_main()
        return "OK", 200
    except Exception as e:
        return f"Error: {str(e)[:200]}", 500

