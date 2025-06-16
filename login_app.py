import os
import json
from flask import Flask, request, render_template_string, redirect, url_for, session
import gspread
from google.oauth2.service_account 
import Credentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # غيّرو في الإنتاج

# بيانات الدخول للموظفين (في الإنتاج خزنها في قاعدة بيانات)
USERS = {
    "201029664170": "pass1",
    "201029773000": "pass2",
    "201029772000": "pass3",
    "201055855040": "pass4",
    "201029455000": "pass5",
    "201027480870": "pass6",
    "201055855030": "pass7"
}

# إعداد Google Sheet
SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM'
scopes = ["https://www.googleapis.com/auth/spreadsheets"]

# تحميل بيانات اعتماد Google من متغير البيئة
json_creds = os.getenv('GOOGLE_CREDENTIALS')
info = json.loads(json_creds)
credentials = Credentials.from_service_account_info(info, scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).worksheet("sheet")

# HTML - صفحة تسجيل الدخول
LOGIN_PAGE = '''
<!doctype html>
<html>
<head><title>تسجيل الدخول</title></head>
<body style="text-align:center; font-family:sans-serif">
<h2>تسجيل الدخول</h2>
<form method="POST">
  <input type="text" name="username" placeholder="رقم الموظف" required><br><br>
  <input type="password" name="password" placeholder="كلمة المرور" required><br><br>
  <input type="submit" value="دخول">
</form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
</body>
</html>
'''

# HTML - لوحة التحكم
DASHBOARD_PAGE = '''
<!doctype html>
<html>
<head><title>لوحة التحكم</title></head>
<body style="font-family:sans-serif">
<h2>مرحبًا {{ username }}</h2>
<table border="1" cellpadding="10">
  <tr><th>رقم العميل</th><th>الرسالة الأخيرة</th><th>الوقت</th><th>رد</th></tr>
  {% for row in messages %}
  <tr>
    <td>{{ row.Phone }}</td>
    <td>{{ row.LastMessage }}</td>
    <td>{{ row.LastAssignedTime }}</td>
    <td><form method="POST" action="/reply/{{ row.Phone }}"><input type="submit" value="رد"></form></td>
  </tr>
  {% endfor %}
</table>
<br><a href="{{ url_for('logout') }}">تسجيل الخروج</a>
</body>
</html>
'''

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if username in USERS and USERS[username] == password:
            session['user'] = username
            return redirect(url_for('dashboard'))
        else:
            error = "رقم الموظف أو كلمة المرور غير صحيحة"
    return render_template_string(LOGIN_PAGE, error=error)

@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    all_data = sheet.get_all_records()
    user_data = [row for row in all_data if row['AssignedTo'] == session['user']]
    return render_template_string(DASHBOARD_PAGE, username=session['user'], messages=user_data)

@app.route('/reply/<phone>', methods=['POST'])
def reply(phone):
    return f"هنا سيتم فتح صفحة الرد على: {phone}"

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
