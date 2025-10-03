# app.py

from flask import Flask, render_template, request, jsonify
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import os, json
from datetime import datetime

# --- KHAI BÁO CẤU HÌNH ---
# Tên Sheet chứa dữ liệu nhân viên
DATA_SHEET_NAME = "Data" 
# Tên Sheet lưu kết quả khảo sát
RESPONSE_SHEET_NAME = "Respond"
# Tiêu đề Form (Được truyền vào template)
FORM_TITLE = "BIỂU MẪU KHẢO SÁT NHU CẦU ĐÀO TẠO"

app = Flask(__name__)

# Khởi tạo kết nối Google Sheets
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
        
        # CHÚ Ý: THAY TÊN FILE GOOGLE SHEET CỦA BẠN VÀO DƯỚI ĐÂY
        spreadsheet = client.open("TÊN FILE GOOGLE SHEET CỦA BẠN") 
        print("✅ Google Sheets kết nối thành công lúc khởi động.")
        return spreadsheet
    except Exception as e:
        # Bắt lỗi JSON, API, hoặc kết nối
        print(f"🚨 LỖI KHỞI TẠO KẾT NỐI GOOGLE SHEETS: {e}")
        return None

# Gọi hàm setup sheets khi ứng dụng khởi động
SPREADSHEET_CLIENT = setup_google_sheets()

# --- MÔ PHỎNG HÀM LẤY DANH SÁCH NHÂN VIÊN ---
def get_employee_list():
    if not SPREADSHEET_CLIENT:
        return []
        
    try:
        data_sheet = SPREADSHEET_CLIENT.worksheet(DATA_SHEET_NAME)
        # Lấy tất cả giá trị. Tùy chỉnh phạm vi nếu cần tối ưu
        values = data_sheet.get_all_values()
        
        employee_data = []
        if len(values) > 1:
            for row in values[1:]: # Bỏ hàng tiêu đề
                if row and row[0].strip(): 
                     employee_data.append({
                        "MaNV": row[0],
                        "HoTen": row[1] if len(row) > 1 else '',
                        "BoPhan": row[2] if len(row) > 2 else ''
                    })
        return employee_data
    except gspread.WorksheetNotFound:
        print(f"🚨 Sheet DATA_SHEET_NAME ({DATA_SHEET_NAME}) không tìm thấy. Không thể tải danh sách NV.")
        return []
    except Exception as e:
        print(f"🚨 LỖI LẤY DANH SÁCH NV: {e}")
        return []

# --- ROUTES ---

@app.route('/', methods=['GET'])
def index():
    # SỬA LỖI TemplateNotFound: Đã thay 'survey_form.html' bằng 'form.html'
    return render_template('form.html', form_title=FORM_TITLE) 

@app.route('/get_employees', methods=['GET'])
def get_employees_route():
    # API endpoint để JavaScript lấy danh sách nhân viên
    employee_list = get_employee_list()
    # Nếu danh sách trống, logs sẽ hiển thị lỗi SheetNotFound hoặc kết nối ở hàm trên
    return jsonify(employee_list)

@app.route('/submit', methods=['POST'])
def submit_form():
    if not SPREADSHEET_CLIENT:
        return jsonify({"status": "error", "message": "Lỗi kết nối Google Sheets. Vui lòng kiểm tra Logs."}), 500
        
    try:
        form_data = request.form.to_dict(flat=False) 
        
        # Xử lý các trường checkbox (NhuCauDT và HinhThucDT)
        nhu_cau_dt_values = form_data.get('NhuCauDT', [])
        hinh_thuc_dt = "; ".join(form_data.get('HinhThucDT', []))
        
        # Xử lý trường "Khác" trong Nhu Cầu ĐT
        other_text = form_data.get('NhuCauDT_OtherText', [''])[0]
        if other_text and other_text.strip():
            # Thêm giá trị 'Khác' vào danh sách nếu có
            nhu_cau_dt_values.append(f"Khác: {other_text}")
            
        nhu_cau_dt = "; ".join(nhu_cau_dt_values)

        response_sheet = SPREADSHEET_CLIENT.worksheet(RESPONSE_SHEET_NAME)

        # Kiểm tra và ghi tiêu đề (GIỮ NGUYÊN LOGIC GAS)
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
        # Nếu có lỗi trong quá trình ghi dữ liệu hoặc xử lý form
        print(f"🚨 LỖI XỬ LÝ FORM: {e}")
        return jsonify({"status": "error", "message": f"Lỗi server khi ghi dữ liệu: {str(e)}"}), 500

if __name__ == '__main__':
    # Chỉ chạy local
    app.run(host='0.0.0.0', port=5000, debug=True)
