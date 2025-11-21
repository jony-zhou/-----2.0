#!/usr/bin/env python3
"""
TECO SSP 加班時數計算器 v0.1.0
GUI 應用程式入口
"""

from src.utils import setup_logging
from ui import MainWindow


def main():
    """主程式入口"""
    # 設定日誌
    setup_logging()
    
    # 啟動 GUI
    app = MainWindow()
    app.mainloop()


if __name__ == "__main__":
    main()
