"""Validation tests for Pydantic response and query parameter models."""

import pytest
from pydantic import ValidationError

from src.models import (
    AttentionBanner,
    BaseResponse,
    FilterItem,
    FiltersData,
    KpiTile,
    OverviewData,
    OverviewMetrics,
    PeriodEnum,
    StatusBreakdownItem,
    StatusDistribution,
)


class TestKpiTile:
    """Tests for KpiTile model validation."""

    def test_valid_kpi_tile(self):
        tile = KpiTile(count=5, trend="increase", change=2)
        assert tile.count == 5
        assert tile.trend == "increase"
        assert tile.change == 2

    def test_kpi_tile_null_trend(self):
        tile = KpiTile(count=0, trend=None, change=0)
        assert tile.trend is None

    def test_kpi_tile_rejects_negative_count(self):
        with pytest.raises(ValidationError):
            KpiTile(count=-1, trend="flat", change=0)

    def test_kpi_tile_rejects_negative_change(self):
        with pytest.raises(ValidationError):
            KpiTile(count=0, trend="flat", change=-1)

    def test_kpi_tile_rejects_invalid_trend(self):
        with pytest.raises(ValidationError):
            KpiTile(count=0, trend="invalid", change=0)


class TestBaseResponse:
    """Tests for BaseResponse model validation."""

    def test_valid_success_response(self):
        resp = BaseResponse(status_code=200, status="success", message="OK", data={"key": "value"})
        assert resp.status_code == 200
        assert resp.status == "success"
        assert resp.data == {"key": "value"}

    def test_valid_failed_response(self):
        resp = BaseResponse(status_code=400, status="failed", message="Bad request", data=[])
        assert resp.status == "failed"
        assert resp.data == []

    def test_valid_error_response(self):
        resp = BaseResponse(status_code=500, status="error", message="Server error", data=[])
        assert resp.status == "error"

    def test_rejects_invalid_status(self):
        with pytest.raises(ValidationError):
            BaseResponse(status_code=200, status="unknown", message="msg", data={})

    def test_rejects_message_over_256_chars(self):
        with pytest.raises(ValidationError):
            BaseResponse(status_code=200, status="success", message="x" * 257, data={})

    def test_accepts_message_at_256_chars(self):
        resp = BaseResponse(status_code=200, status="success", message="x" * 256, data={})
        assert len(resp.message) == 256


class TestStatusBreakdownItem:
    """Tests for StatusBreakdownItem model validation."""

    def test_valid_item(self):
        item = StatusBreakdownItem(status="Active", count=10, percentage=50.0)
        assert item.status == "Active"
        assert item.count == 10
        assert item.percentage == 50.0

    def test_rejects_negative_count(self):
        with pytest.raises(ValidationError):
            StatusBreakdownItem(status="Active", count=-1, percentage=50.0)

    def test_rejects_percentage_over_100(self):
        with pytest.raises(ValidationError):
            StatusBreakdownItem(status="Active", count=10, percentage=100.1)

    def test_rejects_negative_percentage(self):
        with pytest.raises(ValidationError):
            StatusBreakdownItem(status="Active", count=10, percentage=-0.1)


class TestStatusDistribution:
    """Tests for StatusDistribution model validation."""

    def test_valid_distribution(self):
        dist = StatusDistribution(
            total=20,
            breakdown=[
                StatusBreakdownItem(status="Active", count=10, percentage=50.0),
                StatusBreakdownItem(status="Completed", count=10, percentage=50.0),
            ],
        )
        assert dist.total == 20
        assert len(dist.breakdown) == 2

    def test_rejects_negative_total(self):
        with pytest.raises(ValidationError):
            StatusDistribution(total=-1, breakdown=[])


class TestAttentionBanner:
    """Tests for AttentionBanner model validation."""

    def test_valid_critical_banner(self):
        banner = AttentionBanner(message="5 projects at risk", at_risk_count=5, severity="critical")
        assert banner.severity == "critical"

    def test_valid_warning_banner(self):
        banner = AttentionBanner(message="3 projects at risk", at_risk_count=3, severity="warning")
        assert banner.severity == "warning"

    def test_valid_info_banner(self):
        banner = AttentionBanner(message="No projects at risk", at_risk_count=0, severity="info")
        assert banner.severity == "info"

    def test_rejects_message_over_200_chars(self):
        with pytest.raises(ValidationError):
            AttentionBanner(message="x" * 201, at_risk_count=0, severity="info")

    def test_rejects_negative_at_risk_count(self):
        with pytest.raises(ValidationError):
            AttentionBanner(message="msg", at_risk_count=-1, severity="info")

    def test_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            AttentionBanner(message="msg", at_risk_count=0, severity="high")


class TestOverviewData:
    """Tests for OverviewData composite model."""

    def test_valid_overview_data(self):
        tile = KpiTile(count=0, trend="flat", change=0)
        metrics = OverviewMetrics(
            total_projects=tile,
            completed=tile,
            active=tile,
            inactive=tile,
            at_risk=tile,
            not_applicable=tile,
        )
        dist = StatusDistribution(total=0, breakdown=[])
        banner = AttentionBanner(message="No projects at risk", at_risk_count=0, severity="info")
        data = OverviewData(metrics=metrics, status_distribution=dist, attention_banner=banner)
        assert data.metrics.total_projects.count == 0


class TestFilterModels:
    """Tests for FilterItem and FiltersData models."""

    def test_valid_filter_item(self):
        item = FilterItem(id="abc-123", name="Test")
        assert item.id == "abc-123"
        assert item.name == "Test"

    def test_valid_filters_data(self):
        data = FiltersData(
            specializations=[FilterItem(id="1", name="Spec A")],
            clients=[FilterItem(id="2", name="Client B")],
            statuses=[FilterItem(id="3", name="Active")],
        )
        assert len(data.specializations) == 1
        assert len(data.clients) == 1
        assert len(data.statuses) == 1

    def test_empty_filters_data(self):
        data = FiltersData(specializations=[], clients=[], statuses=[])
        assert data.specializations == []
        assert data.clients == []
        assert data.statuses == []


class TestPeriodEnum:
    """Tests for PeriodEnum validation."""

    def test_valid_last_week(self):
        assert PeriodEnum("last_week") == PeriodEnum.LAST_WEEK

    def test_valid_last_month(self):
        assert PeriodEnum("last_month") == PeriodEnum.LAST_MONTH

    def test_valid_last_3_months(self):
        assert PeriodEnum("last_3_months") == PeriodEnum.LAST_3_MONTHS

    def test_rejects_invalid_value(self):
        with pytest.raises(ValueError):
            PeriodEnum("invalid")

    def test_case_sensitive_rejection(self):
        with pytest.raises(ValueError):
            PeriodEnum("Last_Week")

    def test_case_sensitive_rejection_uppercase(self):
        with pytest.raises(ValueError):
            PeriodEnum("LAST_WEEK")

    def test_enum_string_equality(self):
        assert PeriodEnum.LAST_WEEK == "last_week"
        assert PeriodEnum.LAST_MONTH == "last_month"
        assert PeriodEnum.LAST_3_MONTHS == "last_3_months"
