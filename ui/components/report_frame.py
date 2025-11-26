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
            text="出勤異常清單(本月)",
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
        
        # 複製按鈕
        self.copy_button = ctk.CTkButton(
            button_container,
            text="📋 複製總時數",
            command=self.copy_total_hours,
            width=120
        )
        self.copy_button.pack(side="left", padx=5)
        
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
        
        # 綁定右鍵選單
        self.tree.bind("<Button-3>", self._show_context_menu)
        self.tree.bind("<Control-c>", lambda e: self._copy_overtime_hours())
        
        # 捲軸
        scrollbar = ttk.Scrollbar(parent, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=scrollbar.set)
        
        self.tree.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 建立右鍵選單
        self.context_menu = tk.Menu(self.tree, tearoff=0)
        self.context_menu.add_command(label="複製加班時數", command=self._copy_overtime_hours)
        self.context_menu.add_command(label="複製所有加班時數", command=self._copy_all_overtime_hours)
    
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
    
    def copy_total_hours(self):
        """複製總加班時數到剪貼簿"""
        if not self.current_report:
            return
        
        total_hours = self.current_report.total_overtime_hours
        
        # 複製到剪貼簿
        self.clipboard_clear()
        self.clipboard_append(f"{total_hours:.1f}")
        
        # 顯示提示
        self._show_copy_notification(f"已複製: {total_hours:.1f} 小時")
    
    def _show_context_menu(self, event):
        """顯示右鍵選單"""
        # 選擇點擊的行
        item = self.tree.identify_row(event.y)
        if item:
            self.tree.selection_set(item)
        
        # 顯示選單
        try:
            self.context_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.context_menu.grab_release()
    
    def _copy_overtime_hours(self):
        """複製選中行的加班時數"""
        selection = self.tree.selection()
        if not selection:
            return
        
        # 只取加班時數欄位 (第5欄,索引4)
        overtime_hours = []
        for item in selection:
            values = self.tree.item(item)['values']
            overtime_hours.append(str(values[4]))  # 加班時數是第5欄
        
        # 每行一個數字
        data = "\n".join(overtime_hours)
        
        # 複製到剪貼簿
        self.clipboard_clear()
        self.clipboard_append(data)
        
        count = len(selection)
        self._show_copy_notification(f"已複製 {count} 筆加班時數")
    
    def _copy_all_overtime_hours(self):
        """複製所有加班時數"""
        # 只取加班時數欄位
        overtime_hours = []
        for item in self.tree.get_children():
            values = self.tree.item(item)['values']
            overtime_hours.append(str(values[4]))  # 加班時數是第5欄
        
        # 每行一個數字
        data = "\n".join(overtime_hours)
        
        # 複製到剪貼簿
        self.clipboard_clear()
        self.clipboard_append(data)
        
        count = len(self.tree.get_children())
        self._show_copy_notification(f"已複製全部 {count} 筆加班時數")
    
    def _show_copy_notification(self, message: str):
        """顯示複製通知"""
        # 建立臨時標籤顯示提示
        notification = ctk.CTkLabel(
            self,
            text=message,
            font=ctk.CTkFont(size=12),
            text_color="#2ecc71",
            fg_color="#1e1e1e",
            corner_radius=5
        )
        notification.place(relx=0.5, rely=0.5, anchor="center")
        
        # 1秒後自動消失
        self.after(1000, notification.destroy)
