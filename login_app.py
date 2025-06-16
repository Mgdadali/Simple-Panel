import os
import json
import requests
from flask import Flask, request, render_template_string, redirect, url_for, session
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key_here'  # غيّر المفتاح في الإنتاج

# ------------------ إعداد Google Sheets ------------------
SHEET_ID = '10-gDKaxRQfJqkIoiF3BYQ0YiNXzG7Ml9Pm5r9X9xfCM'
scopes = ["https://www.googleapis.com/auth/spreadsheets"]

json_creds = os.getenv('GOOGLE_CREDENTIALS')
info = json.loads(json_creds)
credentials = Credentials.from_service_account_info(info, scopes=scopes)
client = gspread.authorize(credentials)
sheet = client.open_by_key(SHEET_ID).worksheet("sheet")

# ------------------ بيانات الموظفين ------------------
USERS = {
    "201029664170": "pass1",
    "201029773000": "pass2",
    "201029772000": "pass3",
    "201055855040": "pass4",
    "201029455000": "pass5",
    "201027480870": "pass6",
    "201055855030": "pass7"
}

# ------------------ متغيرات Ultramsg ------------------
ULTRAMSG_INSTANCE_ID = os.getenv("ULTRA_INSTANCE_ID")
ULTRAMSG_TOKEN = os.getenv("ULTRA_TOKEN")

# ------------------ دالة إرسال رسالة ------------------
def send_reply(to_number, message):
    url = f"https://api.ultramsg.com/{ULTRAMSG_INSTANCE_ID}/messages/chat"
    headers = {"Content-Type": "application/x-www-form-urlencoded"}
    data = {
        "token": ULTRAMSG_TOKEN,
        "to": to_number,
        "body": message,
    }
    response = requests.post(url, data=data, headers=headers)
    print("📤 إرسال إلى:", to_number, "| كود:", response.status_code)
    return response.status_code == 200

# ------------------ صفحة تسجيل الدخول ------------------
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

# ------------------ لوحة الموظف ------------------
DASHBOARD_PAGE = '''
<!doctype html>
<title>لوحة الموظف</title>
<h2>مرحبًا {{ username }}</h2>
<p>هذه رسائلك:</p>

{% for msg in messages %}
  <div style="border:1px solid #ccc; padding:10px; margin:10px 0; border-radius:10px">
    <p><strong>📱 رقم العميل:</strong> {{ msg.phone }}</p>
    <p><strong>💬 آخر رسالة:</strong> {{ msg.last_message }}</p>
    <form action="{{ url_for('send_reply_route') }}" method="POST">
      <input type="hidden" name="phone" value="{{ msg.phone }}">
      <textarea name="reply" placeholder="اكتب الرد هنا..." rows="2" cols="50" required></textarea><br>
      <button type="submit">📤 إرسال</button>
    </form>
  </div>
{% endfor %}

<a href="{{ url_for('logout') }}">🚪 تسجيل الخروج</a>
'''

# ------------------ فلتر رسائل الموظف ------------------
def get_user_messages(username):
    data = sheet.get_all_records()
    msgs = []
    for row in data:
        if row.get("AssignedTo") == username:
            msgs.append({
                "phone": row.get("Phone"),
                "last_message": row.get("LastMessage"),
            })
    return msgs

# ------------------ Routes ------------------

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
    username = session['user']
    messages = get_user_messages(username)
    return render_template_string(DASHBOARD_PAGE, username=username, messages=messages)

@app.route('/send_reply', methods=['POST'])
def send_reply_route():
    if 'user' not in session:
        return redirect(url_for('login'))
    phone = request.form.get('phone')
    reply = request.form.get('reply')
    if phone and reply:
        success = send_reply(phone, reply)
        return redirect(url_for('dashboard')) if success else "فشل الإرسال", 500
    return "بيانات ناقصة", 400

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('login'))

# ------------------ تشغيل التطبيق ------------------
if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
