"""測試加班補報資料模型"""

import pytest
from src.models import OvertimeReport, AttendanceRecord
from src.models.overtime_submission import (
    OvertimeSubmissionRecord,
    OvertimeSubmissionStatus,
    SubmittedRecord,
)


class TestOvertimeSubmissionStatus:
    """測試加班補報狀態列舉"""

    def test_status_values(self):
        """測試狀態值"""
        assert OvertimeSubmissionStatus.NOT_SUBMITTED.value == "未申請"
        assert OvertimeSubmissionStatus.SUBMITTED.value == "已申請"
        assert OvertimeSubmissionStatus.IN_REVIEW.value == "簽核中"
        assert OvertimeSubmissionStatus.APPROVED.value == "簽核完成"
        assert OvertimeSubmissionStatus.REJECTED.value == "已撤回"


class TestOvertimeSubmissionRecord:
    """測試加班補報記錄"""

    def test_create_record(self):
        """測試建立記錄"""
        record = OvertimeSubmissionRecord(
            date="2024/11/26",
            description="加班作業",
            overtime_hours=2.5,
            is_overtime=True,
            is_selected=True,
        )

        assert record.date == "2024/11/26"
        assert record.description == "加班作業"
        assert record.overtime_hours == 2.5
        assert record.is_overtime is True
        assert record.is_selected is True
        assert record.submitted_status is None

    def test_overtime_minutes_property(self):
        """測試加班分鐘數屬性"""
        record = OvertimeSubmissionRecord(
            date="2024/11/26", description="測試", overtime_hours=2.5
        )

        assert record.overtime_minutes == 150  # 2.5 * 60

    def test_change_minutes_property(self):
        """測試調休分鐘數屬性"""
        overtime_record = OvertimeSubmissionRecord(
            date="2024/11/26", description="測試", overtime_hours=2.0, is_overtime=True
        )
        assert overtime_record.change_minutes == 0

        leave_record = OvertimeSubmissionRecord(
            date="2024/11/26", description="測試", overtime_hours=2.0, is_overtime=False
        )
        assert leave_record.change_minutes == 120  # 2.0 * 60

    def test_is_submitted_property(self):
        """測試是否已申請屬性"""
        # 未申請
        record1 = OvertimeSubmissionRecord(
            date="2024/11/26", description="測試", overtime_hours=2.0
        )
        assert record1.is_submitted is False

        # 已申請
        record2 = OvertimeSubmissionRecord(
            date="2024/11/26",
            description="測試",
            overtime_hours=2.0,
            submitted_status="簽核中",
        )
        assert record2.is_submitted is True


class TestSubmittedRecord:
    """測試已申請記錄"""

    def test_create_submitted_record(self):
        """測試建立已申請記錄"""
        record = SubmittedRecord(
            date="2024/11/26",
            status="簽核中",
            overtime_minutes=150.0,
            change_minutes=0.0,
        )

        assert record.date == "2024/11/26"
        assert record.status == "簽核中"
        assert record.overtime_minutes == 150.0
        assert record.change_minutes == 0.0

    def test_is_overtime_property(self):
        """測試是否為加班屬性"""
        # 加班記錄
        overtime_record = SubmittedRecord(
            date="2024/11/26",
            status="簽核完成",
            overtime_minutes=120.0,
            change_minutes=0.0,
        )
        assert overtime_record.is_overtime is True

        # 調休記錄
        leave_record = SubmittedRecord(
            date="2024/11/27",
            status="簽核完成",
            overtime_minutes=0.0,
            change_minutes=120.0,
        )
        assert leave_record.is_overtime is False


class TestOvertimeReportConversion:
    """測試 OvertimeReport 轉換為 SubmissionRecord"""

    @pytest.fixture
    def sample_report(self):
        """建立測試報表"""
        records = [
            AttendanceRecord(
                date="2024/11/25",
                start_time="08:30:00",
                end_time="20:00:00",
                overtime_hours=2.5,
            ),
            AttendanceRecord(
                date="2024/11/26",
                start_time="08:30:00",
                end_time="18:00:00",
                overtime_hours=0.0,  # 無加班
            ),
            AttendanceRecord(
                date="2024/11/27",
                start_time="09:00:00",
                end_time="21:30:00",
                overtime_hours=3.5,
            ),
        ]
        return OvertimeReport(records=records)

    def test_to_submission_records(self, sample_report):
        """測試轉換為補報記錄"""
        submission_records = sample_report.to_submission_records()

        # 應該只包含有加班的記錄 (2 筆)
        assert len(submission_records) == 2

        # 檢查第一筆
        record1 = submission_records[0]
        assert record1.date == "2024/11/25"
        assert record1.overtime_hours == 2.5
        # 新功能：加班內容為空（必須由使用者填寫）
        assert record1.description == ""
        assert record1.is_overtime is True
        assert record1.is_selected is True

        # 檢查第二筆
        record2 = submission_records[1]
        assert record2.date == "2024/11/27"
        assert record2.overtime_hours == 3.5

    def test_to_submission_records_empty_description(self, sample_report):
        """測試預設空描述（新功能：必須由使用者填寫）"""
        submission_records = sample_report.to_submission_records()

        # 所有記錄的描述都應該是空的
        assert all(r.description == "" for r in submission_records)

    def test_to_submission_records_empty_report(self):
        """測試空報表"""
        empty_report = OvertimeReport(records=[])
        submission_records = empty_report.to_submission_records()

        assert len(submission_records) == 0

    def test_to_submission_records_no_overtime(self):
        """測試無加班記錄"""
        records = [
            AttendanceRecord(
                date="2024/11/26",
                start_time="08:30:00",
                end_time="18:00:00",
                overtime_hours=0.0,
            )
        ]
        report = OvertimeReport(records=records)
        submission_records = report.to_submission_records()

        assert len(submission_records) == 0
