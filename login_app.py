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
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>لوحة التحكم - {{ username }}</title>
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 font-sans">

  <div class="max-w-5xl mx-auto py-8 px-4">

    <div class="flex justify-between items-center mb-8">
      <div class="flex items-center space-x-4 space-x-reverse">
        <img src="https://i.ibb.co/bR2qkN9q/6dd05738-f28d-457f-a1b3-fa9ffa42abb6.png" alt="شعار 249" class="w-16 h-16 rounded shadow-md">
        <h1 class="text-3xl font-extrabold text-gray-800">نظام الرد على العملاء - 249</h1>
      </div>
      <div>
        <span class="text-gray-700 font-semibold">👤 {{ username }}</span>
        <a href="{{ url_for('logout') }}" class="ml-4 text-red-600 hover:underline">🚪 تسجيل الخروج</a>
      </div>
    </div>

    <div class="bg-white shadow-md rounded-lg p-6 mb-8">
      <form method="POST" class="space-y-4">
        <div>
          <label for="recipient" class="block text-gray-700 font-medium mb-1">اختر المحادثة:</label>
          <select name="recipient" class="w-full p-2 border border-gray-300 rounded">
            {% for row in messages %}
              <option value="{{ row['Phone'] }}">{{ row['Phone'] }}: {{ row['LastMessage'][:30] }}</option>
            {% endfor %}
          </select>
        </div>
        <div>
          <label for="reply" class="block text-gray-700 font-medium mb-1">الرد:</label>
          <textarea name="reply" rows="3" class="w-full p-2 border border-gray-300 rounded" placeholder="اكتب الرد هنا..." required></textarea>
        </div>
        <button type="submit" class="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700 transition">
          إرسال الرد
        </button>
      </form>
    </div>

    <div class="bg-white shadow-md rounded-lg p-4">
      <h3 class="text-lg font-semibold mb-4 text-gray-700">المحادثات الحالية</h3>
      <ul class="space-y-3">
        {% for row in messages %}
          <li class="border-b pb-2">
            <span class="font-bold text-gray-800">{{ row['Phone'] }}</span>:
            <span class="text-gray-600">{{ row['LastMessage'] }}</span>
          </li>
        {% endfor %}
      </ul>
    </div>

  </div>

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
    if "@c.us" in to:
        to = to.replace("@c.us", "")
    if not to.startswith("2"):
        print("❌ رقم غير صالح:", to)
        return
    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE}/messages/chat"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": to,
        "body": message
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        print("📤 تم إرسال الرد:", response.status_code, response.text)
    except Exception as e:
        print("❌ فشل الإرسال:", e)

def log_message(phone, sender, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_sheet.append_row([phone, sender, message, timestamp])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port)
