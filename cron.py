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
try:
    import vk_posts
except Exception:
    vk_posts = None

logger = logging.getLogger(__name__)
from backup_db import create_backup

_last_backup_date = None

def _scheduler_loop():
    """Каждую минуту вызывает scheduled_job() для автопостинга и уведомлений."""
    global _last_backup_date
    while True:
        try:
            now = datetime.now()
            # Ежедневный бэкап в 3:00
            if now.hour == 3 and now.minute == 0 and _last_backup_date != now.date():
                try:
                    path = create_backup()
                    if path:
                        _last_backup_date = now.date()
                        logger.info(f"DAILY BACKUP: {path}")
                except Exception as e:
                    logger.error(f"DAILY BACKUP ошибка: {e}")

            # Ежечасный пост в VK (защита от дублей внутри hourly_job)
            try:
                vk_posts.hourly_job()
            except Exception as e:
                logger.error(f"VK HOURLY POST ошибка: {e}")
            
            # Пост в официальный TG-канал каждые 2 часа (синхронно с VK)
            try:
                if advanced_features:
                    tg_result = advanced_features.tg_official_post()
                    if tg_result:
                        logger.info(f"TG OFFICIAL POST: {tg_result}")
            except Exception as e:
                logger.error(f"TG OFFICIAL POST ошибка: {e}")
            
            # Ежечасные уведомления (в начале каждого часа)
            if now.minute == 0:
                try:
                    import send_notifications as _sn
                    _sn.main()
                    logger.info(f"NOTIFICATIONS: проверено в {now.strftime('%H:%M')} UTC")
                except Exception as e:
                    logger.error(f"NOTIFICATIONS ошибка: {e}")
            
            sleep_sec = 60 - now.second - now.microsecond / 1e6
            _time.sleep(max(sleep_sec, 1) + 0.5)
            if advanced_features:
                result = advanced_features.scheduled_job()
                if result and (result.get("notifications") or result.get("channels")):
                    logger.info(f"SCHEDULER: {result}")
        except Exception as e:
            logger.error(f"SCHEDULER ошибка: {e}")
            _time.sleep(30)

import os as _os
@app.route("/vkmedia/<path:fname>")
def vk_media_file(fname):
    from flask import send_from_directory
    d = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "vk_media")
    return send_from_directory(d, fname)

@app.route("/vkpost/<pid>")
def vk_post_page(pid):
    ext = vk_posts.get_card_url(pid)
    if ext:
        img_url, w, h = ext, "1280", "720"
    else:
        fname = f"p{pid}.jpg"
        d = _os.path.join(_os.path.dirname(_os.path.abspath(__file__)), "vk_media")
        if not _os.path.exists(_os.path.join(d, fname)):
            return "not found", 404
        img_url, w, h = f"https://mob100500lvl.pythonanywhere.com/vkmedia/{fname}", "1200", "630"
    page_url = f"https://mob100500lvl.pythonanywhere.com/vkpost/{pid}"
    return (f'<!DOCTYPE html><html><head>'
            f'<meta charset="utf-8">'
            f'<meta property="og:url" content="{page_url}">'
            f'<meta property="og:image" content="{img_url}">'
            f'<meta property="og:image:width" content="{w}">'
            f'<meta property="og:image:height" content="{h}">'
            f'<meta property="og:image:type" content="image/jpeg">'
            f'<meta property="og:title" content="WeatherTomBot">'
            f'<meta property="og:description" content="Погодная открытка часа">'
            f'<meta property="og:type" content="article">'
            f'<meta property="og:site_name" content="mob100500lvl.pythonanywhere.com">'
            f'</head>'
            f'<body style="margin:0;background:#111"><img src="{img_url}" style="max-width:100%"></body></html>')

@app.route('/api/vk_post_now', methods=['GET'])
def vk_post_now():
    """Мгновенная публикация поста в VK (для тестов)."""
    try:
        ok, info = vk_posts.publish_post()
        return {"ok": ok, "info": str(info)[:300]}
    except Exception as e:
        return {"ok": False, "error": str(e)}, 500


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

