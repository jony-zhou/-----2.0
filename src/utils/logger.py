"""工具函式"""
import logging
import sys
from pathlib import Path


def setup_logging():
    """設定日誌系統"""
    # 建立 logs 資料夾
    Path('logs').mkdir(exist_ok=True)
    
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout),
            logging.FileHandler('logs/overtime_calculator.log', encoding='utf-8')
        ]
    )
