#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Админ-панель: вход, пользователи, подписки, тексты."""
import os
import json
import sqlite3
from db import get_conn, DB_FILE
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import request, session, redirect, url_for, render_template_string, jsonify, flash

from app import app
from config import *
from texts import T, TEXTS, LANGUAGES
from storage import (get_user_lang, get_user_city, get_current_plan, is_user_subscribed,
                     get_user_subscription, set_user_subscription, set_user_lang,
                     get_user_b2b_type, _load_json_file, _save_json_file)
from utils import send_message

logger = logging.getLogger(__name__)

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('logged_in'):
            flash('Please log in', 'warning')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated_function

ADMIN_UI = {
 "en": {
  "menu_dashboard":"Dashboard","menu_users":"Users","menu_payments":"Payments","menu_promos":"Promos","menu_subs":"Subscriptions","menu_texts":"Texts","menu_logout":"Logout",
  "title_users":"Users","search_ph":"Search by ID or city...","col_id":"ID","col_city":"City","col_source":"Source","col_first":"First seen","col_sub":"Subscription","col_act":"Actions",
  "no_sub":"No subscription",
  "tip_premium":"Grant Premium 30 days","tip_business":"Grant Business 30 days","tip_disable":"Disable subscription","tip_delete":"Delete user",
  "confirm":"Are you sure?"
 },
 "ru": {
  "menu_dashboard":"Дашборд","menu_users":"Пользователи","menu_payments":"Платежи","menu_promos":"Промокоды","menu_subs":"Подписки","menu_texts":"Тексты","menu_logout":"Выход",
  "title_users":"Пользователи","search_ph":"Поиск по ID или городу...","col_id":"ID","col_city":"Город","col_source":"Источник","col_first":"Первая активность","col_sub":"Подписка","col_act":"Действия",
  "no_sub":"Нет подписки",
  "tip_premium":"Выдать Premium 30 дней","tip_business":"Выдать Business 30 дней","tip_disable":"Отключить подписку","tip_delete":"Удалить пользователя",
  "confirm":"Вы уверены?"
 }
}
def AL(lang, key):
    return ADMIN_UI.get(lang, ADMIN_UI["en"]).get(key, ADMIN_UI["en"].get(key, key))
@app.route('/admin/lang/<lg>')
@login_required
def admin_lang(lg):
    if lg in ("ru", "en"):
        session['admin_lang'] = lg
    return redirect(request.referrer or url_for('admin_dashboard'))
def admin_menu(lang):
    return ('<div class="menu">'
            f'<a href="/admin">{AL(lang, "menu_dashboard")}</a>'
            f'<a href="/admin/users">{AL(lang, "menu_users")}</a>'
            f'<a href="/admin/payments">{AL(lang, "menu_payments")}</a>'
            f'<a href="/admin/promos">{AL(lang, "menu_promos")}</a>'
            f'<a href="/admin/subscriptions">{AL(lang, "menu_subs")}</a>'
            f'<a href="/admin/texts">{AL(lang, "menu_texts")}</a>'
            f'<a href="/admin/lang/ru" title="Русский">🇷🇺</a>'
            f'<a href="/admin/lang/en" title="English">🇬</a>'
            f'<a href="/admin/logout">{AL(lang, "menu_logout")}</a></div>')
@app.route('/admin/login', methods=['GET', 'POST'])
def admin_login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            session['logged_in'] = True
            flash('Welcome!', 'success')
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string('''
            <!DOCTYPE html>
            <html>
            <head><title>MeteoBot - Login</title>
            <style>body{font-family:Arial;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;display:flex;justify-content:center;align-items:center;height:100vh}.box{background:rgba(255,255,255,0.05);padding:40px;border-radius:20px;width:350px}h1{text-align:center;color:#ffd200}input{width:100%;padding:12px;margin:10px 0;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.2);color:#fff;border-radius:8px}button{width:100%;padding:12px;background:linear-gradient(90deg,#f7971e,#ffd200);border:none;border-radius:8px;font-weight:bold;cursor:pointer}.error{color:#ff6b6b;text-align:center;margin-top:10px}</style>
            </head>
            <body>
                <div class="box">
                    <h1>🌤 MeteoBot</h1>
                    <form method="post">
                        <input type="text" name="username" placeholder="Username" required>
                        <input type="password" name="password" placeholder="Password" required>
                        <button type="submit">Login</button>
                    </form>
                    <div class="error">❌ Invalid username or password</div>
                </div>
            </body>
            </html>
            ''')

    return render_template_string('''
    <!DOCTYPE html>
    <html>
    <head><title>MeteoBot - Login</title>
    <style>body{font-family:Arial;background:linear-gradient(135deg,#0f0c29,#302b63,#24243e);color:#fff;display:flex;justify-content:center;align-items:center;height:100vh}.box{background:rgba(255,255,255,0.05);padding:40px;border-radius:20px;width:350px}h1{text-align:center;color:#ffd200}input{width:100%;padding:12px;margin:10px 0;background:rgba(255,255,255,0.05);border:1px solid rgba(255,255,255,0.2);color:#fff;border-radius:8px}button{width:100%;padding:12px;background:linear-gradient(90deg,#f7971e,#ffd200);border:none;border-radius:8px;font-weight:bold;cursor:pointer}</style>
    </head>
    <body>
        <div class="box">
            <h1>🌤 MeteoBot</h1>
            <form method="post">
                <input type="text" name="username" placeholder="Username" required>
                <input type="password" name="password" placeholder="Password" required>
                <button type="submit">Login</button>
            </form>
        </div>
    </body>
    </html>
    ''')
@app.route('/admin/logout')
def admin_logout():
    session.pop('logged_in', None)
    return redirect(url_for('admin_login'))
# ===== Хелперы для чтения данных админки из SQLite =====

def _admin_get_users():
    """Возвращает {chat_id: city} из таблицы users (только цифровые id)."""
    conn = sqlite3.connect(DB_FILE)
    users = {}
    for row in conn.execute("SELECT chat_id, city FROM users"):
        chat_id = str(row[0])
        # Показываем TG и VK пользователей, скрываем только тестовые/отладочные id
        if chat_id.isdigit() or (chat_id.startswith("vk_") and chat_id[3:].isdigit()):
            users[chat_id] = row[1] if row[1] else ""
    conn.close()
    return users

def _admin_get_subscriptions():
    """Возвращает {chat_id: {plan, expiry, activated_by, activated_at, b2b_type}} из subscriptions."""
    conn = sqlite3.connect(DB_FILE)
    subs = {}
    for row in conn.execute("SELECT chat_id, plan, expiry, activated_by, activated_at, b2b_type FROM subscriptions"):
        subs[row[0]] = {
            "plan": row[1],
            "expiry": row[2],
            "activated_by": row[3],
            "activated_at": row[4],
            "b2b_type": row[5],
        }
    conn.close()
    return subs

def _admin_get_b2b_users():
    """Возвращает {chat_id: {type, activated_at, expiry, source}} из b2b_users."""
    conn = sqlite3.connect(DB_FILE)
    b2b = {}
    for row in conn.execute("SELECT chat_id, type, activated_at, expiry, source FROM b2b_users"):
        b2b[row[0]] = {
            "type": row[1],
            "activated_at": row[2],
            "expiry": row[3],
            "source": row[4],
        }
    conn.close()
    return b2b


@app.route('/admin/')
@login_required
def admin_slash_redirect():
    return redirect(url_for('admin_dashboard'))

@app.route('/admin')
@login_required
def admin_dashboard():
    users = _admin_get_users()
    subscriptions = _admin_get_subscriptions()
    b2b_users = _admin_get_b2b_users()

    total_users = len(users)
    subscribed_users = len([u for u in users if u in subscriptions])
    b2b_count = len(b2b_users)

    return f'''<!DOCTYPE html>
    <html>
    <head><title>MeteoBot - Admin Panel</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial;background:#0f0c29;color:#fff;padding:20px}}.container{{max-width:1200px;margin:0 auto}}.header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px}}h1{{color:#ffd200}}.menu a{{color:#aaa;text-decoration:none;margin-left:20px}}.menu a:hover{{color:#fff}}.stats{{display:grid;grid-template-columns:repeat(auto-fit,minmax(150px,1fr));gap:20px;margin-bottom:30px}}.stat-card{{background:rgba(255,255,255,0.05);padding:20px;border-radius:15px;text-align:center}}.stat-number{{font-size:2em;font-weight:bold;color:#ffd200}}.stat-label{{opacity:0.7}}</style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🌤 MeteoBot</h1>
                <div class="menu">
                    <a href="/admin">Dashboard</a>
                    <a href="/admin/users">Users</a>
                    <a href="/admin/subscriptions">Subscriptions</a>
                    <a href="/admin/texts">📝 Texts</a>
                    <a href="/admin/logout">Logout</a>
                </div>
            </div>
            <div class="stats">
                <div class="stat-card"><div class="stat-number">{total_users}</div><div class="stat-label">👥 Users</div></div>
                <div class="stat-card"><div class="stat-number">{subscribed_users}</div><div class="stat-label">✅ Subscribed</div></div>
                <div class="stat-card"><div class="stat-number">{b2b_count}</div><div class="stat-label">🏢 B2B</div></div>
                <div class="stat-card"><div class="stat-number">{total_users - subscribed_users}</div><div class="stat-label">🆓 Free</div></div>
            </div>
        </div>
    </body>
    </html>
    '''
@app.route('/admin/users')
@login_required
def admin_users():
    import html as _html
    lang = session.get('admin_lang', 'en')
    q = (request.args.get('q') or '').strip().lower()
    users = _admin_get_users()
    subscriptions = _admin_get_subscriptions()
    fusers = {}
    try:
        import features as _feat
        fusers = _feat._db().get("users", {})
    except Exception:
        fusers = {}
    now = datetime.now()
    rows_html = ""
    for user_id, city in users.items():
        if q and q not in str(user_id).lower() and q not in (city or "").lower():
            continue
        fu = fusers.get(str(user_id), {}) or {}
        source = fu.get("source") or ("vk" if str(user_id).startswith("vk_") else "telegram")
        first_seen = (fu.get("first_seen") or "")[:10] or "-"
        sub = subscriptions.get(user_id)
        if sub:
            try:
                expiry = datetime.fromisoformat(sub["expiry"])
                days_left = (expiry - now).days
                if days_left >= 0:
                    left = f"{days_left}d left" if lang == "en" else f"осталось {days_left} дн."
                    status = f'{sub["plan"]} · {expiry:%Y-%m-%d} · {left}'
                    cls = "subscribed" if days_left > 7 else "expiring"
                else:
                    ago = f"expired {-days_left}d ago" if lang == "en" else f"истекла {-days_left} дн. назад"
                    status = f'{sub["plan"]} · {ago}'
                    cls = "free"
            except Exception:
                status = sub.get("plan") or "?"
                cls = "subscribed"
        else:
            status = AL(lang, "no_sub")
            cls = "free"
        rows_html += f"""<tr>
            <td>{user_id}</td>
            <td>{city}</td>
            <td>{source}</td>
            <td>{first_seen}</td>
            <td class="{cls}">{status}</td>
            <td>
                <a href="/admin/user/subscribe/{user_id}" class="btn btn-sub" title="{AL(lang, 'tip_premium')}" onclick="return confirm('{AL(lang, 'confirm')}')">👤</a>
                <a href="/admin/user/b2b/{user_id}/business" class="btn btn-b2b" title="{AL(lang, 'tip_business')}" onclick="return confirm('{AL(lang, 'confirm')}')">🏢</a>
                <a href="/admin/subscription/disable/{user_id}" class="btn btn-disable" title="{AL(lang, 'tip_disable')}" onclick="return confirm('{AL(lang, 'confirm')}')">🚫</a>
                <a href="/admin/user/delete/{user_id}" class="btn btn-del" title="{AL(lang, 'tip_delete')}" onclick="return confirm('{AL(lang, 'confirm')}')">🗑️</a>
            </td>
        </tr>"""
    q_esc = _html.escape(q, quote=True)
    return f"""<!DOCTYPE html><html><head><title>MeteoBot - {AL(lang, 'title_users')}</title>
    <style>*{{margin:0;padding:0;box-sizing:border-box}}body{{font-family:Arial;background:#0f0c29;color:#fff;padding:20px}}.container{{max-width:1200px;margin:0 auto}}.header{{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px}}h1{{color:#ffd200}}.menu a{{color:#aaa;text-decoration:none;margin-left:20px}}.menu a:hover{{color:#fff}}table{{width:100%;border-collapse:collapse;background:rgba(255,255,255,0.05);border-radius:15px;overflow:hidden}}th,td{{padding:12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05)}}th{{background:rgba(255,255,255,0.1)}}.subscribed{{color:#0f0}}.free{{color:#ff6b6b}}.expiring{{color:#ffd700}}.btn{{padding:5px 10px;border-radius:5px;text-decoration:none;margin:2px;display:inline-block}}.btn-sub{{color:#0f0;border:1px solid #0f0}}.btn-b2b{{color:#ffd700;border:1px solid #ffd700}}.btn-disable{{color:#ff6b6b;border:1px solid #ff6b6b}}.btn-del{{color:#ff6b6b;border:1px solid #ff6b6b}}.btn-disable:hover{{background:#ff6b6b;color:#fff}}.btn-sub:hover{{background:#0f0;color:#000}}.btn-b2b:hover{{background:#ffd700;color:#000}}.btn-del:hover{{background:#ff6b6b;color:#fff}}.search{{margin-bottom:15px}}.search input{{padding:8px 12px;border-radius:8px;border:1px solid #444;background:rgba(255,255,255,0.08);color:#fff;width:300px}}</style>
    </head><body><div class="container"><div class="header"><h1>👥 {AL(lang, 'title_users')}</h1>
    {admin_menu(lang)}</div>
    <form class="search" method="get" action="/admin/users"><input name="q" value="{q_esc}" placeholder="{AL(lang, 'search_ph')}"></form>
    <table><thead><tr><th>{AL(lang, 'col_id')}</th><th>{AL(lang, 'col_city')}</th><th>{AL(lang, 'col_source')}</th><th>{AL(lang, 'col_first')}</th><th>{AL(lang, 'col_sub')}</th><th>{AL(lang, 'col_act')}</th></tr></thead><tbody>
    {rows_html}
    </tbody></table></div></body></html>"""

@app.route('/admin/user/delete/<chat_id>')
@login_required
def admin_user_delete(chat_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM users WHERE chat_id=?", (str(chat_id),))
    conn.commit()
    conn.close()
    return redirect(url_for('admin_users'))
@app.route('/admin/user/subscribe/<chat_id>')
@login_required
def admin_user_subscribe(chat_id):
    set_user_subscription(chat_id, 30, b2b_type=None)
    return redirect(url_for('admin_users'))
@app.route('/admin/user/b2b/<chat_id>/<b2b_type>')
@login_required
def admin_user_b2b(chat_id, b2b_type):
    if b2b_type in B2B_TYPES:
        set_user_subscription(chat_id, 30, b2b_type=b2b_type)
    return redirect(url_for('admin_users'))
@app.route('/admin/subscription/disable/<chat_id>')
@login_required
def admin_subscription_disable(chat_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM subscriptions WHERE chat_id=?", (str(chat_id),))
    conn.execute("DELETE FROM b2b_users WHERE chat_id=?", (str(chat_id),))
    conn.commit()
    conn.close()

    flash(f'Subscription disabled for user {chat_id}', 'success')
    return redirect(url_for('admin_users'))
@app.route('/admin/subscriptions')
@login_required
def admin_subscriptions():
    subscriptions = _admin_get_subscriptions()
    b2b_users = _admin_get_b2b_users()

    html = '''<!DOCTYPE html><html><head><title>MeteoBot - Subscriptions</title>
    <style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial;background:#0f0c29;color:#fff;padding:20px}.container{max-width:1200px;margin:0 auto}.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px}h1{color:#ffd200}.menu a{color:#aaa;text-decoration:none;margin-left:20px}.menu a:hover{color:#fff}table{width:100%;border-collapse:collapse;background:rgba(255,255,255,0.05);border-radius:15px;overflow:hidden}th,td{padding:12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05)}th{background:rgba(255,255,255,0.1)}.active{color:#0f0}.expired{color:#ff6b6b}.b2b{color:#ffd700}.btn{padding:5px 10px;border-radius:5px;text-decoration:none;margin:2px;display:inline-block;color:#ff6b6b;border:1px solid #ff6b6b}</style>
    </head><body><div class="container"><div class="header"><h1>📋 Subscriptions</h1>
    <div class="menu"><a href="/admin">Dashboard</a><a href="/admin/users">Users</a><a href="/admin/subscriptions">Subscriptions</a><a href="/admin/texts">📝 Texts</a><a href="/admin/logout">Logout</a></div></div>
    <table><thead><tr><th>ID</th><th>Type</th><th>Valid until</th><th>Status</th><th>Actions</th></tr></thead><tbody>'''

    now = datetime.now()
    for user_id, sub in subscriptions.items():
        expiry = datetime.fromisoformat(sub['expiry'])
        is_active = expiry > now
        b2b_type = sub.get('b2b_type')
        status = '✅ Active' if is_active else '❌ Expired'
        status_class = 'active' if is_active else 'expired'

        if b2b_type:
            b2b_data = B2B_TYPES.get(b2b_type, {})
            type_label = f"{b2b_data.get('icon', '🏢')} {b2b_data.get('name', 'B2B')}"
            type_class = 'b2b'
        else:
            type_label = '👤 Personal'
            type_class = 'active' if is_active else 'expired'

        html += f'''<tr>
            <td>{user_id}</td>
            <td class="{type_class}">{type_label}</td>
            <td>{expiry.strftime('%d.%m.%Y')}</td>
            <td class="{status_class}">{status}</td>
            <td><a href="/admin/subscription/revoke/{user_id}" class="btn" onclick="return confirm('Revoke subscription?')">🔄 Revoke</a></td>
        </tr>'''

    html += '''</tbody></table></div></body></html>'''
    return html
@app.route('/admin/subscription/revoke/<chat_id>')
@login_required
def admin_subscription_revoke(chat_id):
    conn = sqlite3.connect(DB_FILE)
    conn.execute("DELETE FROM subscriptions WHERE chat_id=?", (str(chat_id),))
    conn.execute("DELETE FROM b2b_users WHERE chat_id=?", (str(chat_id),))
    conn.commit()
    conn.close()

    return redirect(url_for('admin_subscriptions'))
@app.route('/admin/texts', methods=['GET', 'POST'])
@login_required
def admin_texts():
    global TEXTS

    if request.method == 'POST':
        new_texts = {}
        for lang in TEXTS.keys():
            new_texts[lang] = {}
            for key in TEXTS[lang].keys():
                form_key = f"{lang}_{key}"
                new_texts[lang][key] = request.form.get(form_key, '')

        TEXTS = new_texts
        flash('✅ Texts saved successfully!', 'success')
        return redirect(url_for('admin_texts'))

    html = '''<!DOCTYPE html>
    <html>
    <head>
        <title>📝 Manage Texts</title>
        <style>
            * { margin: 0; padding: 0; box-sizing: border-box; }
            body { font-family: Arial, sans-serif; background: #0f0c29; color: #fff; padding: 20px; }
            .container { max-width: 1200px; margin: 0 auto; }
            .header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 30px; flex-wrap: wrap; }
            h1 { color: #ffd200; }
            .menu a { color: #aaa; text-decoration: none; margin-left: 20px; }
            .menu a:hover { color: #fff; }
            .flash { padding: 15px; border-radius: 8px; margin-bottom: 20px; }
            .flash-success { background: rgba(0,255,0,0.1); border: 1px solid rgba(0,255,0,0.3); color: #0f0; }
            .flash-error { background: rgba(255,0,0,0.1); border: 1px solid rgba(255,0,0,0.3); color: #ff6b6b; }
            .lang-tabs { display: flex; gap: 10px; margin-bottom: 20px; flex-wrap: wrap; }
            .lang-tab { padding: 10px 20px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.1); border-radius: 8px; cursor: pointer; color: #aaa; }
            .lang-tab.active { background: rgba(255,215,0,0.1); border-color: #ffd200; color: #ffd200; }
            .lang-content { display: none; background: rgba(255,255,255,0.05); border-radius: 15px; padding: 20px; }
            .lang-content.active { display: block; }
            .field { margin-bottom: 15px; }
            .field label { display: block; margin-bottom: 5px; font-weight: bold; opacity: 0.8; }
            .field .key { color: #888; font-size: 0.8em; font-family: monospace; display: block; margin-bottom: 5px; }
            .field textarea { width: 100%; padding: 10px; background: rgba(255,255,255,0.05); border: 1px solid rgba(255,255,255,0.2); color: #fff; border-radius: 8px; min-height: 60px; resize: vertical; }
            .field textarea:focus { outline: none; border-color: #ffd200; }
            .btn-save { padding: 12px 40px; background: linear-gradient(90deg, #f7971e, #ffd200); border: none; border-radius: 8px; font-weight: bold; font-size: 16px; cursor: pointer; margin-top: 20px; }
            .btn-save:hover { transform: scale(1.02); }
            .lang-select {
                padding: 10px 15px;
                background: rgba(255,255,255,0.05);
                border: 1px solid rgba(255,255,255,0.2);
                color: #fff;
                border-radius: 8px;
                font-size: 14px;
                margin-bottom: 20px;
                cursor: pointer;
            }
            .lang-select option { background: #0f0c29; }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>📝 Manage Texts</h1>
                <div class="menu">
                    <a href="/admin">Dashboard</a>
                    <a href="/admin/users">Users</a>
                    <a href="/admin/subscriptions">Subscriptions</a>
                    <a href="/admin/texts">📝 Texts</a>
                    <a href="/admin/logout">Logout</a>
                </div>
            </div>

            <div style="display: flex; gap: 15px; align-items: center; margin-bottom: 20px; flex-wrap: wrap;">
                <span style="opacity: 0.7;">🌐 Language:</span>
                <select class="lang-select" id="langSelect" onchange="switchLang(this.value)">
                    <option value="ru">🇷🇺 Русский</option>
                    <option value="en" selected>🇬🇧 English</option>
                                    </select>
                <span style="opacity: 0.5; font-size: 12px;">(default: English)</span>
            </div>

            {% with messages = get_flashed_messages(with_categories=true) %}
                {% if messages %}
                    {% for category, message in messages %}
                        <div class="flash flash-{{ category }}">{{ message }}</div>
                    {% endfor %}
                {% endif %}
            {% endwith %}

            <form method="post">
    '''

    for lang_code, lang_name in [("ru", "🇷🇺 Русский"), ("en", "🇬🇧 English")]:
        display = "block" if lang_code == "en" else "none"
        html += f'<div class="lang-content" id="lang_{lang_code}" style="display:{display}">'
        html += f'<h2>{lang_name}</h2>'

        lang_texts = TEXTS.get(lang_code, TEXTS.get('ru', {}))
        for key, value in lang_texts.items():
            html += f'''
                <div class="field">
                    <label for="{lang_code}_{key}">{key}</label>
                    <span class="key">🔑 {lang_code}.{key}</span>
                    <textarea id="{lang_code}_{key}" name="{lang_code}_{key}" rows="2">{value}</textarea>
                </div>
            '''

        html += '</div>'

    html += '''
                <button type="submit" class="btn-save">💾 Save all texts</button>
            </form>
        </div>

        <script>
            function switchLang(lang) {
                document.querySelectorAll('.lang-content').forEach(el => {
                    el.style.display = el.id === 'lang_' + lang ? 'block' : 'none';
                });
                document.getElementById('langSelect').value = lang;
            }
            document.addEventListener('DOMContentLoaded', function() {
                switchLang('en');
            });
        </script>
    </body>
    </html>
    '''

    return render_template_string(html, TEXTS=TEXTS)
