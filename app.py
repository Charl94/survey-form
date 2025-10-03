# app.py

from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, json
from datetime import datetime

# --- KHAI BÁO CẤU HÌNH ---
# Tên Sheet lưu dữ liệu nhân viên (BẠN CẦN LẤY DỮ LIỆU NÀY BẰNG CÁCH KHÁC)
DATA_SHEET_NAME = "Data" 
# Tên Sheet lưu kết quả khảo sát
RESPONSE_SHEET_NAME = "Respond"
# Tiêu đề Form
FORM_TITLE = "BIỂU MẪU KHẢO SÁT NHU CẦU ĐÀO TẠO"

app = Flask(__name__)

# Khởi tạo kết nối Google Sheets (Sử dụng code đã khắc phục lỗi JSON)
# Cần đảm bảo biến môi trường GOOGLE_CREDENTIALS đã được thiết lập đúng
def setup_google_sheets():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_json = os.environ.get("GOOGLE_CREDENTIALS")
    
    if not creds_json:
        print("⚠️ GOOGLE_CREDENTIALS environment variable not set!")
        return None

    try:
        creds_dict = json.loads(creds_json)
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
        client = gspread.authorize(creds)
        # THAY TÊN GOOGLE SHEET CỦA BẠN VÀO DƯỚI ĐÂY
        spreadsheet = client.open("TÊN FILE GOOGLE SHEET CỦA BẠN") 
        return spreadsheet
    except Exception as e:
        print(f"🚨 LỖI KẾT NỐI GOOGLE SHEETS: {e}")
        return None

# Gọi hàm setup sheets khi ứng dụng khởi động
SPREADSHEET_CLIENT = setup_google_sheets()

# --- MÔ PHỎNG HÀM LẤY DANH SÁCH NHÂN VIÊN ---
# LƯU Ý: Flask không thể tự động quét Sheet như GAS. 
# Bạn phải TẢI DỮ LIỆU NHÂN VIÊN (MaNV, HoTen, BoPhan) và lưu vào một biến Python.
# Dưới đây là cách mô phỏng:
def get_employee_list():
    if not SPREADSHEET_CLIENT:
        return []
        
    try:
        data_sheet = SPREADSHEET_CLIENT.worksheet(DATA_SHEET_NAME)
        values = data_sheet.get_all_values()
        
        # Bỏ hàng tiêu đề (hàng 1)
        employee_data = []
        for row in values[1:]:
            if row and row[0].strip(): # Chỉ lấy hàng có Mã NV
                 employee_data.append({
                    "MaNV": row[0],
                    "HoTen": row[1] if len(row) > 1 else '',
                    "BoPhan": row[2] if len(row) > 2 else ''
                })
        return employee_data
    except gspread.WorksheetNotFound:
        print(f"🚨 Sheet DATA_SHEET_NAME ({DATA_SHEET_NAME}) không tìm thấy.")
        return []
    except Exception as e:
        print(f"🚨 LỖI LẤY DANH SÁCH NV: {e}")
        return []

# --- ROUTES ---

@app.route('/', methods=['GET'])
def index():
    # Render form khảo sát
    return render_template('survey_form.html', form_title=FORM_TITLE)

@app.route('/get_employees', methods=['GET'])
def get_employees_route():
    # API endpoint để JavaScript lấy danh sách nhân viên
    employee_list = get_employee_list()
    return jsonify(employee_list)

@app.route('/submit', methods=['POST'])
def submit_form():
    if not SPREADSHEET_CLIENT:
        return jsonify({"status": "error", "message": "Lỗi kết nối Google Sheets."}), 500
        
    try:
        form_data = request.form.to_dict(flat=False) # Lấy dữ liệu form
        
        # Xử lý các trường checkbox (như trong code JS của bạn)
        nhu_cau_dt = "; ".join(form_data.get('NhuCauDT', []))
        hinh_thuc_dt = "; ".join(form_data.get('HinhThucDT', []))
        
        # Xử lý trường "Khác" trong Nhu Cầu ĐT
        other_text = form_data.get('NhuCauDT_OtherText', [''])[0]
        if other_text and other_text.strip():
            nhu_cau_dt += f"; Khác: {other_text}" if nhu_cau_dt else f"Khác: {other_text}"

        response_sheet = SPREADSHEET_CLIENT.worksheet(RESPONSE_SHEET_NAME)

        # Định nghĩa và ghi tiêu đề nếu sheet trống (GIỐNG HỆT CẤU TRÚC LOGIC GAS)
        if response_sheet.row_count < 1 or not response_sheet.row_values(1) or response_sheet.row_values(1)[0] == '':
             headers = [
                "Thời Gian Gửi", "Mã NV", "Họ và Tên", "Bộ phận", "Thâm niên", 
                "NL_1: Triển khai & giám sát SX", "NL_2: Kiểm soát chất lượng", "NL_3: Quản lý NVL & lãng phí", 
                "NL_4: An toàn & vệ sinh LĐ", "NL_5: An toàn TP & vệ sinh CN", "NL_6: Phân công & quản lý đội ngũ",
                "NL_7: Huấn luyện & kèm cặp", "NL_8: Kỹ năng giao tiếp", "NL_9: Giải quyết mâu thuẫn & đội nhóm",
                "NL_10: Giải quyết VĐ & ra quyết định", "NL_11: Tư duy cải tiến (Kaizen)",
                "Nhu Cầu ĐT", "Thách thức công việc", "Hình thức ĐT", "Đề Xuất Khác" 
            ]
             response_sheet.insert_row(headers, 1)

        # Chuẩn bị dữ liệu để ghi
        row_data = [
            datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            form_data.get('employeeCode', [''])[0],
            form_data.get('employeeName', [''])[0],
            form_data.get('department', [''])[0],
            form_data.get('Seniority', [''])[0],
            
            # 11 Câu hỏi Năng lực
            form_data.get('NL_1', [''])[0], form_data.get('NL_2', [''])[0], form_data.get('NL_3', [''])[0], 
            form_data.get('NL_4', [''])[0], form_data.get('NL_5', [''])[0], form_data.get('NL_6', [''])[0],
            form_data.get('NL_7', [''])[0], form_data.get('NL_8', [''])[0], form_data.get('NL_9', [''])[0],
            form_data.get('NL_10', [''])[0], form_data.get('NL_11', [''])[0],
            
            # C. Nhu Cầu Đào Tạo và Đề Xuất
            nhu_cau_dt,
            form_data.get('ThachThucCongViec', [''])[0],
            hinh_thuc_dt,
            form_data.get('DeXuatKhacMoi', [''])[0]
        ]
        
        response_sheet.append_row(row_data)

        # Trả về JSON cho JavaScript xử lý
        return jsonify({"status": "success", "message": "Gửi khảo sát thành công!"})

    except Exception as e:
        print(f"🚨 LỖI XỬ LÝ FORM: {e}")
        return jsonify({"status": "error", "message": f"Lỗi server: {str(e)}"}), 500

if __name__ == '__main__':
    # Chỉ chạy local
    app.run(host='0.0.0.0', port=5000, debug=True)
