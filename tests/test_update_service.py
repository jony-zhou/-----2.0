"""
更新服務測試
"""
import pytest
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path
import json
from datetime import datetime, timedelta

from src.services.update_service import UpdateService


class TestUpdateService:
    """測試 UpdateService 類別"""
    
    def setup_method(self):
        """測試前設定"""
        self.service = UpdateService(
            repo_owner="test_owner",
            repo_name="test_repo",
            cache_duration_hours=1
        )
        # 清除可能存在的快取
        if self.service.cache_file.exists():
            self.service.cache_file.unlink()
    
    def teardown_method(self):
        """測試後清理"""
        # 清除測試產生的快取
        if self.service.cache_file.exists():
            self.service.cache_file.unlink()
    
    def test_init(self):
        """測試初始化"""
        assert self.service.repo_owner == "test_owner"
        assert self.service.repo_name == "test_repo"
        assert self.service.api_url == "https://api.github.com/repos/test_owner/test_repo/releases/latest"
    
    @patch('src.services.update_service.requests.get')
    def test_check_for_updates_has_update(self, mock_get):
        """測試檢查更新 - 有新版本"""
        # 模擬 API 回應
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'tag_name': 'v999.0.0',  # 遠大於當前版本
            'body': '新功能',
            'html_url': 'https://github.com/test/repo/releases/tag/v999.0.0',
            'published_at': '2025-11-21T00:00:00Z',
            'assets': [
                {
                    'name': 'app.exe',
                    'browser_download_url': 'https://github.com/test/app.exe'
                }
            ]
        }
        mock_get.return_value = mock_response
        
        result = self.service.check_for_updates()
        
        assert result is not None
        assert result['has_update'] is True
        assert result['latest_version'] == '999.0.0'
        assert result['download_url'] == 'https://github.com/test/app.exe'
        assert result['release_url'] == 'https://github.com/test/repo/releases/tag/v999.0.0'
    
    @patch('src.services.update_service.requests.get')
    def test_check_for_updates_no_update(self, mock_get):
        """測試檢查更新 - 已是最新版"""
        # 模擬 API 回應 (版本號與當前相同)
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'tag_name': 'v0.1.0',  # 與當前版本相同
            'body': '',
            'html_url': 'https://github.com/test/repo',
            'published_at': '2025-11-21T00:00:00Z',
            'assets': []
        }
        mock_get.return_value = mock_response
        
        result = self.service.check_for_updates()
        
        assert result is not None
        assert result['has_update'] is False
    
    @patch('src.services.update_service.requests.get')
    def test_check_for_updates_timeout(self, mock_get):
        """測試檢查更新 - 超時"""
        import requests
        mock_get.side_effect = requests.exceptions.Timeout()
        
        result = self.service.check_for_updates(timeout=1)
        
        assert result is None
    
    @patch('src.services.update_service.requests.get')
    def test_check_for_updates_connection_error(self, mock_get):
        """測試檢查更新 - 連線錯誤"""
        import requests
        mock_get.side_effect = requests.exceptions.ConnectionError()
        
        result = self.service.check_for_updates()
        
        assert result is None
    
    @patch('src.services.update_service.requests.get')
    def test_check_for_updates_404(self, mock_get):
        """測試檢查更新 - 倉庫不存在"""
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.return_value = mock_response
        
        result = self.service.check_for_updates()
        
        assert result is None
    
    def test_get_windows_exe_url_with_exe(self):
        """測試取得 EXE 下載連結 - 有 EXE 檔案"""
        release_data = {
            'html_url': 'https://github.com/test/repo',
            'assets': [
                {
                    'name': 'app.exe',
                    'browser_download_url': 'https://github.com/test/app.exe'
                }
            ]
        }
        
        url = self.service._get_windows_exe_url(release_data)
        assert url == 'https://github.com/test/app.exe'
    
    def test_get_windows_exe_url_without_exe(self):
        """測試取得 EXE 下載連結 - 無 EXE 檔案"""
        release_data = {
            'html_url': 'https://github.com/test/repo',
            'assets': []
        }
        
        url = self.service._get_windows_exe_url(release_data)
        assert url == 'https://github.com/test/repo'
    
    def test_cache_save_and_load(self):
        """測試快取儲存和載入 (保留功能但不使用)"""
        test_data = {
            'has_update': True,
            'latest_version': '1.0.0',
            'cached_at': datetime.now().isoformat()
        }
        
        # 儲存快取
        self.service._save_cache(test_data)
        
        # 載入快取
        loaded_data = self.service._load_cache()
        
        assert loaded_data is not None
        assert loaded_data['has_update'] is True
        assert loaded_data['latest_version'] == '1.0.0'
    
    def test_cache_valid(self):
        """測試快取有效性檢查 (保留功能但不使用)"""
        # 新快取應該有效
        cached_data = {
            'cached_at': datetime.now().isoformat()
        }
        assert self.service._is_cache_valid(cached_data) is True
        
        # 過期快取應該無效
        old_data = {
            'cached_at': (datetime.now() - timedelta(hours=7)).isoformat()
        }
        assert self.service._is_cache_valid(old_data) is False
    
    def test_clear_cache(self):
        """測試清除快取"""
        # 建立快取
        test_data = {'test': 'data'}
        self.service._save_cache(test_data)
        assert self.service.cache_file.exists()
        
        # 清除快取
        self.service.clear_cache()
        assert not self.service.cache_file.exists()
    
    @patch('src.services.update_service.requests.get')
    def test_always_check_no_cache(self, mock_get):
        """測試每次啟動都檢查,不使用快取"""
        # 第一次請求會呼叫 API
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            'tag_name': 'v1.0.0',
            'body': '',
            'html_url': 'https://github.com/test',
            'published_at': '2025-11-21T00:00:00Z',
            'assets': []
        }
        mock_get.return_value = mock_response
        
        result1 = self.service.check_for_updates()
        assert mock_get.call_count == 1
        
        # 第二次請求應該再次呼叫 API (不使用快取)
        result2 = self.service.check_for_updates()
        assert mock_get.call_count == 2  # 應該增加
        
        # 兩次結果應該相同
        assert result1['latest_version'] == result2['latest_version']
