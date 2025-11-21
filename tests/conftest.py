"""測試配置"""
import sys
from pathlib import Path

# 將 src 加入路徑
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))
