"""報表框元件"""
import customtkinter as ctk
from typing import Callable, Optional
from tkinter import ttk
import tkinter as tk
import sys
from pathlib import Path

# 加入專案根目錄到路徑
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from src.models import OvertimeReport


class ReportFrame(ctk.CTkFrame):
    """報表顯示框"""
    
    def __init__(self, parent, on_export: Callable, on_refresh: Callable):
        super().__init__(parent)
        
        self.on_export = on_export
        self.on_refresh = on_refresh
        self.current_report: Optional[OvertimeReport] = None
        
        self._create_ui()
    
    def _create_ui(self):
        """建立 UI"""
        # 標題列
        header = ctk.CTkFrame(self, fg_color="transparent")
        header.pack(fill="x", pady=(10, 0))
        
        title = ctk.CTkLabel(
            header,
            text="加班時數報表",
            font=ctk.CTkFont(size=18, weight="bold")
        )
        title.pack(side="left", padx=10)
        
        # 按鈕容器
        button_container = ctk.CTkFrame(header, fg_color="transparent")
        button_container.pack(side="right", padx=10)
        
        # 重新整理按鈕
        self.refresh_button = ctk.CTkButton(
            button_container,
            text="🔄 重新整理",
            command=self.on_refresh,
            width=120
        )
        self.refresh_button.pack(side="left", padx=5)
        
        # 匯出按鈕
        self.export_button = ctk.CTkButton(
            button_container,
            text="📥 匯出 Excel",
            command=self.on_export,
            width=120
        )
        self.export_button.pack(side="left", padx=5)
        
        # 統計資訊框
        self.stats_frame = ctk.CTkFrame(self)
        self.stats_frame.pack(fill="x", padx=10, pady=10)
        
        self.stats_label = ctk.CTkLabel(
            self.stats_frame,
            text="",
            font=ctk.CTkFont(size=12),
            justify="left"
        )
        self.stats_label.pack(padx=15, pady=15)
        
        # 表格容器
        table_container = ctk.CTkFrame(self)
        table_container.pack(fill="both", expand=True, padx=10, pady=10)
        
        # 建立表格
        self._create_table(table_container)
    
    def _create_table(self, parent):
        """建立表格"""
        # 使用 tkinter 的 Treeview (因為 customtkinter 沒有表格元件)
        style = ttk.Style()
        style.theme_use("clam")
        style.configure(
            "Treeview",
            background="#2b2b2b",
            foreground="white",
            fieldbackground="#2b2b2b",
            borderwidth=0
        )
        style.configure("Treeview.Heading", background="#1f538d", foreground="white")
        style.map("Treeview", background=[("selected", "#1f538d")])
        
        # 建立表格
        columns = ("日期", "上班時間", "下班時間", "總工時(分)", "加班時數")
        
        self.tree = ttk.Treeview(
            parent,
            columns=columns,
            show="headings",
            height=15
        )
        
        # 設定欄位
        for col in columns:
            self.tree.heading(col, text=col)
            if col == "日期":
                self.tree.column(col, width=120, anchor="center")
            elif col == "總工時(分)":
                self.tree.column(col, width=100, anchor="center")
            else:
                self.tree.column(col, width=120, anchor="center")
        
        # 捲軸
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
    
    def display_report(self, report: OvertimeReport):
        """顯示報表"""
        self.current_report = report
        
        # 清空表格
        for item in self.tree.get_children():
            self.tree.delete(item)
        
        # 填入資料
        for record in report.records:
            self.tree.insert("", "end", values=(
                record.date,
                record.start_time,
                record.end_time,
                record.total_minutes,
                record.overtime_hours
            ))
        
        # 更新統計資訊
        summary = report.get_summary()
        stats_text = (
            f"記錄天數: {summary['記錄天數']} 天  |  "
            f"加班天數: {summary['加班天數']} 天  |  "
            f"總加班時數: {summary['總加班時數']} 小時  |  "
            f"平均每日加班: {summary['平均每日加班']} 小時  |  "
            f"最長加班: {summary['最長加班']} 小時"
        )
        
        if summary['最長加班日期']:
            stats_text += f"  ({summary['最長加班日期']})"
        
        self.stats_label.configure(text=stats_text)
