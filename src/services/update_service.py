"""
應用程式更新檢查服務
使用 GitHub Releases API 檢查最新版本
"""
import requests
from typing import Optional, Dict, Any
from datetime import datetime, timedelta
from pathlib import Path
import json
import logging

from ..core.version import get_current_version, is_newer_version, VERSION

logger = logging.getLogger(__name__)


class UpdateService:
    """
    更新檢查服務
    
    職責:
    - 從 GitHub Releases API 取得最新版本資訊
    - 本地快取結果以避免頻繁 API 請求
    - 提供版本比較和下載連結
    """
    
    def __init__(
        self, 
        repo_owner: str = "jony-zhou",
        repo_name: str = "overtime-assistant",
        cache_duration_hours: int = 6
    ):
        """
        初始化更新服務
        
        Args:
            repo_owner: GitHub 倉庫擁有者
            repo_name: GitHub 倉庫名稱
            cache_duration_hours: 快取有效時長 (小時)
        """
        self.repo_owner = repo_owner
        self.repo_name = repo_name
        self.cache_duration = timedelta(hours=cache_duration_hours)
        self.cache_file = Path("cache") / "update_cache.json"
        self.api_url = f"https://api.github.com/repos/{repo_owner}/{repo_name}/releases/latest"
        
        # 建立快取目錄
        self.cache_file.parent.mkdir(exist_ok=True)
    
    def check_for_updates(self, timeout: int = 10) -> Optional[Dict[str, Any]]:
        """
        檢查是否有新版本
        
        Args:
            timeout: API 請求超時時間 (秒)
            
        Returns:
            Dict 包含更新資訊,如果沒有更新或發生錯誤則返回 None
            {
                'has_update': bool,
                'latest_version': str,
                'current_version': str,
                'release_notes': str,
                'download_url': str,
                'published_at': str
            }
        """
        try:
            # 每次啟動都檢查最新版本 (不使用快取)
            # 這確保使用者能及時收到更新通知
            logger.info(f"檢查更新: {self.api_url}")
            response = requests.get(
                self.api_url,
                timeout=timeout,
                headers={'Accept': 'application/vnd.github.v3+json'}
            )
            
            if response.status_code == 404:
                logger.warning("GitHub 倉庫或 Release 不存在")
                return None
            
            response.raise_for_status()
            release_data = response.json()
            
            # 解析版本資訊
            latest_version = release_data.get('tag_name', '').lstrip('v')
            current_version = VERSION
            
            if not latest_version:
                logger.warning("無法取得最新版本號")
                return None
            
            # 檢查是否有更新
            has_update = is_newer_version(current_version, latest_version)
            
            # 取得下載連結 (Windows EXE)
            download_url = self._get_windows_exe_url(release_data)
            
            update_info = {
                'has_update': has_update,
                'latest_version': latest_version,
                'current_version': current_version,
                'release_notes': release_data.get('body', ''),
                'download_url': download_url,
                'published_at': release_data.get('published_at', ''),
                'release_url': release_data.get('html_url', ''),  # 新增 Release 頁面連結
                'cached_at': datetime.now().isoformat()
            }
            
            # 不再儲存快取,每次都檢查最新版本
            # self._save_cache(update_info)
            
            if has_update:
                logger.info(f"發現新版本: {latest_version} (當前: {current_version})")
            else:
                logger.info(f"已是最新版本: {current_version}")
            
            return update_info
            
        except requests.exceptions.Timeout:
            logger.warning(f"更新檢查超時 ({timeout}s)")
            return None
        except requests.exceptions.ConnectionError:
            logger.warning("無法連線到 GitHub,請檢查網路")
            return None
        except requests.exceptions.RequestException as e:
            logger.error(f"更新檢查失敗: {e}")
            return None
        except Exception as e:
            logger.error(f"更新檢查時發生未預期錯誤: {e}", exc_info=True)
            return None
    
    def _get_windows_exe_url(self, release_data: Dict[str, Any]) -> str:
        """
        從 release 資料中取得 Windows EXE 下載連結
        
        Args:
            release_data: GitHub Release API 回應資料
            
        Returns:
            str: 下載連結,如果找不到則返回 release 頁面連結
        """
        assets = release_data.get('assets', [])
        
        # 尋找 .exe 檔案
        for asset in assets:
            name = asset.get('name', '').lower()
            if name.endswith('.exe'):
                return asset.get('browser_download_url', '')
        
        # 如果沒有找到 EXE,返回 release 頁面
        return release_data.get('html_url', f"https://github.com/{self.repo_owner}/{self.repo_name}/releases")
    
    def _load_cache(self) -> Optional[Dict[str, Any]]:
        """載入快取的更新資訊"""
        try:
            if not self.cache_file.exists():
                return None
            
            with open(self.cache_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            logger.debug(f"載入快取失敗: {e}")
            return None
    
    def _save_cache(self, data: Dict[str, Any]) -> None:
        """儲存更新資訊到快取"""
        try:
            with open(self.cache_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.debug(f"儲存快取失敗: {e}")
    
    def _is_cache_valid(self, cached_data: Dict[str, Any]) -> bool:
        """檢查快取是否仍然有效"""
        try:
            cached_at_str = cached_data.get('cached_at')
            if not cached_at_str:
                return False
            
            cached_at = datetime.fromisoformat(cached_at_str)
            age = datetime.now() - cached_at
            
            is_valid = age < self.cache_duration
            if not is_valid:
                logger.debug(f"快取已過期 (年齡: {age})")
            
            return is_valid
        except Exception as e:
            logger.debug(f"快取驗證失敗: {e}")
            return False
    
    def clear_cache(self) -> None:
        """清除快取"""
        try:
            if self.cache_file.exists():
                self.cache_file.unlink()
                logger.debug("已清除更新快取")
        except Exception as e:
            logger.warning(f"清除快取失敗: {e}")
