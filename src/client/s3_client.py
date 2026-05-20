"""AWS S3 client for uploading PDF reports and generating pre-signed URLs.

Uses aioboto3 for async S3 operations with configurable bucket and region.
"""

import asyncio
import traceback

import aioboto3
from src.utils.logger import logger

DEFAULT_URL_EXPIRY_SECONDS = 7 * 24 * 60 * 60


class S3Client:
    """Async client for AWS S3 upload and pre-signed URL generation.

    Handles PDF upload and generates time-limited download URLs.
    """
    def __init__(self, bucket_name: str, region: str, url_expiry_days: int = 7) -> None:
        """Initialize the S3 client.

        Args:
            bucket_name: The S3 bucket name for PDF uploads.
            region: AWS region for the S3 bucket.
            url_expiry_days: Number of days the pre-signed URL remains valid.
        """
        self._bucket_name = bucket_name
        self._region = region
        self._url_expiry_seconds = url_expiry_days * 24 * 60 * 60

    async def upload_pdf(self, pdf_bytes: bytes, s3_key: str) -> str:
        """Upload a PDF file to S3.

        Args:
            pdf_bytes: The PDF content as bytes.
            s3_key: The S3 object key (path within the bucket).

        Returns:
            The S3 URI in format s3://bucket/key.

        Raises:
            RuntimeError: If the upload fails.
        """
        return await self.upload_file(pdf_bytes, s3_key, content_type="application/pdf")

    async def upload_file(
        self,
        file_bytes: bytes,
        s3_key: str,
        content_type: str = "application/octet-stream",
    ) -> str:
        """Upload any file to S3 with an explicit content type.

        Args:
            file_bytes: Raw file content as bytes.
            s3_key: The S3 object key (path within the bucket).
            content_type: MIME type of the file (e.g. ``application/pdf``,
                ``image/png``). Defaults to ``application/octet-stream``.

        Returns:
            The S3 URI in format ``s3://bucket/key``.

        Raises:
            RuntimeError: If the upload fails.
        """
        try:
            session = aioboto3.Session()
            async with session.client("s3", region_name=self._region) as s3:
                await s3.put_object(
                    Bucket=self._bucket_name,
                    Key=s3_key,
                    Body=file_bytes,
                    ContentType=content_type,
                )

            s3_uri = f"s3://{self._bucket_name}/{s3_key}"
            logger.info(
                "File uploaded to S3",
                extra={"s3_key": s3_key, "bucket": self._bucket_name, "content_type": content_type},
            )
            return s3_uri

        except Exception as exc:
            logger.error(
                "Failed to upload file to S3",
                extra={"s3_key": s3_key, "error": str(exc)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="upload_file",
                error_file="src/client/s3_client.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise RuntimeError(f"S3 upload failed: {exc}") from exc

    async def generate_presigned_url(self, s3_key: str) -> str:
        """Generate a pre-signed URL for downloading a file from S3.

        Args:
            s3_key: The S3 object key.

        Returns:
            A pre-signed URL string.

        Raises:
            RuntimeError: If URL generation fails.
        """
        try:
            session = aioboto3.Session()
            async with session.client("s3", region_name=self._region) as s3:
                presigned_url = await s3.generate_presigned_url(
                    "get_object",
                    Params={"Bucket": self._bucket_name, "Key": s3_key},
                    ExpiresIn=self._url_expiry_seconds,
                )
            logger.info("Pre-signed URL generated", extra={"s3_key": s3_key})
            return presigned_url

        except Exception as exc:
            logger.error(
                "Failed to generate pre-signed URL",
                extra={"s3_key": s3_key, "error": str(exc)},
            )
            asyncio.create_task(log_error_to_db(
                error_message=str(exc),
                error_function="generate_presigned_url",
                error_file="src/client/s3_client.py",
                stack_trace=traceback.format_exc(),
                created_by="system",
            ))
            raise RuntimeError(f"Pre-signed URL generation failed: {exc}") from exc
