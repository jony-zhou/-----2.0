"""個人加班記錄資料模型"""
from dataclasses import dataclass


@dataclass
class PersonalRecord:
    """
    個人加班記錄 (從 FW21003Z.aspx 個人記錄查詢頁面取得)
    
    包含已申請的加班記錄詳細資訊
    """
    date: str                    # 加班日期 (YYYY/MM/DD)
    content: str                 # 加班內容
    status: str                  # 狀態 (簽核中、簽核完成等)
    overtime_hours: float        # 加班時數 (小時)
    monthly_total: float         # 當月累計 (小時)
    quarterly_total: float       # 當季累計 (小時)
    report_type: str = ""        # 申報類型 (加班/調休)
    
    def __str__(self) -> str:
        return (
            f"{self.date} | {self.content} | "
            f"{self.overtime_hours:.1f}hr | "
            f"月累計:{self.monthly_total:.1f}hr | "
            f"季累計:{self.quarterly_total:.1f}hr | "
            f"{self.status}"
        )


@dataclass
class PersonalRecordSummary:
    """個人記錄統計摘要"""
    total_records: int = 0           # 總筆數
    total_overtime_hours: float = 0.0  # 總加班時數
    average_overtime_hours: float = 0.0  # 平均加班時數
    max_overtime_hours: float = 0.0  # 最高加班時數
    current_month_total: float = 0.0  # 本月累計
    current_quarter_total: float = 0.0  # 本季累計
    
    def __str__(self) -> str:
        return (
            f"總筆數: {self.total_records} | "
            f"總時數: {self.total_overtime_hours:.1f}hr | "
            f"平均: {self.average_overtime_hours:.1f}hr | "
            f"最高: {self.max_overtime_hours:.1f}hr | "
            f"本月: {self.current_month_total:.1f}hr | "
            f"本季: {self.current_quarter_total:.1f}hr"
        )
