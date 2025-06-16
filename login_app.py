import os import json from flask import Flask, request, render_template_string, redirect, url_for, session import gspread from google.oauth2.service_account import Credentials

app = Flask(name) app.secret_key = 'your_secret_key_here'  # غيّر المفتاح في الإنتاج

بيانات الدخول

USERS = { "201029664170": "pass1", "201029773000": "pass2", "201029772000": "pass3", "201055855040": "pass4", "201029455000": "pass5", "201027480870": "pass6", "201055855030": "pass7" }

Google Sheets config

SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM' scopes = ["https://www.googleapis.com/auth/spreadsheets"]

json_creds = os.getenv("GOOGLE_CREDENTIALS") if not json_creds: raise Exception("GOOGLE_CREDENTIALS not found in environment variables")

info = json.loads(json_creds) credentials = Credentials.from_service_account_info(info, scopes=scopes) client = gspread.authorize(credentials) sheet = client.open_by_key(SHEET_ID).worksheet("sheet")

HTML Templates

LOGIN_PAGE = ''' <!doctype html>

<title>تسجيل الدخول</title>
<h2 style="text-align:center">تسجيل الدخول</h2>
<form method="POST" style="max-width: 300px; margin: auto;">
  <label>رقم الموظف:</label><br>
  <input type="text" name="username" required><br>
  <label>كلمة المرور:</label><br>
  <input type="password" name="password" required><br><br>
  <input type="submit" value="دخول">
</form>
{% if error %}<p style="color:red; text-align:center">{{ error }}</p>{% endif %}
'''DASHBOARD_PAGE = ''' <!doctype html>

<title>لوحة الموظف</title>
<h2 style="text-align:center">مرحبًا {{ username }}</h2>
<table border="1" style="width:80%; margin:auto; border-collapse: collapse;">
    <thead>
        <tr style="background-color: #f2f2f2;">
            <th>رقم العميل</th>
            <th>الرسالة</th>
            <th>وقت الإرسال</th>
        </tr>
    </thead>
    <tbody>
        {% for row in messages %}
        <tr>
            <td>{{ row['Phone'] }}</td>
            <td>{{ row['LastMessage'] }}</td>
            <td>{{ row['LastAssignedTime'] }}</td>
        </tr>
        {% endfor %}
    </tbody>
</table>
<p style="text-align:center; margin-top:20px;"><a href="{{ url_for('logout') }}">تسجيل الخروج</a></p>
'''@app.route('/login', methods=['GET', 'POST']) def login(): error = None if request.method == 'POST': username = request.form['username'] password = request.form['password'] if username in USERS and USERS[username] == password: session['user'] = username return redirect(url_for('dashboard')) else: error = "رقم الموظف أو كلمة المرور غير صحيحة" return render_template_string(LOGIN_PAGE, error=error)

@app.route('/dashboard') def dashboard(): if 'user' not in session: return redirect(url_for('login'))

data = sheet.get_all_records()
filtered = [row for row in data if row.get("AssignedTo") == session['user']]
return render_template_string(DASHBOARD_PAGE, username=session['user'], messages=filtered)

@app.route('/logout') def logout(): session.pop('user', None) return redirect(url_for('login'))

if name == 'main': port = int(os.environ.get("PORT", 5000)) app.run(host='0.0.0.0', port=port, debug=True)

