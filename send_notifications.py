#!/usr/bin/env python3
"""
Скрипт для отправки погодных уведомлений с предупреждениями.
Вызывается через веб-хук /api/cron_notifications (cron-job.org каждый час).

Отправляет уведомления:
- Срабатывания по порогам (жара, мороз, ветер, дождь, гроза)
- Если все предупреждения выключены — отправляет обычный прогноз на завтра
"""

import sys
import os
from datetime import datetime

sys.path.insert(0, '/home/mob100500lvl/WeatherTomBot/WeatherTomBot')

from features import _db, notification_prefs, track
from bot import (
    get_tomorrow_detailed_forecast,
    format_tomorrow_forecast_text,
    get_user_city, get_user_lang, send_message, T
)

def should_send_today(prefs, now):
    """Проверяет, нужно ли отправлять уведомление сегодня."""
    frequency = prefs.get("frequency", "daily")
    if frequency == "daily":
        return True
    elif frequency == "weekly":
        return now.weekday() == 0
    elif frequency == "weekdays":
        return now.weekday() < 5
    elif frequency == "weekends":
        return now.weekday() >= 5
    return True

DEFAULT_THRESHOLDS = {
    "heat": 30, "wind": 15, "heavy_rain": 10, "rain": 0.1, "frost": 0,
}

def _alert_cfg(prefs, kind):
    """Возвращает конфиг предупреждения с fallback для старых пользователей."""
    alerts = prefs.get("alerts", {}) or {}
    cfg = alerts.get(kind)
    if not isinstance(cfg, dict):
        # Если блока alerts нет — используем верхнеуровневый флаг
        return {"enabled": bool(prefs.get(kind, True)), "threshold": DEFAULT_THRESHOLDS.get(kind)}
    return cfg

def check_alerts(tomorrow, prefs, lang):
    """Проверяет пороги и формирует список срабатываний."""
    triggered = []
    
    if not tomorrow or "error" in tomorrow:
        return triggered
    
    temp_max = tomorrow.get('temp_max', 0) or 0
    temp_min = tomorrow.get('temp_min', 0) or 0
    precip = tomorrow.get('precipitation_sum', 0) or 0
    wind_max = tomorrow.get('wind_max', 0) or 0
    weather_code = tomorrow.get('weather_code', 0) or 0
    desc = tomorrow.get('description', '')
    
    # Жара
    heat_cfg = _alert_cfg(prefs, "heat")
    if heat_cfg.get("enabled"):
        thr = heat_cfg.get("threshold") or 30
        if temp_max >= thr:
            triggered.append({
                "type": "heat",
                "text": T(lang, "alert_heat", temp=round(temp_max, 1), thr=thr)
            })
    
    # Мороз
    frost_cfg = _alert_cfg(prefs, "frost")
    if frost_cfg.get("enabled"):
        thr = frost_cfg.get("threshold")
        if thr is None or thr == 0:
            if temp_min <= 0:
                triggered.append({
                    "type": "frost",
                    "text": T(lang, "alert_frost", temp=round(temp_min, 1), thr=0)
                })
        elif temp_min <= thr:
            triggered.append({
                "type": "frost",
                "text": T(lang, "alert_frost", temp=round(temp_min, 1), thr=thr)
            })
    
    # Сильный ветер
    wind_cfg = _alert_cfg(prefs, "wind")
    if wind_cfg.get("enabled"):
        thr = wind_cfg.get("threshold") or 15
        if wind_max >= thr:
            triggered.append({
                "type": "wind",
                "text": T(lang, "alert_wind", speed=round(wind_max, 1), thr=thr)
            })
    
    # Гроза (weather_code 95-99)
    storm_cfg = _alert_cfg(prefs, "storm")
    if storm_cfg.get("enabled") and 95 <= weather_code <= 99:
        triggered.append({
            "type": "storm",
            "text": T(lang, "alert_storm", desc=desc)
        })
    
    # Сильный дождь
    heavy_cfg = _alert_cfg(prefs, "heavy_rain")
    if heavy_cfg.get("enabled"):
        thr = heavy_cfg.get("threshold") or 10
        if precip >= thr:
            triggered.append({
                "type": "heavy_rain",
                "text": T(lang, "alert_heavy_rain", mm=round(precip, 1), thr=thr)
            })
    
    # Обычный дождь (если не сработал сильный и если осадки > 0.1)
    rain_cfg = _alert_cfg(prefs, "rain")
    if rain_cfg.get("enabled"):
        thr = rain_cfg.get("threshold") or 0.1
        # Не дублируем, если уже есть heavy_rain
        if not any(a["type"] == "heavy_rain" for a in triggered) and precip >= thr and 51 <= weather_code <= 82:
            triggered.append({
                "type": "rain",
                "text": T(lang, "alert_rain", mm=round(precip, 1))
            })
    
    return triggered

def build_alert_message(lang, tomorrow, alerts):
    """Формирует сообщение с предупреждениями."""
    text = T(lang, "alert_title") + "\n\n"
    for a in alerts:
        text += a["text"] + "\n\n"
    
    # Краткий прогноз
    text += f"🌡 {round(tomorrow['temp_min'])}°...{round(tomorrow['temp_max'])}°\n"
    text += f"💨 {round(tomorrow.get('wind_max', 0), 1)} м/с\n"
    text += f"🌧 {round(tomorrow.get('precipitation_sum', 0), 1)} мм\n"
    text += f"☀️ {tomorrow.get('description', '')}"
    
    return text

def send_notification(chat_id, lang, city, prefs):
    """Отправляет уведомление: предупреждения или прогноз."""
    tomorrow = get_tomorrow_detailed_forecast(city, lang)
    
    if not tomorrow or "error" in tomorrow:
        print(f"  ✗ Ошибка прогноза для {city}")
        return False
    
    # Проверяем срабатывания по порогам
    alerts = check_alerts(tomorrow, prefs, lang)
    
    if alerts:
        # Есть срабатывания — отправляем предупреждения
        text = build_alert_message(lang, tomorrow, alerts)
        send_message(chat_id, text)
        print(f"  ✓ Отправлено {len(alerts)} предупреждений")
    else:
        # Нет срабатываний — отправляем полный прогноз
        text = format_tomorrow_forecast_text(chat_id, tomorrow)
        send_message(chat_id, text)
        print(f"  ✓ Отправлен прогноз на завтра")
    
    return True

def main():
    """Основная функция."""
    now = datetime.now()
    current_hour = now.strftime("%H")
    
    print(f"[{now.strftime('%Y-%m-%d %H:%M:%S')}] Запуск проверки уведомлений...")
    print(f"  Текущее время: {now.strftime('%H:%M')}")
    
    db = _db()
    users = db.get("users", {})
    
    sent_count = 0
    error_count = 0
    skipped_count = 0
    checked_count = 0
    
    for uid, user_data in users.items():
        try:
            prefs = notification_prefs(uid)
            
            if not prefs.get("enabled", False):
                skipped_count += 1
                continue
            
            checked_count += 1
            
            user_time = prefs.get("time") or "08:00"
            try:
                user_hour = str(user_time).split(":")[0]
            except:
                user_hour = "08"
            
            if user_hour != current_hour:
                continue
            
            if not should_send_today(prefs, now):
                continue
            
            city = prefs.get("city") or user_data.get("city") or get_user_city(int(uid))
            if not city:
                print(f"  - {uid}: нет города")
                continue
            
            lang = user_data.get("lang", "ru")
            
            print(f"  → Отправка {uid} ({city}, {lang})...")
            success = send_notification(int(uid), lang, city, prefs)
            
            if success:
                sent_count += 1
                track(uid, "notification_sent", {"city": city, "time": user_time})
            else:
                error_count += 1
            
        except Exception as e:
            error_count += 1
            print(f"  ✗ Критическая ошибка для {uid}: {e}")
    
    print(f"\nРезультат: проверено {checked_count}, отправлено {sent_count}, пропущено {skipped_count}, ошибок {error_count}")

if __name__ == "__main__":
    main()
