"""出勤記錄資料模型"""
from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class AttendanceRecord:
    """出勤記錄"""
    date: str  # 格式: YYYY/MM/DD
    start_time: str  # 格式: HH:MM:SS
    end_time: str  # 格式: HH:MM:SS
    overtime_hours: float = 0.0
    total_minutes: int = 0
    
    @property
    def date_obj(self) -> datetime:
        """轉換為 datetime 物件"""
        return datetime.strptime(self.date, "%Y/%m/%d")
    
    @property
    def start_datetime(self) -> datetime:
        """開始時間 datetime 物件"""
        return datetime.strptime(f"{self.date} {self.start_time}", "%Y/%m/%d %H:%M:%S")
    
    @property
    def end_datetime(self) -> datetime:
        """結束時間 datetime 物件"""
        return datetime.strptime(f"{self.date} {self.end_time}", "%Y/%m/%d %H:%M:%S")
    
    def __hash__(self):
        """用於去重"""
        return hash(f"{self.date}_{self.start_time}_{self.end_time}")
