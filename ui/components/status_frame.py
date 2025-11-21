"""狀態框元件"""
import customtkinter as ctk
import sys
from pathlib import Path

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))


class StatusFrame(ctk.CTkFrame):
    """狀態顯示框"""
    
    def __init__(self, parent):
        super().__init__(parent, height=50)
        
        self.status_label = ctk.CTkLabel(
            self,
            text="",
            font=ctk.CTkFont(size=14)
        )
        self.status_label.pack(pady=10)
    
    def show_status(self, message: str, status_type: str = "info"):
        """
        顯示狀態訊息
        
        Args:
            message: 訊息內容
            status_type: 類型 (info/success/error)
        """
        colors = {
            "info": "#3498db",
            "success": "#2ecc71",
            "error": "#e74c3c"
        }
        
        color = colors.get(status_type, colors["info"])
        self.status_label.configure(text=message, text_color=color)
