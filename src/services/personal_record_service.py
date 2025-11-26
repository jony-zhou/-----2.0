"""個人加班記錄查詢服務"""
import logging
from typing import List, Tuple
import requests
from bs4 import BeautifulSoup
from ..models.personal_record import PersonalRecord, PersonalRecordSummary

logger = logging.getLogger(__name__)


class PersonalRecordService:
    """
    個人加班記錄查詢服務
    
    職責:
    - 查詢個人已申請的加班記錄 (FW21003Z.aspx)
    - 使用 ddlPage=9999 (不換頁) 一次取得所有記錄
    - 解析表格資料並計算統計數據
    """
    
    def __init__(self, base_url: str):
        """
        初始化個人記錄服務
        
        Args:
            base_url: SSP 系統基礎 URL
        """
        self.base_url = base_url
        self.personal_record_url = f"{base_url}/FW21003Z.aspx"
    
    def fetch_personal_records(
        self, 
        session: requests.Session
    ) -> Tuple[List[PersonalRecord], PersonalRecordSummary]:
        """
        查詢個人加班記錄並計算統計
        
        Args:
            session: 已登入的 session
            
        Returns:
            Tuple[記錄列表, 統計摘要]
            
        Raises:
            Exception: 查詢失敗時拋出異常
        """
        try:
            logger.info("開始查詢個人加班記錄 (不換頁模式)")
            
            # 設定不換頁參數
            params = {
                'ctl00$ContentPlaceHolder1$ddlPage': '9999'
            }
            
            response = session.get(
                self.personal_record_url,
                params=params,
                timeout=30,
                verify=False  # 忽略 SSL 憑證驗證 (內部系統)
            )
            response.raise_for_status()
            
            # 解析 HTML
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 解析記錄表格
            records = self._parse_personal_records_table(soup)
            
            # 計算統計摘要
            summary = self._calculate_summary(records)
            
            logger.info(
                "個人記錄查詢成功: %d 筆記錄, 總時數 %.1f hr",
                len(records),
                summary.total_overtime_hours
            )
            
            return records, summary
            
        except requests.RequestException as error:
            logger.error("個人記錄查詢失敗 (網路錯誤): %s", error)
            raise Exception(f"網路錯誤: {error}") from error
        except Exception as error:
            logger.error("個人記錄查詢失敗: %s", error, exc_info=True)
            raise
    
    def _parse_personal_records_table(self, soup: BeautifulSoup) -> List[PersonalRecord]:
        """
        解析個人記錄表格
        
        表格結構:
        - 第 1 欄: 加班人員 + 加班日期 (使用 span id 抓取精確值)
        - 第 2 欄: 加班單位 + 加班內容
        - 第 3 欄: 狀態 (加班/調休)
        - 第 4 欄: 申報 (加班時數/調休時數)
        - 第 5 欄: 當月累積
        - 第 6 欄: 當季累積
        - 第 7 欄: 狀態 (簽核狀態)
        
        Args:
            soup: BeautifulSoup 物件
            
        Returns:
            個人記錄列表
        """
        records = []
        
        # 查找表格 (通常是 GridView,ID 為 ContentPlaceHolder1_gvFlow211)
        table = soup.find('table', id='ContentPlaceHolder1_gvFlow211')
        
        if not table:
            logger.warning("未找到個人記錄表格 (ContentPlaceHolder1_gvFlow211)")
            return records
        
        # 解析表格行 (跳過表頭和分頁列)
        rows = table.find_all('tr', class_=['RowStyle', 'AlternatingRowStyle_update'])
        
        for index, row in enumerate(rows):
            try:
                # 使用 span id 精確抓取資料
                # 日期: ContentPlaceHolder1_gvFlow211_lblOT_Date_{index}
                date_span = row.find('span', id=f'ContentPlaceHolder1_gvFlow211_lblOT_Date_{index}')
                if not date_span:
                    logger.warning("記錄 %d: 未找到日期欄位", index)
                    continue
                date = date_span.get_text(strip=True)
                
                # 加班內容: ContentPlaceHolder1_gvFlow211_lblOT_Describe_{index}
                content_span = row.find('span', id=f'ContentPlaceHolder1_gvFlow211_lblOT_Describe_{index}')
                content = ""
                if content_span:
                    # 優先使用 title 屬性 (完整內容)
                    title_attr = content_span.get('title')
                    if title_attr and isinstance(title_attr, str):
                        content = title_attr
                    else:
                        content = content_span.get_text(strip=True)
                
                # 申報時數 (加班): ContentPlaceHolder1_gvFlow211_lblOT_Minute_{index}
                overtime_span = row.find('span', id=f'ContentPlaceHolder1_gvFlow211_lblOT_Minute_{index}')
                overtime_text = overtime_span.get_text(strip=True) if overtime_span else "0"
                overtime_hours = self._parse_hours(overtime_text)
                
                # 調休時數: ContentPlaceHolder1_gvFlow211_lblChange_Minute_{index}
                change_span = row.find('span', id=f'ContentPlaceHolder1_gvFlow211_lblChange_Minute_{index}')
                change_text = change_span.get_text(strip=True) if change_span else "0"
                change_hours = self._parse_hours(change_text)
                
                # 判斷申報類型並取得總時數
                if overtime_hours > 0:
                    report_type = "加班"
                    total_hours = overtime_hours
                elif change_hours > 0:
                    report_type = "調休"
                    total_hours = change_hours
                else:
                    report_type = ""
                    total_hours = 0.0
                
                # 當月累計: ContentPlaceHolder1_gvFlow211_lblOT_Manhour_{index}
                monthly_span = row.find('span', id=f'ContentPlaceHolder1_gvFlow211_lblOT_Manhour_{index}')
                monthly_text = monthly_span.get_text(strip=True) if monthly_span else "0"
                monthly_total = self._parse_hours(monthly_text)
                
                # 當季累計: ContentPlaceHolder1_gvFlow211_lblOT_Monhour_{index}
                quarterly_span = row.find('span', id=f'ContentPlaceHolder1_gvFlow211_lblOT_Monhour_{index}')
                quarterly_text = quarterly_span.get_text(strip=True) if quarterly_span else "0"
                quarterly_total = self._parse_hours(quarterly_text)
                
                # 簽核狀態: ContentPlaceHolder1_gvFlow211_lblProcess_Flag_Text_{index}
                status_span = row.find('span', id=f'ContentPlaceHolder1_gvFlow211_lblProcess_Flag_Text_{index}')
                status = status_span.get_text(strip=True).replace('<br>', ' ') if status_span else ""
                
                record = PersonalRecord(
                    date=date,
                    content=content,
                    status=status,
                    overtime_hours=total_hours,
                    monthly_total=monthly_total,
                    quarterly_total=quarterly_total,
                    report_type=report_type
                )
                
                records.append(record)
                
            except (IndexError, ValueError, AttributeError) as error:
                logger.warning("解析記錄 %d 失敗: %s", index, error)
                continue
        
        return records
    
    def _parse_hours(self, text: str) -> float:
        """
        解析時數文字
        
        Args:
            text: 時數文字 (可能是 "120" 分鐘或 "2.0" 小時)
            
        Returns:
            小時數
        """
        try:
            text = text.replace(',', '').strip()
            if not text:
                return 0.0
            
            value = float(text)
            
            # 判斷是否為分鐘數 (通常大於 10 的整數)
            if value > 10 and value == int(value):
                return value / 60.0  # 分鐘轉小時
            
            return value
            
        except ValueError:
            logger.warning("無法解析時數: %s", text)
            return 0.0
    
    def _calculate_summary(self, records: List[PersonalRecord]) -> PersonalRecordSummary:
        """
        計算統計摘要
        
        Args:
            records: 個人記錄列表
            
        Returns:
            統計摘要
        """
        if not records:
            return PersonalRecordSummary()
        
        total_hours = sum(r.overtime_hours for r in records)
        avg_hours = total_hours / len(records) if records else 0.0
        max_hours = max(r.overtime_hours for r in records) if records else 0.0
        
        # 本月和本季累計取最後一筆記錄的值
        last_record = records[-1] if records else None
        current_month = last_record.monthly_total if last_record else 0.0
        current_quarter = last_record.quarterly_total if last_record else 0.0
        
        return PersonalRecordSummary(
            total_records=len(records),
            total_overtime_hours=total_hours,
            average_overtime_hours=avg_hours,
            max_overtime_hours=max_hours,
            current_month_total=current_month,
            current_quarter_total=current_quarter
        )
