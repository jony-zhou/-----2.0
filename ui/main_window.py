"""
主視窗 - 專業 UI/UX 設計
遵循 SOLID、DRY、KISS、YAGNI 原則
"""
import customtkinter as ctk
from typing import Optional
import threading
import logging
import sys
from pathlib import Path
from datetime import datetime

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import OvertimeReport
from src.services import AuthService, DataService, ExportService, UpdateService
from src.services.credential_manager import CredentialManager
from src.core import OvertimeCalculator, VERSION
from src.config import Settings
from ui.components import LoginFrame, ReportFrame, StatusFrame, show_update_dialog
from ui.components.statistics_card import StatisticsCard
from ui.config import (
    colors, typography, spacing, border_radius,
    default_styles, get_font_config
)

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """
    主視窗
    
    職責:
    - 管理整體 UI 布局
    - 協調各個元件之間的互動
    - 處理使用者操作流程
    """
    
    def __init__(self):
        super().__init__()
        
        # 初始化屬性
        self.version = VERSION
        self._init_window_settings()
        self._init_services()
        self._init_data()
        
        # 建立 UI
        self._create_ui()
        
        # 啟動後檢查更新 (非阻塞式)
        self.after(1000, self._check_for_updates)
    
    def _init_window_settings(self):
        """初始化視窗設定 (Single Responsibility)"""
        self.title(f"TECO SSP 加班助手 v{self.version}")
        self.geometry("1200x800")
        
        # 設定主題
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 設定圖示
        self._load_app_icon()
    
    def _load_app_icon(self):
        """載入應用程式圖示"""
        icon_ico = Path(__file__).parent.parent / "assets" / "icon.ico"
        icon_png = Path(__file__).parent.parent / "assets" / "icon.png"
        
        try:
            if icon_ico.exists():
                self.iconbitmap(str(icon_ico))
            elif icon_png.exists():
                # iconphoto 需要使用 PhotoImage (Tkinter 原生)
                from PIL import Image, ImageTk
                icon_image = Image.open(str(icon_png))
                photo = ImageTk.PhotoImage(icon_image)
                self.iconphoto(True, photo)
                self._icon_photo = photo  # 保持引用
        except Exception as e:
            logger.debug(f"圖示載入失敗: {e}")
    
    def _init_services(self):
        """初始化服務 (Dependency Injection 準備)"""
        self.settings = Settings()
        self.credential_manager = CredentialManager()
        self.auth_service: Optional[AuthService] = None
        self.data_service: Optional[DataService] = None
        self.export_service = ExportService(self.settings)
        self.calculator = OvertimeCalculator(self.settings)
    
    def _init_data(self):
        """初始化資料"""
        self.current_report: Optional[OvertimeReport] = None
        self._login_username: Optional[str] = None
        self._login_password: Optional[str] = None
        self._remember_me: bool = False
    
    def _create_ui(self):
        """建立使用者介面"""
        # === 主容器 ===
        self.main_container = ctk.CTkFrame(
            self, 
            fg_color=colors.background_primary
        )
        self.main_container.pack(fill="both", expand=True)
        
        # === 登入頁面 (初始顯示) ===
        self._create_login_page()
        
        # 載入儲存的憑證 (如果有)
        self._load_saved_credentials()
        
        # === 主頁面 (初始隱藏) ===
        self._create_main_page()
    
    def _create_login_page(self):
        """建立登入頁面 (DRY - 單一方法負責登入 UI)"""
        self.login_frame = LoginFrame(self.main_container, self.on_login)
        self.login_frame.pack(fill="both", expand=True)
    
    def _load_saved_credentials(self):
        """
        載入儲存的憑證
        
        OWASP 考量:
        - 僅在使用者之前選擇「記住我」時才自動填入
        - 不自動登入,仅填入欄位
        """
        if self.credential_manager.has_saved_credentials():
            username, password = self.credential_manager.load_credentials()
            
            if username:
                self.login_frame.set_account(username)
                self.login_frame.set_remember_me(True)
                
                if password:
                    self.login_frame.set_password(password)
                    logger.info("已載入儲存的憑證")
    
    def _create_main_page(self):
        """建立主頁面 (DRY - 單一方法負責主頁面 UI)"""
        self.main_content = ctk.CTkFrame(
            self.main_container, 
            fg_color=colors.background_primary
        )
        
        # 建立各個區塊
        self._create_navbar()
        self._create_status_section()
        self._create_statistics_section()
        self._create_report_section()
        self._create_footer()
    
    def _create_navbar(self):
        """建立頂部導覽列"""
        navbar = ctk.CTkFrame(
            self.main_content,
            fg_color=colors.background_secondary,
            height=70,
            corner_radius=0
        )
        navbar.pack(fill="x")
        navbar.pack_propagate(False)
        
        # 導覽列內容容器
        content = ctk.CTkFrame(navbar, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=spacing.lg, pady=spacing.md)
        
        # 左側: Logo + 標題
        self._create_navbar_left(content)
        
        # 右側: 使用者資訊 + 登出按鈕
        self._create_navbar_right(content)
    
    def _create_navbar_left(self, parent):
        """建立導覽列左側 (Logo + 標題)"""
        left_section = ctk.CTkFrame(parent, fg_color="transparent")
        left_section.pack(side="left")
        
        # Logo (使用 assets 圖示)
        try:
            from PIL import Image
            from pathlib import Path
            
            # 取得圖示路徑
            icon_path = Path(__file__).parent.parent / "assets" / "icon.png"
            
            if icon_path.exists():
                # 載入並使用 CTkImage (支援高 DPI)
                img = Image.open(str(icon_path))
                ctk_image = ctk.CTkImage(
                    light_image=img,
                    dark_image=img,
                    size=(32, 32)
                )
                
                logo = ctk.CTkLabel(
                    left_section,
                    image=ctk_image,
                    text=""
                )
                logo.pack(side="left", padx=(0, spacing.sm))
            else:
                # 降級方案: 使用 emoji
                logo = ctk.CTkLabel(
                    left_section,
                    text="⏰",
                    font=get_font_config(28),
                    text_color=colors.primary
                )
                logo.pack(side="left", padx=(0, spacing.sm))
        except Exception as e:
            logger.debug(f"載入導覽列圖示失敗: {e}")
            # 降級方案: 使用 emoji
            logo = ctk.CTkLabel(
                left_section,
                text="⏰",
                font=get_font_config(28),
                text_color=colors.primary
            )
            logo.pack(side="left", padx=(0, spacing.sm))
        
        # 標題
        title = ctk.CTkLabel(
            left_section,
            text="TECO SSP 加班助手",
            font=get_font_config(typography.size_h3, typography.weight_bold),
            text_color=colors.text_primary
        )
        title.pack(side="left")
    
    def _create_navbar_right(self, parent):
        """建立導覽列右側 (使用者資訊 + 登出)"""
        right_section = ctk.CTkFrame(parent, fg_color="transparent")
        right_section.pack(side="right")
        
        # 使用者標籤
        self.user_label = ctk.CTkLabel(
            right_section,
            text="👤 使用者",
            font=get_font_config(typography.size_body),
            text_color=colors.text_secondary
        )
        self.user_label.pack(side="left", padx=(0, spacing.md))
        
        # 登出按鈕
        self.logout_button = ctk.CTkButton(
            right_section,
            **default_styles.ERROR_BUTTON,
            text="🚪 登出",
            width=100,
            height=36,
            font=get_font_config(typography.size_body),
            command=self.on_logout
        )
        self.logout_button.pack(side="left")
    
    def _create_status_section(self):
        """建立狀態區域"""
        self.status_frame = StatusFrame(self.main_content)
        self.status_frame.pack(fill="x", padx=spacing.lg, pady=(spacing.md, 0))
    
    def _create_statistics_section(self):
        """建立統計卡片區域"""
        self.stats_container = ctk.CTkFrame(
            self.main_content, 
            fg_color="transparent"
        )
        
        # Grid 布局 (4 欄)
        self.stats_container.grid_columnconfigure((0, 1, 2, 3), weight=1)
        
        # 建立 4 張統計卡片
        self._create_statistics_cards()
    
    def _create_statistics_cards(self):
        """建立統計卡片 (DRY - 避免重複代碼)"""
        # 卡片配置 (資料驅動設計)
        cards_config = [
            {
                "attr": "card_total_days",
                "title": "總筆數",
                "value": "0",
                "icon": "📅",
                "color": colors.primary,
                "column": 0
            },
            {
                "attr": "card_total_hours",
                "title": "總加班時數",
                "value": "0.0 小時",
                "icon": "⏱️",
                "color": colors.secondary,
                "column": 1
            },
            {
                "attr": "card_avg_hours",
                "title": "平均加班時數",
                "value": "0.0 小時",
                "icon": "📊",
                "color": colors.info,
                "column": 2
            },
            {
                "attr": "card_max_hours",
                "title": "最高加班時數",
                "value": "0.0 小時",
                "icon": "🔥",
                "color": colors.warning,
                "column": 3
            }
        ]
        
        # 動態建立卡片
        for config in cards_config:
            card = StatisticsCard(
                self.stats_container,
                title=config["title"],
                value=config["value"],
                icon=config["icon"],
                color=config["color"]
            )
            card.grid(
                row=0, 
                column=config["column"], 
                padx=spacing.sm, 
                pady=spacing.md, 
                sticky="ew"
            )
            setattr(self, config["attr"], card)
    
    def _create_report_section(self):
        """建立報表區域"""
        self.report_frame = ReportFrame(
            self.main_content,
            on_export=self.on_export,
            on_refresh=self.on_refresh
        )
    
    def _create_footer(self):
        """建立底部資訊列"""
        footer = ctk.CTkFrame(
            self.main_content,
            fg_color=colors.background_secondary,
            height=40,
            corner_radius=0
        )
        footer.pack(fill="x", side="bottom")
        footer.pack_propagate(False)
        
        # Footer 內容
        content = ctk.CTkFrame(footer, fg_color="transparent")
        content.pack(fill="both", expand=True, padx=spacing.lg)
        
        # 左側: 更新時間
        self.update_time_label = ctk.CTkLabel(
            content,
            text="最後更新: --",
            font=get_font_config(typography.size_caption),
            text_color=colors.text_tertiary
        )
        self.update_time_label.pack(side="left")
        
        # 右側: 版本號
        version_label = ctk.CTkLabel(
            content,
            text=f"v{self.version}",
            font=get_font_config(typography.size_caption),
            text_color=colors.text_tertiary
        )
        version_label.pack(side="right")
    
    # === 事件處理方法 ===
    
    def on_login(self, username: str, password: str, remember_me: bool = False):
        """
        登入處理
        
        遵循 OWASP 最佳實踐:
        - 不在 log 中記錄密碼
        - 使用安全的認證服務
        """
        self.login_frame.set_loading(True)
        
        # 儲存登入資訊 (密碼僅在記住我時儲存)
        self._login_username = username
        self._remember_me = remember_me
        if remember_me:
            self._login_password = password  # TODO: Task 5 - 改用 keyring 加密儲存
        
        # 背景執行登入 (避免阻塞 UI)
        self._execute_in_background(
            self._login_task,
            args=(username, password),
            callback=self._on_login_complete
        )
    
    def _login_task(self, username: str, password: str) -> tuple[bool, Optional[str]]:
        """
        登入任務 (背景執行)
        
        Returns:
            tuple: (成功狀態, 錯誤訊息)
        """
        try:
            self.auth_service = AuthService(self.settings)
            success = self.auth_service.login(username, password)
            return (success, None)
        except Exception as e:
            logger.error(f"登入錯誤: {e}", exc_info=True)
            return (False, str(e))
    
    def _on_login_complete(self, result: tuple[bool, Optional[str]]):
        """登入完成回調"""
        success, error = result
        self.login_frame.set_loading(False)
        
        if success:
            # 儲存憑證 (如果選擇記住我)
            if self._remember_me:
                self.credential_manager.save_credentials(
                    self._login_username,
                    self._login_password
                )
            else:
                # 清除之前儲存的憑證
                self.credential_manager.clear_credentials()
            
            self._switch_to_main_page()
            self._start_data_fetch()
        else:
            self._show_login_error(error)
    
    def _switch_to_main_page(self):
        """切換到主頁面 (DRY - 統一的頁面切換邏輯)"""
        # 隱藏登入頁面
        self.login_frame.pack_forget()
        
        # 顯示主頁面
        self.main_content.pack(fill="both", expand=True)
        
        # 更新使用者資訊
        if self._login_username:
            self.user_label.configure(text=f"👤 {self._login_username}")
    
    def _start_data_fetch(self):
        """開始資料抓取"""
        # 建立資料服務
        self.data_service = DataService(
            self.auth_service.get_session(),
            self.settings
        )
        
        # 抓取資料
        self.fetch_data()
    
    def _show_login_error(self, error: Optional[str]):
        """顯示登入錯誤 (OWASP - 不洩漏過多系統資訊)"""
        import tkinter.messagebox as mb
        error_msg = "登入失敗,請檢查帳號密碼" if not error else f"登入失敗: {error}"
        mb.showerror("登入失敗", error_msg)
    
    def fetch_data(self):
        """抓取出勤資料"""
        self.status_frame.show_status("正在抓取出勤資料...", "info")
        
        self._execute_in_background(
            self._fetch_data_task,
            callback=self._on_fetch_complete
        )
    
    def _fetch_data_task(self) -> tuple[Optional[OvertimeReport], Optional[str]]:
        """
        資料抓取任務 (背景執行)
        
        Returns:
            tuple: (報表資料, 錯誤訊息)
        """
        try:
            raw_records = self.data_service.get_attendance_data()
            
            if not raw_records:
                return (None, "沒有找到出勤記錄")
            
            report = self.calculator.calculate_overtime(raw_records)
            return (report, None)
            
        except Exception as e:
            logger.error(f"抓取資料錯誤: {e}", exc_info=True)
            return (None, str(e))
    
    def _on_fetch_complete(self, result: tuple[Optional[OvertimeReport], Optional[str]]):
        """資料抓取完成回調"""
        report, error = result
        
        if report and report.records:
            self._handle_successful_fetch(report)
        else:
            self._handle_failed_fetch(error)
    
    def _handle_successful_fetch(self, report: OvertimeReport):
        """處理成功的資料抓取 (Single Responsibility)"""
        self.current_report = report
        
        # 更新狀態
        self.status_frame.show_status(
            f"✓ 成功取得 {report.total_days} 筆記錄",
            "success"
        )
        
        # 更新統計卡片
        self._update_statistics_cards(report)
        
        # 顯示報表
        self._show_report(report)
        
        # 更新時間戳記
        self._update_timestamp()
    
    def _update_statistics_cards(self, report: OvertimeReport):
        """
        更新統計卡片
        
        使用正確的屬性名稱:
        - total_overtime_hours (不是 total_hours)
        - max_overtime_hours
        - average_overtime_hours
        """
        # 總筆數
        self.card_total_days.update_value(str(report.total_days))
        
        # 總加班時數
        self.card_total_hours.update_value(
            f"{report.total_overtime_hours:.1f} 小時"
        )
        
        # 平均加班時數
        self.card_avg_hours.update_value(
            f"{report.average_overtime_hours:.1f} 小時"
        )
        
        # 最高加班時數
        self.card_max_hours.update_value(
            f"{report.max_overtime_hours:.1f} 小時"
        )
    
    def _show_report(self, report: OvertimeReport):
        """顯示報表"""
        # 顯示統計卡片容器
        self.stats_container.pack(
            fill="x", 
            padx=spacing.lg, 
            pady=(spacing.sm, 0)
        )
        
        # 顯示報表框架
        self.report_frame.pack(
            fill="both", 
            expand=True, 
            padx=spacing.lg, 
            pady=spacing.md
        )
        self.report_frame.display_report(report)
    
    def _update_timestamp(self):
        """更新時間戳記"""
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.update_time_label.configure(text=f"最後更新: {current_time}")
    
    def _handle_failed_fetch(self, error: Optional[str]):
        """處理失敗的資料抓取"""
        error_msg = f"✗ {error}" if error else "✗ 抓取資料失敗"
        self.status_frame.show_status(error_msg, "error")
    
    def on_export(self):
        """匯出處理"""
        if not self.current_report:
            self.status_frame.show_status("沒有可匯出的資料", "error")
            return
        
        self.status_frame.show_status("正在匯出...", "info")
        
        self._execute_in_background(
            self._export_task,
            callback=self._on_export_complete
        )
    
    def _export_task(self) -> tuple[Optional[str], Optional[str]]:
        """
        匯出任務 (背景執行)
        
        Returns:
            tuple: (檔案名稱, 錯誤訊息)
        """
        try:
            filename = self.export_service.export_to_excel(self.current_report)
            return (filename, None)
        except Exception as e:
            logger.error(f"匯出錯誤: {e}", exc_info=True)
            return (None, str(e))
    
    def _on_export_complete(self, result: tuple[Optional[str], Optional[str]]):
        """匯出完成回調"""
        filename, error = result
        
        if filename:
            self.status_frame.show_status(f"✓ 已匯出至: {filename}", "success")
        else:
            error_msg = f"✗ 匯出錯誤: {error}" if error else "✗ 匯出失敗"
            self.status_frame.show_status(error_msg, "error")
    
    def on_refresh(self):
        """重新整理資料"""
        if not self.data_service:
            self.status_frame.show_status("請先登入", "error")
            return
        
        # 隱藏報表 (準備重新載入)
        self.report_frame.pack_forget()
        self.stats_container.pack_forget()
        
        # 重新抓取
        self.fetch_data()
    
    def on_logout(self):
        """
        登出處理
        
        OWASP 最佳實踐:
        - 清除所有敏感資料
        - 重置 UI 狀態
        """
        # 清除服務和資料
        self._clear_sensitive_data()
        
        # 重置 UI
        self._switch_to_login_page()
        
        # 顯示訊息
        self.status_frame.show_status("已登出", "info")
    
    def _clear_sensitive_data(self):
        """
        清除敏感資料 (OWASP)
        
        注意: 不清除儲存的憑證,僅清除記憶體中的資料
        使用者下次登入時仍可使用記住我功能
        """
        self.auth_service = None
        self.data_service = None
        self.current_report = None
        self._login_password = None  # 清除密碼
    
    def _switch_to_login_page(self):
        """切換到登入頁面"""
        # 隱藏主頁面
        self.main_content.pack_forget()
        
        # 隱藏報表和統計
        self.report_frame.pack_forget()
        self.stats_container.pack_forget()
        
        # 顯示登入頁面
        self.login_frame.pack(fill="both", expand=True)
        
        # 清空密碼欄位 (OWASP)
        if hasattr(self.login_frame, 'password_entry'):
            self.login_frame.password_entry.delete(0, 'end')
    
    def _check_for_updates(self):
        """背景檢查版本更新"""
        logger.info("開始檢查應用程式更新...")
        
        self._execute_in_background(
            self._check_update_task,
            callback=self._on_update_check_complete
        )
    
    def _check_update_task(self) -> Optional[dict]:
        """
        更新檢查任務
        
        Returns:
            dict: 更新資訊 或 None
        """
        try:
            update_service = UpdateService()
            return update_service.check_for_updates(timeout=5)
        except Exception as e:
            logger.warning(f"版本更新檢查失敗: {e}")
            return None
    
    def _on_update_check_complete(self, update_info: Optional[dict]):
        """更新檢查完成回調"""
        if update_info and update_info.get('has_update'):
            logger.info(f"發現新版本 {update_info.get('latest_version')}")
            show_update_dialog(self, update_info)
        else:
            logger.info("目前已是最新版本")
    
    # === 工具方法 ===
    
    def _execute_in_background(
        self, 
        task: callable, 
        args: tuple = (), 
        callback: Optional[callable] = None
    ):
        """
        在背景執行任務 (DRY - 統一的背景任務執行模式)
        
        Args:
            task: 要執行的任務函式
            args: 任務參數
            callback: 完成後的回調函式
        """
        def thread_func():
            result = task(*args)
            if callback:
                self.after(0, callback, result)
        
        thread = threading.Thread(target=thread_func, daemon=True)
        thread.start()
