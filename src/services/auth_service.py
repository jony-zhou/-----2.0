"""認證服務"""
import requests
from bs4 import BeautifulSoup
import logging
from typing import Optional
import urllib3

from ..config import Settings

logger = logging.getLogger(__name__)


class AuthService:
    """認證服務 - 處理 SSP 系統登入"""
    
    def __init__(self, settings: Optional[Settings] = None):
        self.settings = settings or Settings()
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })
        
        if not self.settings.VERIFY_SSL:
            urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
    
    def login(self, username: str, password: str) -> bool:
        """
        登入 SSP 系統
        
        Args:
            username: 使用者帳號
            password: 使用者密碼
            
        Returns:
            bool: 登入是否成功
        """
        login_url = f"{self.settings.SSP_BASE_URL}/index.aspx"
        
        try:
            logger.info("正在連接登入頁面...")
            response = self.session.get(
                login_url, 
                timeout=self.settings.REQUEST_TIMEOUT, 
                verify=self.settings.VERIFY_SSL
            )
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 提取 ASP.NET 必要的隱藏欄位
            viewstate = soup.find('input', {'name': '__VIEWSTATE'})
            viewstate_generator = soup.find('input', {'name': '__VIEWSTATEGENERATOR'})
            event_validation = soup.find('input', {'name': '__EVENTVALIDATION'})
            
            if not viewstate:
                logger.error("無法找到 ViewState,可能網頁結構已變更")
                return False
            
            # 準備登入資料
            login_data = {
                '__VIEWSTATE': viewstate['value'],
                '__VIEWSTATEGENERATOR': viewstate_generator['value'] if viewstate_generator else '',
                '__EVENTVALIDATION': event_validation['value'] if event_validation else '',
                'ctl00$lblAccount': username,
                'ctl00$lblPassWord': password,
                'ctl00$Submit': '送出'
            }
            
            logger.info("正在驗證登入資訊...")
            response = self.session.post(
                login_url, 
                data=login_data, 
                timeout=self.settings.REQUEST_TIMEOUT, 
                verify=self.settings.VERIFY_SSL
            )
            
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
    
    def get_session(self) -> requests.Session:
        """取得已登入的 session"""
        return self.session
