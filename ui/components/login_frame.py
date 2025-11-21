"""登入框元件"""
import customtkinter as ctk
from typing import Callable
import sys
from pathlib import Path

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class LoginFrame(ctk.CTkFrame):
    """登入框"""
    
    def __init__(self, parent, on_login: Callable[[str, str], None]):
        super().__init__(parent)
        
        self.on_login = on_login
        self._create_ui()
    
    def _create_ui(self):
        """建立 UI"""
        # 標題
        title = ctk.CTkLabel(
            self,
            text="登入 SSP 系統",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(pady=15)
        
        # 輸入欄位容器
        input_container = ctk.CTkFrame(self, fg_color="transparent")
        input_container.pack(pady=10)
        
        # 帳號
        account_label = ctk.CTkLabel(input_container, text="帳號:")
        account_label.grid(row=0, column=0, padx=10, pady=10, sticky="e")
        
        self.account_entry = ctk.CTkEntry(
            input_container,
            width=250,
            placeholder_text="請輸入帳號"
        )
        self.account_entry.grid(row=0, column=1, padx=10, pady=10)
        
        # 密碼
        password_label = ctk.CTkLabel(input_container, text="密碼:")
        password_label.grid(row=1, column=0, padx=10, pady=10, sticky="e")
        
        self.password_entry = ctk.CTkEntry(
            input_container,
            width=250,
            placeholder_text="請輸入密碼",
            show="●"
        )
        self.password_entry.grid(row=1, column=1, padx=10, pady=10)
        
        # 按下 Enter 也能登入
        self.password_entry.bind("<Return>", lambda e: self._handle_login())
        
        # 登入按鈕
        self.login_button = ctk.CTkButton(
            self,
            text="登入",
            command=self._handle_login,
            width=200,
            height=40,
            font=ctk.CTkFont(size=16, weight="bold")
        )
        self.login_button.pack(pady=15)
    
    def _handle_login(self):
        """處理登入"""
        username = self.account_entry.get().strip()
        password = self.password_entry.get().strip()
        
        if not username or not password:
            return
        
        self.on_login(username, password)
    
    def set_loading(self, loading: bool):
        """設定載入狀態"""
        if loading:
            self.login_button.configure(state="disabled", text="登入中...")
            self.account_entry.configure(state="disabled")
            self.password_entry.configure(state="disabled")
        else:
            self.login_button.configure(state="normal", text="登入")
            self.account_entry.configure(state="normal")
            self.password_entry.configure(state="normal")
