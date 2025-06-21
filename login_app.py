import os
import json
from flask import Flask, request, render_template_string, redirect, url_for, session
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import requests

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'

# بيانات تسجيل الدخول
USERS = {
    "201029664170": "pass1",
    "201029773000": "pass2",
    "201029772000": "pass3",
    "201055855040": "pass4",
    "201029455000": "pass5",
    "201027480870": "pass6",
    "201055855030": "pass7"
}

# ربط Google Sheets
SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM'
scopes = ["https://www.googleapis.com/auth/spreadsheets"]
json_creds = os.getenv('GOOGLE_CREDENTIALS')
credentials = Credentials.from_service_account_info(json.loads(json_creds), scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).worksheet("sheet")
log_sheet = client.open_by_key(SHEET_ID).worksheet("Messages Log")

# بيانات ultramsg
ULTRAMSG_INSTANCE = "instance124923"
ULTRAMSG_TOKEN = "cy1phhf1mrsg8eia"

# واجهة تسجيل الدخول
LOGIN_PAGE = '''
<!doctype html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>تسجيل الدخول</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="bg-gray-100 flex items-center justify-center min-h-screen">
  <div class="bg-white p-6 rounded-xl shadow-xl w-full max-w-sm">
    <div class="flex justify-center mb-4">
      <img src="https://i.ibb.co/bR2qkN9q/6dd05738-f28d-457f-a1b3-fa9ffa42abb6.png" class="h-16" alt="logo">
    </div>
    <h2 class="text-center text-2xl font-bold mb-6 text-blue-700">تسجيل الدخول</h2>
    <form method="POST" class="space-y-4">
      <div>
        <label class="block mb-1">📱 رقم الموظف:</label>
        <input type="text" name="username" class="w-full border rounded p-2" required>
      </div>
      <div>
        <label class="block mb-1">🔒 كلمة المرور:</label>
        <input type="password" name="password" class="w-full border rounded p-2" required>
      </div>
      <button type="submit" class="w-full bg-blue-600 text-white py-2 rounded hover:bg-blue-700 transition">دخول</button>
    </form>
    {% if error %}
    <p class="text-red-600 text-sm mt-4 text-center">{{ error }}</p>
    {% endif %}
  </div>
</body>
</html>
'''

# لوحة التحكم والمحادثات

DASHBOARD_CHAT_PAGE = '''
<!DOCTYPE html>
<html lang="ar" dir="rtl">
<head>
  <meta charset="UTF-8">
  <title>Respond 249 - لوحة المحادثات</title>
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <link rel="icon" href="https://i.ibb.co/bR2qkN9q/6dd05738-f28d-457f-a1b3-fa9ffa42abb6.png" type="image/png">
  <script src="https://cdn.tailwindcss.com"></script>
  <style>
    .scrollbar-hide::-webkit-scrollbar {
      display: none;
    }
  </style>
</head>
<body class="bg-gray-100 font-sans">

<div class="flex flex-col md:flex-row h-screen">

  <!-- القائمة الجانبية -->
  <div class="w-full md:w-1/3 bg-white border-r overflow-y-auto scrollbar-hide">
    <div class="p-4 flex items-center justify-between border-b">
      <h2 class="text-xl font-bold">💬 محادثات</h2>
      <span class="text-gray-600 text-sm">👤 {{ username }}</span>
    </div>
    <ul>
      {% for row in clients %}
        <li>
          <a href="{{ url_for('dashboard', phone=row['Phone']) }}"
             class="flex items-center gap-3 px-4 py-3 border-b hover:bg-blue-50 {% if row['Phone'] == selected_phone %}bg-blue-100{% endif %}">
            <img src="https://www.svgrepo.com/show/382106/account-avatar-profile-user-11.svg"
                 class="h-10 w-10 rounded-full border" alt="user">
            <div class="flex-1">
              <div class="font-bold text-gray-800">{{ row['Phone'] }}</div>
              <div class="text-sm text-gray-500 truncate">{{ row['LastMessage'] }}</div>
            </div>
          </a>
        </li>
      {% endfor %}
    </ul>
  </div>

  <!-- واجهة المحادثة -->
  <div class="flex-1 flex flex-col">
    <div class="flex-1 overflow-y-auto p-4 space-y-4 scrollbar-hide bg-gray-50">
      {% if selected_phone %}
        <h3 class="text-lg font-semibold mb-4 text-gray-700 border-b pb-2">📨 المحادثة مع: {{ selected_phone }}</h3>
        {% for msg in selected_messages %}
          <div class="flex {% if msg['Sender'] == username %}justify-start{% else %}justify-end{% endif %}">
            <div class="max-w-xs md:max-w-md px-4 py-3 rounded-2xl shadow 
              {% if msg['Sender'] == username %}
                bg-blue-600 text-white rounded-br-none
              {% else %}
                bg-white text-gray-800 border rounded-bl-none
              {% endif %}">
              <div class="text-sm break-words">{{ msg['Message'] }}</div>
              <div class="text-[10px] text-gray-300 mt-1 text-left ltr:text-right">
                {{ msg['Timestamp'] }}
              </div>
            </div>
          </div>
        {% endfor %}
      {% else %}
        <p class="text-center text-gray-400 mt-20 text-xl">اختر محادثة من القائمة</p>
      {% endif %}
    </div>

    {% if selected_phone %}
    <!-- نموذج الرد -->
    <form method="POST" class="p-4 bg-white border-t flex gap-2">
      <input type="hidden" name="recipient" value="{{ selected_phone }}">
      <textarea name="reply" rows="2" required
        class="flex-1 p-2 border rounded-xl focus:outline-none focus:ring focus:ring-blue-500"
        placeholder="اكتب الرد هنا..."></textarea>
      <button type="submit"
              class="bg-blue-600 text-white px-4 py-2 rounded-xl hover:bg-blue-700 transition">إرسال</button>
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
    to = to.replace("@c.us", "").strip()
    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE}/messages/chat"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    payload = {
        "token": ULTRAMSG_TOKEN,
        "to": to,
        "body": message
    }
    try:
        response = requests.post(url, headers=headers, data=payload)
        print("📤 تم الإرسال:", response.status_code, response.text)
    except Exception as e:
        print("❌ خطأ أثناء الإرسال:", e)

def log_message(phone, sender, message):
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_sheet.append_row([phone, sender, message, timestamp])

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
