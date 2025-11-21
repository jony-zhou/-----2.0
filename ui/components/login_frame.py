"""
登入框架元件 - 專業 UI/UX 設計
"""
import customtkinter as ctk
from typing import Callable
import sys
from pathlib import Path

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.config import (
    colors, typography, spacing, border_radius, 
    default_styles, get_font_config, component_sizes
)


class LoginFrame(ctk.CTkFrame):
    """
    登入框架 - 現代化設計
    
    特色:
    - 卡片式登入框
    - 密碼顯示/隱藏切換
    - 記住我核取框
    - 平滑動畫效果
    """
    
    def __init__(self, parent, on_login: Callable[[str, str, bool], None]):  # 新增 remember_me 參數
        super().__init__(
            parent,
            fg_color=colors.background_primary,
            corner_radius=0
        )
        
        self.on_login = on_login
        self.password_visible = False
        
        self._create_ui()
    
    def _create_ui(self):
        """設置 UI 元件"""
        # 使用 place 布局實現垂直水平置中 (不會被拉伸)
        
        # === 主容器 (卡片) ===
        card = ctk.CTkFrame(
            self,
            **default_styles.CARD,
            width=400,
            height=550
        )
        # 使用 place 置中,不會被 parent 的 pack 影響
        card.place(relx=0.5, rely=0.5, anchor="center")
        card.pack_propagate(False)  # 防止內部元件改變卡片大小
        
        # === Logo / 圖示區域 ===
        logo_frame = ctk.CTkFrame(
            card,
            fg_color="transparent",
            height=80
        )
        logo_frame.pack(pady=(spacing.xl, spacing.lg))
        
        # 應用程式圖示 (使用 assets 圖示)
        try:
            from PIL import Image
            from pathlib import Path
            import logging
            
            logger = logging.getLogger(__name__)
            
            # 取得圖示路徑
            icon_path = Path(__file__).parent.parent.parent / "assets" / "icon.png"
            
            if icon_path.exists():
                # 載入並使用 CTkImage (支援高 DPI)
                img = Image.open(str(icon_path))
                ctk_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(64, 64)
                )
                
                icon_label = ctk.CTkLabel(
                    logo_frame,
                    image=ctk_image,
                    text=""
                )
                icon_label.pack()
            else:
                # 降級方案: 使用 emoji
                icon_label = ctk.CTkLabel(
                    logo_frame,
                    text="⏰",
                    font=get_font_config(48),
                    text_color=colors.primary
                )
                icon_label.pack()
        except Exception as e:
            # 降級方案: 使用 emoji
            icon_label = ctk.CTkLabel(
                logo_frame,
                text="⏰",
                font=get_font_config(48),
                text_color=colors.primary
            )
            icon_label.pack()
        
        # === 標題區域 ===
        title_label = ctk.CTkLabel(
            card,
            text="員工加班助手",
            font=get_font_config(typography.size_h2, typography.weight_bold),
            text_color=colors.text_primary
        )
        title_label.pack(pady=(0, spacing.xs))
        
        subtitle_label = ctk.CTkLabel(
            card,
            text="請輸入您的帳號密碼登入系統",
            font=get_font_config(typography.size_body_small),
            text_color=colors.text_secondary
        )
        subtitle_label.pack(pady=(0, spacing.xl))
        
        # === 表單區域 ===
        form_frame = ctk.CTkFrame(
            card,
            fg_color="transparent"
        )
        form_frame.pack(padx=spacing.xl, fill="x")
        
        # 帳號輸入
        account_label = ctk.CTkLabel(
            form_frame,
            text="帳號",
            font=get_font_config(typography.size_body),
            text_color=colors.text_secondary,
            anchor="w"
        )
        account_label.pack(fill="x", pady=(0, spacing.xs))
        
        self.account_entry = ctk.CTkEntry(
            form_frame,
            **default_styles.INPUT,
            height=component_sizes.input_height_lg,
            font=get_font_config(typography.size_body),
            placeholder_text="請輸入員工帳號"
        )
        self.account_entry.pack(fill="x", pady=(0, spacing.md))
        
        # 密碼輸入
        password_label = ctk.CTkLabel(
            form_frame,
            text="密碼",
            font=get_font_config(typography.size_body),
            text_color=colors.text_secondary,
            anchor="w"
        )
        password_label.pack(fill="x", pady=(0, spacing.xs))
        
        # 密碼輸入框 + 顯示/隱藏按鈕容器
        password_container = ctk.CTkFrame(
            form_frame,
            fg_color="transparent"
        )
        password_container.pack(fill="x", pady=(0, spacing.md))
        
        self.password_entry = ctk.CTkEntry(
            password_container,
            **default_styles.INPUT,
            height=component_sizes.input_height_lg,
            font=get_font_config(typography.size_body),
            show="●",
            placeholder_text="請輸入密碼"
        )
        self.password_entry.pack(side="left", fill="x", expand=True)
        
        # 密碼顯示/隱藏切換按鈕
        self.password_toggle_btn = ctk.CTkButton(
            password_container,
            text="👁",
            width=component_sizes.button_height_lg,
            height=component_sizes.button_height_lg,
            fg_color=colors.background_secondary,
            hover_color=colors.background_tertiary,
            text_color=colors.text_secondary,
            corner_radius=border_radius.md,
            font=get_font_config(16),
            command=self._toggle_password_visibility
        )
        self.password_toggle_btn.pack(side="left", padx=(spacing.xs, 0))
        
        # 記住我核取框
        self.remember_var = ctk.BooleanVar(value=False)
        self.remember_checkbox = ctk.CTkCheckBox(
            form_frame,
            text="記住我",
            variable=self.remember_var,
            font=get_font_config(typography.size_body_small),
            text_color=colors.text_secondary,
            fg_color=colors.primary,
            hover_color=colors.primary_hover,
            border_color=colors.border_medium,
            corner_radius=border_radius.sm
        )
        self.remember_checkbox.pack(anchor="w", pady=(0, spacing.lg))
        
        # 登入按鈕
        self.login_button = ctk.CTkButton(
            form_frame,
            **default_styles.PRIMARY_BUTTON,
            text="登入",
            height=component_sizes.button_height_lg,
            font=get_font_config(typography.size_body, typography.weight_bold),
            command=self._handle_login
        )
        self.login_button.pack(fill="x", pady=(0, spacing.md))
        
        # === 底部版本號 ===
        from src.core import VERSION
        version_label = ctk.CTkLabel(
            card,
            text=f"v{VERSION}",
            font=get_font_config(typography.size_caption),
            text_color=colors.text_tertiary
        )
        version_label.pack(pady=(spacing.lg, 0))
        
        # === 鍵盤快捷鍵 ===
        self.account_entry.bind("<Return>", lambda e: self.password_entry.focus())
        self.password_entry.bind("<Return>", lambda e: self._handle_login())
        
        # 初始焦點
        self.account_entry.focus()
    
    def _toggle_password_visibility(self):
        """切換密碼顯示/隱藏"""
        self.password_visible = not self.password_visible
        
        if self.password_visible:
            self.password_entry.configure(show="")
            self.password_toggle_btn.configure(text="🙈")
        else:
            self.password_entry.configure(show="●")
            self.password_toggle_btn.configure(text="👁")
    
    def _handle_login(self):
        """處理登入"""
        username = self.account_entry.get().strip()
        password = self.password_entry.get().strip()
        remember_me = self.remember_var.get()
        
        if not username or not password:
            return
        
        self.on_login(username, password, remember_me)
    
    def set_loading(self, loading: bool):
        """設定載入狀態"""
        if loading:
            self.login_button.configure(state="disabled", text="登入中...")
            self.account_entry.configure(state="disabled")
            self.password_entry.configure(state="disabled")
            self.password_toggle_btn.configure(state="disabled")
            self.remember_checkbox.configure(state="disabled")
        else:
            self.login_button.configure(state="normal", text="登入")
            self.account_entry.configure(state="normal")
            self.password_entry.configure(state="normal")
            self.password_toggle_btn.configure(state="normal")
            self.remember_checkbox.configure(state="normal")
    
    def set_account(self, account: str):
        """設置帳號 (用於記住我功能)"""
        self.account_entry.delete(0, "end")
        self.account_entry.insert(0, account)
    
    def set_password(self, password: str):
        """設置密碼 (用於記住我功能)"""
        self.password_entry.delete(0, "end")
        self.password_entry.insert(0, password)
    
    def set_remember_me(self, remember: bool):
        """設置記住我狀態"""
        self.remember_var.set(remember)
