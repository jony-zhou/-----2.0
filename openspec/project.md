# Project Context

## Purpose
TECO SSP 加班時數計算器 - 現代化桌面應用程式,自動登入 TECO SSP 內部系統,抓取員工出勤異常清單,並計算每日加班時數。

**核心目標**:
- 簡化員工加班時數查詢流程
- 提供直覺的圖形化介面 (GUI)
- 自動化資料擷取與計算
- 支援 Excel 匯出與資料複製
- 提供統計儀表板與視覺化

## Tech Stack

### 核心技術
- **Python 3.9+**: 主要開發語言
- **CustomTkinter 5.2.2**: 現代化 GUI 框架 (基於 Tkinter)
- **Requests**: HTTP 客戶端,處理 SSP 登入與資料抓取
- **BeautifulSoup4**: HTML 解析,處理 ASP.NET GridView 表格
- **Pandas**: 資料處理與統計計算
- **OpenPyXL**: Excel 檔案生成與匯出

### 安全與憑證管理
- **Cryptography (Fernet)**: 對稱加密,保護使用者密碼
- **Keyring**: Windows Credential Manager 整合
- **pywin32-ctypes**: Windows API 呼叫

### 開發工具
- **Pytest + pytest-cov**: 單元測試與覆蓋率分析 (44 個測試)
- **PyInstaller**: 打包為單一執行檔 (.exe)
- **Logging (colorama)**: 結構化日誌系統
- **Pillow**: 圖示與圖片處理

### 外部系統
- **TECO SSP 系統**: ASP.NET Web Forms (ViewState/PostBack 機制)
- **GitHub Releases API**: 自動版本檢查與更新通知

## Project Conventions

### Code Style

**命名規範**:
- 類別: `PascalCase` (如 `OvertimeCalculator`, `AuthService`)
- 函式/方法: `snake_case` (如 `calculate_overtime`, `fetch_data`)
- 私有方法: `_method_name` (單底線前綴)
- 常數: `UPPER_SNAKE_CASE` (如 `LUNCH_BREAK`, `WORK_HOURS`)
- 模組: `snake_case` (如 `auth_service.py`, `main_window.py`)

**中文註解與文件**:
- Docstring 使用繁體中文
- 程式碼註解使用繁體中文
- 使用者介面文字使用繁體中文
- 變數名稱使用英文 (避免編碼問題)

**格式化規則**:
- 縮排: 4 個空格
- 行寬: 建議 100 字元
- 字串: 優先使用雙引號 `"`
- 型別提示: 使用 `typing` 模組 (如 `Optional[str]`, `List[dict]`)

### Architecture Patterns

**MVC 分層架構**:
```
src/
├── core/       # 業務邏輯層 (計算、版本管理)
├── models/     # 資料模型層 (Dataclass)
├── services/   # 服務層 (認證、資料擷取、匯出)
├── config/     # 配置層 (設定檔)
└── utils/      # 工具層 (日誌、輔助函式)

ui/
├── components/ # UI 元件層 (登入框、報表表格、狀態列)
├── config/     # 設計系統 (顏色、字型、間距)
└── main_window.py  # 主視窗控制器
```

**設計原則 (SOLID)**:
- **Single Responsibility**: 每個類別只負責一件事
  - `AuthService`: 處理登入
  - `DataService`: 處理資料擷取
  - `ExportService`: 處理 Excel 匯出
  - `OvertimeCalculator`: 處理時數計算
  
- **Dependency Injection**: 透過建構子注入依賴
  ```python
  def __init__(self, settings: Optional[Settings] = None):
      self.settings = settings or Settings()
  ```

- **Open/Closed**: 透過繼承擴展,而非修改現有程式碼

**資料流程**:
1. **使用者操作** → UI 元件 (LoginFrame, ReportFrame)
2. **UI 元件** → MainWindow 事件處理器 (on_login, on_export)
3. **MainWindow** → Service 層 (背景執行緒)
4. **Service 層** → 核心業務邏輯 (OvertimeCalculator)
5. **結果回傳** → UI 更新 (主執行緒)

**背景執行機制**:
- 登入與資料抓取在背景執行緒執行 (`threading.Thread`)
- UI 更新透過 `self.after()` 回到主執行緒
- 避免阻塞 GUI,提升使用者體驗

### Testing Strategy

**單元測試覆蓋**:
- 總計 44 個測試案例
- 涵蓋核心業務邏輯 (calculator, version)
- 涵蓋資料模型 (attendance, report)
- 涵蓋服務層 (update_service)

**測試檔案結構**:
```
tests/
├── conftest.py              # Pytest 配置與 fixture
├── test_calculator.py       # 加班計算邏輯測試
├── test_models.py           # 資料模型測試
├── test_version.py          # 版本管理測試
└── test_update_service.py   # 更新服務測試
```

**執行測試**:
```bash
# 執行所有測試
pytest

# 執行特定測試檔案
pytest tests/test_calculator.py

# 執行測試並生成覆蓋率報告
pytest --cov=src --cov-report=html
```

**測試原則**:
- 每個核心功能都有對應測試
- 使用 Mock 隔離外部依賴 (如網路請求)
- 測試邊界條件與異常處理
- 保持測試簡潔且可讀

### Git Workflow

**分支策略**:
- `main`: 主分支,永遠保持可發布狀態
- 功能開發: 直接在 main 分支進行 (小型專案)
- 發布版本: 使用 Git Tag 標記 (如 `v1.1.1`)

**提交訊息格式**:
```
<類型>(<範圍>): <簡短描述>

<詳細描述>

<影響範圍>
```

**類型標籤**:
- `feat`: 新功能
- `fix`: Bug 修正
- `refactor`: 程式碼重構
- `docs`: 文件更新
- `test`: 測試相關
- `build`: 建置系統或工具變更
- `chore`: 其他雜項

**範例提交訊息**:
```
feat(ui): 新增統計儀表板卡片元件

- 新增 StatisticsCard 元件顯示關鍵指標
- 支援圖示、標題、數值、單位顯示
- 使用設計系統的顏色與間距

影響檔案: ui/components/statistics_card.py
```

### Version Management

**版本號規範 (Semantic Versioning)**:
- 格式: `MAJOR.MINOR.PATCH` (如 `1.1.1`)
- **MAJOR**: 不相容的 API 修改
- **MINOR**: 向下相容的功能新增
- **PATCH**: 向下相容的 Bug 修正

**單一真實來源 (SSOT)**:
- 版本號定義在 `src/core/version.py`
- PyInstaller 自動從此檔案讀取版本號
- 修改版本號只需編輯一處

**發布流程**:
1. 更新 `src/core/version.py` 的 `VERSION` 和 `VERSION_NAME`
2. 執行測試: `pytest`
3. 重新打包: `pyinstaller overtime_calculator.spec --clean`
4. 建立 Git Tag: `git tag -a v1.1.1 -m "Release v1.1.1"`
5. 推送 Tag: `git push origin v1.1.1`
6. 建立 GitHub Release 並上傳執行檔

## Domain Context

### 加班計算邏輯

**公式**:
```
加班時數 = 總工時 - 午休時間 - 正常工時 - 休息時間
加班時數 = 下班時間 - 上班時間 - 70分鐘 - 480分鐘 - 30分鐘
```

**時間設定** (可在 `src/config/settings.py` 調整):
- 午休時間: 70 分鐘
- 正常工時: 480 分鐘 (8 小時)
- 休息時間: 30 分鐘
- 標準上班時間: 08:00

**特殊處理**:
- 若上班時間晚於標準時間 (08:00),以標準時間計算
- 加班時數無條件進位至小數點後兩位
- 負數時數設為 0 (避免計算錯誤)
- 單日最大加班時數: 4 小時 (可設定)

### TECO SSP 系統特性

**技術棧**: ASP.NET Web Forms
- 使用 ViewState 維持狀態
- 使用 __EVENTTARGET 和 __EVENTARGUMENT 處理 PostBack
- GridView 控制項呈現表格資料

**資料結構**:
- 日期格式: `YYYY/MM/DD` (如 `2025/01/21`)
- 時間格式: `HH:MM:SS` (如 `08:30:00`)
- 時間範圍: `HH:MM:SS~HH:MM:SS` (如 `08:30:00~18:45:00`)

**分頁處理**:
- 每頁最多 10 筆記錄
- 透過 PostBack 觸發換頁
- 自動抓取所有頁面直到無資料

**SSL 憑證**: 內部系統使用自簽憑證,需設定 `verify=False`

## Important Constraints

### 技術限制
- **Windows 專用**: 使用 Windows Credential Manager,僅支援 Windows 平台
- **Python 版本**: 需要 Python 3.9 或以上版本
- **網路連線**: 必須能夠訪問 `https://ssp.teco.com.tw`
- **SSL 驗證**: 內部系統需停用 SSL 驗證 (`verify=False`)

### 業務限制
- **權限要求**: 使用者必須有 SSP 系統帳號與「出勤異常清單」權限
- **資料範圍**: 僅抓取當前可見的出勤記錄 (通常為當月)
- **時間精度**: 計算精度依賴 SSP 系統提供的打卡時間

### 安全限制
- **密碼儲存**: 使用 Fernet 對稱加密 + Windows Credential Manager
- **憑證管理**: 僅限本機使用者存取,無法跨使用者共用
- **自動登入**: 使用者需主動勾選「記住我」

### UI 限制
- **CustomTkinter**: 基於 Tkinter,功能有限 (無法使用現代 Web 技術)
- **深色主題**: 目前僅支援深色模式
- **字型**: 使用系統預設字型,無法自訂中文字型

## External Dependencies

### TECO SSP 系統 (必要)
- **URL**: `https://ssp.teco.com.tw`
- **用途**: 員工出勤資料來源
- **協定**: HTTPS (自簽憑證)
- **技術**: ASP.NET Web Forms
- **資料格式**: HTML 表格 (GridView)

### GitHub Releases API (選用)
- **URL**: `https://api.github.com/repos/jony-zhou/overtime-assistant/releases/latest`
- **用途**: 自動版本檢查
- **頻率**: 每次啟動檢查一次
- **失敗處理**: 靜默失敗,不影響主功能

### Windows Credential Manager (必要)
- **用途**: 安全儲存使用者憑證
- **API**: `keyring` Python 套件
- **平台**: 僅限 Windows
- **權限**: 需要本機使用者權限

### PyPI 套件 (必要)
- **來源**: `requirements.txt`
- **關鍵套件**: customtkinter, requests, beautifulsoup4, pandas, openpyxl, cryptography
- **安裝**: `pip install -r requirements.txt`
