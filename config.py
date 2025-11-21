# config.py - 配置檔案
# 請勿將此檔案上傳至版本控制系統

# SSP 系統設定
SSP_BASE_URL = "https://ssp.teco.com.tw"
SSP_LOGIN_URL = "https://ssp.teco.com.tw/index.aspx"
SSP_ATTENDANCE_URL = "https://ssp.teco.com.tw/FW99001Z.aspx"

# 時間設定(單位:分鐘)
LUNCH_BREAK = 70      # 午休時間
WORK_HOURS = 480      # 正常上班時間 (8小時)
REST_TIME = 30        # 休息時間

# 如果不想每次都輸入帳號密碼,可以在這裡設定(不建議,有安全風險)
# USERNAME = ""
# PASSWORD = ""

# 輸出設定
EXCEL_FILENAME_PREFIX = "overtime_report"
DATE_FORMAT = "%Y/%m/%d"
TIME_FORMAT = "%H:%M:%S"