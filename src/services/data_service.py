"""資料擷取服務"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import List, Dict, Optional
import re

from ..config import Settings

logger = logging.getLogger(__name__)


class DataService:
    """資料擷取服務 - 處理出勤資料抓取"""
    
    def __init__(self, session: requests.Session, settings: Optional[Settings] = None):
        self.session = session
        self.settings = settings or Settings()
    
    def get_attendance_data(self, max_pages: Optional[int] = None) -> List[Dict]:
        """
        取得出勤異常清單資料
        
        Args:
            max_pages: 最大頁數限制
            
        Returns:
            List[Dict]: 出勤記錄列表 [{'date': 'YYYY/MM/DD', 'time_range': 'HH:MM:SS~HH:MM:SS'}]
        """
        max_pages = max_pages or self.settings.MAX_PAGES
        attendance_url = f"{self.settings.SSP_BASE_URL}/FW99001Z.aspx"
        all_records = []
        current_page = 1
        
        try:
            logger.info("正在訪問出勤異常頁面...")
            response = self.session.get(
                attendance_url, 
                timeout=self.settings.REQUEST_TIMEOUT, 
                verify=self.settings.VERIFY_SSL
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 使用 set 來追蹤已處理的記錄
            seen_records = set()
            
            while current_page <= max_pages:
                logger.info(f"正在處理第 {current_page} 頁...")
                
                # 解析當前頁面的資料
                records = self._parse_attendance_table(soup)
                
                # 去重處理
                new_count = 0
                for record in records:
                    record_key = f"{record['date']}_{record['time_range']}"
                    if record_key not in seen_records:
                        seen_records.add(record_key)
                        all_records.append(record)
                        new_count += 1
                
                if new_count > 0:
                    logger.info(f"  新增 {new_count} 筆記錄 (本頁共 {len(records)} 筆)")
                else:
                    logger.warning(f"  第 {current_page} 頁沒有新資料")
                
                # 檢查是否有下一頁
                has_next = self._has_next_page(soup, current_page)
                if not has_next:
                    logger.info("已處理完所有頁面")
                    break
                
                # 執行翻頁
                response = self._goto_next_page(soup, current_page + 1)
                if not response:
                    logger.warning("翻頁失敗,停止處理")
                    break
                    
                soup = BeautifulSoup(response.text, 'html.parser')
                current_page += 1
            
            logger.info(f"✓ 共取得 {len(all_records)} 筆不重複記錄")
            return all_records
            
        except Exception as e:
            logger.error(f"✗ 取得出勤資料時發生錯誤: {e}", exc_info=True)
            return all_records
    
    def _parse_attendance_table(self, soup: BeautifulSoup) -> List[Dict]:
        """解析出勤表格"""
        records = []
        
        # 尋找 tabs-2 div
        tabs2_div = soup.find('div', id='tabs-2')
        search_soup = tabs2_div if tabs2_div else soup
        
        # 尋找表格
        table = search_soup.find('table', id='ContentPlaceHolder1_gvWeb012')
        if not table:
            table = search_soup.find('table', {'id': re.compile('.*gvWeb012.*')})
        if not table:
            table = search_soup.find('table', {'cellspacing': '0', 'cellpadding': '3', 'rules': 'rows'})
        
        if not table:
            logger.warning("找不到出勤表格")
            # 嘗試尋找包含 "出勤日期" 的表格
            all_tables = soup.find_all('table')
            for t in all_tables:
                if '出勤日期' in t.get_text():
                    table = t
                    break
            
            if not table:
                return records
        
        logger.info(f"✓ 找到表格: {table.get('id', 'unknown')}")
        
        # 找出所有資料列
        rows = table.find_all('tr')
        data_rows = []
        
        for row in rows:
            if row.find('th'):
                continue
            
            row_class = row.get('class')
            if row_class and 'PagerStyle' in (row_class if isinstance(row_class, list) else [row_class]):
                continue
            
            row_classes = ' '.join(row_class) if isinstance(row_class, list) else str(row_class) if row_class else ''
            if 'RowStyle' in row_classes or 'AlternatingRowStyle' in row_classes:
                data_rows.append(row)
        
        logger.info(f"  發現 {len(data_rows)} 筆資料列")
        
        for idx, row in enumerate(data_rows):
            try:
                cells = row.find_all('td')
                if len(cells) < 3:
                    continue
                
                first_cell = cells[0]
                
                # 取得日期
                date_span = first_cell.find('span', id=re.compile('.*lblWork_Date.*'))
                if not date_span:
                    all_spans = first_cell.find_all('span')
                    for span in all_spans:
                        text = span.text.strip()
                        if re.match(r'\d{4}/\d{1,2}/\d{1,2}', text):
                            date_span = span
                            break
                
                date_str = date_span.text.strip() if date_span else ''
                
                # 取得刷卡時間
                time_span = first_cell.find('span', id=re.compile('.*lblCard_Time.*'))
                if not time_span:
                    all_spans = first_cell.find_all('span')
                    for span in all_spans:
                        text = span.text.strip()
                        if '~' in text and ':' in text:
                            time_span = span
                            break
                
                time_str = time_span.text.strip() if time_span else ''
                time_str = time_str.replace('\xa0', '').replace('\u3000', '').replace(' ', '').strip()
                
                if date_str and time_str and '~' in time_str:
                    records.append({
                        'date': date_str,
                        'time_range': time_str
                    })
                    logger.debug(f"  ✓ 第 {idx+1} 列: {date_str} {time_str}")
                    
            except Exception as e:
                logger.warning(f"  解析第 {idx+1} 列時發生錯誤: {e}")
                continue
        
        logger.info(f"  成功解析 {len(records)} 筆記錄")
        return records
    
    def _has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """檢查是否有下一頁"""
        table = soup.find('table', id='ContentPlaceHolder1_gvWeb012')
        if not table:
            table = soup.find('table', {'id': re.compile('.*gvWeb012.*')})
        
        if not table:
            return False
        
        pager = table.find('tr', class_='PagerStyle')
        if not pager:
            return False
        
        all_links = pager.find_all('a')
        for link in all_links:
            if link.text.strip().isdigit() and int(link.text.strip()) == current_page + 1:
                return True
        
        return False
    
    def _goto_next_page(self, soup: BeautifulSoup, page_num: int) -> Optional[requests.Response]:
        """前往下一頁"""
        try:
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
            
            if not viewstate:
                logger.error("無法取得 ViewState,翻頁失敗")
                return None
            
            post_data = {
                '__VIEWSTATE': viewstate['value'],
                '__VIEWSTATEGENERATOR': viewstate_generator['value'] if viewstate_generator else '',
                '__EVENTVALIDATION': event_validation['value'] if event_validation else '',
                '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gvWeb012',
                '__EVENTARGUMENT': f'Page${page_num}'
            }
            
            response = self.session.post(
                f"{self.settings.SSP_BASE_URL}/FW99001Z.aspx",
                data=post_data,
                timeout=self.settings.REQUEST_TIMEOUT,
                verify=self.settings.VERIFY_SSL
            )
            
            return response
            
        except Exception as e:
            logger.error(f"翻頁時發生錯誤: {e}")
            return None
