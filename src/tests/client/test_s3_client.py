"""Tests for S3Client AWS S3 operations."""

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.client.s3_client import S3Client


@pytest.fixture
def s3_client():
    """Create an S3Client instance with test configuration."""
    return S3Client(
        bucket_name="test-bucket",
        region="us-east-1",
        url_expiry_days=7,
    )


class TestUploadPdf:
    """Tests for upload_pdf method."""

    @pytest.mark.asyncio
    async def test_upload_pdf_success(self, s3_client):
        """Should upload PDF and return S3 URI."""
        mock_s3 = AsyncMock()
        mock_s3.put_object = AsyncMock()

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("src.client.s3_client.aioboto3.Session", return_value=mock_session):
            result = await s3_client.upload_pdf(
                pdf_bytes=b"%PDF-1.4 test content",
                s3_key="reports/DevSecOps/Summary report/2026/05/test.pdf",
            )

            assert result == "s3://test-bucket/reports/DevSecOps/Summary report/2026/05/test.pdf"

    @pytest.mark.asyncio
    async def test_upload_pdf_failure(self, s3_client):
        """Should raise RuntimeError on upload failure."""
        mock_s3 = AsyncMock()
        mock_s3.put_object = AsyncMock(side_effect=Exception("S3 error"))

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("src.client.s3_client.aioboto3.Session", return_value=mock_session):
            with pytest.raises(RuntimeError, match="S3 upload failed"):
                await s3_client.upload_pdf(
                    pdf_bytes=b"%PDF-1.4 test content",
                    s3_key="reports/test.pdf",
                )


class TestGeneratePresignedUrl:
    """Tests for generate_presigned_url method."""

    @pytest.mark.asyncio
    async def test_generate_presigned_url_success(self, s3_client):
        """Should generate and return a pre-signed URL."""
        mock_s3 = AsyncMock()
        mock_s3.generate_presigned_url = AsyncMock(
            return_value="https://test-bucket.s3.amazonaws.com/reports/test.pdf?signature=abc"
        )

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("src.client.s3_client.aioboto3.Session", return_value=mock_session):
            result = await s3_client.generate_presigned_url("reports/test.pdf")

            assert "test-bucket" in result
            assert "test.pdf" in result

    @pytest.mark.asyncio
    async def test_generate_presigned_url_failure(self, s3_client):
        """Should raise RuntimeError on URL generation failure."""
        mock_s3 = AsyncMock()
        mock_s3.generate_presigned_url = AsyncMock(side_effect=Exception("URL generation error"))

        mock_session = MagicMock()
        mock_session.client.return_value.__aenter__ = AsyncMock(return_value=mock_s3)
        mock_session.client.return_value.__aexit__ = AsyncMock(return_value=False)

        with patch("src.client.s3_client.aioboto3.Session", return_value=mock_session):
            with pytest.raises(RuntimeError, match="Pre-signed URL generation failed"):
                await s3_client.generate_presigned_url("reports/test.pdf")
