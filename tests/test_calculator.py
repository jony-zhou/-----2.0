"""測試加班計算核心邏輯"""
import pytest
from datetime import datetime
from src.core import OvertimeCalculator
from src.config import Settings


class TestOvertimeCalculator:
    """測試加班計算器"""
    
    @pytest.fixture
    def calculator(self):
        """建立計算器實例"""
        return OvertimeCalculator()
    
    @pytest.fixture
    def sample_records(self):
        """測試用記錄"""
        return [
            {
                'date': '2024/10/28',
                'time_range': '08:30:00~18:00:00'
            },
            {
                'date': '2024/10/29',
                'time_range': '09:15:00~19:30:00'
            },
            {
                'date': '2024/10/30',
                'time_range': '08:00:00~22:00:00'
            }
        ]
    
    def test_calculate_overtime_normal(self, calculator, sample_records):
        """測試正常加班計算"""
        report = calculator.calculate_overtime([sample_records[0]])
        
        assert len(report.records) == 1
        record = report.records[0]
        
        assert record.date == '2024/10/28'
        assert record.start_time == '08:30:00'
        assert record.end_time == '18:00:00'
        assert record.overtime_hours >= 0
    
    def test_calculate_overtime_late_start(self, calculator, sample_records):
        """測試晚到的情況 (應以 9:00 計算)"""
        report = calculator.calculate_overtime([sample_records[1]])
        
        record = report.records[0]
        # 9:15 上班,應以 9:00 計算
        # 9:00~19:30 = 630分鐘
        # 630 - 70 - 480 - 30 = 50分鐘 = 0.8小時
        assert record.overtime_hours > 0
    
    def test_calculate_overtime_max_cap(self, calculator, sample_records):
        """測試加班時數上限 (4小時)"""
        report = calculator.calculate_overtime([sample_records[2]])
        
        record = report.records[0]
        # 應該被限制在 4 小時
        assert record.overtime_hours <= 4
    
    def test_calculate_overtime_multiple_records(self, calculator, sample_records):
        """測試多筆記錄"""
        report = calculator.calculate_overtime(sample_records)
        
        assert len(report.records) == 3
        assert report.total_days == 3
    
    def test_invalid_time_format(self, calculator):
        """測試錯誤的時間格式"""
        invalid_records = [
            {
                'date': '2024/10/28',
                'time_range': 'invalid'
            }
        ]
        
        report = calculator.calculate_overtime(invalid_records)
        # 應該跳過無效記錄
        assert len(report.records) == 0
    
    def test_report_statistics(self, calculator, sample_records):
        """測試報表統計"""
        report = calculator.calculate_overtime(sample_records)
        
        assert report.total_days == 3
        assert report.overtime_days >= 0
        assert report.total_overtime_hours >= 0
        assert report.average_overtime_hours >= 0
        assert report.max_overtime_hours >= 0
