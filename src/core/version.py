"""
版本管理模組
遵循語義化版本規範 (Semantic Versioning 2.0.0)
"""
from dataclasses import dataclass
from typing import Tuple


# 當前版本號
VERSION = "1.1.0"
VERSION_NAME = "專業 UI/UX 大改版 + 記住我功能"


@dataclass(frozen=True)
class Version:
    """版本資訊 (不可變)"""
    major: int  # 主版本號 (不相容的 API 修改)
    minor: int  # 次版本號 (向下相容的功能性新增)
    patch: int  # 修訂號 (向下相容的問題修正)
    
    @classmethod
    def from_string(cls, version_str: str) -> 'Version':
        """
        從版本字串解析
        
        Args:
            version_str: 版本字串,如 "0.1.0" 或 "v0.1.0"
            
        Returns:
            Version 實例
            
        Raises:
            ValueError: 版本字串格式錯誤
        """
        # 移除可能的 'v' 前綴
        clean_version = version_str.strip().lstrip('v')
        
        try:
            parts = clean_version.split('.')
            if len(parts) != 3:
                raise ValueError(f"版本號必須是 X.Y.Z 格式,收到: {version_str}")
            
            major, minor, patch = map(int, parts)
            return cls(major=major, minor=minor, patch=patch)
        except (ValueError, AttributeError) as e:
            raise ValueError(f"無效的版本字串: {version_str}") from e
    
    def to_string(self) -> str:
        """轉換為標準版本字串"""
        return f"{self.major}.{self.minor}.{self.patch}"
    
    def to_tuple(self) -> Tuple[int, int, int]:
        """轉換為元組以便比較"""
        return (self.major, self.minor, self.patch)
    
    def __str__(self) -> str:
        return self.to_string()
    
    def __lt__(self, other: 'Version') -> bool:
        """小於比較"""
        return self.to_tuple() < other.to_tuple()
    
    def __le__(self, other: 'Version') -> bool:
        """小於等於比較"""
        return self.to_tuple() <= other.to_tuple()
    
    def __gt__(self, other: 'Version') -> bool:
        """大於比較"""
        return self.to_tuple() > other.to_tuple()
    
    def __ge__(self, other: 'Version') -> bool:
        """大於等於比較"""
        return self.to_tuple() >= other.to_tuple()
    
    def __eq__(self, other: object) -> bool:
        """等於比較"""
        if not isinstance(other, Version):
            return False
        return self.to_tuple() == other.to_tuple()


def get_current_version() -> Version:
    """取得當前應用程式版本"""
    return Version.from_string(VERSION)


def is_newer_version(current: str, latest: str) -> bool:
    """
    比較版本是否有更新
    
    Args:
        current: 當前版本字串
        latest: 最新版本字串
        
    Returns:
        bool: latest 是否比 current 新
    """
    try:
        current_ver = Version.from_string(current)
        latest_ver = Version.from_string(latest)
        return latest_ver > current_ver
    except ValueError:
        # 版本格式錯誤時保守處理,認為沒有更新
        return False
