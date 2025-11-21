"""加班時數計算核心邏輯"""
from datetime import datetime
from typing import List, Optional
import logging
from ..models import AttendanceRecord, OvertimeReport
from ..config import Settings

logger = logging.getLogger(__name__)


class OvertimeCalculator:
    """加班時數計算器"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
    
    def calculate_overtime(self, records: List[dict]) -> OvertimeReport:
        """
        計算加班時數
        
        Args:
            records: 原始出勤記錄列表 [{'date': 'YYYY/MM/DD', 'time_range': 'HH:MM:SS~HH:MM:SS'}]
            
        Returns:
            OvertimeReport: 加班報表
        """
        attendance_records = []
        
        for idx, record in enumerate(records):
            try:
                date = record['date']
                time_range = record['time_range']
                
                # 解析時間範圍
                times = time_range.split('~')
                if len(times) != 2:
                    logger.warning(f"記錄 {idx+1}: 時間格式錯誤 - {time_range}")
                    continue
                
                start_time_str = times[0].strip()
                end_time_str = times[1].strip()
                
                # 轉換為 datetime 物件
                start_time = datetime.strptime(f"{date} {start_time_str}", 
                                              f"{self.settings.DATE_FORMAT} {self.settings.TIME_FORMAT}")
                end_time = datetime.strptime(f"{date} {end_time_str}", 
                                            f"{self.settings.DATE_FORMAT} {self.settings.TIME_FORMAT}")
                
                # 如果上班時間晚於標準時間,以標準時間計算
                standard_start = datetime.strptime(
                    f"{date} {self.settings.STANDARD_START_HOUR:02d}:00:00", 
                    f"{self.settings.DATE_FORMAT} {self.settings.TIME_FORMAT}"
                )
                
                if start_time > standard_start:
                    actual_start = standard_start
                    logger.debug(f"{date}: 上班時間 {start_time_str} 晚於 {self.settings.STANDARD_START_HOUR}:00,以標準時間計算")
                else:
                    actual_start = start_time
                
                # 計算總工作時間(分鐘)
                total_minutes = (end_time - actual_start).total_seconds() / 60
                
                # 計算加班時數 = 總時間 - 午休 - 正常上班時間 - 休息時間
                overtime_minutes = total_minutes - self.settings.LUNCH_BREAK - self.settings.WORK_HOURS - self.settings.REST_TIME
                
                # 轉換為小時(保留一位小數)
                overtime_hours = round(overtime_minutes / 60, 1)
                
                # 限制加班時數範圍
                if overtime_hours < 0:
                    overtime_hours = 0
                elif overtime_hours > self.settings.MAX_OVERTIME_HOURS:
                    overtime_hours = self.settings.MAX_OVERTIME_HOURS
                
                # 建立記錄
                attendance_record = AttendanceRecord(
                    date=date,
                    start_time=start_time_str,
                    end_time=end_time_str,
                    total_minutes=int(total_minutes),
                    overtime_hours=overtime_hours
                )
                attendance_records.append(attendance_record)
                
                logger.debug(f"{date}: {start_time_str}~{end_time_str} → 加班 {overtime_hours}hr")
                
            except ValueError as e:
                logger.warning(f"記錄 {idx+1}: 時間解析錯誤 - {e}")
                continue
            except Exception as e:
                logger.error(f"記錄 {idx+1}: 計算時發生錯誤 - {e}")
                continue
        
        # 排序(由新到舊)
        attendance_records.sort(key=lambda r: r.date_obj, reverse=True)
        
        return OvertimeReport(records=attendance_records)
