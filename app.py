from flask import Flask, render_template, request, redirect
import gspread
from oauth2client.service_account import ServiceAccountCredentials

app = Flask(__name__)

# Kết nối Google Sheets
scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
creds = ServiceAccountCredentials.from_json_keyfile_name("credentials.json", scope)
client = gspread.authorize(creds)

# Dùng Google Sheet ID thay vì tên
# 👉 Thay YOUR_SHEET_ID bằng ID thật trong link Google Sheet
SHEET_ID = "1_Iu5lJ1LukSY71gDN7aksSPrzn-ySHVn1ZCzckO9yO4"
sheet = client.open_by_key(SHEET_ID).sheet1

@app.route("/", methods=["GET", "POST"])
def survey():
    if request.method == "POST":
        name = request.form["name"]
        email = request.form["email"]
        feedback = request.form["feedback"]

        # Ghi dữ liệu vào Google Sheets
        sheet.append_row([name, email, feedback])

        return redirect("/")
    return render_template("form.html")

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
