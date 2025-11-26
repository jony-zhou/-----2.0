"""加班補報表單填寫服務"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Any, Optional
import urllib3

from ..config import Settings
from ..models import OvertimeSubmissionRecord

logger = logging.getLogger(__name__)


class OvertimeReportService:
    """加班補報表單填寫服務"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        
        if not self.settings.VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def preview_form(self, session: requests.Session, records: List[OvertimeSubmissionRecord]) -> Dict[str, Any]:
        """
        預覽表單填寫 (不實際送出)
        
        Args:
            session: 已登入的 Session
            records: 要填寫的記錄列表
            
        Returns:
            預覽結果
        """
        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_REPORT_URL}"
        
        try:
            logger.info(f"正在預覽填寫 {len(records)} 筆記錄...")
            
            # 取得初始頁面
            response = session.get(
                url,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL
            )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 如果需要多筆記錄,先增加列
            if len(records) > 1:
                soup = self._add_form_rows(session, soup, len(records) - 1)
            
            # 構建表單資料
            form_data = self._build_form_data(soup, records)
            
            preview_result = {
                'success': True,
                'records_count': len(records),
                'form_data': form_data,
                'preview_data': [
                    {
                        'date': r.date,
                        'description': r.description,
                        'overtime_minutes': r.overtime_minutes if r.is_overtime else 0,
                        'change_minutes': r.change_minutes,
                        'type': '加班' if r.is_overtime else '調休'
                    }
                    for r in records
                ]
            }
            
            logger.info(f"✓ 預覽成功: {len(records)} 筆記錄")
            return preview_result
            
        except Exception as e:
            logger.error(f"✗ 預覽失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def submit_form(self, session: requests.Session, records: List[OvertimeSubmissionRecord]) -> Dict[str, Any]:
        """
        送出加班補報表單
        
        Args:
            session: 已登入的 Session
            records: 要送出的記錄列表
            
        Returns:
            送出結果
        """
        # Beta 版本檢查
        if not self.settings.ENABLE_SUBMISSION:
            logger.warning("送出功能已禁用 (Beta 版本)")
            return {
                'success': False,
                'error': '此功能尚在測試階段,無法實際送出。請使用「預覽填寫」功能。'
            }
        
        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_REPORT_URL}"
        
        try:
            logger.info(f"正在送出 {len(records)} 筆加班申請...")
            
            # 取得初始頁面
            response = session.get(
                url,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL
            )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 如果需要多筆記錄,先增加列
            if len(records) > 1:
                soup = self._add_form_rows(session, soup, len(records) - 1)
            
            # 構建表單資料
            form_data = self._build_form_data(soup, records)
            
            # 加入送出按鈕
            form_data['ctl00$ContentPlaceHolder1$btnCommit'] = '送出'
            
            # 送出表單
            response = session.post(
                url,
                data=form_data,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL
            )
            
            # 檢查送出結果
            success = self._check_submission_result(response.text)
            
            if success:
                logger.info(f"✓ 成功送出 {len(records)} 筆加班申請")
                return {
                    'success': True,
                    'submitted_count': len(records)
                }
            else:
                logger.error("✗ 送出失敗")
                return {
                    'success': False,
                    'error': '表單送出失敗,請檢查日誌'
                }
            
        except Exception as e:
            logger.error(f"✗ 送出失敗: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    def _add_form_rows(self, session: requests.Session, soup: BeautifulSoup, count: int) -> BeautifulSoup:
        """
        增加表單列
        
        Args:
            session: 已登入的 Session
            soup: 當前頁面的 BeautifulSoup 物件
            count: 要增加的列數
            
        Returns:
            更新後的 BeautifulSoup 物件
        """
        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_REPORT_URL}"
        
        try:
            for i in range(count):
                logger.debug(f"正在增加第 {i + 1} 列...")
                
                # 提取 ViewState
                viewstate = soup.find('input', {'name': '__VIEWSTATE'})
                viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
                event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
                
                if not viewstate:
                    raise ValueError("找不到 ViewState")
                
                # 準備 PostBack 資料 (觸發「增加列」)
                post_data = {
                    '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$lbgvAddRowi',
                    '__EVENTARGUMENT': '',
                    '__VIEWSTATE': viewstate['value'],
                    '__VIEWSTATEGENERATOR': viewstate_generator['value'] if viewstate_generator else '',
                    '__EVENTVALIDATION': event_validation['value'] if event_validation else '',
                }
                
                # 發送 PostBack 請求
                response = session.post(
                    url,
                    data=post_data,
                    timeout=self.settings.REQUEST_TIMEOUT,
                    verify=self.settings.VERIFY_SSL
                )
                
                # 更新 soup
                soup = BeautifulSoup(response.text, 'html.parser')
            
            logger.debug(f"✓ 成功增加 {count} 列")
            return soup
            
        except Exception as e:
            logger.error(f"✗ 增加列失敗: {e}")
            raise
    
    def _build_form_data(self, soup: BeautifulSoup, records: List[OvertimeSubmissionRecord]) -> Dict[str, str]:
        """
        構建表單資料
        
        Args:
            soup: BeautifulSoup 物件
            records: 記錄列表
            
        Returns:
            表單資料字典
        """
        # 提取 ViewState 等必要欄位
        viewstate = soup.find('input', {'name': '__VIEWSTATE'})
        viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
        event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
        
        if not viewstate:
            raise ValueError("找不到 ViewState")
        
        form_data = {
            '__VIEWSTATE': viewstate['value'],
            '__VIEWSTATEGENERATOR': viewstate_generator['value'] if viewstate_generator else '',
            '__EVENTVALIDATION': event_validation['value'] if event_validation else '',
        }
        
        # 填寫每筆記錄 (第一筆從 ctl03 開始,0-based index)
        for index, record in enumerate(records):
            ctl_index = f"{index + 3:02d}"  # 03, 04, 05...
            
            # 日期
            form_data[f'ctl00$ContentPlaceHolder1$gvFlow211i$ctl{ctl_index}$txtOT_Datei'] = record.date
            
            # 加班內容
            form_data[f'ctl00$ContentPlaceHolder1$gvFlow211i$ctl{ctl_index}$txtOT_Describei'] = record.description
            
            # 加班或調休時數 (使用小時,取到小數點第二位)
            if record.is_overtime:
                form_data[f'ctl00$ContentPlaceHolder1$gvFlow211i$ctl{ctl_index}$txtOT_Minutei'] = f"{record.overtime_hours:.2f}"
                form_data[f'ctl00$ContentPlaceHolder1$gvFlow211i$ctl{ctl_index}$txtChange_Minutei'] = '0'
            else:
                form_data[f'ctl00$ContentPlaceHolder1$gvFlow211i$ctl{ctl_index}$txtOT_Minutei'] = '0'
                form_data[f'ctl00$ContentPlaceHolder1$gvFlow211i$ctl{ctl_index}$txtChange_Minutei'] = f"{record.overtime_hours:.2f}"
        
        return form_data
    
    def _check_submission_result(self, html: str) -> bool:
        """
        檢查表單送出結果
        
        Args:
            html: 回應的 HTML
            
        Returns:
            是否成功
        """
        try:
            soup = BeautifulSoup(html, 'html.parser')
            
            # 檢查是否有明確的錯誤訊息
            error_indicators = [
                '系統錯誤',
                '送出失敗',
                '申請失敗',
            ]
            
            page_text = soup.get_text()
            
            # 只檢查明確的錯誤訊息,其他情況視為成功
            for indicator in error_indicators:
                if indicator in page_text:
                    logger.error("發現錯誤指標: %s", indicator)
                    return False
            
            # 沒有明確錯誤訊息,視為送出成功
            logger.info("✓ 表單送出成功 (未發現錯誤訊息)")
            return True
            
        except Exception as error:
            logger.error("檢查送出結果失敗: %s", error)
            return False
