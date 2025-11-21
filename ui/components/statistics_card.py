"""
統計卡片元件 - 用於顯示關鍵數據指標
"""
import customtkinter as ctk
import sys
from pathlib import Path

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from ui.config import (
    colors, typography, spacing, border_radius, 
    default_styles, get_font_config
)


class StatisticsCard(ctk.CTkFrame):
    """
    統計卡片元件
    
    用於顯示單一數據指標,包含:
    - 標題
    - 數值
    - 圖示 (可選)
    - 趨勢指示 (可選)
    """
    
    def __init__(
        self,
        master,
        title: str,
        value: str,
        icon: str = "",
        color: str = colors.primary,
        **kwargs
    ):
        """
        Args:
            master: 父元件
            title: 卡片標題
            value: 顯示數值
            icon: 圖示 (emoji 或文字)
            color: 主題色
        """
        super().__init__(
            master,
            **default_styles.CARD,
            **kwargs
        )
        
        self.title = title
        self.value = value
        self.icon = icon
        self.color = color
        
        self._create_ui()
    
    def _create_ui(self):
        """建立 UI"""
        # 設置內距
        self.configure(
            width=280,
            height=140
        )
        self.grid_propagate(False)
        
        # 使用 pack 布局
        content_frame = ctk.CTkFrame(self, fg_color="transparent")
        content_frame.pack(fill="both", expand=True, padx=spacing.md, pady=spacing.md)
        
        # === 頂部區域 (圖示 + 標題) ===
        header_frame = ctk.CTkFrame(content_frame, fg_color="transparent")
        header_frame.pack(fill="x", pady=(0, spacing.sm))
        
        # 圖示
        if self.icon:
            icon_label = ctk.CTkLabel(
                header_frame,
                text=self.icon,
                font=get_font_config(24),
                text_color=self.color
            )
            icon_label.pack(side="left")
        
        # 標題
        title_label = ctk.CTkLabel(
            header_frame,
            text=self.title,
            font=get_font_config(typography.size_body_small),
            text_color=colors.text_secondary,
            anchor="w"
        )
        title_label.pack(side="left", padx=(spacing.xs if self.icon else 0, 0))
        
        # === 數值區域 ===
        value_label = ctk.CTkLabel(
            content_frame,
            text=self.value,
            font=get_font_config(typography.size_h2, typography.weight_bold),
            text_color=colors.text_primary,
            anchor="w"
        )
        value_label.pack(fill="x", pady=(spacing.sm, 0))
    
    def update_value(self, new_value: str):
        """
        更新卡片數值
        
        Args:
            new_value: 新數值
        """
        self.value = new_value
        # 重新建立 UI
        for widget in self.winfo_children():
            widget.destroy()
        self._create_ui()
    
    def update_title(self, new_title: str):
        """
        更新卡片標題
        
        Args:
            new_title: 新標題
        """
        self.title = new_title
        for widget in self.winfo_children():
            widget.destroy()
        self._create_ui()
