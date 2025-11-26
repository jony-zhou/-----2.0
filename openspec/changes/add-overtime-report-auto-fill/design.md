# 技術設計文件

## Context

加班補報自動填寫功能需要與 TECO SSP 系統的 ASP.NET Web Forms 深度整合,處理複雜的表單填寫、狀態查詢、分頁資料抓取等邏輯。此功能是現有「加班時數計算」功能的自然延伸,將「查詢」與「填寫」串聯成完整工作流程。

**技術環境**:
- SSP 系統: ASP.NET Web Forms (ViewState + PostBack 機制)
- 加班補報頁面: `FW21001Z.aspx?Kind=B`
- 個人紀錄查詢: `FW21003Z.aspx`
- 表單特性: 動態新增列、必填欄位驗證、二擇一選項

## Goals / Non-Goals

### Goals
- ✅ 自動填寫加班補報表單,減少手動操作
- ✅ 查詢已申請記錄,避免重複申請
- ✅ 分頁式 UI,清楚區分「查詢」與「申請」
- ✅ 預覽模式,確保安全測試
- ✅ 靈活的加班/調休選擇
- ✅ 手動編輯加班內容

### Non-Goals
- ❌ 不自動判斷加班內容 (需使用者輸入)
- ❌ 不支援「預報申請單」(僅補報)
- ❌ 不支援「一日多人」模式 (僅一人多日)
- ❌ 不處理加班單的簽核流程
- ❌ 不提供歷史記錄修改功能

## Decisions

### 決策 1: 分頁式 UI 架構

**選擇**: 使用 `customtkinter.CTkTabview` 實現分頁切換

**原因**:
- 功能職責清晰: 「查詢」與「申請」分離
- 減少單頁資訊過載
- 符合使用者心智模型 (先查詢 → 再申請)
- 易於未來擴展 (可新增更多分頁)

**替代方案**:
- ❌ 單頁滾動: 內容過多,操作混亂
- ❌ 多視窗: 管理複雜,使用者體驗差

---

### 決策 2: 服務層設計

**架構**:
```
OvertimeStatusService     # 查詢已申請記錄
└── fetch_submitted_records(session) → List[SubmittedRecord]
    ├── _fetch_status_page(session, page_num)
    └── _parse_status_table(html)

OvertimeReportService     # 填寫加班補報表單
├── preview_form(session, records) → PreviewResult
└── submit_form(session, records) → SubmissionResult
    ├── _add_form_rows(session, count)
    └── _fill_form_data(form_data, records)
```

**原因**:
- **單一職責**: 每個服務專注一個任務
- **依賴注入**: 透過 `session` 參數注入已登入的會話
- **可測試性**: 易於 Mock 網路請求
- **可重用性**: 服務層可獨立於 UI 使用

---

### 決策 3: ASP.NET 表單處理策略

**挑戰**: 動態新增表單列需要多次 PostBack

**解決方案**:
1. **取得初始頁面** → 提取 ViewState
2. **計算需要的列數** → 執行 N-1 次「增加列」PostBack
3. **填寫所有欄位** → 構建完整 POST 資料
4. **提交表單** (或預覽)

**欄位命名規則**:
```python
# 第一筆從 ctl03 開始 (0-based index 對應)
txtOT_Datei      = f"ctl00$ContentPlaceHolder1$gvFlow211i$ctl{index:02d}$txtOT_Datei"
txtOT_Describei  = f"ctl00$ContentPlaceHolder1$gvFlow211i$ctl{index:02d}$txtOT_Describei"
txtOT_Minutei    = f"ctl00$ContentPlaceHolder1$gvFlow211i$ctl{index:02d}$txtOT_Minutei"
txtChange_Minutei = f"ctl00$ContentPlaceHolder1$gvFlow211i$ctl{index:02d}$txtChange_Minutei"
```

**注意事項**:
- ViewState 必須在每次 PostBack 後更新
- `__EVENTTARGET` 和 `__EVENTARGUMENT` 需正確設定
- 時數欄位只能填一個 (加班 OR 調休)

---

### 決策 4: 已申請記錄查詢與重複檢查

**查詢邏輯**:
```python
def fetch_submitted_records(session) -> Dict[str, SubmittedRecord]:
    """
    返回: {
        "2025/11/21": SubmittedRecord(date="2025/11/21", status="簽核完成", ...),
        "2025/11/22": SubmittedRecord(date="2025/11/22", status="簽核中", ...),
    }
    """
    # 1. 取得第一頁
    # 2. 解析分頁資訊 (FlowPagerStyle)
    # 3. 抓取所有頁面
    # 4. 解析每筆記錄的日期與狀態
```

**重複檢查**:
- UI 層根據日期比對 `submitted_records`
- 已申請的記錄顯示狀態,禁用勾選框
- 允許使用者手動刪除不需要的記錄

**分頁處理**:
```python
# PostBack 到第 N 頁
post_data = {
    '__EVENTTARGET': 'ctl00$ContentPlaceHolder1$gvFlow211',
    '__EVENTARGUMENT': f'Page${page_num}',
    '__VIEWSTATE': viewstate,
    ...
}
```

---

### 決策 5: UI 元件設計

**OvertimeReportTab 佈局**:
```
┌─────────────────────────────────────────────┐
│  [預覽填寫] [送出申請] [重新整理] [全選/取消] │
├─────────────────────────────────────────────┤
│  ┌───────────────────────────────────────┐  │
│  │ ☑ 2025/11/21 | [加班內容...] | 1.5h  │  │
│  │   ● 加班  ○ 調休                      │  │
│  ├───────────────────────────────────────┤  │
│  │ ☑ 2025/11/22 | [加班內容...] | 2.0h  │  │
│  │   ● 加班  ○ 調休                      │  │
│  ├───────────────────────────────────────┤  │
│  │ ☐ 2025/11/23 | 已申請 (簽核完成)      │  │  <- 禁用
│  │   狀態: 簽核完成                      │  │
│  └───────────────────────────────────────┘  │
├─────────────────────────────────────────────┤
│  狀態: 已選擇 2 筆,共 3.5 小時             │
└─────────────────────────────────────────────┘
```

**元件選擇**:
- `CTkScrollableFrame`: 包含所有記錄
- `CTkCheckBox`: 勾選記錄
- `CTkEntry`: 編輯加班內容
- `CTkRadioButton`: 加班/調休選擇
- `CTkLabel`: 顯示狀態

---

### 決策 6: 預覽 vs 送出模式

**預覽模式** (v1.2.0-beta):
```python
def preview_form(session, records):
    # 1. 模擬填寫表單
    # 2. 返回 HTML 預覽或結構化資料
    # 3. 不執行最後的 btnCommit
    return {
        'success': True,
        'preview_data': [...],
        'form_html': '...'  # 可選
    }
```

**送出模式** (v1.2.0):
```python
def submit_form(session, records):
    # 1. 填寫表單
    # 2. 執行 btnCommit PostBack
    # 3. 檢查提交結果
    return {
        'success': True,
        'submitted_count': 5,
        'errors': []
    }
```

**切換機制**:
- 配置檔案設定 `ENABLE_SUBMISSION = False/True`
- Beta 版本強制 `False`

---

### 決策 7: 資料模型

**OvertimeSubmissionRecord**:
```python
@dataclass
class OvertimeSubmissionRecord:
    date: str                    # YYYY/MM/DD
    description: str             # 加班內容 (使用者可編輯)
    overtime_hours: float        # 加班時數
    is_overtime: bool = True     # True=加班, False=調休
    is_selected: bool = True     # 是否勾選
    submitted_status: Optional[str] = None  # 已申請狀態
    
    @property
    def is_submitted(self) -> bool:
        return self.submitted_status is not None
    
    @property
    def overtime_minutes(self) -> int:
        return int(self.overtime_hours * 60)
```

**從 OvertimeReport 轉換**:
```python
class OvertimeReport:
    def to_submission_records(self, default_description: str = "加班作業") -> List[OvertimeSubmissionRecord]:
        return [
            OvertimeSubmissionRecord(
                date=record.date,
                description=default_description,
                overtime_hours=record.overtime_hours,
            )
            for record in self.records
            if record.overtime_hours > 0
        ]
```

## Risks / Trade-offs

### 風險 1: ASP.NET 網頁結構變更
- **風險**: SSP 系統更新後,欄位 ID 或表單結構改變
- **緩解**: 
  - 使用常數定義所有選擇器
  - 完整的錯誤處理與日誌
  - 提供降級方案 (手動開啟網頁)

### 風險 2: 重複申請
- **風險**: 狀態查詢失敗導致重複填寫
- **緩解**:
  - 嚴格的日期比對邏輯
  - 顯示警告訊息
  - 預覽模式降低風險

### 風險 3: 效能問題
- **風險**: 多次 PostBack 導致速度慢
- **緩解**:
  - 背景執行緒執行
  - 顯示進度條
  - 優化請求數量 (批次處理)

### Trade-off: UI 複雜度 vs 功能完整性
- **選擇**: 提供完整編輯功能 (每筆記錄可編輯)
- **代價**: UI 元件較多,實作複雜
- **理由**: 靈活性對使用者更重要

## Migration Plan

### 階段 1: 基礎設施 (Week 1)
1. 建立資料模型與服務層
2. 實作狀態查詢功能
3. 單元測試

### 階段 2: 表單填寫 (Week 2)
1. 實作 `OvertimeReportService`
2. 處理 ViewState 與 PostBack
3. 測試預覽模式

### 階段 3: UI 重構 (Week 3)
1. 建立分頁式主視窗
2. 實作 `OvertimeReportTab`
3. 整合所有功能

### 階段 4: 測試與發布 (Week 4)
1. 完整測試 (單元+整合)
2. Beta 版本發布
3. 收集回饋後正式發布

### 回滾計劃
- 保留現有功能完整性
- 新功能可獨立禁用 (配置檔案)
- Git Tag 可快速回退

## Open Questions

1. **Q**: 是否需要支援修改已申請的記錄?
   - **A**: 不支援,需使用者手動到 SSP 系統撤回

2. **Q**: 加班內容範本如何管理?
   - **A**: 初版使用固定預設值,未來可新增範本管理功能

3. **Q**: 是否需要支援匯出加班單 PDF?
   - **A**: 不在此版本範圍,可作為未來功能

4. **Q**: 如何處理網路中斷或逾時?
   - **A**: 完整的異常處理,顯示錯誤訊息,允許重試
