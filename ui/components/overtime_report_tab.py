"""加班補報分頁元件"""
import customtkinter as ctk
from typing import List, Optional, Dict
import threading
import logging
from tkinter import messagebox
from requests import Session

from src.models import OvertimeSubmissionRecord, SubmittedRecord
from src.services import OvertimeReportService, OvertimeStatusService
from src.config import Settings
from ui.config.design_system import colors, typography, spacing, border_radius

logger = logging.getLogger(__name__)


def get_font_config(style: str) -> dict:
    """取得字體配置"""
    configs = {
        "h1": {"family": typography.font_family_primary, "size": typography.size_h1, "weight": typography.weight_bold},
        "h2": {"family": typography.font_family_primary, "size": typography.size_h2, "weight": typography.weight_bold},
        "h3": {"family": typography.font_family_primary, "size": typography.size_h3, "weight": typography.weight_bold},
        "body": {"family": typography.font_family_primary, "size": typography.size_body, "weight": typography.weight_normal},
        "body_bold": {"family": typography.font_family_primary, "size": typography.size_body, "weight": typography.weight_bold},
        "caption": {"family": typography.font_family_primary, "size": typography.size_caption, "weight": typography.weight_normal},
    }
    return {"font": (configs[style]["family"], configs[style]["size"], configs[style]["weight"])}


class OvertimeReportTab(ctk.CTkFrame):
    """
    加班補報分頁
    
    職責:
    - 顯示待填寫的加班記錄列表
    - 允許使用者編輯加班內容
    - 選擇加班/調休
    - 預覽和送出表單
    """
    
    def __init__(self, master, **kwargs):
        super().__init__(master, **kwargs)
        
        self.settings = Settings()
        self.report_service = OvertimeReportService(self.settings)
        self.status_service = OvertimeStatusService(self.settings)
        
        # 資料
        self.submission_records: List[OvertimeSubmissionRecord] = []
        self.submitted_records: Dict[str, SubmittedRecord] = {}
        self.session: Optional[Session] = None  # 登入的 session
        
        # 建立 UI
        self._create_ui()
    
    def _create_ui(self):
        """建立 UI"""
        # 配置列權重
        self.grid_rowconfigure(1, weight=1)
        self.grid_columnconfigure(0, weight=1)
        
        # 上方: 操作按鈕區
        self._create_button_frame()
        
        # 中間: 記錄列表
        self._create_records_frame()
        
        # 下方: 狀態訊息
        self._create_status_frame()
    
    def _create_button_frame(self):
        """建立操作按鈕區 (改善視覺層次)"""
        # 主容器: 使用卡片樣式提升視覺層次
        button_container = ctk.CTkFrame(
            self,
            fg_color=colors.background_secondary,
            corner_radius=border_radius.md
        )
        button_container.grid(row=0, column=0, sticky="ew", padx=spacing.lg, pady=(spacing.lg, spacing.md))
        
        # 內部框架 (保持透明)
        button_frame = ctk.CTkFrame(button_container, fg_color="transparent")
        button_frame.pack(fill="x", padx=spacing.md, pady=spacing.md)
        
        # 左側: 主要操作按鈕組
        action_group = ctk.CTkFrame(button_frame, fg_color="transparent")
        action_group.pack(side="left")
        
        self.preview_button = ctk.CTkButton(
            action_group,
            text="👁 預覽填寫",
            command=self.on_preview,
            **get_font_config("body"),
            fg_color=colors.primary,
            hover_color=colors.primary_hover,
            height=36,
            corner_radius=border_radius.sm
        )
        self.preview_button.pack(side="left", padx=(0, spacing.sm))
        
        self.submit_button = ctk.CTkButton(
            action_group,
            text="✓ 送出申請",
            command=self.on_submit,
            **get_font_config("body"),
            fg_color=colors.success,
            hover_color=colors.success_hover,
            height=36,
            corner_radius=border_radius.sm
        )
        self.submit_button.pack(side="left", padx=(0, spacing.sm))
        
        # 右側: 次要操作按鈕組
        utility_group = ctk.CTkFrame(button_frame, fg_color="transparent")
        utility_group.pack(side="right")
        
        self.select_all_button = ctk.CTkButton(
            utility_group,
            text="☑ 全選",
            command=self.on_select_all,
            **get_font_config("body"),
            fg_color=colors.background_tertiary,
            hover_color=colors.border_medium,
            text_color=colors.text_secondary,
            height=36,
            width=90,
            corner_radius=border_radius.sm
        )
        self.select_all_button.pack(side="left", padx=(0, spacing.sm))
        
        self.refresh_button = ctk.CTkButton(
            utility_group,
            text="🔄 重新整理",
            command=self.on_refresh,
            **get_font_config("body"),
            fg_color=colors.background_tertiary,
            hover_color=colors.border_medium,
            text_color=colors.text_secondary,
            height=36,
            corner_radius=border_radius.sm
        )
        self.refresh_button.pack(side="left")
        
        # 預設禁用主要操作按鈕
        self.preview_button.configure(state="disabled")
        self.submit_button.configure(state="disabled")
    
    def _create_records_frame(self):
        """建立記錄列表 (改善可讀性與層次)"""
        # 使用卡片式可滾動框架
        self.records_container = ctk.CTkScrollableFrame(
            self,
            fg_color=colors.background_primary,
            corner_radius=border_radius.md,
            border_width=1,
            border_color=colors.border_light
        )
        self.records_container.grid(row=1, column=0, sticky="nsew", padx=spacing.lg, pady=(0, spacing.md))
        
        # 載入/空狀態容器
        self.loading_container = ctk.CTkFrame(
            self.records_container,
            fg_color="transparent"
        )
        self.loading_container.pack(expand=True, fill="both", pady=spacing.xl)
        
        # 載入提示標籤
        self.loading_label = ctk.CTkLabel(
            self.loading_container,
            text="⏳ 正在載入加班記錄...\n\n正在查詢已申請狀態,請稍候",
            **get_font_config("body"),
            text_color=colors.text_secondary,
            justify="center"
        )
        
        # 空狀態提示
        self.empty_label = ctk.CTkLabel(
            self.loading_container,
            text="📋 尚無加班記錄\n\n請先登入並載入本月出勤資料",
            **get_font_config("body"),
            text_color=colors.text_tertiary,
            justify="center"
        )
        self.empty_label.pack(pady=spacing.xl)
    
    def _create_status_frame(self):
        """建立狀態訊息區 (增加視覺回饋)"""
        status_container = ctk.CTkFrame(
            self,
            fg_color=colors.background_secondary,
            corner_radius=border_radius.sm,
            height=40
        )
        status_container.grid(row=2, column=0, sticky="ew", padx=spacing.lg, pady=(0, spacing.lg))
        status_container.grid_propagate(False)
        
        self.status_label = ctk.CTkLabel(
            status_container,
            text="✨ 準備就緒",
            **get_font_config("body"),
            text_color=colors.text_secondary
        )
        self.status_label.pack(side="left", padx=spacing.md, pady=spacing.sm)
    
    def load_data(self, submission_records: List[OvertimeSubmissionRecord], session: Session):
        """
        載入加班記錄資料
        
        Args:
            submission_records: 加班補報記錄列表
            session: 已登入的 session
        """
        self.submission_records = submission_records
        self.session = session
        
        # 顯示載入狀態
        self._show_loading_state()
        
        # 啟動背景執行緒查詢已申請狀態
        threading.Thread(
            target=self._load_submitted_status,
            daemon=True
        ).start()
    
    def _show_loading_state(self):
        """顯示載入狀態"""
        # 清空容器
        for widget in self.records_container.winfo_children():
            widget.destroy()
        
        # 重新建立容器
        self.loading_container = ctk.CTkFrame(
            self.records_container,
            fg_color="transparent"
        )
        self.loading_container.pack(expand=True, fill="both", pady=spacing.xl)
        
        # 顯示載入提示
        self.loading_label = ctk.CTkLabel(
            self.loading_container,
            text="⏳ 正在載入加班記錄...\n\n正在查詢已申請狀態,請稍候",
            **get_font_config("body"),
            text_color=colors.info,
            justify="center"
        )
        self.loading_label.pack(pady=spacing.xl)
        
        # 更新狀態訊息
        self._show_status("🔍 正在查詢已申請狀態...", colors.info)
    
    def _load_submitted_status(self):
        """背景載入已申請狀態"""
        try:
            if not self.session:
                return
                
            # 查詢已申請記錄
            self.submitted_records = self.status_service.fetch_submitted_records(self.session)
            
            # 更新記錄狀態
            for record in self.submission_records:
                if record.date in self.submitted_records:
                    submitted = self.submitted_records[record.date]
                    record.submitted_status = submitted.status
                    record.is_selected = False  # 已申請的不勾選
            
            # 回到主執行緒更新 UI
            self.after(0, self._refresh_records_ui)
            
        except Exception as error:
            logger.error("載入已申請狀態失敗: %s", error)
            self.after(0, lambda: self._show_status(f"載入狀態失敗: {error}", colors.error))
    
    def _refresh_records_ui(self):
        """重新整理記錄列表 UI"""
        # 清空容器
        for widget in self.records_container.winfo_children():
            widget.destroy()
        
        if not self.submission_records:
            self.empty_label = ctk.CTkLabel(
                self.records_container,
                text="尚無加班記錄",
                **get_font_config("body"),
                text_color=colors.text_secondary
            )
            self.empty_label.pack(pady=spacing.lg)
            return
        
        # 建立每筆記錄的 UI
        for record in self.submission_records:
            self._create_record_item(record)
        
        # 更新狀態
        self._update_status()
    
    def _create_record_item(self, record: OvertimeSubmissionRecord):
        """建立單筆記錄的 UI (卡片式設計)"""
        # 記錄卡片容器
        item_frame = ctk.CTkFrame(
            self.records_container,
            fg_color=colors.background_secondary if not record.is_submitted else colors.background_tertiary,
            corner_radius=border_radius.md,
            border_width=1,
            border_color=colors.border_light if not record.is_submitted else colors.border_dark
        )
        item_frame.pack(fill="x", padx=spacing.md, pady=spacing.sm)
        
        # 左側: 勾選框
        checkbox_var = ctk.BooleanVar(value=record.is_selected)
        checkbox = ctk.CTkCheckBox(
            item_frame,
            text="",
            variable=checkbox_var,
            command=lambda: self._on_record_check(record, checkbox_var.get()),
            state="disabled" if record.is_submitted else "normal"
        )
        checkbox.pack(side="left", padx=spacing.sm)
        
        # 日期標籤 (使用徽章樣式)
        date_badge = ctk.CTkFrame(
            item_frame,
            fg_color=colors.primary if not record.is_submitted else colors.text_tertiary,
            corner_radius=border_radius.sm
        )
        date_badge.pack(side="left", padx=spacing.sm)
        
        date_label = ctk.CTkLabel(
            date_badge,
            text=record.date,
            **get_font_config("body_bold"),
            text_color=colors.text_primary,
            width=90
        )
        date_label.pack(padx=spacing.sm, pady=spacing.xs)
        
        # 加班內容 (可編輯 - 必填)
        if not record.is_submitted:
            content_entry = ctk.CTkEntry(
                item_frame,
                placeholder_text="請輸入加班內容 (必填)",
                **get_font_config("body"),
                width=300,
                border_color=colors.error if not record.description else colors.background_tertiary
            )
            content_entry.insert(0, record.description)
            
            def on_content_change(e):
                record.description = content_entry.get()
                # 更新邊框顏色
                content_entry.configure(
                    border_color=colors.background_tertiary if record.description else colors.error
                )
            
            content_entry.bind("<KeyRelease>", on_content_change)
            content_entry.pack(side="left", padx=spacing.sm)
        else:
            content_label = ctk.CTkLabel(
                item_frame,
                text=record.description,
                **get_font_config("body"),
                text_color=colors.text_secondary,
                width=300
            )
            content_label.pack(side="left", padx=spacing.sm)
        
        # 時數 (小時)
        hours_label = ctk.CTkLabel(
            item_frame,
            text=f"{record.overtime_hours:.1f} hr",
            **get_font_config("body"),
            width=70
        )
        hours_label.pack(side="left", padx=spacing.sm)
        
        # 加班/調休選擇
        if not record.is_submitted:
            type_var = ctk.StringVar(value="加班" if record.is_overtime else "調休")
            
            overtime_radio = ctk.CTkRadioButton(
                item_frame,
                text="加班",
                variable=type_var,
                value="加班",
                command=lambda: setattr(record, 'is_overtime', True)
            )
            overtime_radio.pack(side="left", padx=spacing.sm)
            
            change_radio = ctk.CTkRadioButton(
                item_frame,
                text="調休",
                variable=type_var,
                value="調休",
                command=lambda: setattr(record, 'is_overtime', False)
            )
            change_radio.pack(side="left", padx=spacing.sm)
        else:
            # 已申請: 顯示狀態
            status_label = ctk.CTkLabel(
                item_frame,
                text=f"已申請 ({record.submitted_status})",
                **get_font_config("caption"),
                text_color=colors.warning
            )
            status_label.pack(side="left", padx=spacing.sm)
    
    def _on_record_check(self, record: OvertimeSubmissionRecord, checked: bool):
        """記錄勾選狀態變更"""
        record.is_selected = checked
        self._update_status()
    
    def _update_status(self):
        """更新狀態訊息"""
        selected = [r for r in self.submission_records if r.is_selected]
        total_hours = sum(r.overtime_hours for r in selected)
        
        self.status_label.configure(text=f"已選擇 {len(selected)} 筆,共 {total_hours:.1f} 小時")
        
        # 更新按鈕狀態
        has_selection = len(selected) > 0
        self.preview_button.configure(state="normal" if has_selection else "disabled")
        self.submit_button.configure(state="normal" if has_selection else "disabled")
    
    def on_select_all(self):
        """全選/取消全選"""
        # 檢查當前狀態
        all_selected = all(r.is_selected for r in self.submission_records if not r.is_submitted)
        
        # 切換狀態
        for record in self.submission_records:
            if not record.is_submitted:
                record.is_selected = not all_selected
        
        # 更新 UI
        self._refresh_records_ui()
        
        # 更新按鈕文字
        self.select_all_button.configure(text="取消全選" if not all_selected else "全選")
    
    def on_preview(self):
        """預覽填寫"""
        selected = [r for r in self.submission_records if r.is_selected]
        
        if not selected:
            messagebox.showwarning("提示", "請至少勾選一筆記錄")
            return
        
        # 驗證加班內容
        for record in selected:
            if not record.description.strip():
                messagebox.showerror("錯誤", f"{record.date} 的加班內容為空,請填寫")
                return
        
        # 背景執行緒執行預覽
        self._show_status("正在預覽填寫...", colors.info)
        threading.Thread(
            target=self._do_preview,
            args=(selected,),
            daemon=True
        ).start()
    
    def _do_preview(self, records: List[OvertimeSubmissionRecord]):
        """執行預覽 (背景執行緒)"""
        try:
            if not self.session:
                return
                
            result = self.report_service.preview_form(self.session, records)
            
            if result['success']:
                # 顯示預覽結果
                preview_text = "\n".join([
                    f"日期: {d['date']}, 內容: {d['description']}, 時數: {d['overtime_minutes'] if d['type'] == '加班' else d['change_minutes']}分, 類型: {d['type']}"
                    for d in result['preview_data']
                ])
                
                self.after(0, lambda: messagebox.showinfo(
                    "預覽結果",
                    f"即將填寫 {result['records_count']} 筆記錄:\n\n{preview_text}"
                ))
                self.after(0, lambda: self._show_status("預覽成功", colors.success))
            else:
                self.after(0, lambda: messagebox.showerror("錯誤", result.get('error', '預覽失敗')))
                self.after(0, lambda: self._show_status("預覽失敗", colors.error))
                
        except Exception as error:
            logger.error("預覽失敗: %s", error)
            self.after(0, lambda: messagebox.showerror("錯誤", str(error)))
            self.after(0, lambda: self._show_status(f"預覽失敗: {error}", colors.error))
    
    def on_submit(self):
        """送出申請"""
        selected = [r for r in self.submission_records if r.is_selected]
        
        if not selected:
            messagebox.showwarning("提示", "請至少勾選一筆記錄")
            return
        
        # 驗證加班內容必填
        empty_records = [r for r in selected if not r.description.strip()]
        if empty_records:
            messagebox.showerror(
                "驗證失敗",
                f"以下記錄的加班內容為空,請填寫後再送出:\n\n" +
                "\n".join([f"- {r.date}" for r in empty_records[:5]])
            )
            return
        
        # 確認對話框
        confirm_text = f"確定要送出 {len(selected)} 筆加班申請嗎?\n\n" + "\n".join([
            f"- {r.date}: {r.description} ({r.overtime_hours:.1f}h)"
            for r in selected[:5]  # 只顯示前 5 筆
        ])
        
        if len(selected) > 5:
            confirm_text += f"\n... 及其他 {len(selected) - 5} 筆"
        
        if not messagebox.askyesno("確認送出", confirm_text):
            return
        
        # 背景執行緒執行送出
        self._show_status("正在送出申請...", colors.info)
        threading.Thread(
            target=self._do_submit,
            args=(selected,),
            daemon=True
        ).start()
    
    def _do_submit(self, records: List[OvertimeSubmissionRecord]):
        """執行送出 (背景執行緒)"""
        try:
            if not self.session:
                return
                
            result = self.report_service.submit_form(self.session, records)
            
            if result['success']:
                self.after(0, lambda: messagebox.showinfo(
                    "成功",
                    f"已成功送出 {result['submitted_count']} 筆加班申請"
                ))
                self.after(0, lambda: self._show_status("送出成功", colors.success))
                # 重新整理狀態
                self.after(0, self.on_refresh)
            else:
                self.after(0, lambda: messagebox.showerror("錯誤", result.get('error', '送出失敗')))
                self.after(0, lambda: self._show_status("送出失敗", colors.error))
                
        except Exception as error:
            logger.error("送出失敗: %s", error)
            self.after(0, lambda: messagebox.showerror("錯誤", str(error)))
            self.after(0, lambda: self._show_status(f"送出失敗: {error}", colors.error))
    
    def on_refresh(self):
        """重新整理"""
        if self.session:
            self._show_status("正在重新整理...", colors.info)
            threading.Thread(
                target=self._load_submitted_status,
                daemon=True
            ).start()
    
    def _show_status(self, message: str, color: Optional[str] = None):
        """顯示狀態訊息"""
        if color is None:
            color = colors.text_secondary
        self.status_label.configure(text=message, text_color=color)
