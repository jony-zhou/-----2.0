"""測試資料模型"""
import pytest
from datetime import datetime
from src.models import AttendanceRecord, OvertimeReport


class TestAttendanceRecord:
    """測試出勤記錄模型"""
    
    def test_create_record(self):
        """測試建立記錄"""
        record = AttendanceRecord(
            date='2024/10/28',
            start_time='08:30:00',
            end_time='18:00:00',
            total_minutes=570,
            overtime_hours=1.5
        )
        
        assert record.date == '2024/10/28'
        assert record.start_time == '08:30:00'
        assert record.end_time == '18:00:00'
        assert record.overtime_hours == 1.5
    
    def test_date_properties(self):
        """測試日期屬性"""
        record = AttendanceRecord(
            date='2024/10/28',
            start_time='08:30:00',
            end_time='18:00:00'
        )
        
        assert isinstance(record.date_obj, datetime)
        assert isinstance(record.start_datetime, datetime)
        assert isinstance(record.end_datetime, datetime)
    
    def test_record_hash(self):
        """測試記錄雜湊 (用於去重)"""
        record1 = AttendanceRecord(
            date='2024/10/28',
            start_time='08:30:00',
            end_time='18:00:00'
        )
        
        record2 = AttendanceRecord(
            date='2024/10/28',
            start_time='08:30:00',
            end_time='18:00:00'
        )
        
        # 相同內容應該有相同的 hash
        assert hash(record1) == hash(record2)


class TestOvertimeReport:
    """測試加班報表模型"""
    
    @pytest.fixture
    def sample_records(self):
        """測試用記錄"""
        return [
            AttendanceRecord(
                date='2024/10/28',
                start_time='08:30:00',
                end_time='18:00:00',
                overtime_hours=1.5
            ),
            AttendanceRecord(
                date='2024/10/29',
                start_time='09:00:00',
                end_time='19:00:00',
                overtime_hours=2.0
            ),
            AttendanceRecord(
                date='2024/10/30',
                start_time='08:00:00',
                end_time='17:30:00',
                overtime_hours=0.0
            )
        ]
    
    def test_create_report(self, sample_records):
        """測試建立報表"""
        report = OvertimeReport(records=sample_records)
        
        assert len(report.records) == 3
        assert isinstance(report.generated_at, datetime)
    
    def test_total_days(self, sample_records):
        """測試記錄天數"""
        report = OvertimeReport(records=sample_records)
        assert report.total_days == 3
    
    def test_overtime_days(self, sample_records):
        """測試加班天數"""
        report = OvertimeReport(records=sample_records)
        assert report.overtime_days == 2  # 只有前兩筆有加班
    
    def test_total_overtime_hours(self, sample_records):
        """測試總加班時數"""
        report = OvertimeReport(records=sample_records)
        assert report.total_overtime_hours == 3.5  # 1.5 + 2.0 + 0.0
    
    def test_average_overtime_hours(self, sample_records):
        """測試平均加班時數"""
        report = OvertimeReport(records=sample_records)
        expected_avg = 3.5 / 3
        assert abs(report.average_overtime_hours - expected_avg) < 0.01
    
    def test_max_overtime(self, sample_records):
        """測試最長加班"""
        report = OvertimeReport(records=sample_records)
        assert report.max_overtime_hours == 2.0
        assert report.max_overtime_date == '2024/10/29'
    
    def test_get_summary(self, sample_records):
        """測試統計摘要"""
        report = OvertimeReport(records=sample_records)
        summary = report.get_summary()
        
        assert summary['記錄天數'] == 3
        assert summary['加班天數'] == 2
        assert '3.5' in summary['總加班時數']
        assert summary['最長加班日期'] == '2024/10/29'
    
    def test_empty_report(self):
        """測試空報表"""
        report = OvertimeReport()
        
        assert report.total_days == 0
        assert report.overtime_days == 0
        assert report.total_overtime_hours == 0
        assert report.average_overtime_hours == 0
        assert report.max_overtime_hours == 0
        assert report.max_overtime_date == ""
