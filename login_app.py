import os
import json
from flask import Flask, request, render_template_string, redirect, url_for, session
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # غيّره في الإنتاج

# بيانات الدخول للمستخدمين
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

json_creds = os.getenv('GOOGLE_CREDENTIALS')
info = json.loads(json_creds)
credentials = Credentials.from_service_account_info(info, scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).worksheet("sheet")  # اسم الورقة

# واجهة تسجيل الدخول
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

# لوحة التحكم
DASHBOARD_PAGE = '''
<!doctype html>
<title>لوحة التحكم</title>
<h2>مرحبًا {{ username }}</h2>
{% if messages %}
  <ul>
    {% for msg in messages %}
      <li><strong>{{ msg.phone }}</strong>: {{ msg.last_message }}</li>
    {% endfor %}
  </ul>
{% else %}
  <p>🚫 لا توجد رسائل حتى الآن.</p>
{% endif %}
<a href="{{ url_for('logout') }}">🚪 تسجيل الخروج</a>
'''

def get_user_messages(username):
    data = sheet.get_all_records()
    msgs = []
    for row in data:
        assigned = str(row.get("AssignedTo")).strip()
        if assigned == str(username).strip():
            msgs.append({
                "phone": str(row.get("Phone")),
                "last_message": row.get("LastMessage"),
            })
    return msgs

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
    user = session['user']
    messages = get_user_messages(user)
    return render_template_string(DASHBOARD_PAGE, username=user, messages=messages)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
