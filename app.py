from flask import Flask, render_template, request, jsonify, session, redirect, url_for, render_template_string
import requests
import sqlite3
import hashlib
import os
from functools import wraps
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'supersecretkey'

OPENROUTER_API_KEY = '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'
MODEL_NAME = 'openai/gpt-3.5-turbo-0613'
ADMIN_PASSWORD = 'fima1456Game!'

def init_db():
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 username TEXT UNIQUE NOT NULL,
                 password TEXT NOT NULL,
                 is_admin INTEGER DEFAULT 0,
                 registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP)''')
    c.execute('''CREATE TABLE IF NOT EXISTS sites
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER NOT NULL,
                 prompt TEXT NOT NULL,
                 html_code TEXT NOT NULL,
                 is_public INTEGER DEFAULT 1,
                 views INTEGER DEFAULT 0,
                 created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users (id))''')
    c.execute('''CREATE TABLE IF NOT EXISTS visits
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                 user_id INTEGER,
                 username TEXT,
                 ip_address TEXT,
                 user_agent TEXT,
                 page TEXT,
                 visited_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                 FOREIGN KEY (user_id) REFERENCES users (id))''')
    conn.commit()
    conn.close()

init_db()

def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not session.get('is_admin'):
            return redirect(url_for('index'))
        return f(*args, **kwargs)
    return decorated_function

index_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - AI сайтостроитель</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
            padding: 20px;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            width: 500px;
            padding: 40px;
            text-align: center;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 36px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 25px;
            font-size: 18px;
        }
        
        .asinoite {
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            font-weight: bold;
        }
        
        .free-note {
            color: #4caf50;
            font-size: 14px;
            margin-bottom: 25px;
            padding: 8px;
            background: #e8f5e9;
            border-radius: 30px;
            display: inline-block;
        }
        
        .features {
            display: flex;
            justify-content: space-around;
            margin-bottom: 30px;
            padding: 15px 0;
            border-top: 1px solid #e0e0e0;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .feature {
            text-align: center;
        }
        
        .feature-icon {
            font-size: 24px;
            margin-bottom: 5px;
        }
        
        .feature-text {
            font-size: 12px;
            color: #666;
        }
        
        .feed-button {
            background: linear-gradient(135deg, #ff7e5f, #feb47b);
            color: white;
            border: none;
            border-radius: 50px;
            padding: 15px 30px;
            font-size: 18px;
            font-weight: bold;
            cursor: pointer;
            margin-bottom: 30px;
            width: 100%;
            transition: transform 0.3s, box-shadow 0.3s;
            box-shadow: 0 10px 20px rgba(255,126,95,0.3);
        }
        
        .feed-button:hover {
            transform: translateY(-3px);
            box-shadow: 0 15px 30px rgba(255,126,95,0.4);
        }
        
        .feed-icon {
            margin-right: 10px;
            font-size: 20px;
        }
        
        .toggle-buttons {
            display: flex;
            gap: 10px;
            margin-bottom: 20px;
        }
        
        .toggle-btn {
            flex: 1;
            padding: 10px;
            background: #f0f0f0;
            color: #333;
            border: none;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }
        
        .toggle-btn.active {
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
        }
        
        .form-container {
            display: none;
        }
        
        .form-container.active {
            display: block;
        }
        
        .input-group {
            margin-bottom: 20px;
            text-align: left;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .message {
            margin-top: 15px;
            padding: 10px;
            border-radius: 8px;
            display: none;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            display: block;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            display: block;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>ASINOITE</h1>
        <div class="subtitle">Создай <span class="asinoite">сайт с помощью AI</span></div>
        
        <div class="free-note">✨ Сервис полностью бесплатный ✨</div>
        
        <button class="feed-button" onclick="window.location.href='/feed'">
            <span class="feed-icon">📱</span> Посмотреть ленту сайтов
        </button>
        
        <div class="features">
            <div class="feature">
                <div class="feature-icon">🤖</div>
                <div class="feature-text">AI генерация</div>
            </div>
            <div class="feature">
                <div class="feature-icon">🎨</div>
                <div class="feature-text">Любой дизайн</div>
            </div>
            <div class="feature">
                <div class="feature-icon">⚡</div>
                <div class="feature-text">Мгновенно</div>
            </div>
            <div class="feature">
                <div class="feature-icon">💎</div>
                <div class="feature-text">Бесплатно</div>
            </div>
        </div>
        
        <div class="toggle-buttons">
            <button class="toggle-btn active" onclick="showForm('login')">Вход</button>
            <button class="toggle-btn" onclick="showForm('register')">Регистрация</button>
        </div>
        
        <div id="login-form" class="form-container active">
            <div class="input-group">
                <label>Имя пользователя</label>
                <input type="text" id="login-username" placeholder="Введите имя">
            </div>
            <div class="input-group">
                <label>Пароль</label>
                <input type="password" id="login-password" placeholder="Введите пароль">
            </div>
            <button onclick="login()">Войти</button>
        </div>
        
        <div id="register-form" class="form-container">
            <div class="input-group">
                <label>Имя пользователя</label>
                <input type="text" id="register-username" placeholder="Введите имя">
            </div>
            <div class="input-group">
                <label>Пароль</label>
                <input type="password" id="register-password" placeholder="Введите пароль">
            </div>
            <button onclick="register()">Зарегистрироваться</button>
        </div>
        
        <div id="message" class="message"></div>
    </div>
    
    <script>
        function showForm(form) {
            document.querySelectorAll('.toggle-btn').forEach(btn => btn.classList.remove('active'));
            document.querySelectorAll('.form-container').forEach(container => container.classList.remove('active'));
            
            if (form === 'login') {
                document.querySelector('.toggle-btn:first-child').classList.add('active');
                document.getElementById('login-form').classList.add('active');
            } else {
                document.querySelector('.toggle-btn:last-child').classList.add('active');
                document.getElementById('register-form').classList.add('active');
            }
        }
        
        async function register() {
            const username = document.getElementById('register-username').value;
            const password = document.getElementById('register-password').value;
            
            const response = await fetch('/register', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const data = await response.json();
            const messageDiv = document.getElementById('message');
            
            if (data.success) {
                messageDiv.className = 'message success';
                messageDiv.textContent = 'Регистрация успешна! Перенаправление...';
                setTimeout(() => window.location.href = '/dashboard', 1000);
            } else {
                messageDiv.className = 'message error';
                messageDiv.textContent = data.message;
            }
        }
        
        async function login() {
            const username = document.getElementById('login-username').value;
            const password = document.getElementById('login-password').value;
            
            const response = await fetch('/login', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({username, password})
            });
            
            const data = await response.json();
            const messageDiv = document.getElementById('message');
            
            if (data.success) {
                messageDiv.className = 'message success';
                messageDiv.textContent = 'Вход выполнен! Перенаправление...';
                setTimeout(() => window.location.href = '/dashboard', 1000);
            } else {
                messageDiv.className = 'message error';
                messageDiv.textContent = data.message;
            }
        }
    </script>
</body>
</html>
'''

feed_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Лента сайтов</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        
        .navbar {
            background: white;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 20px;
        }
        
        .nav-link {
            padding: 8px 16px;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s;
        }
        
        .nav-link:hover {
            background: #e0e0e0;
        }
        
        .container {
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        h1 {
            color: #333;
            margin-bottom: 30px;
            font-size: 32px;
        }
        
        .sites-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 25px;
        }
        
        .site-card {
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            transition: transform 0.3s, box-shadow 0.3s;
            display: flex;
            flex-direction: column;
        }
        
        .site-card:hover {
            transform: translateY(-5px);
            box-shadow: 0 15px 30px rgba(0,0,0,0.1);
        }
        
        .site-preview {
            height: 200px;
            background: #f8f9fa;
            border-bottom: 1px solid #e0e0e0;
            overflow: hidden;
            position: relative;
        }
        
        .preview-overlay {
            position: absolute;
            top: 0;
            left: 0;
            right: 0;
            bottom: 0;
            background: rgba(0,0,0,0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            opacity: 0;
            transition: opacity 0.3s;
        }
        
        .site-card:hover .preview-overlay {
            opacity: 1;
        }
        
        .view-btn {
            padding: 10px 20px;
            background: white;
            color: #333;
            text-decoration: none;
            border-radius: 30px;
            font-weight: 600;
            transition: transform 0.3s;
        }
        
        .view-btn:hover {
            transform: scale(1.05);
        }
        
        .site-info {
            padding: 20px;
        }
        
        .site-author {
            display: flex;
            align-items: center;
            margin-bottom: 10px;
        }
        
        .author-avatar {
            width: 30px;
            height: 30px;
            border-radius: 50%;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            display: flex;
            justify-content: center;
            align-items: center;
            font-weight: bold;
            margin-right: 10px;
        }
        
        .author-name {
            font-weight: 600;
            color: #667eea;
        }
        
        .site-prompt {
            font-size: 18px;
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            word-break: break-word;
        }
        
        .site-meta {
            display: flex;
            justify-content: space-between;
            color: #999;
            font-size: 14px;
            margin-bottom: 15px;
        }
        
        .views {
            display: flex;
            align-items: center;
            gap: 5px;
        }
        
        .views-icon {
            font-size: 16px;
        }
        
        .site-actions {
            display: flex;
            gap: 10px;
        }
        
        .action-btn {
            flex: 1;
            padding: 8px;
            text-align: center;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            transition: background 0.3s;
            border: none;
            cursor: pointer;
        }
        
        .action-btn:hover {
            background: #e0e0e0;
        }
        
        .action-btn.primary {
            background: #667eea;
            color: white;
        }
        
        .action-btn.primary:hover {
            background: #5a6fd6;
        }
        
        .empty-feed {
            text-align: center;
            padding: 60px;
            background: white;
            border-radius: 15px;
            color: #999;
        }
        
        .empty-icon {
            font-size: 48px;
            margin-bottom: 20px;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">ASINOITE</div>
        <div class="nav-links">
            <a href="/" class="nav-link">Главная</a>
            <a href="/feed" class="nav-link">Лента</a>
            {% if session.user_id %}
                <a href="/dashboard" class="nav-link">Дашборд</a>
                <a href="/logout" class="nav-link">Выйти</a>
            {% else %}
                <a href="/" class="nav-link">Вход</a>
            {% endif %}
        </div>
    </div>
    
    <div class="container">
        <h1>📱 Лента сайтов</h1>
        
        {% if sites %}
        <div class="sites-grid">
            {% for site in sites %}
            <div class="site-card">
                <div class="site-preview">
                    <iframe srcdoc="{{ site[4] }}" style="width:100%; height:100%; border:none; pointer-events:none;"></iframe>
                    <div class="preview-overlay">
                        <a href="/public/site/{{ site[0] }}" class="view-btn" target="_blank">Открыть сайт</a>
                    </div>
                </div>
                <div class="site-info">
                    <div class="site-author">
                        <div class="author-avatar">{{ site[2][0]|upper }}</div>
                        <span class="author-name">{{ site[2] }}</span>
                    </div>
                    <div class="site-prompt">{{ site[3] }}</div>
                    <div class="site-meta">
                        <span>{{ site[5] }}</span>
                        <span class="views">
                            <span class="views-icon">👁️</span>
                            {{ site[6] }}
                        </span>
                    </div>
                    <div class="site-actions">
                        <a href="/public/site/{{ site[0] }}" class="action-btn primary" target="_blank">Просмотр</a>
                        <button class="action-btn" onclick="showCode({{ site[0] }})">Код</button>
                    </div>
                </div>
            </div>
            {% endfor %}
        </div>
        {% else %}
        <div class="empty-feed">
            <div class="empty-icon">📭</div>
            <h2>Пока нет сайтов</h2>
            <p>Будьте первым, кто создаст сайт!</p>
            {% if not session.user_id %}
                <p style="margin-top: 20px;"><a href="/" style="color: #667eea;">Войдите</a> чтобы создать сайт</p>
            {% endif %}
        </div>
        {% endif %}
    </div>
    
    <script>
        function showCode(siteId) {
            window.open('/public/site/' + siteId + '/code', '_blank');
        }
    </script>
</body>
</html>
'''

public_view_site_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Просмотр сайта</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .navbar {
            background: white;
            padding: 15px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
            position: sticky;
            top: 0;
            z-index: 100;
        }
        
        .logo {
            font-size: 20px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 15px;
        }
        
        .nav-link {
            padding: 6px 12px;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .nav-link:hover {
            background: #e0e0e0;
        }
        
        .preview-container {
            height: calc(100vh - 70px);
            width: 100%;
        }
        
        iframe {
            width: 100%;
            height: 100%;
            border: none;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">ASINOITE</div>
        <div class="nav-links">
            <a href="/" class="nav-link">Главная</a>
            <a href="/feed" class="nav-link">Лента</a>
            {% if session.user_id %}
                <a href="/dashboard" class="nav-link">Дашборд</a>
                <a href="/logout" class="nav-link">Выйти</a>
            {% else %}
                <a href="/" class="nav-link">Вход</a>
            {% endif %}
        </div>
    </div>
    
    <div class="preview-container">
        <iframe srcdoc="{{ html_code }}"></iframe>
    </div>
</body>
</html>
'''

public_code_view_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Код сайта</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .navbar {
            background: white;
            padding: 15px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 20px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 15px;
        }
        
        .nav-link {
            padding: 6px 12px;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .nav-link:hover {
            background: #e0e0e0;
        }
        
        .code-container {
            padding: 20px;
            background: #1e1e1e;
            color: #fff;
            overflow: auto;
            height: calc(100vh - 70px);
            font-family: 'Courier New', monospace;
            font-size: 14px;
            white-space: pre-wrap;
            word-wrap: break-word;
        }
        
        .copy-btn {
            position: fixed;
            bottom: 20px;
            right: 20px;
            padding: 12px 24px;
            background: #667eea;
            color: white;
            border: none;
            border-radius: 30px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            box-shadow: 0 5px 20px rgba(102,126,234,0.4);
            transition: transform 0.3s;
        }
        
        .copy-btn:hover {
            transform: scale(1.05);
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">ASINOITE</div>
        <div class="nav-links">
            <a href="/" class="nav-link">Главная</a>
            <a href="/feed" class="nav-link">Лента</a>
            {% if session.user_id %}
                <a href="/dashboard" class="nav-link">Дашборд</a>
                <a href="/logout" class="nav-link">Выйти</a>
            {% else %}
                <a href="/" class="nav-link">Вход</a>
            {% endif %}
        </div>
    </div>
    
    <div class="code-container">
        <pre>{{ html_code }}</pre>
    </div>
    
    <button class="copy-btn" onclick="copyCode()">📋 Копировать код</button>
    
    <script>
        function copyCode() {
            const code = `{{ html_code|safe }}`;
            navigator.clipboard.writeText(code).then(() => {
                alert('Код скопирован!');
            });
        }
    </script>
</body>
</html>
'''

dashboard_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Дашборд</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        
        .navbar {
            background: white;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 15px;
        }
        
        .nav-link {
            padding: 8px 16px;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s;
        }
        
        .nav-link:hover {
            background: #e0e0e0;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .username {
            color: #333;
            font-weight: 500;
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: #e0e0e0;
        }
        
        .container {
            max-width: 1200px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .generate-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            margin-bottom: 40px;
        }
        
        h2 {
            color: #333;
            margin-bottom: 20px;
        }
        
        textarea {
            width: 100%;
            height: 150px;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 10px;
            font-size: 16px;
            font-family: inherit;
            resize: vertical;
            margin-bottom: 20px;
        }
        
        textarea:focus {
            outline: none;
            border-color: #667eea;
        }
        
        .generate-btn {
            padding: 12px 30px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        .generate-btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .generate-btn:disabled {
            opacity: 0.5;
            cursor: not-allowed;
            transform: none;
        }
        
        .result-section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            margin-bottom: 40px;
            display: none;
        }
        
        .result-header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 20px;
        }
        
        .view-btn {
            padding: 8px 16px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
        }
        
        .preview {
            background: #f5f5f5;
            border-radius: 10px;
            padding: 20px;
            max-height: 400px;
            overflow: auto;
        }
        
        .sites-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
            gap: 20px;
        }
        
        .site-card {
            background: white;
            border-radius: 10px;
            padding: 20px;
            box-shadow: 0 5px 15px rgba(0,0,0,0.05);
            transition: transform 0.3s;
        }
        
        .site-card:hover {
            transform: translateY(-5px);
        }
        
        .site-prompt {
            font-weight: 600;
            color: #333;
            margin-bottom: 10px;
            word-break: break-word;
        }
        
        .site-date {
            color: #999;
            font-size: 14px;
            margin-bottom: 15px;
        }
        
        .site-stats {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
            color: #666;
            font-size: 14px;
        }
        
        .site-actions {
            display: flex;
            gap: 10px;
        }
        
        .site-btn {
            flex: 1;
            padding: 8px;
            text-align: center;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            transition: background 0.3s;
            border: none;
            cursor: pointer;
        }
        
        .site-btn:hover {
            background: #e0e0e0;
        }
        
        .message {
            margin-top: 15px;
            padding: 10px;
            border-radius: 8px;
            display: none;
        }
        
        .message.success {
            background: #d4edda;
            color: #155724;
            display: block;
        }
        
        .message.error {
            background: #f8d7da;
            color: #721c24;
            display: block;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">ASINOITE</div>
        <div class="nav-links">
            <a href="/feed" class="nav-link">Лента</a>
        </div>
        <div class="user-info">
            <span class="username">{{ username }}</span>
            <a href="/logout" class="logout-btn">Выйти</a>
        </div>
    </div>
    
    <div class="container">
        <div class="generate-section">
            <h2>Создать новый сайт</h2>
            <textarea id="prompt" placeholder="Опишите сайт, который хотите создать..."></textarea>
            <button class="generate-btn" onclick="generateSite()">Создать сайт</button>
            <div id="generate-message" class="message"></div>
        </div>
        
        <div id="result-section" class="result-section">
            <div class="result-header">
                <h2>Результат</h2>
                <a id="view-site-link" href="#" class="view-btn" target="_blank">Открыть сайт</a>
            </div>
            <div class="preview" id="preview"></div>
        </div>
        
        <h2>Мои сайты</h2>
        <div class="sites-grid">
            {% for site in sites %}
            <div class="site-card">
                <div class="site-prompt">{{ site[1] }}</div>
                <div class="site-date">{{ site[4] }}</div>
                <div class="site-stats">
                    <span>👁️ {{ site[3] }} просмотров</span>
                </div>
                <div class="site-actions">
                    <a href="/site/{{ site[0] }}" class="site-btn" target="_blank">Просмотр</a>
                    <button class="site-btn" onclick="showCode({{ site[0] }})">Код</button>
                </div>
            </div>
            {% endfor %}
        </div>
    </div>
    
    <script>
        async function generateSite() {
            const prompt = document.getElementById('prompt').value;
            if (!prompt) {
                showMessage('generate-message', 'Введите описание сайта', 'error');
                return;
            }
            
            document.querySelector('.generate-btn').disabled = true;
            showMessage('generate-message', 'Генерация сайта...', 'success');
            
            const response = await fetch('/generate', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({prompt})
            });
            
            const data = await response.json();
            
            if (data.success) {
                showMessage('generate-message', 'Сайт успешно создан!', 'success');
                document.getElementById('result-section').style.display = 'block';
                document.getElementById('preview').innerHTML = data.html;
                document.getElementById('view-site-link').href = '/site/' + data.site_id;
                setTimeout(() => location.reload(), 2000);
            } else {
                showMessage('generate-message', data.message, 'error');
            }
            
            document.querySelector('.generate-btn').disabled = false;
        }
        
        function showMessage(elementId, text, type) {
            const messageDiv = document.getElementById(elementId);
            messageDiv.className = 'message ' + type;
            messageDiv.textContent = text;
        }
        
        function showCode(siteId) {
            window.open('/site/' + siteId, '_blank');
        }
    </script>
</body>
</html>
'''

view_site_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Просмотр сайта</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
        }
        
        .navbar {
            background: white;
            padding: 15px 30px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 20px;
            font-weight: bold;
            background: linear-gradient(135deg, #667eea, #764ba2);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        
        .nav-links {
            display: flex;
            gap: 15px;
        }
        
        .nav-link {
            padding: 6px 12px;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
            transition: background 0.3s;
        }
        
        .nav-link:hover {
            background: #e0e0e0;
        }
        
        .code-container {
            padding: 20px;
            background: #1e1e1e;
            color: #fff;
            overflow: auto;
            max-height: 200px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
        }
        
        .preview-container {
            padding: 20px;
            height: calc(100vh - 300px);
        }
        
        iframe {
            width: 100%;
            height: 100%;
            border: none;
            background: white;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">ASINOITE</div>
        <div class="nav-links">
            <a href="/" class="nav-link">Главная</a>
            <a href="/feed" class="nav-link">Лента</a>
            <a href="/dashboard" class="nav-link">Дашборд</a>
            <a href="/logout" class="nav-link">Выйти</a>
        </div>
    </div>
    
    <div class="code-container">
        <pre>{{ html_code }}</pre>
    </div>
    
    <div class="preview-container">
        <iframe srcdoc="{{ html_code }}"></iframe>
    </div>
</body>
</html>
'''

admin_login_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Админ панель</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: linear-gradient(135deg, #1a1a1a 0%, #2d2d2d 100%);
            height: 100vh;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .container {
            background: white;
            border-radius: 20px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.5);
            width: 400px;
            padding: 40px;
            text-align: center;
        }
        
        h1 {
            color: #333;
            margin-bottom: 10px;
            font-size: 32px;
        }
        
        .subtitle {
            color: #666;
            margin-bottom: 30px;
            font-size: 16px;
        }
        
        .admin-icon {
            font-size: 48px;
            margin-bottom: 20px;
        }
        
        .input-group {
            margin-bottom: 20px;
            text-align: left;
        }
        
        label {
            display: block;
            margin-bottom: 5px;
            color: #333;
            font-weight: 500;
        }
        
        input {
            width: 100%;
            padding: 12px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 16px;
            transition: border-color 0.3s;
        }
        
        input:focus {
            outline: none;
            border-color: #667eea;
        }
        
        button {
            width: 100%;
            padding: 12px;
            background: linear-gradient(135deg, #667eea, #764ba2);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.3s, box-shadow 0.3s;
        }
        
        button:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        
        .error {
            background: #f8d7da;
            color: #721c24;
            padding: 10px;
            border-radius: 8px;
            margin-bottom: 20px;
        }
        
        .back-link {
            display: block;
            margin-top: 20px;
            color: #667eea;
            text-decoration: none;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="admin-icon">🔒</div>
        <h1>ASINOITE</h1>
        <div class="subtitle">Административная панель</div>
        
        {% if error %}
        <div class="error">{{ error }}</div>
        {% endif %}
        
        <form method="POST">
            <div class="input-group">
                <label>Пароль администратора</label>
                <input type="password" name="password" placeholder="Введите пароль" required>
            </div>
            <button type="submit">Войти</button>
        </form>
        
        <a href="/" class="back-link">← На главную</a>
    </div>
</body>
</html>
'''

admin_dashboard_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Админ панель</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        
        .navbar {
            background: #1a1a1a;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #fff;
        }
        
        .admin-badge {
            background: #ff4757;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .username {
            color: #fff;
            font-weight: 500;
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: #333;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: #444;
        }
        
        .container {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .stats-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .stat-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            text-align: center;
        }
        
        .stat-value {
            font-size: 36px;
            font-weight: bold;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .stat-label {
            color: #666;
            font-size: 16px;
        }
        
        .nav-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 20px;
            margin-bottom: 40px;
        }
        
        .nav-card {
            background: white;
            border-radius: 15px;
            padding: 25px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            text-align: center;
            text-decoration: none;
            color: #333;
            transition: transform 0.3s;
        }
        
        .nav-card:hover {
            transform: translateY(-5px);
        }
        
        .nav-icon {
            font-size: 32px;
            margin-bottom: 10px;
        }
        
        .section {
            background: white;
            border-radius: 15px;
            padding: 30px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
            margin-bottom: 40px;
        }
        
        h2 {
            color: #333;
            margin-bottom: 20px;
        }
        
        table {
            width: 100%;
            border-collapse: collapse;
        }
        
        th {
            text-align: left;
            padding: 12px;
            background: #f8f9fa;
            color: #333;
            font-weight: 600;
        }
        
        td {
            padding: 12px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .delete-btn {
            padding: 5px 10px;
            background: #ff4757;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .delete-btn:hover {
            background: #ff6b81;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">
            ASINOITE Admin
            <span class="admin-badge">ADMIN</span>
        </div>
        <div class="user-info">
            <span class="username">admin</span>
            <a href="/logout" class="logout-btn">Выйти</a>
        </div>
    </div>
    
    <div class="container">
        <div class="stats-grid">
            <div class="stat-card">
                <div class="stat-value">{{ total_users }}</div>
                <div class="stat-label">Пользователей</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ total_sites }}</div>
                <div class="stat-label">Создано сайтов</div>
            </div>
            <div class="stat-card">
                <div class="stat-value">{{ total_visits }}</div>
                <div class="stat-label">Посещений</div>
            </div>
        </div>
        
        <div class="nav-grid">
            <a href="/admin/users" class="nav-card">
                <div class="nav-icon">👥</div>
                <div>Управление пользователями</div>
            </a>
            <a href="/admin/sites" class="nav-card">
                <div class="nav-icon">🌐</div>
                <div>Все сайты</div>
            </a>
            <a href="/admin/visits" class="nav-card">
                <div class="nav-icon">📊</div>
                <div>Кто заходил?</div>
            </a>
        </div>
        
        <div class="section">
            <h2>Топ пользователей</h2>
            <table>
                <tr>
                    <th>Пользователь</th>
                    <th>Количество сайтов</th>
                </tr>
                {% for user in top_users %}
                <tr>
                    <td>{{ user[0] }}</td>
                    <td>{{ user[1] }}</td>
                </tr>
                {% endfor %}
            </table>
        </div>
    </div>
</body>
</html>
'''

admin_users_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Управление пользователями</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        
        .navbar {
            background: #1a1a1a;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #fff;
        }
        
        .admin-badge {
            background: #ff4757;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .username {
            color: #fff;
            font-weight: 500;
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: #333;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: #444;
        }
        
        .container {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        
        .back-btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s;
        }
        
        .back-btn:hover {
            background: #5a6fd6;
        }
        
        table {
            width: 100%;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        }
        
        th {
            text-align: left;
            padding: 15px;
            background: #f8f9fa;
            color: #333;
            font-weight: 600;
        }
        
        td {
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
        }
        
        .delete-btn {
            padding: 5px 10px;
            background: #ff4757;
            color: white;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        
        .delete-btn:hover {
            background: #ff6b81;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">
            ASINOITE Admin
            <span class="admin-badge">ADMIN</span>
        </div>
        <div class="user-info">
            <span class="username">admin</span>
            <a href="/logout" class="logout-btn">Выйти</a>
        </div>
    </div>
    
    <div class="container">
        <div class="header">
            <h1>Управление пользователями</h1>
            <a href="/admin/dashboard" class="back-btn">← Назад</a>
        </div>
        
        <table>
            <tr>
                <th>ID</th>
                <th>Имя пользователя</th>
                <th>Дата регистрации</th>
                <th>Создано сайтов</th>
                <th>Действия</th>
            </tr>
            {% for user in users %}
            <tr>
                <td>{{ user[0] }}</td>
                <td>{{ user[1] }}</td>
                <td>{{ user[2] }}</td>
                <td>{{ user[3] }}</td>
                <td>
                    <button class="delete-btn" onclick="deleteUser({{ user[0] }})">Удалить</button>
                </td>
            </tr>
            {% endfor %}
        </table>
    </div>
    
    <script>
        async function deleteUser(userId) {
            if (confirm('Вы уверены, что хотите удалить этого пользователя?')) {
                const response = await fetch('/admin/delete_user/' + userId, {
                    method: 'POST'
                });
                const data = await response.json();
                if (data.success) {
                    location.reload();
                }
            }
        }
    </script>
</body>
</html>
'''

admin_sites_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - Все сайты</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        
        .navbar {
            background: #1a1a1a;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #fff;
        }
        
        .admin-badge {
            background: #ff4757;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .username {
            color: #fff;
            font-weight: 500;
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: #333;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: #444;
        }
        
        .container {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        
        .back-btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s;
        }
        
        .back-btn:hover {
            background: #5a6fd6;
        }
        
        .sites-grid {
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(350px, 1fr));
            gap: 20px;
        }
        
        .site-card {
            background: white;
            border-radius: 15px;
            padding: 20px;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        }
        
        .site-user {
            font-weight: 600;
            color: #667eea;
            margin-bottom: 10px;
        }
        
        .site-prompt {
            color: #333;
            margin-bottom: 10px;
            word-break: break-word;
        }
        
        .site-date {
            color: #999;
            font-size: 14px;
            margin-bottom: 15px;
        }
        
        .site-views {
            color: #666;
            font-size: 14px;
            margin-bottom: 15px;
        }
        
        .view-link {
            display: inline-block;
            padding: 8px 16px;
            background: #f0f0f0;
            color: #333;
            text-decoration: none;
            border-radius: 6px;
            font-size: 14px;
        }
        
        .view-link:hover {
            background: #e0e0e0;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">
            ASINOITE Admin
            <span class="admin-badge">ADMIN</span>
        </div>
        <div class="user-info">
            <span class="username">admin</span>
            <a href="/logout" class="logout-btn">Выйти</a>
        </div>
    </div>
    
    <div class="container">
        <div class="header">
            <h1>Все созданные сайты</h1>
            <a href="/admin/dashboard" class="back-btn">← Назад</a>
        </div>
        
        <div class="sites-grid">
            {% for site in sites %}
            <div class="site-card">
                <div class="site-user">Пользователь: {{ site[1] }}</div>
                <div class="site-prompt">Запрос: {{ site[2] }}</div>
                <div class="site-date">Создан: {{ site[3] }}</div>
                <div class="site-views">👁️ {{ site[4] }} просмотров</div>
                <a href="/public/site/{{ site[0] }}" class="view-link" target="_blank">Просмотреть сайт</a>
            </div>
            {% endfor %}
        </div>
    </div>
</body>
</html>
'''

admin_visits_html = '''
<!DOCTYPE html>
<html lang="ru">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>ASINOITE - История посещений</title>
    <style>
        * {
            margin: 0;
            padding: 0;
            box-sizing: border-box;
        }
        
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            background: #f5f5f5;
        }
        
        .navbar {
            background: #1a1a1a;
            padding: 20px 40px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.3);
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        
        .logo {
            font-size: 24px;
            font-weight: bold;
            color: #fff;
        }
        
        .admin-badge {
            background: #ff4757;
            color: white;
            padding: 5px 10px;
            border-radius: 5px;
            font-size: 12px;
            margin-left: 10px;
        }
        
        .user-info {
            display: flex;
            align-items: center;
            gap: 20px;
        }
        
        .username {
            color: #fff;
            font-weight: 500;
        }
        
        .logout-btn {
            padding: 8px 16px;
            background: #333;
            color: white;
            text-decoration: none;
            border-radius: 6px;
            transition: background 0.3s;
        }
        
        .logout-btn:hover {
            background: #444;
        }
        
        .container {
            max-width: 1400px;
            margin: 40px auto;
            padding: 0 20px;
        }
        
        .header {
            display: flex;
            justify-content: space-between;
            align-items: center;
            margin-bottom: 30px;
        }
        
        .back-btn {
            padding: 10px 20px;
            background: #667eea;
            color: white;
            text-decoration: none;
            border-radius: 8px;
            transition: background 0.3s;
        }
        
        .back-btn:hover {
            background: #5a6fd6;
        }
        
        table {
            width: 100%;
            background: white;
            border-radius: 15px;
            overflow: hidden;
            box-shadow: 0 5px 20px rgba(0,0,0,0.05);
        }
        
        th {
            text-align: left;
            padding: 15px;
            background: #f8f9fa;
            color: #333;
            font-weight: 600;
        }
        
        td {
            padding: 15px;
            border-bottom: 1px solid #e0e0e0;
            font-size: 14px;
        }
        
        .user-badge {
            display: inline-block;
            padding: 3px 8px;
            border-radius: 4px;
            font-size: 12px;
            font-weight: 600;
        }
        
        .user-badge.registered {
            background: #d4edda;
            color: #155724;
        }
        
        .user-badge.guest {
            background: #f8d7da;
            color: #721c24;
        }
        
        .page {
            background: #e9ecef;
            padding: 2px 6px;
            border-radius: 4px;
            font-family: monospace;
        }
    </style>
</head>
<body>
    <div class="navbar">
        <div class="logo">
            ASINOITE Admin
            <span class="admin-badge">ADMIN</span>
        </div>
        <div class="user-info">
            <span class="username">admin</span>
            <a href="/logout" class="logout-btn">Выйти</a>
        </div>
    </div>
    
    <div class="container">
        <div class="header">
            <h1>Кто заходил на сайт?</h1>
            <a href="/admin/dashboard" class="back-btn">← Назад</a>
        </div>
        
        <table>
            <tr>
                <th>Время</th>
                <th>Пользователь</th>
                <th>IP адрес</th>
                <th>Страница</th>
                <th>User Agent</th>
            </tr>
            {% for visit in visits %}
            <tr>
                <td>{{ visit[7] }}</td>
                <td>
                    {% if visit[2] %}
                        <span class="user-badge registered">{{ visit[2] }}</span>
                    {% else %}
                        <span class="user-badge guest">Гость</span>
                    {% endif %}
                </td>
                <td>{{ visit[3] }}</td>
                <td><span class="page">{{ visit[5] }}</span></td>
                <td style="max-width: 300px; overflow: auto;">{{ visit[4] }}</td>
            </tr>
            {% endfor %}
        </table>
    </div>
</body>
</html>
'''

@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('dashboard'))
    return render_template_string(index_html)

@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'success': False, 'message': 'Username and password required'})
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    try:
        conn = sqlite3.connect('asinoite.db')
        c = conn.cursor()
        c.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, hashed_password))
        conn.commit()
        user_id = c.lastrowid
        conn.close()
        
        session['user_id'] = user_id
        session['username'] = username
        session['is_admin'] = False
        
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Username already exists'})

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    hashed_password = hashlib.sha256(password.encode()).hexdigest()
    
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute("SELECT id, is_admin FROM users WHERE username = ? AND password = ?", (username, hashed_password))
    user = c.fetchone()
    conn.close()
    
    if user:
        session['user_id'] = user[0]
        session['username'] = username
        session['is_admin'] = bool(user[1])
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'message': 'Invalid credentials'})

@app.route('/dashboard')
def dashboard():
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute("SELECT id, prompt, html_code, views, created_at FROM sites WHERE user_id = ? ORDER BY created_at DESC", (session['user_id'],))
    sites = c.fetchall()
    conn.close()
    
    return render_template_string(dashboard_html, username=session['username'], sites=sites)

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/generate', methods=['POST'])
def generate():
    if 'user_id' not in session:
        return jsonify({'success': False, 'message': 'Not logged in'})
    
    data = request.get_json()
    prompt = data.get('prompt')
    
    if not prompt:
        return jsonify({'success': False, 'message': 'Prompt required'})
    
    ai_prompt = f"Привет сделай сайт на HTML НО пиши только код без лишнего без объяснений как работает код Пиши без MARKDOWN форматирование и не пиши типа для форматирование кода Пиши только код Запрос пользователя {prompt}"
    
    try:
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:5000",
                "X-Title": "ASINOITE"
            },
            json={
                "model": MODEL_NAME,
                "messages": [
                    {"role": "user", "content": ai_prompt}
                ]
            },
            timeout=30
        )
        
        if response.status_code == 200:
            result = response.json()
            
            if 'choices' in result and len(result['choices']) > 0:
                html_code = result['choices'][0]['message']['content']
                
                conn = sqlite3.connect('asinoite.db')
                c = conn.cursor()
                c.execute("INSERT INTO sites (user_id, prompt, html_code) VALUES (?, ?, ?)", 
                         (session['user_id'], prompt, html_code))
                conn.commit()
                site_id = c.lastrowid
                conn.close()
                
                return jsonify({'success': True, 'html': html_code, 'site_id': site_id})
            else:
                return jsonify({'success': False, 'message': 'AI response format error'})
        else:
            error_text = response.text
            return jsonify({'success': False, 'message': f'AI generation failed with status {response.status_code}: {error_text}'})
            
    except Exception as e:
        return jsonify({'success': False, 'message': str(e)})

@app.route('/site/<int:site_id>')
def view_site(site_id):
    if 'user_id' not in session:
        return redirect(url_for('index'))
    
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute("SELECT html_code, user_id FROM sites WHERE id = ?", (site_id,))
    site = c.fetchone()
    conn.close()
    
    if site and (site[1] == session['user_id'] or session.get('is_admin')):
        return render_template_string(view_site_html, html_code=site[0])
    else:
        return redirect(url_for('dashboard'))

@app.route('/feed')
def feed():
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute('''SELECT sites.id, sites.user_id, users.username, sites.prompt, sites.html_code, sites.created_at, sites.views 
                 FROM sites JOIN users ON sites.user_id = users.id 
                 WHERE sites.is_public = 1 
                 ORDER BY sites.created_at DESC''')
    sites = c.fetchall()
    conn.close()
    
    return render_template_string(feed_html, sites=sites, session=session)

@app.route('/public/site/<int:site_id>')
def public_view_site(site_id):
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute("SELECT html_code, user_id FROM sites WHERE id = ? AND is_public = 1", (site_id,))
    site = c.fetchone()
    
    if site:
        c.execute("UPDATE sites SET views = views + 1 WHERE id = ?", (site_id,))
        conn.commit()
        conn.close()
        return render_template_string(public_view_site_html, html_code=site[0])
    else:
        conn.close()
        return redirect(url_for('feed'))

@app.route('/public/site/<int:site_id>/code')
def public_view_code(site_id):
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute("SELECT html_code FROM sites WHERE id = ? AND is_public = 1", (site_id,))
    site = c.fetchone()
    conn.close()
    
    if site:
        return render_template_string(public_code_view_html, html_code=site[0])
    else:
        return redirect(url_for('feed'))

@app.route('/sysadminpanel', methods=['GET', 'POST'])
def admin_panel():
    if request.method == 'POST':
        password = request.form.get('password')
        if password == ADMIN_PASSWORD:
            session['is_admin'] = True
            return redirect(url_for('admin_dashboard'))
        else:
            return render_template_string(admin_login_html, error='Неверный пароль')
    return render_template_string(admin_login_html)

@app.route('/admin/dashboard')
@admin_required
def admin_dashboard():
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    
    c.execute("SELECT COUNT(*) FROM users")
    total_users = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM sites")
    total_sites = c.fetchone()[0]
    
    c.execute("SELECT COUNT(*) FROM visits")
    total_visits = c.fetchone()[0]
    
    c.execute('''SELECT users.username, COUNT(sites.id) as site_count 
                 FROM users LEFT JOIN sites ON users.id = sites.user_id 
                 GROUP BY users.id ORDER BY site_count DESC LIMIT 5''')
    top_users = c.fetchall()
    
    conn.close()
    
    return render_template_string(admin_dashboard_html, 
                                 total_users=total_users, 
                                 total_sites=total_sites, 
                                 total_visits=total_visits,
                                 top_users=top_users)

@app.route('/admin/users')
@admin_required
def admin_users():
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute('''SELECT id, username, registered_at, 
                 (SELECT COUNT(*) FROM sites WHERE user_id = users.id) as site_count 
                 FROM users ORDER BY registered_at DESC''')
    users = c.fetchall()
    conn.close()
    
    return render_template_string(admin_users_html, users=users)

@app.route('/admin/sites')
@admin_required
def admin_sites():
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute('''SELECT sites.id, users.username, sites.prompt, sites.created_at, sites.views 
                 FROM sites JOIN users ON sites.user_id = users.id 
                 ORDER BY sites.created_at DESC''')
    sites = c.fetchall()
    conn.close()
    
    return render_template_string(admin_sites_html, sites=sites)

@app.route('/admin/visits')
@admin_required
def admin_visits():
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute('''SELECT * FROM visits ORDER BY visited_at DESC LIMIT 100''')
    visits = c.fetchall()
    conn.close()
    
    return render_template_string(admin_visits_html, visits=visits)

@app.route('/admin/delete_user/<int:user_id>', methods=['POST'])
@admin_required
def delete_user(user_id):
    conn = sqlite3.connect('asinoite.db')
    c = conn.cursor()
    c.execute("DELETE FROM sites WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM visits WHERE user_id = ?", (user_id,))
    c.execute("DELETE FROM users WHERE id = ?", (user_id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.before_request
def log_visit():
    if request.endpoint and request.endpoint != 'static' and request.endpoint != 'public_view_site' and request.endpoint != 'public_view_code':
        try:
            conn = sqlite3.connect('asinoite.db')
            c = conn.cursor()
            user_id = session.get('user_id')
            username = session.get('username')
            c.execute('''INSERT INTO visits (user_id, username, ip_address, user_agent, page)
                        VALUES (?, ?, ?, ?, ?)''',
                     (user_id, username, request.remote_addr, request.user_agent.string, request.path))
            conn.commit()
            conn.close()
        except:
            pass

if __name__ == '__main__':
    app.run(debug=True)
