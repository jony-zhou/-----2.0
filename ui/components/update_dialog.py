"""
應用程式更新通知對話框
"""
import customtkinter as ctk
import webbrowser
from typing import Dict, Any, Optional
import logging

logger = logging.getLogger(__name__)


class UpdateDialog(ctk.CTkToplevel):
    """
    更新通知對話框
    
    顯示新版本資訊並提供下載連結
    遵循 KISS 原則: 簡單明瞭的介面
    """
    
    def __init__(
        self, 
        parent: ctk.CTk,
        update_info: Dict[str, Any]
    ):
        """
        初始化更新對話框
        
        Args:
            parent: 父視窗
            update_info: 更新資訊字典
        """
        super().__init__(parent)
        
        self.update_info = update_info
        
        # 視窗設定
        self.title("發現新版本")
        self.geometry("500x400")
        self.resizable(False, False)
        
        # 置中顯示
        self.transient(parent)
        self.grab_set()
        
        self._create_widgets()
        
        # 聚焦到此視窗
        self.focus()
    
    def _create_widgets(self) -> None:
        """建立 UI 元件"""
        # 主框架
        main_frame = ctk.CTkFrame(self)
        main_frame.pack(fill="both", expand=True, padx=20, pady=20)
        
        # 標題
        title_label = ctk.CTkLabel(
            main_frame,
            text="🎉 發現新版本",
            font=ctk.CTkFont(size=20, weight="bold")
        )
        title_label.pack(pady=(0, 10))
        
        # 版本資訊框架
        version_frame = ctk.CTkFrame(main_frame)
        version_frame.pack(fill="x", pady=10)
        
        current_ver = self.update_info.get('current_version', 'Unknown')
        latest_ver = self.update_info.get('latest_version', 'Unknown')
        
        current_label = ctk.CTkLabel(
            version_frame,
            text=f"目前版本: {current_ver}",
            font=ctk.CTkFont(size=14)
        )
        current_label.pack(pady=5)
        
        arrow_label = ctk.CTkLabel(
            version_frame,
            text="↓",
            font=ctk.CTkFont(size=16)
        )
        arrow_label.pack()
        
        latest_label = ctk.CTkLabel(
            version_frame,
            text=f"最新版本: {latest_ver}",
            font=ctk.CTkFont(size=14, weight="bold"),
            text_color="#4CAF50"
        )
        latest_label.pack(pady=5)
        
        # 發布日期
        published_at = self.update_info.get('published_at', '')
        if published_at:
            try:
                from datetime import datetime
                pub_date = datetime.fromisoformat(published_at.replace('Z', '+00:00'))
                date_str = pub_date.strftime('%Y年%m月%d日')
                date_label = ctk.CTkLabel(
                    version_frame,
                    text=f"發布時間: {date_str}",
                    font=ctk.CTkFont(size=12),
                    text_color="gray"
                )
                date_label.pack(pady=(0, 5))
            except Exception:
                pass
        
        # 更新說明
        notes_label = ctk.CTkLabel(
            main_frame,
            text="更新內容:",
            font=ctk.CTkFont(size=14, weight="bold")
        )
        notes_label.pack(anchor="w", pady=(10, 5))
        
        # 更新內容文字框
        notes_text = ctk.CTkTextbox(
            main_frame,
            height=120,
            font=ctk.CTkFont(size=12)
        )
        notes_text.pack(fill="both", expand=True, pady=(0, 10))
        
        release_notes = self.update_info.get('release_notes', '無更新說明')
        notes_text.insert("1.0", release_notes)
        notes_text.configure(state="disabled")  # 唯讀
        
        # 下載連結顯示
        download_url = self.update_info.get('download_url', '')
        release_url = self.update_info.get('release_url', '')
        
        if download_url or release_url:
            link_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
            link_frame.pack(fill="x", pady=(0, 10))
            
            link_label = ctk.CTkLabel(
                link_frame,
                text="📥 下載連結:",
                font=ctk.CTkFont(size=12),
                anchor="w"
            )
            link_label.pack(side="left", padx=(0, 5))
            
            # 可點擊的超連結
            url_to_display = download_url if download_url else release_url
            # 縮短顯示的 URL
            display_url = url_to_display
            if len(display_url) > 50:
                display_url = display_url[:47] + "..."
            
            url_button = ctk.CTkButton(
                link_frame,
                text=display_url,
                command=lambda: self._open_url(url_to_display),
                font=ctk.CTkFont(size=11, underline=True),
                fg_color="transparent",
                text_color="#2196F3",
                hover_color="#E3F2FD",
                cursor="hand2",
                anchor="w"
            )
            url_button.pack(side="left", fill="x", expand=True)
        
        # 按鈕框架
        button_frame = ctk.CTkFrame(main_frame, fg_color="transparent")
        button_frame.pack(fill="x", pady=(10, 0))
        
        # 下載按鈕
        download_btn = ctk.CTkButton(
            button_frame,
            text="前往下載頁面",
            command=self._on_download,
            font=ctk.CTkFont(size=14, weight="bold"),
            height=40,
            fg_color="#4CAF50",
            hover_color="#45a049"
        )
        download_btn.pack(side="left", fill="x", expand=True, padx=(0, 5))
        
        # 稍後提醒按鈕
        later_btn = ctk.CTkButton(
            button_frame,
            text="稍後提醒",
            command=self._on_later,
            font=ctk.CTkFont(size=14),
            height=40,
            fg_color="gray",
            hover_color="#666666"
        )
        later_btn.pack(side="right", fill="x", expand=True, padx=(5, 0))
    
    def _open_url(self, url: str) -> None:
        """開啟 URL"""
        try:
            logger.info(f"開啟連結: {url}")
            webbrowser.open(url)
        except Exception as e:
            logger.error(f"開啟瀏覽器失敗: {e}")
    
    def _on_download(self) -> None:
        """處理下載按鈕點擊"""
        download_url = self.update_info.get('download_url', '')
        
        if download_url:
            try:
                logger.info(f"開啟下載頁面: {download_url}")
                webbrowser.open(download_url)
            except Exception as e:
                logger.error(f"開啟瀏覽器失敗: {e}")
        
        self.destroy()
    
    def _on_later(self) -> None:
        """處理稍後提醒按鈕點擊"""
        logger.debug("使用者選擇稍後更新")
        self.destroy()


def show_update_dialog(parent: ctk.CTk, update_info: Dict[str, Any]) -> None:
    """
    顯示更新對話框的便利函式
    
    Args:
        parent: 父視窗
        update_info: 更新資訊
    """
    # 只有在有更新時才顯示
    if update_info and update_info.get('has_update', False):
        UpdateDialog(parent, update_info)
    else:
        logger.debug("沒有可用更新,不顯示對話框")
