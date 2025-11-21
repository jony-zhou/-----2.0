# 快速開始指南

## 1. 安裝依賴

```bash
# 使用虛擬環境的 Python (推薦)
.\.venv\Scripts\python.exe -m pip install -r requirements.txt

# 或使用系統 Python
pip install -r requirements.txt
```

## 2. 執行應用程式

```bash
# 使用虛擬環境
.\.venv\Scripts\python.exe app.py

# 或使用系統 Python
python app.py
```

## 3. 使用步驟

1. **登入**: 輸入 SSP 帳號和密碼
2. **等待**: 系統自動抓取出勤資料並計算加班時數
3. **查看報表**: 檢視出勤記錄和統計資訊
4. **匯出**: 點擊「匯出 Excel」按鈕儲存報表

## 4. 開發者指南

### 執行測試

```bash
# 使用虛擬環境
.\venv\Scripts\python.exe -m pytest

# 查看測試覆蓋率
.\venv\Scripts\python.exe -m pytest --cov=src --cov-report=html
```

### 打包成執行檔

```bash
# 完整重新打包 (推薦)
.\venv\Scripts\python.exe -m PyInstaller overtime_calculator.spec --clean --noconfirm

# 快速打包 (增量)
.\venv\Scripts\python.exe -m PyInstaller overtime_calculator.spec
```

執行檔位於 `dist/TECO加班計算器.exe`

### 圖示檔案

專案使用的應用程式圖示:
- `assets/icon.png`: PNG 格式 (原始圖檔)
- `assets/icon.ico`: ICO 格式 (Windows 圖示)

打包時會自動包含這兩個檔案,執行檔的檔案圖示和視窗圖示都會使用 `icon.ico`

## 5. 專案結構說明

```
overtime-assistant/
├── src/                # 核心程式碼
│   ├── core/          # 業務邏輯 (加班計算)
│   ├── models/        # 資料模型
│   ├── services/      # 服務層 (認證、資料擷取、匯出)
│   ├── config/        # 配置設定
│   └── utils/         # 工具函式
├── ui/                # 使用者介面
│   ├── components/    # UI 元件
│   └── main_window.py # 主視窗
├── tests/             # 單元測試
├── app.py            # 應用程式入口
└── main.py           # 舊版 CLI (已棄用)
```

## 6. 配置調整

修改 `src/config/settings.py`:

```python
LUNCH_BREAK = 70        # 午休時間 (分鐘)
WORK_HOURS = 480        # 正常工時 (分鐘)
REST_TIME = 30          # 休息時間 (分鐘)
MAX_OVERTIME_HOURS = 4  # 最大加班時數
STANDARD_START_HOUR = 9 # 標準上班時間
```

## 7. 常見問題

### Q: GUI 無法啟動?
A: 確保使用虛擬環境的 Python 並已安裝所有依賴

### Q: 登入失敗?
A: 檢查帳號密碼,確認可連線到 SSP 系統

### Q: 測試失敗?
A: 確保所有依賴已安裝,執行 `pip install -r requirements.txt`

### Q: 打包後執行檔很大?
A: 這是正常的,因為包含了 Python 環境和所有依賴

## 8. 技術支援

- 查看日誌: `logs/overtime_calculator.log`
- 檢查報表: `reports/` 資料夾
- 執行測試: 確保所有測試通過

## 9. 版本資訊

- **v2.0**: 全新 GUI 版本,模組化架構
- **v1.x**: 舊版 CLI (main.py)
