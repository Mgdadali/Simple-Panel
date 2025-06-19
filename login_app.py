import os
import json
from flask import Flask, request, render_template_string, redirect, url_for, session
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # غيّر المفتاح في الإنتاج

# بيانات تسجيل الدخول للموظفين
USERS = {
    "201029664170": "pass1",
    "201029773000": "pass2",
    "201029772000": "pass3",
    "201055855040": "pass4",
    "201029455000": "pass5",
    "201027480870": "pass6",
    "201055855030": "pass7"
}

# Google Sheets
SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM'
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
json_creds = os.getenv('GOOGLE_CREDENTIALS')
credentials = Credentials.from_service_account_info(json.loads(json_creds), scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).worksheet("sheet")
log_sheet = client.open_by_key(SHEET_ID).worksheet("Messages Log")

# Ultramsg - تم التثبيت يدويًا من قيمك
ULTRAMSG_INSTANCE = "instance124923"
ULTRAMSG_TOKEN = "cy1phhf1mrsg8eia"

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

# واجهة لوحة التحكم
DASHBOARD_CHAT_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>Respond 249 - دردشة العملاء</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="https://i.ibb.co/bR2qkN9q/6dd05738-f28d-457f-a1b3-fa9ffa42abb6.png" type="image/png">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 font-sans">

<div class="flex flex-col md:flex-row h-screen">

  <!-- قائمة المحادثات -->
  <div class="w-full md:w-1/3 bg-white border-r overflow-y-auto">
    <div class="p-4 flex items-center justify-between border-b">
      <h2 class="text-xl font-bold">📱 المحادثات</h2>
      <span class="text-gray-600 text-sm">👤 {{ username }}</span>
    </div>
    <ul>
      {% for row in clients %}
        <li>
          <a href="{{ url_for('dashboard', phone=row['Phone']) }}"
             class="block px-4 py-3 border-b hover:bg-blue-50 {% if row['Phone'] == selected_phone %}bg-blue-100{% endif %}">
            <div class="font-bold text-gray-800">{{ row['Phone'] }}</div>
            <div class="text-sm text-gray-600 truncate">{{ row['LastMessage'] }}</div>
          </a>
        </li>
      {% endfor %}
    </ul>
  </div>

  <!-- شاشة الرسائل -->
  <div class="flex-1 flex flex-col">
    <div class="flex-1 overflow-y-auto p-4">
      {% if selected_phone %}
        <h3 class="text-lg font-semibold mb-4 text-gray-800">📨 الرسائل مع: {{ selected_phone }}</h3>
        <div class="space-y-3">
          {% for msg in selected_messages %}
            <div class="{% if msg['Sender'] == username %}text-left{% else %}text-right{% endif %}">
              <div class="inline-block px-4 py-2 rounded-xl 
                {% if msg['Sender'] == username %}
                  bg-blue-600 text-white
                {% else %}
                  bg-gray-200 text-gray-800
                {% endif %}">
                {{ msg['Message'] }}
              </div>
              <div class="text-xs text-gray-500 mt-1">{{ msg['Timestamp'] }}</div>
            </div>
          {% endfor %}
        </div>
      {% else %}
        <p class="text-center text-gray-500 mt-10">اختر محادثة من القائمة</p>
      {% endif %}
    </div>

    {% if selected_phone %}
    <!-- نموذج الرد -->
    <form method="POST" class="p-4 bg-white border-t flex gap-3">
      <input type="hidden" name="recipient" value="{{ selected_phone }}">
      <textarea name="reply" rows="2" required
        class="flex-1 p-2 border rounded-lg focus:outline-none focus:ring focus:ring-blue-500"
        placeholder="اكتب الرد هنا..."></textarea>
      <button type="submit" class="bg-blue-600 text-white px-4 rounded hover:bg-blue-700 transition">إرسال</button>
    </form>
    {% endif %}
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
    my_clients = [row for row in data if str(row['AssignedTo']) == username]

    selected_phone = request.args.get("phone")
    selected_messages = []

    if selected_phone:
        log_data = log_sheet.get_all_records()
        selected_messages = [row for row in log_data if row['Phone'] == selected_phone]

    if request.method == 'POST':
        recipient = request.form['recipient']
        reply = request.form['reply']
        send_message(recipient, reply)
        log_message(recipient, username, reply)
        return redirect(url_for('dashboard', phone=recipient))

    return render_template_string(DASHBOARD_CHAT_PAGE,
                                  username=username,
                                  clients=my_clients,
                                  selected_phone=selected_phone,
                                  selected_messages=selected_messages)
    
@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

def send_message(to, message):
    # تنظيف الرقم
    to = to.replace("@c.us", "").replace(" ", "").strip()

    print("📤 إرسال إلى:", to)
    print("🔐 TOKEN:", ULTRAMSG_TOKEN[:6], "...")  # جزء فقط

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
        print("❌ خطأ أثناء الإرسال:", e)

def log_message(phone, sender, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_sheet.append_row([phone, sender, message, timestamp])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
