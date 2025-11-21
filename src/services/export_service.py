"""匯出服務"""
import pandas as pd
from pathlib import Path
from datetime import datetime
import logging
from typing import Optional

from ..models import OvertimeReport
from ..config import Settings

logger = logging.getLogger(__name__)


class ExportService:
    """匯出服務 - 處理報表匯出"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self._ensure_reports_folder()
    
    def _ensure_reports_folder(self):
        """確保 reports 資料夾存在"""
        Path('reports').mkdir(exist_ok=True)
    
    def export_to_excel(self, report: OvertimeReport, filename: Optional[str] = None) -> Optional[str]:
        """
        匯出為 Excel 檔案
        
        Args:
            report: 加班報表
            filename: 檔案名稱 (可選)
            
        Returns:
            str: 匯出的檔案路徑,失敗則返回 None
        """
        if not report.records:
            logger.warning("沒有記錄可匯出")
            return None
        
        if filename is None:
            filename = f"{self.settings.EXCEL_FILENAME_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        
        if not filename.startswith('reports/'):
            filename = f"reports/{filename}"
        
        try:
            # 準備資料
            data = []
            for record in report.records:
                data.append({
                    '日期': record.date,
                    '上班時間': record.start_time,
                    '下班時間': record.end_time,
                    '總工時(分)': record.total_minutes,
                    '加班時數': record.overtime_hours
                })
            
            df = pd.DataFrame(data)
            
            # 加入統計資料
            summary = report.get_summary()
            summary_df = pd.DataFrame({
                '日期': ['', '統計資訊', '記錄天數', '加班天數', '總加班時數', '平均每日加班', '最長加班', '最長加班日期'],
                '上班時間': ['', '', summary['記錄天數'], summary['加班天數'], 
                           f"{summary['總加班時數']} hr", 
                           f"{summary['平均每日加班']} hr",
                           f"{summary['最長加班']} hr",
                           summary['最長加班日期']],
                '下班時間': [''] * 8,
                '總工時(分)': [''] * 8,
                '加班時數': [''] * 8
            })
            
            final_df = pd.concat([df, summary_df], ignore_index=True)
            
            # 寫入 Excel
            with pd.ExcelWriter(filename, engine='openpyxl') as writer:
                final_df.to_excel(writer, sheet_name='加班記錄', index=False)
                
                # 調整欄寬
                worksheet = writer.sheets['加班記錄']
                worksheet.column_dimensions['A'].width = 15
                worksheet.column_dimensions['B'].width = 12
                worksheet.column_dimensions['C'].width = 12
                worksheet.column_dimensions['D'].width = 12
                worksheet.column_dimensions['E'].width = 12
            
            logger.info(f"✓ 已匯出至: {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"✗ 匯出 Excel 時發生錯誤: {e}")
            return None
    
    def generate_text_report(self, report: OvertimeReport, show_all: bool = True) -> str:
        """
        生成文字報表
        
        Args:
            report: 加班報表
            show_all: 是否顯示所有記錄 (包含無加班的)
            
        Returns:
            str: 報表文字
        """
        if not report.records:
            return "沒有找到任何出勤記錄"
        
        text = "\n" + "="*80 + "\n"
        text += f"{'加班時數統計報表':^70}\n"
        text += f"{'產生時間: ' + report.generated_at.strftime('%Y-%m-%d %H:%M:%S'):^70}\n"
        text += "="*80 + "\n\n"
        
        # 準備資料
        data = []
        for record in report.records:
            if show_all or record.overtime_hours > 0:
                data.append({
                    '日期': record.date,
                    '上班時間': record.start_time,
                    '下班時間': record.end_time,
                    '加班時數': record.overtime_hours
                })
        
        if data:
            df = pd.DataFrame(data)
            text += df.to_string(index=False)
        else:
            text += "沒有加班記錄\n"
        
        # 統計資訊
        summary = report.get_summary()
        text += "\n\n" + "-"*80 + "\n"
        text += "統計資訊:\n"
        text += "-"*80 + "\n"
        text += f"記錄天數: {summary['記錄天數']} 天\n"
        text += f"加班天數: {summary['加班天數']} 天\n"
        text += f"總加班時數: {summary['總加班時數']} 小時\n"
        text += f"平均每日加班: {summary['平均每日加班']} 小時\n"
        text += f"最長加班: {summary['最長加班']} 小時\n"
        
        if summary['最長加班日期']:
            text += f"最長加班日期: {summary['最長加班日期']}\n"
        
        text += "="*80 + "\n"
        
        return text
