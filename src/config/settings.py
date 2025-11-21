"""系統設定"""
from dataclasses import dataclass


@dataclass
class Settings:
    """系統設定"""
    # SSP 系統
    SSP_BASE_URL: str = "https://ssp.teco.com.tw"
    
    # 時間設定 (分鐘)
    LUNCH_BREAK: int = 70
    WORK_HOURS: int = 480
    REST_TIME: int = 30
    MAX_OVERTIME_HOURS: int = 4
    STANDARD_START_HOUR: int = 9
    
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
