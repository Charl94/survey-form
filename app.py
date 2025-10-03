from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, json

app = Flask(__name__)

# Google Sheets setup
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# Lấy credentials từ biến môi trường
creds_json = os.environ.get("GOOGLE_CREDENTIALS")
if creds_json:
    creds_dict = json.loads(creds_json)
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    sheet = client.open("KQKhaosat").sheet1   # Thay bằng tên Google Sheet của bạn
else:
    sheet = None
    print("⚠️ GOOGLE_CREDENTIALS environment variable not set!")

@app.route('/')
def form():
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    if sheet is None:
        return "Google Sheets chưa được kết nối! 🚨"

    name = request.form.get('name')
    email = request.form.get('email')
    feedback = request.form.get('feedback')

    # Thêm dữ liệu vào Google Sheets
    sheet.append_row([name, email, feedback])

    return f"✅ Cảm ơn {name}, phản hồi của bạn đã được ghi nhận!"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
