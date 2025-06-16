import os
import json
from flask import Flask, request, render_template_string, redirect, url_for, session
import gspread
from google.oauth2.service_account import Credentials

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # غيّره في الإنتاج

# بيانات تسجيل الدخول (تقدر تخزنها في DB لاحقاً)
USERS = {
    "201029664170": "pass1",
    "201029773000": "pass2",
    "201029772000": "pass3",
    "201055855040": "pass4",
    "201029455000": "pass5",
    "201027480870": "pass6",
    "201055855030": "pass7"
}

# HTML: صفحة تسجيل الدخول
LOGIN_PAGE = '''
<!doctype html>
<title>تسجيل الدخول</title>
<h2>تسجيل الدخول</h2>
<form method="POST">
  <label>رقم الموظف:</label><br>
  <input type="text" name="username" required><br>
  <label>كلمة المرور:</label><br>
  <input type="password" name="password" required><br><br>
  <input type="submit" value="دخول">
</form>
{% if error %}<p style="color:red">{{ error }}</p>{% endif %}
'''

# HTML: لوحة الموظف مع عرض الرسائل
DASHBOARD_PAGE = '''
<!doctype html>
<title>لوحة الموظف</title>
<h2>مرحبًا {{ username }}</h2>
<h3>الرسائل المخصصة لك:</h3>
<table border="1" cellpadding="5">
  <tr><th>رقم العميل</th><th>الرسالة</th><th>الزمن</th></tr>
  {% for row in messages %}
    <tr>
      <td>{{ row.Phone }}</td>
      <td>{{ row.LastMessage }}</td>
      <td>{{ row.LastAssignedTime }}</td>
    </tr>
  {% endfor %}
</table>
<br>
<a href="{{ url_for('logout') }}">تسجيل الخروج</a>
'''

# إعداد Google Sheets
SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM'
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
json_creds = os.getenv("GOOGLE_CREDENTIALS")

credentials = Credentials.from_service_account_info(json.loads(json_creds), scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).worksheet("sheet")

# مسار تسجيل الدخول
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

# مسار لوحة التحكم
@app.route('/dashboard')
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))
    
    username = session['user']
    data = sheet.get_all_records()

    user_msgs = [
        row for row in data if str(row.get("AssignedTo")) == username
    ]

    return render_template_string(DASHBOARD_PAGE, username=username, messages=user_msgs)

# مسار تسجيل الخروج
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# تشغيل التطبيق
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 8080))
    app.run(host='0.0.0.0', port=port, debug=True)
