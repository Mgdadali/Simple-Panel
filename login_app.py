import os
import json
from flask import Flask, request, render_template_string, redirect, url_for, session
import gspread
from google.oauth2.service_account import Credentials

app = Flask(name) app.secret_key = 'your_secret_key_here'  # غيّرو في الإنتاج

Google Sheets إعداد

SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM' scopes = ["https://www.googleapis.com/auth/spreadsheets"]

تحميل بيانات اعتماد Google من متغير البيئة

json_creds = os.getenv('GOOGLE_CREDENTIALS') if not json_creds: raise Exception("❌ GOOGLE_CREDENTIALS not found in environment.") credentials = Credentials.from_service_account_info(json.loads(json_creds), scopes=scopes) client = gspread.authorize(credentials)

sheet = client.open_by_key(SHEET_ID).worksheet("sheet")

بيانات تسجيل الدخول (مؤقتة)

USERS = { "201029664170": "pass1", "201029773000": "pass2", "201029772000": "pass3", "201055855040": "pass4", "201029455000": "pass5", "201027480870": "pass6", "201055855030": "pass7" }

واجهة تسجيل الدخول

LOGIN_PAGE = ''' <!doctype html>

<html lang="ar" dir="rtl">
  <head>
    <meta charset="utf-8">
    <title>تسجيل الدخول</title>
    <style>
      body { font-family: Arial; background: #f2f2f2; padding: 50px; }
      .login-box {
        background: white;
        padding: 30px;
        max-width: 400px;
        margin: auto;
        border-radius: 8px;
        box-shadow: 0 0 10px #ccc;
      }
      input[type=text], input[type=password] {
        width: 100%%; padding: 10px; margin: 10px 0; border: 1px solid #ccc;
        border-radius: 5px;
      }
      input[type=submit] {
        background: #007bff; color: white; padding: 10px; width: 100%%;
        border: none; border-radius: 5px; cursor: pointer;
      }
      .error { color: red; margin-top: 10px; }
    </style>
  </head>
  <body>
    <div class="login-box">
      <h2>تسجيل الدخول</h2>
      <form method="POST">
        <label>رقم الموظف:</label>
        <input type="text" name="username" required>
        <label>كلمة المرور:</label>
        <input type="password" name="password" required>
        <input type="submit" value="دخول">
      </form>
      {% if error %}
        <div class="error">{{ error }}</div>
      {% endif %}
    </div>
  </body>
</html>
'''واجهة لوحة التحكم

DASHBOARD_PAGE = ''' <!doctype html>

<html lang="ar" dir="rtl">
  <head>
    <meta charset="utf-8">
    <title>لوحة الموظف</title>
    <style>
      body { font-family: Arial; background: #f9f9f9; padding: 30px; }
      .dashboard-box {
        background: white; padding: 20px; border-radius: 8px;
        max-width: 700px; margin: auto;
        box-shadow: 0 0 10px rgba(0,0,0,0.1);
      }
      .message-item {
        padding: 10px; margin: 10px 0; border-bottom: 1px solid #eee;
        cursor: pointer;
      }
      .message-item:hover {
        background-color: #f0f0f0;
      }
      textarea {
        width: 100%%; height: 80px; margin-top: 10px;
        border-radius: 5px; padding: 10px; border: 1px solid #ccc;
      }
      button {
        background-color: #28a745; color: white; padding: 10px;
        border: none; border-radius: 5px; margin-top: 10px;
        cursor: pointer;
      }
    </style>
  </head>
  <body>
    <div class="dashboard-box">
      <h2>مرحبًا {{ username }}</h2>
      <p>اختر رسالة للرد عليها:</p>
      <div id="messages">
        <div class="message-item" onclick="selectMessage('رقم1')">رسالة من: رقم1 - السلام عليكم</div>
        <div class="message-item" onclick="selectMessage('رقم2')">رسالة من: رقم2 - محتاج مساعدة</div>
        <!-- سيتم استبدال هذه برسائل حقيقية لاحقًا -->
      </div>
      <form method="POST" action="#">
        <label>الرد:</label>
        <textarea name="reply"></textarea>
        <button type="submit">إرسال الرد</button>
      </form>
      <br>
      <a href="{{ url_for('logout') }}">تسجيل الخروج</a>
    </div>
    <script>
      function selectMessage(sender) {
        alert('تم اختيار الشات من ' + sender);
        // في النسخة القادمة ممكن نظهر الرسالة في مربع الرد
      }
    </script>
  </body>
</html>
'''@app.route('/login', methods=['GET', 'POST']) def login(): error = None if request.method == 'POST': username = request.form['username'] password = request.form['password'] if username in USERS and USERS[username] == password: session['user'] = username return redirect(url_for('dashboard')) else: error = "رقم الموظف أو كلمة المرور غير صحيحة" return render_template_string(LOGIN_PAGE, error=error)

@app.route('/dashboard', methods=['GET', 'POST']) def dashboard(): if 'user' not in session: return redirect(url_for('login')) return render_template_string(DASHBOARD_PAGE, username=session['user'])

@app.route('/logout') def logout(): session.pop('user', None) return redirect(url_for('login'))

if name == 'main': port = int(os.environ.get("PORT", 5000)) app.run(host='0.0.0.0', port=port, debug=True)

