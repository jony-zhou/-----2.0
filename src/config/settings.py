"""系統設定"""
from dataclasses import dataclass


@dataclass
class Settings:
    """系統設定"""
    # SSP 系統
    SSP_BASE_URL: str = "https://ssp.teco.com.tw"
    ATTENDANCE_URL: str = "/FW99001Z.aspx"  # 出勤異常清單
    OVERTIME_REPORT_URL: str = "/FW21001Z.aspx?Kind=B"  # 加班補報申請單
    OVERTIME_STATUS_URL: str = "/FW21003Z.aspx"  # 個人紀錄查詢
    
    # 時間設定 (分鐘)
    LUNCH_BREAK: int = 70
    WORK_HOURS: int = 480
    REST_TIME: int = 30
    MAX_OVERTIME_HOURS: int = 4
    STANDARD_START_HOUR: int = 9
    
    # 加班補報設定
    DEFAULT_OVERTIME_DESCRIPTION: str = "加班作業"
    ENABLE_SUBMISSION: bool = False  # Beta 版本預設禁用送出功能
    
    # 日期格式
    DATE_FORMAT: str = "%Y/%m/%d"
    TIME_FORMAT: str = "%H:%M:%S"
    
    # 匯出設定
    EXCEL_FILENAME_PREFIX: str = "overtime_report"
    
    # 連線設定
    VERIFY_SSL: bool = False
    REQUEST_TIMEOUT: int = 30
    MAX_PAGES: int = 10
    
    @classmethod
    def from_file(cls, filepath: str = "config.py"):
        """從舊的 config.py 載入設定"""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location("config", filepath)
            config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(config_module)
            
            return cls(
                SSP_BASE_URL=getattr(config_module, 'SSP_BASE_URL', cls.SSP_BASE_URL),
                LUNCH_BREAK=getattr(config_module, 'LUNCH_BREAK', cls.LUNCH_BREAK),
                WORK_HOURS=getattr(config_module, 'WORK_HOURS', cls.WORK_HOURS),
                REST_TIME=getattr(config_module, 'REST_TIME', cls.REST_TIME),
            )
        except:
            return cls()
