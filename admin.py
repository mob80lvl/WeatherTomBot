#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Админ-панель: вход, пользователи, подписки, тексты."""
import os
import json
import logging
from functools import wraps
from datetime import datetime, timedelta
from flask import request, session, redirect, url_for, render_template_string, jsonify

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
@app.route('/admin')
@login_required
def admin_dashboard():
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)

    subscriptions = {}
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)

    b2b_users = {}
    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)

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
    users = {}
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)

    subscriptions = {}
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)

    b2b_users = {}
    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)

    html = '''<!DOCTYPE html><html><head><title>MeteoBot - Users</title>
    <style>*{margin:0;padding:0;box-sizing:border-box}body{font-family:Arial;background:#0f0c29;color:#fff;padding:20px}.container{max-width:1200px;margin:0 auto}.header{display:flex;justify-content:space-between;align-items:center;margin-bottom:30px}h1{color:#ffd200}.menu a{color:#aaa;text-decoration:none;margin-left:20px}.menu a:hover{color:#fff}table{width:100%;border-collapse:collapse;background:rgba(255,255,255,0.05);border-radius:15px;overflow:hidden}th,td{padding:12px;text-align:left;border-bottom:1px solid rgba(255,255,255,0.05)}th{background:rgba(255,255,255,0.1)}.subscribed{color:#0f0}.free{color:#ff6b6b}.b2b{color:#ffd700}.btn{padding:5px 10px;border-radius:5px;text-decoration:none;margin:2px;display:inline-block}.btn-sub{color:#0f0;border:1px solid #0f0}.btn-b2b{color:#ffd700;border:1px solid #ffd700}.btn-disable{color:#ff6b6b;border:1px solid #ff6b6b}.btn-del{color:#ff6b6b;border:1px solid #ff6b6b}.btn-disable:hover{background:#ff6b6b;color:#fff}.btn-sub:hover{background:#0f0;color:#000}.btn-b2b:hover{background:#ffd700;color:#000}.btn-del:hover{background:#ff6b6b;color:#fff}</style>
    </head><body><div class="container"><div class="header"><h1>👥 Users</h1>
    <div class="menu"><a href="/admin">Dashboard</a><a href="/admin/users">Users</a><a href="/admin/subscriptions">Subscriptions</a><a href="/admin/texts">📝 Texts</a><a href="/admin/logout">Logout</a></div></div>
    <table><thead><tr><th>ID</th><th>City</th><th>Subscription</th><th>Type</th><th>Actions</th></tr></thead><tbody>'''

    for user_id, city in users.items():
        is_sub = user_id in subscriptions
        b2b_info = b2b_users.get(user_id, {})
        b2b_type = b2b_info.get('type')
        status = '✅ Active' if is_sub else '❌ No'
        status_class = 'subscribed' if is_sub else 'free'

        if b2b_type:
            b2b_data = B2B_TYPES.get(b2b_type, {})
            type_label = f"{b2b_data.get('icon', '🏢')} {b2b_data.get('name', 'B2B')}"
            type_class = 'b2b'
        else:
            type_label = '👤 Personal' if is_sub else '-'
            type_class = 'subscribed' if is_sub else 'free'

        html += f'''<tr>
            <td>{user_id}</td>
            <td>{city}</td>
            <td class="{status_class}">{status}</td>
            <td class="{type_class}">{type_label}</td>
            <td>
                <a href="/admin/user/subscribe/{user_id}" class="btn btn-sub" onclick="return confirm('Activate personal subscription?')">👤</a>
                <a href="/admin/user/b2b/{user_id}/agriculture" class="btn btn-b2b" onclick="return confirm('Activate B2B (Agriculture)?')">🌾</a>
                <a href="/admin/user/b2b/{user_id}/construction" class="btn btn-b2b" onclick="return confirm('Activate B2B (Construction)?')">🏗️</a>
                <a href="/admin/user/b2b/{user_id}/tourism" class="btn btn-b2b" onclick="return confirm('Activate B2B (Tourism)?')">✈️</a>
                <a href="/admin/user/b2b/{user_id}/business" class="btn btn-b2b" onclick="return confirm('Activate B2B (Business)?')">🏢</a>
                <a href="/admin/subscription/disable/{user_id}" class="btn btn-disable" onclick="return confirm('Disable subscription?')">🚫</a>
                <a href="/admin/user/delete/{user_id}" class="btn btn-del" onclick="return confirm('Delete user?')">🗑️</a>
            </td>
        </tr>'''

    html += '''</tbody></table></div></body></html>'''
    return html
@app.route('/admin/user/delete/<chat_id>')
@login_required
def admin_user_delete(chat_id):
    if os.path.exists(USERS_FILE):
        with open(USERS_FILE, 'r', encoding='utf-8') as f:
            users = json.load(f)
        if chat_id in users:
            del users[chat_id]
            with open(USERS_FILE, 'w', encoding='utf-8') as f:
                json.dump(users, f, ensure_ascii=False, indent=2)
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
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)
        if chat_id in subscriptions:
            del subscriptions[chat_id]
            with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)

    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)
        if chat_id in b2b_users:
            del b2b_users[chat_id]
            with open(B2B_FILE, 'w', encoding='utf-8') as f:
                json.dump(b2b_users, f, ensure_ascii=False, indent=2)

    flash(f'Subscription disabled for user {chat_id}', 'success')
    return redirect(url_for('admin_users'))
@app.route('/admin/subscriptions')
@login_required
def admin_subscriptions():
    subscriptions = {}
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)

    b2b_users = {}
    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)

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
    if os.path.exists(SUBSCRIPTIONS_FILE):
        with open(SUBSCRIPTIONS_FILE, 'r', encoding='utf-8') as f:
            subscriptions = json.load(f)
        if chat_id in subscriptions:
            del subscriptions[chat_id]
            with open(SUBSCRIPTIONS_FILE, 'w', encoding='utf-8') as f:
                json.dump(subscriptions, f, ensure_ascii=False, indent=2)

    if os.path.exists(B2B_FILE):
        with open(B2B_FILE, 'r', encoding='utf-8') as f:
            b2b_users = json.load(f)
        if chat_id in b2b_users:
            del b2b_users[chat_id]
            with open(B2B_FILE, 'w', encoding='utf-8') as f:
                json.dump(b2b_users, f, ensure_ascii=False, indent=2)

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
