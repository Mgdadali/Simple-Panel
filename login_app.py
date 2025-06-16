import os
import json
from flask import Flask, request, render_template_string, redirect, url_for, session
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # غيّرو في الإنتاج

# بيانات الموظفين
USERS = {
    "201029664170": "pass1",
    "201029773000": "pass2",
    "201029772000": "pass3",
    "201055855040": "pass4",
    "201029455000": "pass5",
    "201027480870": "pass6",
    "201055855030": "pass7"
}

# إعداد Google Sheets
SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM'
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
json_creds = os.getenv('GOOGLE_CREDENTIALS')
credentials = Credentials.from_service_account_info(json.loads(json_creds), scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).worksheet("sheet")
log_sheet = client.open_by_key(SHEET_ID).worksheet("Messages Log")

# إعداد Ultramsg
ULTRAMSG_TOKEN = os.getenv('ULTRAMSG_TOKEN')
ULTRAMSG_INSTANCE = os.getenv('ULTRAMSG_INSTANCE')

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

# واجهة لوحة الرسائل
DASHBOARD_PAGE = '''
<!doctype html>
<title>لوحة الرسائل</title>
<h2>مرحباً {{ username }}</h2>
<form method="POST">
  <label for="recipient">اختر المحادثة:</label><br>
  <select name="recipient">
    {% for row in messages %}
      <option value="{{ row['Phone'] }}">{{ row['Phone'] }}: {{ row['LastMessage'][:30] }}</option>
    {% endfor %}
  </select><br><br>
  <label for="reply">رد:</label><br>
  <textarea name="reply" rows="3" cols="50" required></textarea><br><br>
  <input type="submit" value="إرسال الرد">
</form>
<ul>
{% for row in messages %}
  <li><b>{{ row['Phone'] }}</b>: {{ row['LastMessage'] }}</li>
{% endfor %}
</ul>
<a href="{{ url_for('logout') }}">🚪 تسجيل الخروج</a>
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

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
    if 'user' not in session:
        return redirect(url_for('login'))

    username = session['user']
    data = sheet.get_all_records()
    my_messages = [row for row in data if str(row['AssignedTo']) == username]

    if request.method == 'POST':
        recipient = request.form['recipient']
        reply = request.form['reply']
        send_message(recipient, reply)
        log_message(recipient, username, reply)

    return render_template_string(DASHBOARD_PAGE, username=username, messages=my_messages)

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

def send_message(to, message):
    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE}/messages/chat"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": to,
        "body": message
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        print("📤 تم الإرسال:", response.status_code, response.text)  # ← سطر التتبع المهم
    except Exception as e:
        print("❌ فشل الإرسال:", e)

def log_message(phone, sender, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_sheet.append_row([phone, sender, message, timestamp])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
