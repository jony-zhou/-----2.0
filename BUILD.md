# PyInstaller 打包指南

## 產生 spec 檔案

如果需要重新產生或自訂 spec 檔案:

```bash
pyi-makespec --name="TECO加班計算器" --noconsole app.py
```

## 打包成單一執行檔

### 推薦方式 (完整重建)

```bash
# 使用虛擬環境的 Python (推薦)
.\venv\Scripts\python.exe -m PyInstaller overtime_calculator.spec --clean --noconfirm

# 或使用系統 Python
pyinstaller overtime_calculator.spec --clean --noconfirm
```

### 快速打包 (增量更新)

```bash
pyinstaller overtime_calculator.spec
```

## 打包參數說明

### spec 檔案選項
- `--onefile`: 打包成單一執行檔
- `--noconsole` / `console=False`: 不顯示終端機視窗
- `--name`: 執行檔名稱
- `--icon`: 指定圖示檔案 (.ico)
- `datas=[]`: 包含額外的資料檔案 (如圖示)
- `hiddenimports=[]`: 手動指定隱藏的模組依賴

### 命令列選項
- `--clean`: 清除暫存檔和快取,重新分析所有依賴 (建議使用)
- `--noconfirm`: 自動覆蓋輸出檔案,不詢問
- `--log-level`: 設定日誌等級 (DEBUG, INFO, WARN, ERROR)

## 輸出位置

- `dist/TECO加班計算器.exe`: 執行檔
- `build/`: 暫存建置檔案

## 測試執行檔

```bash
.\dist\TECO加班計算器.exe
```

## 注意事項

1. 首次執行可能需要較長時間啟動
2. 確保已安裝所有依賴套件
3. Windows Defender 可能會掃描執行檔
4. 檔案大小約 50-100MB (包含 Python 環境)

## 常見問題

### 打包失敗

確認已安裝 PyInstaller:
```bash
pip install pyinstaller
```

### 執行時缺少模組

在 spec 檔案的 `hiddenimports` 中加入缺少的模組:
```python
hiddenimports=['missing_module']
```

### CustomTkinter 相關問題

確保 spec 檔案包含:
```python
hiddenimports=['customtkinter', 'PIL._tkinter_finder']
```
