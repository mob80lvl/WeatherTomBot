#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Погода: агрегация, прогнозы, UV, луна, B2B-прогнозы, форматирование."""
import math
import logging
from datetime import datetime, timedelta
import requests

from config import *
from texts import T, b2b_name, b2b_features, api_language
from storage import get_user_lang, get_user_city

try:
    import features as advanced_features
except Exception:
    advanced_features = None

logger = logging.getLogger(__name__)

def get_uv_level(uv, lang="ru"):
    if uv is None:
        return None
    try:
        uv = float(uv)
    except (TypeError, ValueError):
        return None
    if uv < 3:
        return T(lang, "uv_low")
    elif uv < 6:
        return T(lang, "uv_moderate")
    elif uv < 8:
        return T(lang, "uv_high")
    elif uv < 11:
        return T(lang, "uv_very_high")
    else:
        return T(lang, "uv_extreme")
def convert_pressure_to_mmhg(pressure_hpa):
    """Конвертирует давление из гектопаскалей (hPa) в миллиметры ртутного столба (мм рт.ст.)."""
    if pressure_hpa is None:
        return None
    # 1 hPa = 0.750062 мм рт.ст.
    return round(pressure_hpa * 0.750062, 1)
def get_weather_aggregated(city_name, lang="en"):
    results = []
    errors = []

    try:
        owm_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric&lang={api_language(lang)}"
        resp = requests.get(owm_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            results.append({
                "temp": data['main']['temp'],
                "humidity": data['main']['humidity'],
                "wind": data['wind']['speed'],
                "wind_deg": data['wind'].get('deg', 0),
                "pressure": data['main'].get('pressure'),
                "description": data['weather'][0]['description'],
                "weather_id": data['weather'][0].get('id', 0),
                "source": "OpenWeatherMap"
            })
        else:
            errors.append(f"OWM: {resp.status_code}")
    except Exception as e:
        errors.append(f"OWM: {str(e)}")

    try:
        wa_url = f"https://api.weatherapi.com/v1/current.json?key={WEATHERAPI_KEY}&q={city_name}&lang={api_language(lang)}"
        wa_resp = requests.get(wa_url, timeout=10)
        if wa_resp.status_code == 200:
            data = wa_resp.json()
            results.append({
                "temp": data['current']['temp_c'],
                "humidity": data['current']['humidity'],
                "wind": data['current']['wind_kph'] / 3.6,
                "wind_deg": data['current'].get('wind_degree', 0),
                "pressure": data['current'].get('pressure_mb'),
                "uv": data['current'].get('uv'),
                "description": data['current']['condition']['text'],
                "source": "WeatherAPI"
            })
        else:
            errors.append(f"WeatherAPI: {wa_resp.status_code}")
    except Exception as e:
        errors.append(f"WeatherAPI: {str(e)}")

    try:
        geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url, timeout=5)
        if geo_resp.status_code == 200:
            geo = geo_resp.json()
            lat, lon = geo['coord']['lat'], geo['coord']['lon']
            om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&current_weather=true"
            om_resp = requests.get(om_url, timeout=10)
            if om_resp.status_code == 200:
                data = om_resp.json()['current_weather']
                results.append({
                    "temp": data['temperature'],
                    "wind": data['windspeed'],
                    "wind_deg": data.get('winddirection', 0),
                    "weathercode": data.get('weathercode', 0),
                    "source": "Open-Meteo"
                })
            else:
                errors.append(f"Open-Meteo: {om_resp.status_code}")
    except Exception as e:
        errors.append(f"Open-Meteo: {str(e)}")

    if not results:
        error_msg = "; ".join(errors) if errors else "Нет данных от API"
        return {"error": f"Не удалось получить погоду: {error_msg}"}

    avg_temp = sum(r['temp'] for r in results) / len(results)
    humidity_values = [r.get('humidity', 50) for r in results if 'humidity' in r]
    avg_humidity = sum(humidity_values) / len(humidity_values) if humidity_values else 50
    wind_values = [r['wind'] for r in results if 'wind' in r]
    avg_wind = sum(wind_values) / len(wind_values) if wind_values else 0
    
    # Среднее направление ветра
    wind_deg_values = [r.get('wind_deg') for r in results if r.get('wind_deg') is not None]
    avg_wind_deg = sum(wind_deg_values) / len(wind_deg_values) if wind_deg_values else 0
    
    # Среднее давление (конвертируем из hPa в мм рт.ст.)
    pressure_values = [r.get('pressure') for r in results if r.get('pressure')]
    avg_pressure_hpa = sum(pressure_values) / len(pressure_values) if pressure_values else None
    avg_pressure = convert_pressure_to_mmhg(avg_pressure_hpa) if avg_pressure_hpa else None
    
    # UV индекс (берём из WeatherAPI если есть)
    uv_values = [r.get('uv') for r in results if r.get('uv') is not None]
    avg_uv = sum(uv_values) / len(uv_values) if uv_values else None
    descriptions = [r.get('description') for r in results if r.get('description')]
    if descriptions:
        from collections import Counter
        desc_counter = Counter(descriptions)
        description = desc_counter.most_common(1)[0][0]
    else:
        description = T(lang, "weather_unknown")

    return {
        "city": city_name,
        "country": "RU",
        "temp": round(avg_temp, 1),
        "feels_like": round(avg_temp - 1, 1),
        "humidity": round(avg_humidity),
        "description": description,
        "wind_speed": round(avg_wind, 1),
        "wind_deg": round(avg_wind_deg),
        "pressure": round(avg_pressure, 1) if avg_pressure else None,
        "uv": round(avg_uv, 1) if avg_uv else None,
        "weather_id": next((r.get('weather_id') for r in results if r.get('weather_id')), None),
        "source_count": len(results),
        "sources": [r['source'] for r in results]
    }
def get_forecast_aggregated(city_name, days=10, lang="en"):
    daily_data = {}
    lat = lon = None
    daily_min_temps = {}
    daily_max_temps = {}
    daily_weather_codes = {}
    daily_uv_max = {}
    daily_precip_sum = {}

    try:
        owm_url = f"https://api.openweathermap.org/data/2.5/forecast?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric&lang={api_language(lang)}"
        resp = requests.get(owm_url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            _coord = data.get('city', {}).get('coord', {})
            if _coord:
                lat, lon = _coord.get('lat'), _coord.get('lon')
            for item in data['list']:
                date = item['dt_txt'].split()[0]
                if date not in daily_data:
                    daily_data[date] = {"temps": [], "descriptions": [], "rains": [], "winds": [], "wind_degs": [], "humidities": [], "pressures": [], "weather_codes": [], "feels": [], "precip_probs": []}
                daily_data[date]["temps"].append(item['main']['temp'])
                daily_data[date]["descriptions"].append(item['weather'][0]['description'])
                daily_data[date]["rains"].append(item.get('rain', {}).get('3h', 0))
                daily_data[date]["winds"].append(item['wind']['speed'])
                if item.get("wind", {}).get("deg") is not None:
                    daily_data[date]["wind_degs"].append(float(item["wind"]["deg"]))
    except Exception as e:
        logger.error(f"OWM Forecast ошибка: {e}")

    try:
        if lat is None:
            geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
            geo_resp = requests.get(geo_url, timeout=5)
            if geo_resp.status_code == 200:
                geo = geo_resp.json()
                lat, lon = geo['coord']['lat'], geo['coord']['lon']
        if lat is not None:
            om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,apparent_temperature,relative_humidity_2m,precipitation,precipitation_probability,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,uv_index&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_sum,wind_speed_10m_max&timezone=auto&forecast_days=14"
            om_resp = requests.get(om_url, timeout=10)
            if om_resp.status_code == 200:
                data = om_resp.json()
                for i, time in enumerate(data['hourly']['time']):
                    date = time.split('T')[0]
                    if date not in daily_data:
                        daily_data[date] = {"temps": [], "descriptions": [], "rains": [], "winds": [], "wind_degs": [], "humidities": [], "pressures": [], "weather_codes": [], "feels": [], "precip_probs": []}
                    daily_data[date]["temps"].append(data['hourly']['temperature_2m'][i])
                    daily_data[date]["rains"].append(data['hourly']['precipitation'][i])
                    daily_data[date]["winds"].append(data['hourly']['wind_speed_10m'][i])
                    if data['hourly'].get('wind_direction_10m'):
                        daily_data[date]["wind_degs"].append(float(data['hourly']['wind_direction_10m'][i]))
    except Exception as e:
        logger.error(f"Open-Meteo Forecast ошибка: {e}")

    if not daily_data:
        return {"error": T(lang, "error_no_data_forecast")}

    def _wind_direction(degrees):
        if not degrees:
            return "—"
        import math as _math
        sx = sum(_math.sin(_math.radians(x)) for x in degrees)
        cx = sum(_math.cos(_math.radians(x)) for x in degrees)
        angle = (_math.degrees(_math.atan2(sx, cx)) + 360) % 360
        return wind_deg_to_direction(angle, lang)

    result = {}
    days_list = sorted(daily_data.keys())[:days]
    
    # Инициализируем daily данные (могут быть не заполнены если Open-Meteo недоступен)
    daily_min_temps = {}
    daily_max_temps = {}
    daily_weather_codes = {}
    daily_uv_max = {}
    daily_precip_sum = {}
    
    # Пытаемся получить daily данные из Open-Meteo если они ещё не загружены
    try:
        geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url, timeout=5)
        if geo_resp.status_code == 200:
            geo = geo_resp.json()
            lat, lon = geo['coord']['lat'], geo['coord']['lon']
            om_daily_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&daily=temperature_2m_max,temperature_2m_min,weather_code,uv_index_max,precipitation_sum&timezone=auto&forecast_days=14"
            om_daily_resp = requests.get(om_daily_url, timeout=10)
            if om_daily_resp.status_code == 200:
                daily_info = om_daily_resp.json().get('daily', {})
                daily_dates = daily_info.get('time', [])
                daily_min_temps = {d: t for d, t in zip(daily_dates, daily_info.get('temperature_2m_min', []))}
                daily_max_temps = {d: t for d, t in zip(daily_dates, daily_info.get('temperature_2m_max', []))}
                daily_weather_codes = {d: c for d, c in zip(daily_dates, daily_info.get('weather_code', []))}
                daily_uv_max = {d: u for d, u in zip(daily_dates, daily_info.get('uv_index_max', []))}
                daily_precip_sum = {d: p for d, p in zip(daily_dates, daily_info.get('precipitation_sum', []))}
    except Exception as e:
        logger.error(f"Ошибка получения daily данных: {e}")

    for date in days_list:
        data = daily_data[date]
        if data["temps"]:
            date_obj = datetime.strptime(date, "%Y-%m-%d")
            
            # Описание погоды
            descriptions = data.get("descriptions", [])
            if descriptions:
                from collections import Counter
                desc_counter = Counter(descriptions)
                description = desc_counter.most_common(1)[0][0]
            else:
                # По коду погоды из Open-Meteo
                weather_codes = data.get("weather_codes", [])
                if weather_codes:
                    wc = max(set(weather_codes), key=weather_codes.count)
                    if wc in (0, 1):
                        description = T(lang, "weather_clear")
                    elif wc in (2, 3):
                        description = T(lang, "weather_partly_cloudy")
                    elif 51 <= wc <= 57:
                        description = T(lang, "weather_drizzle")
                    elif 61 <= wc <= 67:
                        description = T(lang, "weather_rain")
                    elif 71 <= wc <= 77:
                        description = T(lang, "weather_snow")
                    elif 80 <= wc <= 82:
                        description = T(lang, "weather_shower")
                    elif 95 <= wc <= 99:
                        description = T(lang, "weather_thunderstorm")
                    else:
                        description = T(lang, "weather_cloudy")
                else:
                    description = T(lang, "forecast_word")
            
            # Средние значения
            avg_temp = round(sum(data["temps"]) / len(data["temps"]), 1)
            avg_feels = round(sum(data.get("feels", [avg_temp])) / len(data.get("feels", [avg_temp])), 1) if data.get("feels") else avg_temp
            avg_humidity = round(sum(data.get("humidities", [50])) / len(data.get("humidities", [50]))) if data.get("humidities") else 50
            avg_wind = round(sum(data["winds"]) / len(data["winds"]) / 3.6, 1) if data["winds"] else 0
            avg_pressure = round(sum(data.get("pressures", [1013])) / len(data.get("pressures", [1013])) * 0.750062, 1) if data.get("pressures") else 760
            avg_precip_prob = round(sum(data.get("precip_probs", [0])) / len(data.get("precip_probs", [0]))) if data.get("precip_probs") else 0
            
            # Min/Max температура из daily
            temp_min = daily_min_temps.get(date, min(data["temps"]))
            temp_max = daily_max_temps.get(date, max(data["temps"]))
            
            # UV индекс из daily
            uv_max = daily_uv_max.get(date)
            
            # Суммарные осадки из daily
            precip_sum = daily_precip_sum.get(date, sum(data["rains"]))
            
            result[date] = {
                'date_str': date_obj.strftime("%d.%m.%Y"),
                'weekday': T(lang, f"weekday_{date_obj.weekday()}"),
                'temp': avg_temp,
                'temp_min': round(temp_min, 1),
                'temp_max': round(temp_max, 1),
                'feels_like': avg_feels,
                'description': description,
                'rain': round(precip_sum, 1) if precip_sum else 0,
                'precip_prob': avg_precip_prob,
                'wind_speed': avg_wind,
                'wind_direction': _wind_direction(data.get("wind_degs", [])),
                'humidity': avg_humidity,
                'pressure': avg_pressure,
                'uv': round(uv_max, 1) if uv_max else None
            }

    return result
def get_tomorrow_detailed_forecast(city_name, lang="en"):
    """Получает детальный прогноз на завтрашний день."""
    try:
        # Получаем координаты города
        geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url, timeout=10)
        if geo_resp.status_code != 200:
            return {"error": "Не удалось получить координаты города"}
        
        try:
            geo = geo_resp.json()
        except Exception:
            return {"error": "Не удалось получить координаты города"}
        lat, lon = geo['coord']['lat'], geo['coord']['lon']
        country = geo.get('sys', {}).get('country', '')
        
        # Получаем прогноз от Open-Meteo (есть все нужные данные)
        om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,relative_humidity_2m,apparent_temperature,precipitation_probability,weather_code,wind_speed_10m,wind_direction_10m,pressure_msl,uv_index&daily=weather_code,temperature_2m_max,temperature_2m_min,sunrise,sunset,uv_index_max,precipitation_sum,wind_speed_10m_max&timezone=auto&forecast_days=2"
        om_resp = None
        for _attempt in range(2):
            try:
                om_resp = requests.get(om_url, timeout=30)
                if om_resp.status_code == 200:
                    break
            except requests.exceptions.Timeout:
                if _attempt == 0:
                    import time as _time
                    _time.sleep(1)
                    continue
                return {"error": "Превышено время ожидания прогноза"}
            except requests.exceptions.RequestException as e:
                return {"error": f"Ошибка сети: {e}"}
        
        if om_resp is None or om_resp.status_code != 200:
            return {"error": "Не удалось получить прогноз"}
        
        try:
            data = om_resp.json()
        except Exception:
            return {"error": "Не удалось получить прогноз"}
        
        # Берём данные на завтра (индекс 1, т.к. 0 - сегодня)
        if 'daily' not in data or len(data['daily']['time']) < 2:
            return {"error": "Нет данных на завтра"}
        
        tomorrow = {
            'date': data['daily']['time'][1],
            'temp_max': data['daily']['temperature_2m_max'][1],
            'temp_min': data['daily']['temperature_2m_min'][1],
            'weather_code': data['daily']['weather_code'][1],
            'sunrise': data['daily']['sunrise'][1],
            'sunset': data['daily']['sunset'][1],
            'precipitation_sum': data['daily']['precipitation_sum'][1],
            'wind_max': data['daily']['wind_speed_10m_max'][1],
            'uv_max': data['daily']['uv_index_max'][1],
            'country': country,
            'city': city_name
        }
        
        # Средние значения за день из hourly данных
        # Находим индексы часов для завтрашнего дня
        hourly_times = data['hourly']['time']
        tomorrow_date = tomorrow['date']
        
        hourly_data = {
            'temps': [],
            'humidity': [],
            'pressure': [],
            'uv': [],
            'wind_speed': [],
            'wind_deg': [],
            'precip_prob': [],
            'apparent_temp': []
        }
        
        for i, time_str in enumerate(hourly_times):
            if time_str.startswith(tomorrow_date):
                hourly_data['temps'].append(data['hourly']['temperature_2m'][i])
                hourly_data['humidity'].append(data['hourly']['relative_humidity_2m'][i])
                hourly_data['pressure'].append(data['hourly']['pressure_msl'][i])
                hourly_data['uv'].append(data['hourly']['uv_index'][i])
                hourly_data['wind_speed'].append(data['hourly']['wind_speed_10m'][i])
                hourly_data['wind_deg'].append(data['hourly']['wind_direction_10m'][i])
                hourly_data['precip_prob'].append(data['hourly']['precipitation_probability'][i])
                hourly_data['apparent_temp'].append(data['hourly']['apparent_temperature'][i])
        
        # Считаем средние
        tomorrow['avg_temp'] = round(sum(hourly_data['temps']) / len(hourly_data['temps']), 1) if hourly_data['temps'] else 0
        tomorrow['avg_feels'] = round(sum(hourly_data['apparent_temp']) / len(hourly_data['apparent_temp']), 1) if hourly_data['apparent_temp'] else 0
        tomorrow['avg_humidity'] = round(sum(hourly_data['humidity']) / len(hourly_data['humidity'])) if hourly_data['humidity'] else 0
        tomorrow['avg_pressure'] = round(sum(hourly_data['pressure']) / len(hourly_data['pressure']) * 0.750062, 1) if hourly_data['pressure'] else 0
        tomorrow['avg_uv'] = round(sum(hourly_data['uv']) / len(hourly_data['uv']), 1) if hourly_data['uv'] else 0
        tomorrow['avg_wind'] = round(sum(hourly_data['wind_speed']) / len(hourly_data['wind_speed']) / 3.6, 1) if hourly_data['wind_speed'] else 0
        
        # Среднее направление ветра
        if hourly_data['wind_deg']:
            import math
            sx = sum(math.sin(math.radians(d)) for d in hourly_data['wind_deg'] if d is not None)
            cx = sum(math.cos(math.radians(d)) for d in hourly_data['wind_deg'] if d is not None)
            avg_deg = (math.degrees(math.atan2(sx, cx)) + 360) % 360
            tomorrow['wind_deg'] = round(avg_deg)
        else:
            tomorrow['wind_deg'] = 0
        
        # Средняя вероятность осадков
        tomorrow['precip_prob'] = round(sum(hourly_data['precip_prob']) / len(hourly_data['precip_prob'])) if hourly_data['precip_prob'] else 0
        
        # Описание погоды по коду
        weather_code = tomorrow['weather_code']
        if weather_code in (0, 1):
            tomorrow['description'] = T(lang, "weather_clear")
        elif weather_code in (2, 3):
            tomorrow['description'] = T(lang, "weather_partly_cloudy")
        elif weather_code in (45, 48):
            tomorrow['description'] = T(lang, "weather_fog")
        elif 51 <= weather_code <= 57:
            tomorrow['description'] = T(lang, "weather_drizzle")
        elif 61 <= weather_code <= 67:
            tomorrow['description'] = T(lang, "weather_rain")
        elif 71 <= weather_code <= 77:
            tomorrow['description'] = T(lang, "weather_snow")
        elif 80 <= weather_code <= 82:
            tomorrow['description'] = T(lang, "weather_shower")
        elif 85 <= weather_code <= 86:
            tomorrow['description'] = T(lang, "weather_snow_shower")
        elif 95 <= weather_code <= 99:
            tomorrow['description'] = T(lang, "weather_thunderstorm")
        else:
            tomorrow['description'] = T(lang, "weather_cloudy")
        
        return tomorrow
        
    except Exception as e:
        return {"error": f"Ошибка получения прогноза: {str(e)}"}
def format_tomorrow_forecast_text(chat_id, forecast_data):
    if "error" in forecast_data:
        return f"❌ {forecast_data['error']}"
    from datetime import datetime
    date_obj = datetime.strptime(forecast_data['date'], '%Y-%m-%d')
    lang = get_user_lang(chat_id)
    if lang == "ru":
        weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
    else:
        weekdays = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    weekday = weekdays[date_obj.weekday()]
    weather_code = forecast_data['weather_code']
    if weather_code in (0, 1): icon = "☀️"
    elif weather_code in (2, 3): icon = "⛅"
    elif weather_code in (45, 48): icon = "🌫"
    elif 51 <= weather_code <= 57: icon = "🌦"
    elif 61 <= weather_code <= 67: icon = "🌧"
    elif 71 <= weather_code <= 77: icon = "❄️"
    elif 80 <= weather_code <= 82: icon = "🌧"
    elif 85 <= weather_code <= 86: icon = "❄️"
    elif 95 <= weather_code <= 99: icon = "⛈"
    else: icon = "☁️"
    wind_dir = wind_deg_to_direction(forecast_data.get('wind_deg'), lang)
    uv_level = get_uv_level(forecast_data.get('uv_max'), lang)
    sunrise = forecast_data.get('sunrise', '').split('T')[1] if 'T' in forecast_data.get('sunrise', '') else '—'
    sunset = forecast_data.get('sunset', '').split('T')[1] if 'T' in forecast_data.get('sunset', '') else '—'
    text = f"📅 {icon} {weekday}, {date_obj.strftime('%d.%m.%Y')}\n\n"
    text += f"📍 {forecast_data['city']}, {forecast_data['country']}\n\n"
    text += T(lang, "temp", temp=f"{forecast_data['temp_min']}...{forecast_data['temp_max']}") + "\n"
    text += T(lang, "feels_like", feels=forecast_data['avg_feels']) + "\n"
    text += T(lang, "wind_full", wind=forecast_data['avg_wind'], direction=wind_dir) + "\n"
    text += T(lang, "humidity", humidity=forecast_data['avg_humidity']) + "\n"
    text += T(lang, "pressure_mm", pressure=forecast_data['avg_pressure']) + "\n"
    if uv_level:
        text += T(lang, "uv_with_level", uv=forecast_data['uv_max'], level=uv_level) + "\n"
    text += T(lang, "precip_prob", prob=forecast_data['precip_prob']) + "\n"
    text += T(lang, "sunrise", time=sunrise) + "\n"
    text += T(lang, "sunset", time=sunset) + "\n\n"
    text += f"{forecast_data['description']}\n\n"
    text += T(lang, "updated_time", time=datetime.now().strftime('%H:%M:%S'))
    return text
def get_weather_statistics(city_name, days=14):
    stats = {
        "avg_temp": 0,
        "max_temp": -100,
        "min_temp": 100,
        "avg_humidity": 0,
        "rain_days": 0,
        "clear_days": 0,
        "cloudy_days": 0,
        "total_rain": 0,
        "days": []
    }

    try:
        geo_url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}"
        geo_resp = requests.get(geo_url, timeout=5)
        if geo_resp.status_code != 200:
            return {"error": "Не удалось получить геоданные"}

        geo = geo_resp.json()
        lat, lon = geo['coord']['lat'], geo['coord']['lon']

        om_url = f"https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lon}&hourly=temperature_2m,precipitation&forecast_days=14"
        om_resp = requests.get(om_url, timeout=10)
        if om_resp.status_code == 200:
            data = om_resp.json()
            temps = data['hourly']['temperature_2m'][:24*14]
            rains = data['hourly']['precipitation'][:24*14]

            for i in range(0, len(temps), 24):
                day_temps = temps[i:i+24]
                day_rains = rains[i:i+24]
                if day_temps:
                    avg = sum(day_temps) / len(day_temps)
                    max_t = max(day_temps)
                    min_t = min(day_temps)
                    rain_sum = sum(day_rains)

                    stats["days"].append({
                        "avg": avg,
                        "max": max_t,
                        "min": min_t,
                        "rain": rain_sum
                    })

                    stats["avg_temp"] += avg
                    stats["max_temp"] = max(stats["max_temp"], max_t)
                    stats["min_temp"] = min(stats["min_temp"], min_t)
                    stats["total_rain"] += rain_sum
                    if rain_sum > 0:
                        stats["rain_days"] += 1
                    if rain_sum == 0 and max_t > 20:
                        stats["clear_days"] += 1
                    if rain_sum > 0 and max_t < 15:
                        stats["cloudy_days"] += 1

            if stats["days"]:
                stats["avg_temp"] = round(stats["avg_temp"] / len(stats["days"]), 1)
                stats["max_temp"] = round(stats["max_temp"], 1)
                stats["min_temp"] = round(stats["min_temp"], 1)
                stats["total_rain"] = round(stats["total_rain"], 1)
                stats["city"] = city_name
                return stats

    except Exception as e:
        logger.error(f"Статистика ошибка: {e}")

    return {"error": "Не удалось получить статистику"}
def get_sunrise_sunset(city_name, lang="en"):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city_name}&appid={OPENWEATHER_API_KEY}&units=metric&lang={api_language(lang)}"
    try:
        resp = requests.get(url, timeout=10)
        if resp.status_code == 200:
            data = resp.json()
            sunrise = datetime.fromtimestamp(data['sys']['sunrise']).strftime('%H:%M')
            sunset = datetime.fromtimestamp(data['sys']['sunset']).strftime('%H:%M')
            diff = data['sys']['sunset'] - data['sys']['sunrise']
            return {
                "city": data['name'],
                "country": data['sys']['country'],
                "sunrise": sunrise,
                "sunset": sunset,
                "day_length": f"{int(diff//3600)}ч {int((diff%3600)//60)}м"
            }
        return {"error": f"Ошибка API: {resp.status_code}"}
    except Exception as e:
        return {"error": f"Ошибка: {str(e)}"}
def get_moon_phase(lang="en"):
    today = datetime.now()
    phase = (today.year * 12 + today.month + today.day) % 30
    if phase < 2: key, emoji = "moon_new", "🌑"
    elif phase < 7: key, emoji = "moon_waxing_crescent", "🌒"
    elif phase < 10: key, emoji = "moon_first_quarter", "🌓"
    elif phase < 15: key, emoji = "moon_waxing_gibbous", "🌔"
    elif phase < 18: key, emoji = "moon_full", "🌕"
    elif phase < 23: key, emoji = "moon_waning_gibbous", "🌖"
    elif phase < 26: key, emoji = "moon_last_quarter", "🌗"
    else: key, emoji = "moon_old", "🌘"
    return {"name": T(lang, key), "emoji": emoji}
def get_agri_forecast(city_name, lang="en"):
    weather = get_weather_aggregated(city_name, lang)
    if "error" in weather:
        return {"error": weather["error"]}
    soil_temp = weather['temp'] - 2
    frost = T(lang, "frost_expected") if weather['temp'] < 2 else T(lang, "frost_not_expected")
    recommendations = []
    if weather['temp'] < 0: recommendations.append(T(lang, "agri_rec_frost"))
    if weather.get('rain', 0) > 10: recommendations.append(T(lang, "agri_rec_wet"))
    elif weather.get('rain', 0) < 5: recommendations.append(T(lang, "agri_rec_water"))
    if weather['temp'] > 25: recommendations.append(T(lang, "agri_rec_heat"))
    if not recommendations: recommendations.append(T(lang, "agri_rec_good"))
    return {"city": city_name, "soil_temp": round(soil_temp, 1), "humidity": weather['humidity'], "rain": weather.get('rain', 0), "frost": frost, "recommendations": "\n".join(recommendations)}
def get_construction_forecast(city_name, lang="en"):
    weather = get_weather_aggregated(city_name, lang)
    if "error" in weather:
        return {"error": weather["error"]}
    wind_safe = weather['wind_speed'] < 10
    recommendations = []
    if wind_safe: recommendations.append(T(lang, "construction_rec_safe"))
    else: recommendations.append(T(lang, "construction_rec_wind"))
    if weather.get('rain', 0) > 5: recommendations.append(T(lang, "construction_rec_rain"))
    if weather['temp'] < -5: recommendations.append(T(lang, "construction_rec_frost"))
    if weather['temp'] > 30: recommendations.append(T(lang, "construction_rec_heat"))
    return {"city": city_name, "wind": weather['wind_speed'], "rain": weather.get('rain', 0), "temp": weather['temp'], "wind_safe": wind_safe, "recommendations": "\n".join(recommendations)}
def get_tourism_forecast(chat_id, city_name):
    lang = get_user_lang(chat_id)
    weather = get_weather_aggregated(city_name, lang)
    sun_data = get_sunrise_sunset(city_name, lang)

    if "error" in weather:
        return {"error": weather["error"]}

    uv_index = 3
    if weather['temp'] > 25:
        uv_index = 7
    elif weather['temp'] > 20:
        uv_index = 5
    elif weather['temp'] > 15:
        uv_index = 3
    else:
        uv_index = 1

    uv_levels = {
        "ru": {0: "Низкий", 1: "Низкий", 2: "Низкий", 3: "Средний", 4: "Средний", 5: "Средний", 6: "Высокий", 7: "Высокий", 8: "Очень высокий", 9: "Очень высокий", 10: "Экстремальный"},
        "en": {0: "Low", 1: "Low", 2: "Low", 3: "Moderate", 4: "Moderate", 5: "Moderate", 6: "High", 7: "High", 8: "Very high", 9: "Very high", 10: "Extreme"},
        "es": {0: "Bajo", 1: "Bajo", 2: "Bajo", 3: "Medio", 4: "Medio", 5: "Medio", 6: "Alto", 7: "Alto", 8: "Muy alto", 9: "Muy alto", 10: "Extremo"},
        "zh": {0: "低", 1: "低", 2: "低", 3: "中等", 4: "中等", 5: "中等", 6: "高", 7: "高", 8: "非常高", 9: "非常高", 10: "极端"}
    }

    recommendations = []
    if uv_index > 6:
        if lang == "ru":
            recommendations.append("🧴 Используйте солнцезащитный крем")
        elif lang == "en":
            recommendations.append("🧴 Use sunscreen")
        elif lang == "es":
            recommendations.append("🧴 Use protector solar")
        else:
            recommendations.append("🧴 使用防晒霜")

    if weather.get('rain', 0) > 2:
        if lang == "ru":
            recommendations.append("☔ Возьмите зонт")
        elif lang == "en":
            recommendations.append("☔ Take an umbrella")
        elif lang == "es":
            recommendations.append("☔ Lleva paraguas")
        else:
            recommendations.append("☔ 带伞")

    if weather['temp'] > 25:
        if lang == "ru":
            recommendations.append("💧 Пейте больше воды")
        elif lang == "en":
            recommendations.append("💧 Drink more water")
        elif lang == "es":
            recommendations.append("💧 Bebe más agua")
        else:
            recommendations.append("💧 多喝水")

    if weather['temp'] < 5:
        if lang == "ru":
            recommendations.append("🧥 Одевайтесь теплее")
        elif lang == "en":
            recommendations.append("🧥 Dress warmly")
        elif lang == "es":
            recommendations.append("🧥 Vístete abrigado")
        else:
            recommendations.append("🧥 穿暖和些")

    if not recommendations:
        if lang == "ru":
            recommendations.append("⭐ Отличная погода для прогулок")
        elif lang == "en":
            recommendations.append("⭐ Great weather for walks")
        elif lang == "es":
            recommendations.append("⭐ Buen clima para pasear")
        else:
            recommendations.append("⭐ 散步的好天气")

    return {
        "city": city_name,
        "weather": weather['description'],
        "temp": weather['temp'],
        "sunrise": sun_data.get('sunrise', '--:--') if 'error' not in sun_data else '--:--',
        "sunset": sun_data.get('sunset', '--:--') if 'error' not in sun_data else '--:--',
        "uv": uv_index,
        "uv_level": uv_levels.get(lang, uv_levels["en"]).get(uv_index, uv_levels["en"][3]),
        "recommendations": "\n".join(recommendations)
    }
def get_clothing_recommendations(chat_id, temp, description, wind_speed):
    """Рекомендации одежды с разнообразными фразами (рандомный выбор)."""
    import random
    lang = get_user_lang(chat_id)
    recommendations = []
    
    # Пул фраз: [язык][диапазон] = список категорий, каждая = список вариантов
    CLOTHING = {
        "ru": {
            "freezing": [
                ["🧥 Тёплый пуховик", "🧥 Зимняя парка", "🧥 Пуховик с капюшоном", "🧥 Утеплённая куртка с мехом", "🧥 Длинный пуховик"],
                ["🧶 Шерстяной свитер", "🧶 Термобельё + свитер", "🧶 Флисовая кофта", "🧶 Вязаный кардиган"],
                ["🧤 Тёплые перчатки", "🧤 Варежки с мехом", "🧤 Утеплённые перчатки", "🧤 Кожаные перчатки с мехом"],
                ["🧣 Шарф и шапка", "🧣 Тёплый снуд и шапка", "🧣 Шерстяной шарф и ушанка", "🧣 Балаклава и шапка"],
                ["🥾 Тёплые ботинки", "🥾 Зимние сапоги", "🥾 Утеплённая обувь", "🥾 Сапоги с мехом"],
            ],
            "cold": [
                ["🧥 Зимняя куртка", "🧥 Тёплая куртка", "🧥 Пальто с утеплителем", "🧥 Пуховик со свитером"],
                ["🧤 Перчатки", "🧤 Лёгкие перчатки", "🧤 Варежки"],
                ["🧣 Шарф", "🧣 Лёгкий шарф", "🧣 Снуд", "🧢 Тёплая шапка"],
                ["🥾 Утеплённые ботинки", "🥾 Зимняя обувь", "🥾 Ботинки с мехом"],
            ],
            "cool": [
                ["🧥 Осенняя куртка или пальто", "🧥 Демисезонная куртка", "🧥 Тёплый свитер и куртка", "🧥 Ветровка с подкладкой", "🧥 Тренч со свитером"],
                ["🧣 Лёгкий шарф", "🧣 Шарф или снуд", "🧣 Палантин", "🧢 Лёгкая шапка"],
                ["🥾 Демисезонная обувь", "🥾 Ботинки", "🥾 Непромокаемые кроссовки"],
            ],
            "mild": [
                ["👕 Лёгкая куртка или свитер", "👕 Кофта или худи", "👕 Джинсовка с футболкой", "👕 Кардиган", "👕 Свитшот с лёгкой курткой"],
                ["👖 Джинсы", "👖 Лёгкие брюки", "👖 Чиносы"],
                ["👟 Кроссовки", "👟 Лёгкая обувь", "👟 Лоферы"],
            ],
            "warm": [
                ["👕 Футболка с длинным рукавом", "👕 Лёгкая рубашка", "👕 Лонгслив", "👕 Тонкий свитер", "👕 Футболка с лёгкой рубашкой"],
                ["👖 Лёгкие брюки", "👖 Джинсы", "🩳 Шорты днём"],
                ["👟 Кроссовки", "👟 Сандалии", "👟 Мокасины"],
            ],
            "hot": [
                ["👕 Лёгкая одежда", "👕 Футболка и шорты", "👕 Лёгкое платье или рубашка", "👕 Хлопковая одежда", "👕 Льняной костюм", "👕 Светлая свободная одежда"],
                ["🧢 Головной убор", "🧢 Панама", "🧢 Кепка от солнца", "🕶 Солнечные очки"],
                ["🧴 Солнцезащитный крем", "🧴 SPF-защита", "🧴 Крем от загара", "💧 Бутылка воды"],
                ["🩴 Сандалии", "🩴 Шлёпанцы", "🩴 Лёгкие кроссовки"],
            ],
        },
        "en": {
            "freezing": [
                ["🧥 Warm down jacket", "🧥 Winter parka", "🧥 Hooded puffer jacket", "🧥 Insulated coat"],
                ["🧶 Wool sweater", "🧶 Thermal base + sweater", "🧶 Fleece hoodie"],
                ["🧤 Warm gloves", "🧤 Mittens", "🧤 Insulated gloves"],
                ["🧣 Scarf and hat", "🧣 Warm beanie and scarf"],
                ["🥾 Insulated boots", "🥾 Winter boots"],
            ],
            "cold": [
                ["🧥 Winter jacket", "🧥 Warm coat", "🧥 Puffer with sweater"],
                ["🧤 Gloves", "🧤 Light gloves"],
                ["🧣 Scarf", "🧣 Snood", "🧢 Warm hat"],
                ["🥾 Insulated boots", "🥾 Winter shoes"],
            ],
            "cool": [
                ["🧥 Autumn jacket or coat", "🧥 Light jacket", "🧥 Sweater with jacket"],
                ["🧣 Light scarf", "🧣 Scarf"],
                ["🥾 Autumn shoes", "🥾 Boots"],
            ],
            "mild": [["👕 Light jacket or sweater", "👕 Hoodie", "👕 Cardigan", "👕 Denim jacket"], ["👖 Jeans", "👖 Light pants"], ["👟 Sneakers", "👟 Loafers"]],
            "warm": [["👕 Long-sleeved shirt", "👕 Light sweater", "👕 T-shirt with shirt"], ["👖 Light pants", "🩳 Shorts"], ["👟 Sneakers", "👟 Sandals"]],
            "hot": [
                ["👕 Light clothing", "👕 T-shirt and shorts", "👕 Cotton or linen clothes"],
                ["🧢 Headwear", "🧢 Sun hat", "🕶 Sunglasses"],
                ["🧴 Sunscreen", "🧴 SPF protection", "💧 Water bottle"],
                ["🩴 Sandals", "🩴 Flip-flops"],
            ],
        },
        "es": {
            "freezing": [
                ["🧥 Chaqueta abrigada", "🧥 Parka de invierno", "🧥 Abrigo de plumas"],
                ["🧶 Suéter de lana", "🧶 Ropa térmica"],
                ["🧤 Guantes calientes", "🧤 Manoplas"],
                ["🧣 Bufanda y gorro", "🧣 Bufanda y gorro de lana"],
                ["🥾 Botas de invierno", "🥾 Botas aislantes"],
            ],
            "cold": [
                ["🧥 Chaqueta de invierno", "🧥 Abrigo"],
                ["🧤 Guantes", "🧤 Guantes ligeros"],
                ["🧣 Bufanda", "🧣 Bufanda ligera", "🧢 Gorro"],
                ["🥾 Botas", "🥾 Calzado de invierno"],
            ],
            "cool": [
                ["🧥 Chaqueta de otoño o abrigo", "🧥 Chaqueta ligera", "🧥 Suéter con chaqueta"],
                ["🧣 Bufanda ligera", "🧣 Bufanda"],
                ["🥾 Zapatos de otoño", "🥾 Botines"],
            ],
            "mild": [["👕 Chaqueta ligera o suéter", "👕 Suéter", "👕 Cárdigan"], ["👖 Vaqueros", "👖 Pantalones ligeros"], ["👟 Zapatillas"]],
            "warm": [["👕 Camisa de manga larga", "👕 Camisa ligera"], ["👖 Pantalones ligeros", "🩳 Shorts"], ["👟 Zapatillas", "👟 Sandalias"]],
            "hot": [
                ["👕 Ropa ligera", "👕 Camiseta y shorts", "👕 Ropa de algodón"],
                ["🧢 Sombrero", "🧢 Gorra", "🕶 Gafas de sol"],
                ["🧴 Protector solar", "🧴 Crema solar", "💧 Botella de agua"],
                ["🩴 Sandalias", "🩴 Chanclas"],
            ],
        },
        "zh": {
            "freezing": [["🧥 保暖羽绒服", "🧥 冬季派克大衣", "🧥 连帽羽绒服"], ["🧶 羊毛衫", "🧶 保暖内衣+毛衣"], ["🧤 保暖手套", "🧤 连指手套"], ["🧣 围巾和帽子", "🧣 围巾和毛线帽"], ["🥾 保暖靴", "🥾 雪地靴"]],
            "cold": [["🧥 冬季夹克", "🧥 厚外套"], ["🧤 手套", "🧤 薄手套"], ["🧣 围巾", "🧢 帽子"], ["🥾 保暖鞋", "🥾 冬靴"]],
            "cool": [["🧥 秋季夹克或大衣", "🧥 轻便夹克", "🧥 毛衣加外套"], ["🧣 轻便围巾"], ["🥾 秋季鞋", "🥾 靴子"]],
            "mild": [["👕 轻便夹克或毛衣", "👕 卫衣", "👕 开衫"], ["👖 牛仔裤", "👖 轻便裤"], ["👟 运动鞋"]],
            "warm": [["👕 长袖衬衫", "👕 薄毛衣"], ["👖 轻便裤", "🩳 短裤"], ["👟 运动鞋", "👟 凉鞋"]],
            "hot": [["👕 轻便衣物", "👕 T恤和短裤", "👕 棉麻衣物"], ["🧢 帽子", "🕶 太阳镜"], ["🧴 防晒霜", "💧 水瓶"], ["🩴 凉鞋", "🩴 拖鞋"]],
        },
    }
    
    # Определяем диапазон
    if temp < -10:
        range_key = "freezing"
    elif temp < 0:
        range_key = "cold"
    elif temp < 10:
        range_key = "cool"
    elif temp < 20:
        range_key = "mild"
    elif temp < 25:
        range_key = "warm"
    else:
        range_key = "hot"
    
    lang_pools = CLOTHING.get(lang, CLOTHING["ru"])
    for category in lang_pools.get(range_key, []):
        recommendations.append(random.choice(category))
    
    # Дождь
    if any(w in description.lower() for w in ["дождь", "rain", "lluvia", "雨", "морось", "drizzle"]):
        rain_items = {"ru": ["☂️ Зонт", "☂️ Не забудьте зонт", "☂️ Зонт или дождевик"],
                      "en": ["☂️ Umbrella", "☂️ Take an umbrella"],
                      "es": ["☂️ Paraguas", "☂️ Lleva paraguas"],
                      "zh": ["☂️ 雨伞", "☂️ 带伞"]}
        recommendations.append(random.choice(rain_items.get(lang, rain_items["ru"])))
    
    # Сильный ветер
    if wind_speed > 10:
        wind_items = {"ru": ["🌬️ Ветровка", "🌬️ Куртка от ветра", "🌬️ Непродуваемая куртка"],
                      "en": ["🌬️ Windbreaker", "🌬️ Windproof jacket"],
                      "es": ["🌬️ Rompevientos", "🌬️ Chaqueta cortavientos"],
                      "zh": ["🌬️ 防风夹克", "🌬️ 防风外套"]}
        recommendations.append(random.choice(wind_items.get(lang, wind_items["ru"])))
    
    return recommendations
def get_weather_icon(weather_id=None, description=""):
    """Возвращает эмодзи иконки погоды по weather_id или описанию."""
    desc_lower = str(description).lower()
    
    # По weather_id (OpenWeatherMap)
    if weather_id:
        if 200 <= weather_id < 300:  # Гроза
            return "⛈"
        elif 300 <= weather_id < 400:  # Морось
            return "🌦"
        elif 500 <= weather_id < 600:  # Дождь
            return "🌧"
        elif 600 <= weather_id < 700:  # Снег
            return "❄️"
        elif 700 <= weather_id < 800:  # Туман, дымка
            return "🌫"
        elif weather_id == 800:  # Ясно
            return "☀️"
        elif weather_id == 801:  # Малооблачно
            return "🌤"
        elif weather_id == 802:  # Облачно
            return "⛅"
        elif weather_id in (803, 804):  # Пасмурно
            return "☁️"
    
    # По описанию
    if any(word in desc_lower for word in ["гроза", "thunderstorm", "гроза"]):
        return "⛈"
    elif any(word in desc_lower for word in ["дождь", "ливень", "rain", "shower"]):
        return "🌧"
    elif any(word in desc_lower for word in ["снег", "snow"]):
        return "❄️"
    elif any(word in desc_lower for word in ["туман", "дымка", "fog", "mist"]):
        return "🌫"
    elif any(word in desc_lower for word in ["ясно", "солнечно", "clear", "sunny"]):
        return "☀️"
    elif any(word in desc_lower for word in ["малооблачно", "partly cloudy"]):
        return "🌤"
    elif any(word in desc_lower for word in ["облачно", "пасмурно", "cloudy", "overcast"]):
        return "☁️"
    
    return "🌤"  # По умолчанию
def wind_deg_to_direction(deg, lang="ru"):
    dirs_ru = ["С", "ССВ", "СВ", "ВСВ", "В", "ВЮВ", "ЮВ", "ЮЮВ", "Ю", "ЮЮЗ", "ЮЗ", "ЗЮЗ", "З", "ЗСЗ", "СЗ", "ССЗ"]
    dirs_en = ["N", "NNE", "NE", "ENE", "E", "ESE", "SE", "SSE", "S", "SSW", "SW", "WSW", "W", "WNW", "NW", "NNW"]
    directions = dirs_ru if lang == "ru" else dirs_en
    if deg is None:
        return "—"
    idx = round(deg / 22.5) % 16
    return directions[idx]
def format_weather_text(chat_id, weather_data):
    lang = get_user_lang(chat_id)
    if "error" in weather_data:
        return T(lang, "weather_error")
    icon = get_weather_icon(weather_id=weather_data.get('weather_id'), description=weather_data.get('description', ''))
    wind_dir = wind_deg_to_direction(weather_data.get('wind_deg'), lang)
    text = f"{icon} {weather_data['city']}, {weather_data['country']}\n\n"
    text += T(lang, "temp", temp=weather_data['temp']) + "\n"
    text += T(lang, "feels_like", feels=weather_data['feels_like']) + "\n"
    text += T(lang, "wind_full", wind=weather_data['wind_speed'], direction=wind_dir) + "\n"
    text += T(lang, "humidity", humidity=weather_data['humidity']) + "\n"
    pressure = weather_data.get('pressure')
    if pressure:
        text += T(lang, "pressure_mm", pressure=pressure) + "\n"
    uv = weather_data.get('uv')
    if uv is not None:
        uv_level = get_uv_level(uv, lang)
        if uv_level:
            text += T(lang, "uv_with_level", uv=uv, level=uv_level) + "\n"
        else:
            text += T(lang, "uv_simple", uv=uv) + "\n"
    text += f"\n{weather_data.get('description', '').capitalize()}\n"
    text += f"\n{T(lang, 'updated_time', time=datetime.now().strftime('%H:%M:%S'))}"
    return text
def format_forecast_text(chat_id, forecast_data, city_name, days):
    from datetime import datetime
    lang = get_user_lang(chat_id)
    if "error" in forecast_data:
        return T(lang, "forecast_error")
    if not forecast_data:
        return T(lang, "error_no_data_forecast")
    if lang == "ru":
        if days == 1:
            day_word = T(lang, "day_1")
        elif days in (2, 3, 4):
            day_word = T(lang, "day_2_4")
        else:
            day_word = T(lang, "day_5_plus")
        title_days = f"{days} {day_word}"
    else:
        title_days = f"{days} {T(lang, 'day_5_plus')}"
    text = T(lang, "forecast_title", days_text=title_days, city=city_name)
    for date, item in list(forecast_data.items())[:days]:
        desc = item.get('description', '').lower()
        if any(w in desc for w in ['ясно', 'солнечно', 'clear', 'sunny']): icon = "☀️"
        elif any(w in desc for w in ['переменная', 'partly']): icon = "⛅"
        elif any(w in desc for w in ['дождь', 'ливень', 'rain', 'shower']): icon = "🌧"
        elif any(w in desc for w in ['снег', 'snow']): icon = "❄️"
        elif any(w in desc for w in ['гроза', 'thunder']): icon = "⛈"
        elif any(w in desc for w in ['туман', 'fog', 'mist']): icon = "🌫"
        elif any(w in desc for w in ['морось', 'drizzle']): icon = "🌦"
        else: icon = "☁️"
        weekday = item.get('weekday', '')[:3]
        date_str = item.get('date_str', '')
        temp_min = item.get('temp_min', item.get('temp', 0))
        temp_max = item.get('temp_max', item.get('temp', 0))
        feels = item.get('feels_like', item.get('temp', 0))
        wind = item.get('wind_speed', 0)
        wind_dir = item.get('wind_direction', '—')
        humidity = item.get('humidity', 50)
        pressure = item.get('pressure', 760)
        uv = item.get('uv')
        uv_level = get_uv_level(uv, lang) if uv else None
        precip = item.get('rain', 0)
        precip_prob = item.get('precip_prob', 0)
        text += f"{icon} *{weekday}, {date_str}*\n"
        text += T(lang, "forecast_day_line", min=temp_min, max=temp_max, feels=feels) + "\n"
        text += T(lang, "forecast_wind_line", wind=wind, dir=wind_dir, hum=humidity) + "\n"
        text += T(lang, "forecast_pressure", pressure=pressure)
        if uv_level:
            text += T(lang, "forecast_uv_line", uv=uv, level=uv_level)
        text += "\n"
        if precip > 0 or precip_prob > 0:
            text += T(lang, "forecast_precip", prob=precip_prob, mm=precip) + "\n"
        desc_text = item.get('description', T(lang, 'cloudy_default'))
        text += f"{desc_text.capitalize()}\n"
        text += "\n"
    text += T(lang, "updated_time", time=datetime.now().strftime('%H:%M'))
    return text
