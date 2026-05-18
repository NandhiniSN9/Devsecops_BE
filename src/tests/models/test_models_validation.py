"""Validation tests for Pydantic response and query parameter models."""

import pytest
from pydantic import ValidationError

from src.dtos.request.overview_request import PeriodEnum
from src.dtos.response.base_response import BaseResponse
from src.dtos.response.filter_response import FilterItemResponse, FiltersDataResponse
from src.dtos.response.overview_response import (
    AttentionBannerResponse,
    KpiTileResponse,
    OverviewDataResponse,
    OverviewMetricsResponse,
    StatusBreakdownItemResponse,
    StatusDistributionResponse,
    SyncDetailResponse,
)


class TestKpiTile:
    """Tests for KpiTileResponse model validation."""

    def test_valid_kpi_tile(self):
        tile = KpiTileResponse(count=5, trend="increase", change=2)
        assert tile.count == 5
        assert tile.trend == "increase"
        assert tile.change == 2

    def test_kpi_tile_null_trend(self):
        tile = KpiTileResponse(count=0, trend=None, change=0)
        assert tile.trend is None

    def test_kpi_tile_rejects_negative_count(self):
        with pytest.raises(ValidationError):
            KpiTileResponse(count=-1, trend="flat", change=0)

    def test_kpi_tile_rejects_negative_change(self):
        with pytest.raises(ValidationError):
            KpiTileResponse(count=0, trend="flat", change=-1)

    def test_kpi_tile_rejects_invalid_trend(self):
        with pytest.raises(ValidationError):
            KpiTileResponse(count=0, trend="invalid", change=0)


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
    """Tests for StatusBreakdownItemResponse model validation."""

    def test_valid_item(self):
        item = StatusBreakdownItemResponse(status="Active", count=10, percentage=50.0)
        assert item.status == "Active"
        assert item.count == 10
        assert item.percentage == 50.0

    def test_rejects_negative_count(self):
        with pytest.raises(ValidationError):
            StatusBreakdownItemResponse(status="Active", count=-1, percentage=50.0)

    def test_rejects_percentage_over_100(self):
        with pytest.raises(ValidationError):
            StatusBreakdownItemResponse(status="Active", count=10, percentage=100.1)

    def test_rejects_negative_percentage(self):
        with pytest.raises(ValidationError):
            StatusBreakdownItemResponse(status="Active", count=10, percentage=-0.1)


class TestStatusDistribution:
    """Tests for StatusDistributionResponse model validation."""

    def test_valid_distribution(self):
        dist = StatusDistributionResponse(
            total=20,
            breakdown=[
                StatusBreakdownItemResponse(status="Active", count=10, percentage=50.0),
                StatusBreakdownItemResponse(status="Completed", count=10, percentage=50.0),
            ],
        )
        assert dist.total == 20
        assert len(dist.breakdown) == 2

    def test_rejects_negative_total(self):
        with pytest.raises(ValidationError):
            StatusDistributionResponse(total=-1, breakdown=[])


class TestAttentionBanner:
    """Tests for AttentionBannerResponse model validation."""

    def test_valid_critical_banner(self):
        banner = AttentionBannerResponse(message="5 projects at risk", at_risk_count=5, severity="critical")
        assert banner.severity == "critical"

    def test_valid_warning_banner(self):
        banner = AttentionBannerResponse(message="3 projects at risk", at_risk_count=3, severity="warning")
        assert banner.severity == "warning"

    def test_valid_info_banner(self):
        banner = AttentionBannerResponse(message="No projects at risk", at_risk_count=0, severity="info")
        assert banner.severity == "info"

    def test_rejects_message_over_200_chars(self):
        with pytest.raises(ValidationError):
            AttentionBannerResponse(message="x" * 201, at_risk_count=0, severity="info")

    def test_rejects_negative_at_risk_count(self):
        with pytest.raises(ValidationError):
            AttentionBannerResponse(message="msg", at_risk_count=-1, severity="info")

    def test_rejects_invalid_severity(self):
        with pytest.raises(ValidationError):
            AttentionBannerResponse(message="msg", at_risk_count=0, severity="high")


class TestOverviewData:
    """Tests for OverviewDataResponse composite model."""

    def test_valid_overview_data(self):
        tile = KpiTileResponse(count=0, trend="flat", change=0)
        metrics = OverviewMetricsResponse(
            total_projects=tile,
            completed=tile,
            active=tile,
            inactive=tile,
            at_risk=tile,
            not_applicable=tile,
        )
        dist = StatusDistributionResponse(total=0, breakdown=[])
        sync_detail = SyncDetailResponse(last_sync_datetime=None, is_sync_in_progress=False)
        data = OverviewDataResponse(sync_detail=sync_detail, metrics=metrics, status_distribution=dist)
        assert data.metrics.total_projects.count == 0


class TestFilterModels:
    """Tests for FilterItemResponse and FiltersDataResponse models."""

    def test_valid_filter_item(self):
        item = FilterItemResponse(id="abc-123", name="Test")
        assert item.id == "abc-123"
        assert item.name == "Test"

    def test_valid_filters_data(self):
        data = FiltersDataResponse(
            specializations=[FilterItemResponse(id="1", name="Spec A")],
            clients=[FilterItemResponse(id="2", name="Client B")],
            statuses=[FilterItemResponse(id="3", name="Active")],
        )
        assert len(data.specializations) == 1
        assert len(data.clients) == 1
        assert len(data.statuses) == 1

    def test_empty_filters_data(self):
        data = FiltersDataResponse(specializations=[], clients=[], statuses=[])
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
