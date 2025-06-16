import os
import json 
from flask import Flask, request, render_template_string, redirect, url_for, session, jsonify 
import gspread 
from google.oauth2.service_account import Credentials 
from datetime import datetime 
import requests

app = Flask(name) app.secret_key = 'your_secret_key_here'

إعداد Google Sheet

SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM' scopes = ["https://www.googleapis.com/auth/spreadsheets"]

تحميل بيانات الاعتماد

json_creds = os.getenv('GOOGLE_CREDENTIALS') info = json.loads(json_creds) credentials = Credentials.from_service_account_info(info, scopes=scopes) client = gspread.authorize(credentials) sheet = client.open_by_key(SHEET_ID).worksheet("sheet")

بيانات تسجيل الدخول

USERS = { "201029664170": "pass1", "201029773000": "pass2", "201029772000": "pass3", "201055855040": "pass4", "201029455000": "pass5", "201027480870": "pass6", "201055855030": "pass7" }

ULTRAMSG_INSTANCE_ID = os.getenv("ULTRAMSG_INSTANCE_ID") ULTRAMSG_TOKEN = os.getenv("ULTRAMSG_TOKEN")

LOGIN_PAGE = ''' <!doctype html>

<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>تسجيل الدخول</title>
  <style>
    body { font-family: Tahoma; background: #f0f4f7; text-align: center; padding: 50px; }
    form { background: white; padding: 20px; border-radius: 10px; display: inline-block; box-shadow: 0 0 10px rgba(0,0,0,0.1); }
    input { padding: 10px; margin: 10px; width: 200px; }
    .error { color: red; }
  </style>
</head>
<body>
  <h2>تسجيل الدخول</h2>
  <form method="POST">
    <input type="text" name="username" placeholder="رقم الموظف" required><br>
    <input type="password" name="password" placeholder="كلمة المرور" required><br>
    <input type="submit" value="دخول">
  </form>
  {% if error %}<p class="error">{{ error }}</p>{% endif %}
</body>
</html>
'''DASHBOARD_PAGE = ''' <!doctype html>

<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>لوحة الموظف</title>
  <style>
    body { font-family: Tahoma; background: #eef2f3; padding: 30px; }
    .chat-box { background: #fff; padding: 20px; border-radius: 10px; max-width: 600px; margin: auto; box-shadow: 0 0 15px rgba(0,0,0,0.1); }
    .msg { padding: 10px; border-bottom: 1px solid #ddd; }
    .msg:last-child { border-bottom: none; }
    form { margin-top: 20px; text-align: center; }
    input, textarea { width: 80%; padding: 10px; margin: 5px; border-radius: 5px; border: 1px solid #ccc; }
    button { padding: 10px 20px; border: none; background: #008cba; color: white; border-radius: 5px; cursor: pointer; }
    a { display: block; text-align: center; margin-top: 20px; color: red; }
  </style>
</head>
<body>
  <div class="chat-box">
    <h2>مرحبًا {{ username }}</h2>
    {% for row in messages %}
      <div class="msg">
        <strong>{{ row['Phone'] }}:</strong> {{ row['LastMessage'] }}
        <form method="POST" action="{{ url_for('reply') }}">
          <input type="hidden" name="to" value="{{ row['Phone'] }}">
          <textarea name="message" placeholder="اكتب الرد هنا..."></textarea><br>
          <button type="submit">📨 إرسال</button>
        </form>
      </div>
    {% endfor %}
    {% if not messages %}<p>لا توجد رسائل مخصصة لك</p>{% endif %}
    <a href="{{ url_for('logout') }}">🚪 تسجيل الخروج</a>
  </div>
</body>
</html>
'''@app.route('/login', methods=['GET', 'POST']) def login(): error = None if request.method == 'POST': username = request.form['username'] password = request.form['password'] if username in USERS and USERS[username] == password: session['user'] = username return redirect(url_for('dashboard')) else: error = "رقم الموظف أو كلمة المرور غير صحيحة" return render_template_string(LOGIN_PAGE, error=error)

@app.route('/dashboard') def dashboard(): if 'user' not in session: return redirect(url_for('login')) records = sheet.get_all_records() messages = [row for row in records if row['AssignedTo'] == session['user']] return render_template_string(DASHBOARD_PAGE, username=session['user'], messages=messages)

@app.route('/reply', methods=['POST']) def reply(): if 'user' not in session: return redirect(url_for('login')) to = request.form['to'] message = request.form['message'] url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat" payload = { "token": ULTRAMSG_TOKEN, "to": to, "body": message } response = requests.post(url, data=payload) print("📤 Sending response:", response.text) return redirect(url_for('dashboard'))

@app.route('/logout') def logout(): session.pop('user', None) return redirect(url_for('login'))

if name == 'main': port = int(os.environ.get("PORT", 5000)) app.run(host='0.0.0.0', port=port, debug=True)

