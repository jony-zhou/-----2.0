"""主視窗"""
import customtkinter as ctk
from typing import Optional
import threading
import logging
import sys
from pathlib import Path

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.models import OvertimeReport
from src.services import AuthService, DataService, ExportService, UpdateService
from src.core import OvertimeCalculator, VERSION
from src.config import Settings
from ui.components import LoginFrame, ReportFrame, StatusFrame, show_update_dialog

logger = logging.getLogger(__name__)


class MainWindow(ctk.CTk):
    """主視窗"""
    
    def __init__(self):
        super().__init__()
        
        # 設定視窗
        self.title(f"TECO SSP 加班時數計算器 v{VERSION}")
        self.geometry("900x700")
        
        # 設定圖示 (優先使用 .ico 格式)
        icon_ico = Path(__file__).parent.parent / "assets" / "icon.ico"
        icon_png = Path(__file__).parent.parent / "assets" / "icon.png"
        
        # 嘗試載入圖示
        try:
            if icon_ico.exists():
                # Windows 優先使用 .ico
                self.iconbitmap(str(icon_ico))
            elif icon_png.exists():
                # 備用方案使用 PNG
                from PIL import Image, ImageTk
                icon_image = Image.open(str(icon_png))
                photo = ImageTk.PhotoImage(icon_image)
                self.iconphoto(True, photo)
                # 保持引用避免被垃圾回收
                self._icon_photo = photo
        except Exception as e:
            # 圖示載入失敗不影響程式運行
            logger.debug(f"圖示載入失敗: {e}")
        
        # 初始化服務
        self.settings = Settings()
        self.auth_service: Optional[AuthService] = None
        self.data_service: Optional[DataService] = None
        self.export_service = ExportService(self.settings)
        self.calculator = OvertimeCalculator(self.settings)
        
        # 資料
        self.current_report: Optional[OvertimeReport] = None
        
        # 設定主題
        ctk.set_appearance_mode("dark")
        ctk.set_default_color_theme("blue")
        
        # 建立 UI
        self._create_ui()
        
        # 啟動後檢查更新 (非阻塞式,不影響正常使用)
        self.after(1000, self._check_for_updates)
    
    def _create_ui(self):
        """建立使用者介面"""
        # 主容器
        self.main_container = ctk.CTkFrame(self)
        self.main_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 標題
        self.title_label = ctk.CTkLabel(
            self.main_container,
            text="TECO SSP 加班時數計算器",
            font=ctk.CTkFont(size=24, weight="bold")
        )
        self.title_label.pack(pady=20)
        
        # 登入框
        self.login_frame = LoginFrame(self.main_container, self.on_login)
        self.login_frame.pack(fill="x", padx=20, pady=10)
        
        # 狀態框
        self.status_frame = StatusFrame(self.main_container)
        self.status_frame.pack(fill="x", padx=20, pady=10)
        
        # 報表框 (初始隱藏)
        self.report_frame = ReportFrame(
            self.main_container,
            on_export=self.on_export,
            on_refresh=self.on_refresh
        )
        
        # 底部容器 (用於放置登出按鈕)
        self.bottom_container = ctk.CTkFrame(self.main_container, fg_color="transparent")
        
        # 登出按鈕 (初始隱藏,放在底部容器中)
        self.logout_button = ctk.CTkButton(
            self.bottom_container,
            text="🚪 登出",
            command=self.on_logout,
            width=150,
            height=40,
            fg_color="#e74c3c",
            hover_color="#c0392b",
            font=ctk.CTkFont(size=14)
        )
        self.logout_button.pack(pady=15)
    
    def on_login(self, username: str, password: str):
        """登入處理"""
        self.login_frame.set_loading(True)
        self.status_frame.show_status("正在登入...", "info")
        
        # 在背景執行登入
        def login_thread():
            try:
                # 建立認證服務
                self.auth_service = AuthService(self.settings)
                
                # 執行登入
                success = self.auth_service.login(username, password)
                
                # 在主執行緒更新 UI
                self.after(0, self._on_login_complete, success)
                
            except Exception as e:
                logger.error(f"登入錯誤: {e}", exc_info=True)
                self.after(0, self._on_login_complete, False, str(e))
        
        thread = threading.Thread(target=login_thread, daemon=True)
        thread.start()
    
    def _on_login_complete(self, success: bool, error: Optional[str] = None):
        """登入完成回調"""
        self.login_frame.set_loading(False)
        
        if success:
            self.status_frame.show_status("✓ 登入成功", "success")
            self.login_frame.pack_forget()  # 隱藏登入框
            
            # 建立資料服務
            self.data_service = DataService(
                self.auth_service.get_session(),
                self.settings
            )
            
            # 自動開始抓取資料
            self.fetch_data()
        else:
            error_msg = f"✗ 登入失敗: {error}" if error else "✗ 登入失敗,請檢查帳號密碼"
            self.status_frame.show_status(error_msg, "error")
    
    def fetch_data(self):
        """抓取出勤資料"""
        self.status_frame.show_status("正在抓取出勤資料...", "info")
        
        def fetch_thread():
            try:
                # 抓取資料
                raw_records = self.data_service.get_attendance_data()
                
                if not raw_records:
                    self.after(0, self._on_fetch_complete, None, "沒有找到出勤記錄")
                    return
                
                # 計算加班時數
                report = self.calculator.calculate_overtime(raw_records)
                
                # 在主執行緒更新 UI
                self.after(0, self._on_fetch_complete, report)
                
            except Exception as e:
                logger.error(f"抓取資料錯誤: {e}", exc_info=True)
                self.after(0, self._on_fetch_complete, None, str(e))
        
        thread = threading.Thread(target=fetch_thread, daemon=True)
        thread.start()
    
    def _on_fetch_complete(self, report: Optional[OvertimeReport], error: Optional[str] = None):
        """抓取資料完成回調"""
        if report and report.records:
            self.current_report = report
            self.status_frame.show_status(
                f"✓ 成功取得 {report.total_days} 筆記錄", 
                "success"
            )
            
            # 顯示報表
            self.report_frame.pack(fill="both", expand=True, padx=20, pady=(10, 5))
            self.report_frame.display_report(report)
            
            # 顯示登出按鈕在最下方
            self.bottom_container.pack(fill="x", padx=20, pady=(0, 10))
        else:
            error_msg = f"✗ {error}" if error else "✗ 抓取資料失敗"
            self.status_frame.show_status(error_msg, "error")
    
    def on_export(self):
        """匯出處理"""
        if not self.current_report:
            self.status_frame.show_status("沒有可匯出的資料", "error")
            return
        
        self.status_frame.show_status("正在匯出...", "info")
        
        def export_thread():
            try:
                filename = self.export_service.export_to_excel(self.current_report)
                
                if filename:
                    self.after(0, lambda: self.status_frame.show_status(
                        f"✓ 已匯出至: {filename}", 
                        "success"
                    ))
                else:
                    self.after(0, lambda: self.status_frame.show_status(
                        "✗ 匯出失敗", 
                        "error"
                    ))
                    
            except Exception as e:
                logger.error(f"匯出錯誤: {e}", exc_info=True)
                self.after(0, lambda: self.status_frame.show_status(
                    f"✗ 匯出錯誤: {e}", 
                    "error"
                ))
        
        thread = threading.Thread(target=export_thread, daemon=True)
        thread.start()
    
    def on_refresh(self):
        """重新整理資料"""
        if self.data_service:
            self.report_frame.pack_forget()
            self.bottom_container.pack_forget()
            self.fetch_data()
        else:
            self.status_frame.show_status("請先登入", "error")
    
    def on_logout(self):
        """登出處理"""
        # 清理資料
        self.auth_service = None
        self.data_service = None
        self.current_report = None
        
        # 重置 UI
        self.report_frame.pack_forget()
        self.bottom_container.pack_forget()
        self.login_frame.pack(fill="x", padx=20, pady=10)
        
        # 清空登入框的密碼欄位
        self.login_frame.password_entry.delete(0, 'end')
        
        # 顯示訊息
        self.status_frame.show_status("已登出", "info")
    
    def _check_for_updates(self):
        """背景檢查版本更新"""
        logger.info("開始檢查應用程式更新...")
        
        def check_thread():
            try:
                update_service = UpdateService()
                update_info = update_service.check_for_updates(timeout=5)
                
                # 在主執行緒顯示對話框
                if update_info and update_info.get('has_update'):
                    logger.info(f"發現新版本 {update_info.get('latest_version')},顯示更新對話框")
                    self.after(0, lambda: show_update_dialog(self, update_info))
                else:
                    logger.info("目前已是最新版本")
                
            except Exception as e:
                # 更新檢查失敗不影響主程式
                logger.warning(f"版本更新檢查失敗: {e}")
        
        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
