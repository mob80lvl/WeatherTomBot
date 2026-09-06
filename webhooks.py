#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Технические роуты: индекс, регистрация и информация о вебхуке."""
import os
import json
import logging
import requests
from flask import request

from app import app
from config import *

logger = logging.getLogger(__name__)

@app.route('/')
def index():
    total_users = 0
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            total_users = len(json.load(f))

    return f'''<!DOCTYPE html><html><head><title>MeteoBot</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;display:flex;justify-content:center;align-items:center;min-height:100vh;padding:20px}}.container{{text-align:center;max-width:600px}}h1{{font-size:3em;color:#ffd200;margin-bottom:20px}}.status{{background:rgba(255,255,255,0.05);padding:20px;border-radius:15px;margin:20px 0}}.status-item{{padding:10px 0;border-bottom:1px solid rgba(255,255,255,0.05)}}.status-item:last-child{{border-bottom:none}}.label{{opacity:0.7}}.value{{font-weight:bold;color:#ffd200}}.btn{{display:inline-block;padding:12px 30px;background:linear-gradient(90deg,#f7971e,#ffd200);color:#000;text-decoration:none;border-radius:10px;font-weight:bold;margin-top:20px}}.btn:hover{{transform:scale(1.05)}}.version{{opacity:0.5;font-size:12px;margin-top:20px}}</style>
    </head><body><div class="container"><h1>🌤 MeteoBot</h1><p>Smart weather bot with subscription</p>
    <div class="status"><div class="status-item"><span class="label">Status:</span> <span class="value">🟢 Running</span></div>
    <div class="status-item"><span class="label">Version:</span> <span class="value">3.0 (B2B + Multi-language)</span></div>
    <div class="status-item"><span class="label">Users:</span> <span class="value">{total_users}</span></div>
    <div class="status-item"><span class="label">Time:</span> <span class="value" id="dt"></span></div></div>
    <a href="/admin" class="btn">🔐 Admin Panel</a>
    <div class="version">Running on PythonAnywhere</div></div>
    <script>document.getElementById('dt').textContent = new Date().toLocaleString('ru-RU');</script></body></html>'''

@app.route('/set_webhook', methods=['GET'])
@app.route('/set_webhook', methods=['GET'])
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
        return f"Error: {e}"

def webhook_info():
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/getWebhookInfo"
    try:
        response = requests.get(url, timeout=30)
        return response.json()
    except Exception as e:
        return {'error': str(e)}

