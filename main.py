#!/usr/bin/env python3
"""
TECO SSP 加班時數計算器 - 進階版
支援配置檔案、批次處理、詳細日誌
"""

import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import pandas as pd
from typing import List, Dict, Optional, Tuple
import re
import logging
import sys
from pathlib import Path

# 嘗試載入配置檔案
try:
    from config import (
        SSP_BASE_URL, LUNCH_BREAK, WORK_HOURS, REST_TIME,
        EXCEL_FILENAME_PREFIX, DATE_FORMAT, TIME_FORMAT
    )
except ImportError:
    # 使用預設值
    SSP_BASE_URL = "https://ssp.teco.com.tw"
    LUNCH_BREAK = 70
    WORK_HOURS = 480
    REST_TIME = 30
    EXCEL_FILENAME_PREFIX = "report/overtime_report"
    DATE_FORMAT = "%Y/%m/%d"
    TIME_FORMAT = "%H:%M:%S"


# 設定日誌
# 建立 logs 資料夾
Path('logs').mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('logs/overtime_calculator.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


class OvertimeCalculatorAdvanced:
    """加班時數計算器 - 進階版"""
    
    def __init__(self, base_url: str = SSP_BASE_URL, verify_ssl: bool = False):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        # 關閉 SSL 憑證驗證(適用於公司內部網站)
        self.verify_ssl = verify_ssl
        if not verify_ssl:
            # 停用 SSL 警告訊息
            import urllib3
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        self.lunch_break = LUNCH_BREAK
        self.work_hours = WORK_HOURS
        self.rest_time = REST_TIME
        
    def login(self, username: str, password: str) -> bool:
        """
        登入系統
        
        Args:
            username: 使用者帳號
            password: 使用者密碼
            
        Returns:
            bool: 登入是否成功
        """
        login_url = f"{self.base_url}/index.aspx"
        
        try:
            logger.info("正在連接登入頁面...")
            response = self.session.get(login_url, timeout=30, verify=self.verify_ssl)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取 ASP.NET 必要的隱藏欄位
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
            
            if not viewstate:
                logger.error("無法找到 ViewState,可能網頁結構已變更")
                return False
            
            # 準備登入資料 (使用正確的欄位名稱)
            login_data = {
                '__VIEWSTATE': viewstate['value'],
                '__VIEWSTATEGENERATOR': viewstate_generator['value'] if viewstate_generator else '',
                '__EVENTVALIDATION': event_validation['value'] if event_validation else '',
                'ctl00$lblAccount': username,      # 帳號欄位
                'ctl00$lblPassWord': password,     # 密碼欄位
                'ctl00$Submit': '送出'             # 送出按鈕
            }
            
            logger.info("正在驗證登入資訊...")
            response = self.session.post(login_url, data=login_data, timeout=30, verify=self.verify_ssl)
            
            # 檢查是否登入成功
            if 'FW99001Z.aspx' in response.url or '登出' in response.text:
                logger.info("✓ 登入成功")
                return True
            else:
                logger.error("✗ 登入失敗,請檢查帳號密碼")
                return False
                
        except requests.exceptions.Timeout:
            logger.error("✗ 連線逾時,請檢查網路連線")
            return False
        except Exception as e:
            logger.error(f"✗ 登入時發生錯誤: {e}", exc_info=True)
            return False
    
    def get_attendance_data(self, max_pages: int = 10) -> List[Dict]:
        """
        取得出勤異常清單資料
        
        Args:
            max_pages: 最大頁數限制
            
        Returns:
            List[Dict]: 出勤記錄列表
        """
        # 訪問出勤異常清單頁面 (移除錨點,讓後端正常載入)
        attendance_url = f"{self.base_url}/FW99001Z.aspx"
        all_records = []
        current_page = 1
        
        try:
            logger.info("正在訪問出勤異常頁面...")
            response = self.session.get(attendance_url, timeout=30, verify=self.verify_ssl)
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 使用 set 來追蹤已處理的記錄 (避免重複)
            seen_records = set()
            
            while current_page <= max_pages:
                logger.info(f"正在處理第 {current_page} 頁...")
                
                # 解析當前頁面的資料
                records = self._parse_attendance_table(soup)
                
                # 去重處理
                new_count = 0
                for record in records:
                    # 使用日期+時間範圍作為唯一鍵
                    record_key = f"{record['date']}_{record['time_range']}"
                    if record_key not in seen_records:
                        seen_records.add(record_key)
                        all_records.append(record)
                        new_count += 1
                
                if new_count > 0:
                    logger.info(f"  新增 {new_count} 筆記錄 (本頁共 {len(records)} 筆)")
                else:
                    logger.warning(f"  第 {current_page} 頁沒有新資料 (可能重複或空白)")
                
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
        
        # 除錯: 尋找 tabs-2 div
        tabs2_div = soup.find('div', id='tabs-2')
        if tabs2_div:
            logger.info("✓ 找到 tabs-2 div")
            # 在 tabs-2 內部尋找表格
            search_soup = tabs2_div
        else:
            logger.warning("找不到 tabs-2 div, 在全域尋找")
            search_soup = soup
        
        # 嘗試多種方式找到表格
        table = search_soup.find('table', id='ContentPlaceHolder1_gvWeb012')
        if not table:
            table = search_soup.find('table', {'id': re.compile('.*gvWeb012.*')})
        if not table:
            table = search_soup.find('table', {'cellspacing': '0', 'cellpadding': '3', 'rules': 'rows'})
        
        if not table:
            logger.warning("找不到出勤表格")
            # 除錯: 顯示可用的表格
            all_tables = soup.find_all('table')
            logger.debug(f"全域共有 {len(all_tables)} 個 table")
            for idx, t in enumerate(all_tables[:10]):  # 只顯示前10個
                table_id = t.get('id', '無ID')
                table_class = t.get('class')
                class_str = str(table_class) if table_class else '無class'
                logger.debug(f"  Table {idx+1}: id='{table_id}' class={class_str}")
            
            # 嘗試尋找包含 "出勤日期" 的表格
            for t in all_tables:
                if '出勤日期' in t.get_text():
                    logger.info("✓ 找到包含 '出勤日期' 的表格")
                    table = t
                    break
            
            if not table:
                return records
        
        logger.info(f"✓ 找到表格: {table.get('id', 'unknown')}")
        
        # 找出所有資料列 (排除表頭和分頁列)
        rows = table.find_all('tr')
        data_rows = []
        
        for row in rows:
            # 跳過表頭
            if row.find('th'):
                continue
            # 跳過分頁列
            row_class = row.get('class')
            if row_class and 'PagerStyle' in (row_class if isinstance(row_class, list) else [row_class]):
                continue
            # 只處理包含 RowStyle 或 AlternatingRowStyle 的列
            row_classes = ' '.join(row_class) if isinstance(row_class, list) else str(row_class) if row_class else ''
            if 'RowStyle' in row_classes or 'AlternatingRowStyle' in row_classes:
                data_rows.append(row)
        
        logger.info(f"  發現 {len(data_rows)} 筆資料列")
        
        for idx, row in enumerate(data_rows):
            try:
                cells = row.find_all('td')
                if len(cells) < 3:
                    logger.debug(f"  跳過第 {idx+1} 列: 欄位數不足 ({len(cells)} < 3)")
                    continue
                
                # 第一個 cell 包含日期和時間
                first_cell = cells[0]
                
                # 取得日期 - 使用更靈活的方式
                date_span = first_cell.find('span', id=re.compile('.*lblWork_Date.*'))
                if not date_span:
                    # 嘗試尋找任何包含日期格式的 span
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
                    # 嘗試尋找包含時間範圍的 span
                    all_spans = first_cell.find_all('span')
                    for span in all_spans:
                        text = span.text.strip()
                        if '~' in text and ':' in text:
                            time_span = span
                            break
                
                time_str = time_span.text.strip() if time_span else ''
                
                # 清理時間字串 (移除 &nbsp; 等空白字元)
                time_str = time_str.replace('\xa0', '').replace('\u3000', '').replace(' ', '').strip()
                
                if date_str and time_str and '~' in time_str:
                    records.append({
                        'date': date_str,
                        'time_range': time_str
                    })
                    logger.debug(f"  ✓ 第 {idx+1} 列: {date_str} {time_str}")
                else:
                    logger.debug(f"  跳過第 {idx+1} 列: 日期='{date_str}' 時間='{time_str}'")
                    
            except Exception as e:
                logger.warning(f"  解析第 {idx+1} 列時發生錯誤: {e}")
                continue
        
        logger.info(f"  成功解析 {len(records)} 筆記錄")
        return records
    
    def _has_next_page(self, soup: BeautifulSoup, current_page: int) -> bool:
        """檢查是否有下一頁"""
        # 先找到目標表格
        table = soup.find('table', id='ContentPlaceHolder1_gvWeb012')
        if not table:
            table = soup.find('table', {'id': re.compile('.*gvWeb012.*')})
        
        if not table:
            return False
        
        # 在該表格內尋找 PagerStyle
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
                f"{self.base_url}/FW99001Z.aspx",
                data=post_data,
                timeout=30,
                verify=self.verify_ssl
            )
            
            return response
            
        except Exception as e:
            logger.error(f"翻頁時發生錯誤: {e}")
            return None
    
    def calculate_overtime(self, records: List[Dict]) -> pd.DataFrame:
        """
        計算加班時數
        
        Args:
            records: 出勤記錄列表
            
        Returns:
            pd.DataFrame: 包含加班時數的資料表
        """
        results = []
        
        for idx, record in enumerate(records):
            try:
                date = record['date']
                time_range = record['time_range']
                
                # 解析時間範圍
                times = time_range.split('~')
                if len(times) != 2:
                    logger.warning(f"  記錄 {idx+1}: 時間格式錯誤 - {time_range}")
                    continue
                
                start_time_str = times[0].strip()
                end_time_str = times[1].strip()
                
                # 轉換為 datetime 物件
                start_time = datetime.strptime(f"{date} {start_time_str}", f"{DATE_FORMAT} {TIME_FORMAT}")
                end_time = datetime.strptime(f"{date} {end_time_str}", f"{DATE_FORMAT} {TIME_FORMAT}")
                
                # 如果上班時間晚於 9:00,以 9:00 計算
                standard_start = datetime.strptime(f"{date} 09:00:00", f"{DATE_FORMAT} {TIME_FORMAT}")
                if start_time > standard_start:
                    actual_start = standard_start
                    logger.debug(f"  {date}: 上班時間 {start_time_str} 晚於 9:00,以 9:00 計算")
                else:
                    actual_start = start_time
                
                # 計算總工作時間(分鐘)
                total_minutes = (end_time - actual_start).total_seconds() / 60
                
                # 計算加班時數
                # 加班時數 = 總時間 - 午休 - 正常上班時間 - 休息時間
                overtime_minutes = total_minutes - self.lunch_break - self.work_hours - self.rest_time
                
                # 轉換為小時(保留一位小數)
                overtime_hours = round(overtime_minutes / 60, 1)
                
                # 限制加班時數在 0~4 小時之間
                if overtime_hours < 0:
                    overtime_hours = 0
                elif overtime_hours > 4:
                    overtime_hours = 4
                
                results.append({
                    '日期': date,
                    '上班時間': start_time_str,
                    '下班時間': end_time_str,
                    '總工時(分)': int(total_minutes),
                    '加班時數': overtime_hours
                })
                
                logger.debug(f"  {date}: {start_time_str}~{end_time_str} → 加班 {overtime_hours}hr")
                
            except ValueError as e:
                logger.warning(f"  記錄 {idx+1}: 時間解析錯誤 - {e}")
                continue
            except Exception as e:
                logger.error(f"  記錄 {idx+1}: 計算時發生錯誤 - {e}")
                continue
        
        # 建立 DataFrame
        df = pd.DataFrame(results)
        
        # 排序(由新到舊)
        if not df.empty:
            df['日期_dt'] = pd.to_datetime(df['日期'], format=DATE_FORMAT)
            df = df.sort_values('日期_dt', ascending=False)
            df = df.drop('日期_dt', axis=1)
            df = df.reset_index(drop=True)
        
        return df
    
    def generate_report(self, df: pd.DataFrame, show_details: bool = True) -> str:
        """生成加班報表"""
        if df.empty:
            return "沒有找到任何出勤記錄"
        
        report = "\n" + "="*80 + "\n"
        report += f"{'加班時數統計報表':^70}\n"
        report += f"{'產生時間: ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S'):^70}\n"
        report += "="*80 + "\n\n"
        
        if show_details:
            # 顯示詳細資料
            display_df = df[['日期', '上班時間', '下班時間', '加班時數']].copy()
            report += display_df.to_string(index=False)
        else:
            # 僅顯示有加班的記錄
            overtime_df = df[df['加班時數'] > 0][['日期', '上班時間', '下班時間', '加班時數']].copy()
            report += overtime_df.to_string(index=False)
        
        report += "\n\n" + "-"*80 + "\n"
        report += "統計資訊:\n"
        report += "-"*80 + "\n"
        
        total_overtime = df['加班時數'].sum()
        avg_overtime = df['加班時數'].mean()
        max_overtime = df['加班時數'].max()
        overtime_days = len(df[df['加班時數'] > 0])
        
        report += f"記錄天數: {len(df)} 天\n"
        report += f"加班天數: {overtime_days} 天\n"
        report += f"總加班時數: {total_overtime:.1f} 小時\n"
        report += f"平均每日加班: {avg_overtime:.1f} 小時\n"
        report += f"最長加班: {max_overtime:.1f} 小時\n"
        
        # 找出最長加班的日期
        if max_overtime > 0:
            max_date = df[df['加班時數'] == max_overtime]['日期'].iloc[0]
            report += f"最長加班日期: {max_date}\n"
        
        report += "="*80 + "\n"
        
        return report
    
    def export_to_excel(self, df: pd.DataFrame, filename: Optional[str] = None) -> Optional[str]:
        """匯出為 Excel 檔案"""
        # 建立 reports 資料夾
        Path('reports').mkdir(exist_ok=True)
        
        if filename is None:
            filename = f"reports/{EXCEL_FILENAME_PREFIX}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
        elif not filename.startswith('reports/'):
            filename = f"reports/{filename}"
        
        try:
            # 準備匯出資料
            export_df = df.copy()
            
            # 加入統計資料
            summary_df = pd.DataFrame({
                '日期': ['', '統計資訊', '記錄天數', '加班天數', '總加班時數', '平均每日加班', '最長加班'],
                '上班時間': ['', '', len(df), len(df[df['加班時數'] > 0]), 
                           f"{df['加班時數'].sum():.1f} hr", 
                           f"{df['加班時數'].mean():.1f} hr",
                           f"{df['加班時數'].max():.1f} hr"],
                '下班時間': [''] * 7,
                '總工時(分)': [''] * 7,
                '加班時數': [''] * 7
            })
            
            final_df = pd.concat([export_df, summary_df], ignore_index=True)
            
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


def main():
    """主程式"""
    print("="*80)
    print(f"{'TECO SSP 加班時數計算器':^70}")
    print(f"{'v2.0 進階版':^70}")
    print("="*80 + "\n")
    
    # 建立計算器實例
    calculator = OvertimeCalculatorAdvanced()
    
    # 登入
    print("請輸入登入資訊")
    print("-" * 40)
    username = input("帳號: ").strip()
    password = input("密碼: ").strip()
    
    print("\n" + "="*80)
    logger.info("開始執行...")
    
    if not calculator.login(username, password):
        logger.error("程式終止")
        return
    
    # 取得資料
    records = calculator.get_attendance_data(max_pages=10)
    
    if not records:
        logger.warning("沒有找到任何出勤記錄")
        return
    
    # 計算加班時數
    logger.info("正在計算加班時數...")
    df = calculator.calculate_overtime(records)
    
    # 顯示報表
    report = calculator.generate_report(df, show_details=True)
    print(report)
    
    # 詢問是否匯出
    print("\n選項:")
    print("1. 匯出完整報表為 Excel")
    print("2. 匯出所有出勤記錄 (包含加班0小時)")
    print("3. 不匯出")
    
    choice = input("\n請選擇 (1/2/3): ").strip()
    
    if choice == '1':
        filename = calculator.export_to_excel(df)
        if filename:
            print(f"\n✓ 完整報表已匯出: {filename}")
    elif choice == '2':
        # 匯出所有記錄 (與選項1相同,保持向後相容)
        filename = calculator.export_to_excel(df)
        if filename:
            print(f"\n✓ 出勤記錄已匯出: {filename}")
    
    logger.info("程式執行完成")


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n程式被使用者中斷")
        logger.info("程式被使用者中斷")
    except Exception as e:
        logger.error(f"程式發生未預期的錯誤: {e}", exc_info=True)
        print(f"\n✗ 發生錯誤: {e}")