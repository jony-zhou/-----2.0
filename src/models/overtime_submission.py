"""加班補報資料模型"""
from dataclasses import dataclass
from typing import Optional
from enum import Enum


class OvertimeSubmissionStatus(Enum):
    """加班申請狀態"""
    NOT_SUBMITTED = "未申請"
    SUBMITTED = "已申請"
    IN_REVIEW = "簽核中"
    APPROVED = "簽核完成"
    REJECTED = "已撤回"


@dataclass
class OvertimeSubmissionRecord:
    """
    加班補報記錄
    
    用於 UI 顯示和表單填寫
    """
    date: str                                    # 加班日期 (YYYY/MM/DD)
    description: str                             # 加班內容 (使用者可編輯)
    overtime_hours: float                        # 加班時數
    is_overtime: bool = True                     # True=加班, False=調休
    is_selected: bool = True                     # 是否勾選
    submitted_status: Optional[str] = None       # 已申請狀態文字
    
    @property
    def is_submitted(self) -> bool:
        """是否已申請"""
        return self.submitted_status is not None
    
    @property
    def overtime_minutes(self) -> int:
        """加班時數轉換為分鐘"""
        return int(self.overtime_hours * 60)
    
    @property
    def change_minutes(self) -> int:
        """調休時數轉換為分鐘"""
        return int(self.overtime_hours * 60) if not self.is_overtime else 0
    
    def __str__(self) -> str:
        status = f" ({self.submitted_status})" if self.is_submitted else ""
        type_str = "調休" if not self.is_overtime else "加班"
        return f"{self.date} | {self.description} | {self.overtime_hours}h {type_str}{status}"


@dataclass
class SubmittedRecord:
    """
    已申請的加班記錄
    
    從 FW21003Z.aspx 解析出來的資料
    """
    date: str                  # 加班日期 (YYYY/MM/DD)
    status: str                # 狀態文字 (簽核中、簽核完成等)
    overtime_minutes: float    # 加班分鐘數
    change_minutes: float      # 調休分鐘數
    
    @property
    def is_overtime(self) -> bool:
        """是否為加班 (而非調休)"""
        return self.overtime_minutes > 0
    
    def __str__(self) -> str:
        type_str = "加班" if self.is_overtime else "調休"
        minutes = self.overtime_minutes if self.is_overtime else self.change_minutes
        hours = minutes / 60
        return f"{self.date} | {type_str} {hours}h | {self.status}"
