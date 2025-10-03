from flask import Flask, render_template, request
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, json

app = Flask(__name__)

# Cấu hình Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]

# --- KHU VỰC CẢI TIẾN: Xử lý Credentials an toàn hơn ---
creds_json = os.environ.get("GOOGLE_CREDENTIALS")
sheet = None # Khởi tạo biến sheet
print(f"DEBUG: GOOGLE_CREDENTIALS is set: {bool(creds_json)}")

if creds_json:
    try:
        # Lỗi JSONDecodeError thường xảy ra ở đây.
        # Đảm bảo giá trị của GOOGLE_CREDENTIALS trên Render là JSON HỢP LỆ và MỘT DÒNG.
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # Thay bằng tên Google Sheet của bạn
        sheet = client.open("KQKhaosat").sheet1
        print("✅ Google Sheets kết nối thành công!")
    except json.JSONDecodeError as e:
        # Nếu gặp lỗi JSON, in ra thông báo chi tiết để dễ debug hơn
        print(f"🚨 LỖI CẤU HÌNH GOOGLE_CREDENTIALS: JSON không hợp lệ. Vui lòng kiểm tra lại chuỗi JSON. Lỗi: {e}")
        sheet = None
    except Exception as e:
        # Bắt các lỗi kết nối khác (ví dụ: tên sheet sai, authorization fail)
        print(f"🚨 LỖI KẾT NỐI GOOGLE SHEETS: {e}")
        sheet = None
else:
    print("⚠️ GOOGLE_CREDENTIALS environment variable not set! Form submit sẽ không hoạt động.")

# --- Routes ---
@app.route('/')
def form():
    # Giả định file template của bạn là 'form.html'
    return render_template('form.html')

@app.route('/submit', methods=['POST'])
def submit():
    if sheet is None:
        return "Google Sheets chưa được kết nối! Vui lòng kiểm tra Logs và Biến Môi Trường GOOGLE_CREDENTIALS. 🚨", 500

    name = request.form.get('name')
    email = request.form.get('email')
    feedback = request.form.get('feedback')

    try:
        # Thêm dữ liệu vào Google Sheets
        sheet.append_row([name, email, feedback])
    except Exception as e:
        print(f"🚨 LỖI KHI GHI DỮ LIỆU vào Sheets: {e}")
        return "Đã xảy ra lỗi khi ghi dữ liệu. Vui lòng thử lại. ❌", 500

    return f"✅ Cảm ơn {name}, phản hồi của bạn đã được ghi nhận!", 200

# --- KHU VỰC CẢI TIẾN: Khởi chạy ứng dụng ---
# Chỉ chạy lệnh này khi phát triển LOCAL (không chạy trên Render/Gunicorn)
if __name__ == '__main__':
    # Render sẽ dùng Gunicorn (Procfile) để chạy app và xử lý cổng $PORT
    # Lệnh này chỉ dùng để debug local.
    app.run(host='0.0.0.0', port=5000, debug=True)
