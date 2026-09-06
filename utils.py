#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Утилиты Telegram API: отправка сообщений, фото, длинные тексты, callback."""
import logging
import time as _time
import requests

from config import *
from texts import T
from storage import get_user_lang

logger = logging.getLogger(__name__)

def send_message(chat_id, text, keyboard=None):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": chat_id, "text": text, "parse_mode": "Markdown"}
    if keyboard:
        payload["reply_markup"] = keyboard

    try:
        response = requests.post(url, json=payload, timeout=30)
        if response.status_code != 200:
            logger.error(f"Ошибка отправки: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки: {e}")
        return None
def send_photo(chat_id, photo_path, caption=""):
    """Send a local image to Telegram."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendPhoto"
    try:
        with open(photo_path, "rb") as photo:
            response = requests.post(
                url,
                data={"chat_id": chat_id, "caption": caption, "parse_mode": "Markdown"},
                files={"photo": photo},
                timeout=60,
            )
        if response.status_code != 200:
            logger.error(f"Ошибка отправки фото: {response.text}")
        return response.json()
    except Exception as e:
        logger.error(f"Ошибка отправки фото: {e}", exc_info=True)
        return None
def send_long_text(chat_id, text, keyboard=None):
    """Отправляет длинный текст частями (лимит Telegram 4096)."""
    limit = 4000
    if len(text) <= limit:
        send_message(chat_id, text, keyboard)
        return
    parts = []
    current = ""
    for block in text.split("\n\n"):
        if len(current) + len(block) + 2 > limit:
            if current:
                parts.append(current)
            if len(block) > limit:
                for line in block.split("\n"):
                    if len(current) + len(line) + 1 > limit:
                        if current:
                            parts.append(current)
                        current = line
                    else:
                        current = current + "\n" + line if current else line
            else:
                current = block
        else:
            current = current + "\n\n" + block if current else block
    if current:
        parts.append(current)
    for i, part in enumerate(parts):
        send_message(chat_id, part, keyboard if i == len(parts) - 1 else None)
def answer_callback_query(callback_query_id, text=None):
    """Отвечает на callback_query чтобы убрать 'часики' у пользователя."""
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/answerCallbackQuery"
    payload = {"callback_query_id": callback_query_id}
    if text:
        payload["text"] = text
    try:
        requests.post(url, json=payload, timeout=10)
    except Exception as e:
        logger.error(f"Ошибка answer_callback_query: {e}")

def _paywall(chat_id, required_plan="premium"):
    lang = get_user_lang(chat_id)
    if required_plan == "business":
        text = T(lang, "business_required")
        keyboard = {"keyboard": [[T(lang, "btn_business_sub")], [T(lang, "btn_back")]], "resize_keyboard": True}
    else:
        text = T(lang, "premium_required_paywall")
        keyboard = {"keyboard": [[T(lang, "btn_personal"), T(lang, "btn_business_sub")], [T(lang, "btn_back")]], "resize_keyboard": True}
    send_message(chat_id, text, keyboard)

