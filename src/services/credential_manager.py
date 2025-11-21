"""
安全憑證管理服務
遵循 OWASP 最佳實踐進行密碼儲存和管理
"""
import keyring
import logging
from typing import Optional, Tuple
from cryptography.fernet import Fernet
import base64
import hashlib

logger = logging.getLogger(__name__)


class CredentialManager:
    """
    憑證管理器
    
    職責:
    - 安全地儲存和讀取使用者憑證
    - 使用系統 keyring 進行加密儲存
    - 遵循 OWASP 密碼儲存最佳實踐
    
    安全特性:
    - 使用作業系統的安全儲存機制 (Windows Credential Manager / macOS Keychain)
    - 密碼經過加密後才儲存
    - 不在記憶體中長期保留明文密碼
    """
    
    SERVICE_NAME = "TECO_SSP_OvertimeAssistant"
    USERNAME_KEY = "saved_username"
    PASSWORD_KEY_PREFIX = "password_for_"
    ENCRYPTION_KEY_NAME = "encryption_key"
    
    def __init__(self):
        """初始化憑證管理器"""
        self._cipher = self._get_or_create_cipher()
    
    def _get_or_create_cipher(self) -> Fernet:
        """
        取得或建立加密器
        
        使用固定的加密金鑰,儲存在 keyring 中
        這樣確保每次啟動都使用相同的金鑰解密
        """
        try:
            # 嘗試從 keyring 讀取金鑰
            key_str = keyring.get_password(
                self.SERVICE_NAME, 
                self.ENCRYPTION_KEY_NAME
            )
            
            if key_str:
                key = key_str.encode()
            else:
                # 首次使用,生成新金鑰
                key = Fernet.generate_key()
                keyring.set_password(
                    self.SERVICE_NAME,
                    self.ENCRYPTION_KEY_NAME,
                    key.decode()
                )
                logger.info("已生成新的加密金鑰")
            
            return Fernet(key)
            
        except Exception as e:
            logger.error(f"加密器初始化失敗: {e}")
            # 降級方案:使用臨時金鑰 (不推薦,僅作為備援)
            return Fernet(Fernet.generate_key())
    
    def save_credentials(self, username: str, password: str) -> bool:
        """
        儲存憑證
        
        Args:
            username: 使用者名稱
            password: 密碼 (明文)
            
        Returns:
            bool: 是否成功儲存
            
        OWASP 考量:
        - 密碼經過加密後儲存
        - 使用系統 keyring (Windows Credential Manager)
        - 不在記憶體中保留明文密碼過長時間
        """
        try:
            # 1. 儲存使用者名稱 (不加密,作為識別)
            keyring.set_password(
                self.SERVICE_NAME,
                self.USERNAME_KEY,
                username
            )
            
            # 2. 加密並儲存密碼
            encrypted_password = self._encrypt_password(password)
            password_key = f"{self.PASSWORD_KEY_PREFIX}{username}"
            
            keyring.set_password(
                self.SERVICE_NAME,
                password_key,
                encrypted_password
            )
            
            logger.info(f"已儲存使用者 '{username}' 的憑證")
            return True
            
        except Exception as e:
            logger.error(f"儲存憑證失敗: {e}", exc_info=True)
            return False
    
    def load_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """
        載入儲存的憑證
        
        Returns:
            tuple: (使用者名稱, 密碼) 或 (None, None)
            
        OWASP 考量:
        - 解密後立即使用,不長期保留
        - 失敗時返回 None,不洩漏錯誤細節
        """
        try:
            # 1. 讀取使用者名稱
            username = keyring.get_password(
                self.SERVICE_NAME,
                self.USERNAME_KEY
            )
            
            if not username:
                return (None, None)
            
            # 2. 讀取並解密密碼
            password_key = f"{self.PASSWORD_KEY_PREFIX}{username}"
            encrypted_password = keyring.get_password(
                self.SERVICE_NAME,
                password_key
            )
            
            if not encrypted_password:
                return (username, None)
            
            password = self._decrypt_password(encrypted_password)
            
            logger.info(f"已載入使用者 '{username}' 的憑證")
            return (username, password)
            
        except Exception as e:
            logger.warning(f"載入憑證失敗: {e}")
            return (None, None)
    
    def clear_credentials(self) -> bool:
        """
        清除儲存的憑證
        
        Returns:
            bool: 是否成功清除
            
        OWASP 考量:
        - 登出時清除敏感資料
        """
        try:
            # 讀取使用者名稱 (用於刪除密碼)
            username = keyring.get_password(
                self.SERVICE_NAME,
                self.USERNAME_KEY
            )
            
            if username:
                # 刪除密碼
                password_key = f"{self.PASSWORD_KEY_PREFIX}{username}"
                try:
                    keyring.delete_password(self.SERVICE_NAME, password_key)
                except Exception:
                    pass  # 密碼可能不存在
            
            # 刪除使用者名稱
            try:
                keyring.delete_password(self.SERVICE_NAME, self.USERNAME_KEY)
            except Exception:
                pass
            
            logger.info("已清除儲存的憑證")
            return True
            
        except Exception as e:
            logger.error(f"清除憑證失敗: {e}")
            return False
    
    def has_saved_credentials(self) -> bool:
        """
        檢查是否有儲存的憑證
        
        Returns:
            bool: 是否有儲存憑證
        """
        try:
            username = keyring.get_password(
                self.SERVICE_NAME,
                self.USERNAME_KEY
            )
            return username is not None
        except Exception:
            return False
    
    def _encrypt_password(self, password: str) -> str:
        """
        加密密碼
        
        Args:
            password: 明文密碼
            
        Returns:
            str: 加密後的密碼 (Base64 編碼)
        """
        encrypted_bytes = self._cipher.encrypt(password.encode())
        return base64.b64encode(encrypted_bytes).decode()
    
    def _decrypt_password(self, encrypted_password: str) -> str:
        """
        解密密碼
        
        Args:
            encrypted_password: 加密的密碼 (Base64 編碼)
            
        Returns:
            str: 明文密碼
        """
        encrypted_bytes = base64.b64decode(encrypted_password.encode())
        decrypted_bytes = self._cipher.decrypt(encrypted_bytes)
        return decrypted_bytes.decode()
    
    @staticmethod
    def hash_username(username: str) -> str:
        """
        對使用者名稱進行雜湊 (用於 logging,不洩漏真實使用者名稱)
        
        Args:
            username: 使用者名稱
            
        Returns:
            str: 雜湊後的使用者名稱 (前 8 個字元)
        """
        hash_obj = hashlib.sha256(username.encode())
        return hash_obj.hexdigest()[:8]
