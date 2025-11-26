"""加班申請狀態查詢服務"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import Dict, Optional
import urllib3

from ..config import Settings
from ..models import SubmittedRecord

logger = logging.getLogger(__name__)


class OvertimeStatusService:
    """加班申請狀態查詢服務 - 查詢已申請的加班記錄"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        
        if not self.settings.VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def fetch_submitted_records(self, session: requests.Session) -> Dict[str, SubmittedRecord]:
        """
        查詢已申請的加班記錄
        
        Args:
            session: 已登入的 Session
            
        Returns:
            字典 {日期: SubmittedRecord}
        """
        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_STATUS_URL}"
        submitted_records = {}
        
        try:
            logger.info("正在查詢已申請的加班記錄...")
            
            # 取得第一頁
            response = session.get(
                url,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL
            )
            
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 解析第一頁資料
            records = self._parse_status_table(soup)
            submitted_records.update(records)
            
            # 檢查是否有分頁
            total_pages = self._get_total_pages(soup)
            logger.info(f"發現 {total_pages} 頁記錄")
            
            # 抓取其他頁面
            if total_pages > 1:
                for page_num in range(2, min(total_pages + 1, self.settings.MAX_PAGES + 1)):
                    logger.info(f"正在抓取第 {page_num} 頁...")
                    page_records = self._fetch_status_page(session, soup, page_num)
                    submitted_records.update(page_records)
            
            logger.info(f"✓ 已查詢 {len(submitted_records)} 筆已申請記錄")
            return submitted_records
            
        except Exception as e:
            logger.error(f"✗ 查詢已申請記錄失敗: {e}")
            return {}
    
    def _parse_status_table(self, soup: BeautifulSoup) -> Dict[str, SubmittedRecord]:
        """
        解析狀態表格
        
        Args:
            soup: BeautifulSoup 物件
            
        Returns:
            字典 {日期: SubmittedRecord}
        """
        records = {}
        
        try:
            # 找到表格
            table = soup.find('table', {'id': 'ContentPlaceHolder1_gvFlow211'})
            if not table:
                logger.warning("找不到狀態表格")
                return records
            
            # 解析每一列 (從 ctl02 開始,0-based index)
            rows = table.find_all('tr')
            for i, row in enumerate(rows[1:]):  # 跳過標題列
                try:
                    # 日期: ContentPlaceHolder1_gvFlow211_lblOT_Date_N
                    date_span = row.find('span', {'id': f'ContentPlaceHolder1_gvFlow211_lblOT_Date_{i}'})
                    if not date_span:
                        continue
                    
                    date = date_span.get_text(strip=True)
                    
                    # 狀態: ContentPlaceHolder1_gvFlow211_lblProcess_Flag_Text_N
                    status_span = row.find('span', {'id': f'ContentPlaceHolder1_gvFlow211_lblProcess_Flag_Text_{i}'})
                    status = status_span.get_text(strip=True) if status_span else "未知"
                    
                    # 加班時數: ContentPlaceHolder1_gvFlow211_lblOT_Minute_N
                    overtime_span = row.find('span', {'id': f'ContentPlaceHolder1_gvFlow211_lblOT_Minute_{i}'})
                    overtime_minutes = float(overtime_span.get_text(strip=True)) if overtime_span and overtime_span.get_text(strip=True) else 0.0
                    
                    # 調休時數: ContentPlaceHolder1_gvFlow211_lblChange_Minute_N
                    change_span = row.find('span', {'id': f'ContentPlaceHolder1_gvFlow211_lblChange_Minute_{i}'})
                    change_minutes = float(change_span.get_text(strip=True)) if change_span and change_span.get_text(strip=True) else 0.0
                    
                    # 建立記錄
                    record = SubmittedRecord(
                        date=date,
                        status=status,
                        overtime_minutes=overtime_minutes,
                        change_minutes=change_minutes
                    )
                    
                    records[date] = record
                    logger.debug(f"解析記錄: {record}")
                    
                except Exception as e:
                    logger.warning(f"解析第 {i} 列失敗: {e}")
                    continue
            
            return records
            
        except Exception as e:
            logger.error(f"解析狀態表格失敗: {e}")
            return records
    
    def _get_total_pages(self, soup: BeautifulSoup) -> int:
        """
        取得總頁數
        
        Args:
            soup: BeautifulSoup 物件
            
        Returns:
            總頁數
        """
        try:
            # 找到分頁區域: class="FlowPagerStyle"
            pager = soup.find('tr', {'class': 'FlowPagerStyle'})
            if not pager:
                return 1
            
            # 找到分頁表格中的所有頁碼連結
            page_links = pager.find_all('a')
            if not page_links:
                return 1
            
            # 最後一個連結通常是最大頁數
            max_page = 1
            for link in page_links:
                try:
                    page_num = int(link.get_text(strip=True))
                    max_page = max(max_page, page_num)
                except ValueError:
                    continue
            
            return max_page
            
        except Exception as e:
            logger.warning(f"無法取得總頁數: {e}")
            return 1
    
    def _fetch_status_page(self, session: requests.Session, soup: BeautifulSoup, page_num: int) -> Dict[str, SubmittedRecord]:
        """
        抓取指定頁面的已申請記錄
        
        Args:
            session: 已登入的 Session
            soup: 當前頁面的 BeautifulSoup 物件 (用於取得 ViewState)
            page_num: 頁碼
            
        Returns:
            字典 {日期: SubmittedRecord}
        """
        url = f"{self.settings.SSP_BASE_URL}{self.settings.OVERTIME_STATUS_URL}"
        
        try:
            # 提取 ViewState
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
            
            if not viewstate:
                logger.error("找不到 ViewState")
                return {}
            
            # 準備 PostBack 資料
            post_data = {
                '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gvFlow211',
                '__EVENTARGUMENT': f'Page${page_num}',
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
            
            # 解析新頁面
            new_soup = BeautifulSoup(response.text, 'html.parser')
            records = self._parse_status_table(new_soup)
            
            # 更新 soup 為新頁面 (為下次分頁準備)
            soup.clear()
            soup.append(new_soup)
            
            return records
            
        except Exception as e:
            logger.error(f"抓取第 {page_num} 頁失敗: {e}")
            return {}
