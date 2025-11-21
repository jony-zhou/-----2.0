"""加班報表資料模型"""
from dataclasses import dataclass, field
from typing import List
from datetime import datetime
from .attendance import AttendanceRecord


@dataclass
class OvertimeReport:
    """加班報表"""
    records: List[AttendanceRecord] = field(default_factory=list)
    generated_at: datetime = field(default_factory=datetime.now)
    
    @property
    def total_days(self) -> int:
        """記錄天數"""
        return len(self.records)
    
    @property
    def overtime_days(self) -> int:
        """加班天數"""
        return len([r for r in self.records if r.overtime_hours > 0])
    
    @property
    def total_overtime_hours(self) -> float:
        """總加班時數"""
        return sum(r.overtime_hours for r in self.records)
    
    @property
    def average_overtime_hours(self) -> float:
        """平均每日加班時數"""
        if not self.records:
            return 0.0
        return self.total_overtime_hours / self.total_days
    
    @property
    def max_overtime_hours(self) -> float:
        """最長加班時數"""
        if not self.records:
            return 0.0
        return max(r.overtime_hours for r in self.records)
    
    @property
    def max_overtime_date(self) -> str:
        """最長加班日期"""
        if not self.records:
            return ""
        max_record = max(self.records, key=lambda r: r.overtime_hours)
        return max_record.date
    
    def get_summary(self) -> dict:
        """取得統計摘要"""
        return {
            "記錄天數": self.total_days,
            "加班天數": self.overtime_days,
            "總加班時數": f"{self.total_overtime_hours:.1f}",
            "平均每日加班": f"{self.average_overtime_hours:.1f}",
            "最長加班": f"{self.max_overtime_hours:.1f}",
            "最長加班日期": self.max_overtime_date
        }
