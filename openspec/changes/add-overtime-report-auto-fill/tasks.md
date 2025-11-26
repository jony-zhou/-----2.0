# 實作任務清單

## 1. 資料模型層 (Models)
- [ ] 1.1 建立 `OvertimeSubmissionRecord` 資料類別
  - 日期、加班內容、加班/調休選擇、時數、狀態
- [ ] 1.2 建立 `OvertimeSubmissionStatus` 列舉
  - 未申請、已申請、簽核中、簽核完成、已撤回
- [ ] 1.3 擴充 `OvertimeReport` 模型
  - 新增 `to_submission_records()` 方法

## 2. 服務層 (Services)

### 2.1 已申請記錄查詢服務
- [ ] 2.1.1 建立 `OvertimeStatusService` 類別
- [ ] 2.1.2 實作 `fetch_submitted_records(session)` 方法
  - 取得 FW21003Z.aspx 頁面
  - 解析 ViewState
  - 抓取所有分頁資料
- [ ] 2.1.3 實作 `_parse_status_table(html)` 方法
  - 解析 `ContentPlaceHolder1_gvFlow211` 表格
  - 提取日期、狀態、時數
- [ ] 2.1.4 實作 `_fetch_status_page(session, page_num)` 方法
  - 使用 `__doPostBack` 處理分頁
- [ ] 2.1.5 測試多頁資料抓取

### 2.2 加班補報填寫服務
- [ ] 2.2.1 建立 `OvertimeReportService` 類別
- [ ] 2.2.2 實作 `preview_form(session, records)` 方法
  - 取得 FW21001Z.aspx?Kind=B 頁面
  - 模擬填寫表單(不送出)
  - 返回填寫結果預覽
- [ ] 2.2.3 實作 `submit_form(session, records)` 方法
  - 解析 ViewState
  - 使用 `lbgvAddRowi` 增加列
  - 填寫所有欄位
  - 提交表單
- [ ] 2.2.4 實作 `_add_form_rows(session, count)` 方法
  - 動態增加表單行數
- [ ] 2.2.5 實作 `_fill_form_data(form_data, records)` 方法
  - 填寫日期 `txtOT_Datei`
  - 填寫內容 `txtOT_Describei`
  - 填寫時數 `txtOT_Minutei` 或 `txtChange_Minutei`
- [ ] 2.2.6 測試表單填寫邏輯

## 3. UI 元件層 (Components)

### 3.1 加班補報分頁
- [ ] 3.1.1 建立 `OvertimeReportTab` 類別 (繼承 CTkFrame)
- [ ] 3.1.2 設計 UI 佈局
  - 上方: 操作按鈕區 (預覽、送出、重新整理)
  - 中間: 記錄列表 (Treeview 或 CTkScrollableFrame)
  - 下方: 狀態訊息
- [ ] 3.1.3 實作記錄列表顯示
  - 勾選框、日期、加班內容(可編輯)、時數、加班/調休選擇、狀態
- [ ] 3.1.4 實作 `on_preview()` 方法 (背景執行緒)
- [ ] 3.1.5 實作 `on_submit()` 方法 (背景執行緒)
- [ ] 3.1.6 實作 `on_refresh()` 方法 (重新載入狀態)
- [ ] 3.1.7 實作已申請記錄的禁用邏輯
- [ ] 3.1.8 實作確認對話框 (送出前)

### 3.2 出勤異常清單分頁
- [ ] 3.2.1 建立 `AttendanceTab` 類別
- [ ] 3.2.2 將現有 `ReportFrame` 邏輯移至此分頁
- [ ] 3.2.3 保留所有現有功能 (表格、複製、匯出)

## 4. 主視窗重構 (Main Window)

- [ ] 4.1 重構 `MainWindow` 為分頁式介面
  - 使用 `customtkinter.CTkTabview`
  - 分頁 1: 加班補報 (預設)
  - 分頁 2: 本月異常清單
- [ ] 4.2 修改登入後流程
  - 載入加班報表資料
  - 同時查詢已申請狀態
  - 切換到加班補報分頁
- [ ] 4.3 保留現有功能
  - 登出按鈕
  - 狀態訊息
  - 統計卡片 (移到異常清單分頁)
- [ ] 4.4 測試分頁切換

## 5. 配置與設定 (Config)

- [ ] 5.1 在 `Settings` 新增配置
  - `OVERTIME_REPORT_URL` = "/FW21001Z.aspx?Kind=B"
  - `OVERTIME_STATUS_URL` = "/FW21003Z.aspx"
  - `DEFAULT_OVERTIME_DESCRIPTION` = "加班作業"
- [ ] 5.2 新增加班內容範本設定 (可選)

## 6. 測試 (Tests)

- [ ] 6.1 建立 `test_overtime_status_service.py`
  - 測試狀態查詢
  - 測試分頁處理
  - 測試資料解析
- [ ] 6.2 建立 `test_overtime_report_service.py`
  - 測試表單填寫
  - 測試增加列邏輯
  - 測試 ViewState 處理
- [ ] 6.3 建立 `test_overtime_submission.py`
  - 測試資料模型轉換
- [ ] 6.4 UI 整合測試
  - 測試分頁切換
  - 測試記錄勾選
  - 測試預覽功能

## 7. 文件更新 (Documentation)

- [ ] 7.1 更新 `readme.md`
  - 新增加班補報功能說明
  - 更新截圖
- [ ] 7.2 建立 `docs/release/RELEASE_v1.2.0.md`
  - 詳細功能說明
  - 使用指南
- [ ] 7.3 更新 `QUICKSTART.md`
  - 新增加班補報流程

## 8. 版本發布 (Release)

- [ ] 8.1 更新版本號
  - `src/core/version.py` → `VERSION = "1.2.0-beta"`
  - `VERSION_NAME = "加班補報自動填寫 (預覽版)"`
- [ ] 8.2 執行完整測試
  - `pytest`
  - 手動 UI 測試
- [ ] 8.3 打包執行檔
  - `pyinstaller overtime_calculator.spec --clean`
- [ ] 8.4 建立 Git Tag
  - `git tag -a v1.2.0-beta -m "Beta: 加班補報自動填寫"`
- [ ] 8.5 發布到 GitHub Releases

## 9. 正式版本 (v1.2.0)

- [ ] 9.1 收集 beta 版回饋
- [ ] 9.2 修正問題
- [ ] 9.3 啟用送出功能
- [ ] 9.4 更新版本號為 `1.2.0`
- [ ] 9.5 正式發布

---

## 依賴關係

- **任務 3.1 依賴**: 任務 2.1, 2.2 (服務層完成)
- **任務 4.1 依賴**: 任務 3.1, 3.2 (UI 元件完成)
- **任務 6 可並行**: 與開發同步進行

## 預估時間

- 資料模型: 2 小時
- 服務層: 8 小時
- UI 元件: 10 小時
- 主視窗重構: 4 小時
- 測試: 6 小時
- 文件: 2 小時
- **總計**: 約 32 小時 (4 個工作天)
