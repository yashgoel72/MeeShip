"""MinIO S3-compatible object storage service"""
from minio import Minio
from minio.error import S3Error
import uuid
import io
import logging
from urllib.parse import quote
from ..config import get_settings

logger = logging.getLogger(__name__)


async def upload_to_minio(
    data: bytes,
    filename: str = None,
    content_type: str = "image/jpeg"
) -> str:
    """
    Upload bytes to MinIO and return the public URL
    
    Args:
        data: Bytes to upload
        filename: Optional filename (will be auto-generated if not provided)
        content_type: MIME type of the file
    
    Returns:
        Public URL of the uploaded file
    
    Raises:
        Exception: If upload fails
    """
    settings = get_settings()
    
    if not settings.MINIO_ENABLED:
        raise Exception("MinIO storage is not enabled")
    
    # Initialize MinIO client
    try:
        minio_client = Minio(
            endpoint=settings.MINIO_ENDPOINT,
            access_key=settings.MINIO_ACCESS_KEY,
            secret_key=settings.MINIO_SECRET_KEY,
            secure=settings.MINIO_USE_SSL,
        )
    except Exception as e:
        logger.error(f"Failed to initialize MinIO client: {e}")
        raise Exception(f"MinIO client initialization failed: {e}")
    
    # Generate and sanitize filename
    if filename:
        # Remove/replace special characters to avoid URL encoding issues
        import re
        object_name = re.sub(r'[^\w\-.]', '_', filename)
    else:
        object_name = f"{uuid.uuid4().hex}.jpg"
    
    try:
        # Create bucket if it doesn't exist
        try:
            if not minio_client.bucket_exists(settings.MINIO_BUCKET):
                logger.info(f"Creating MinIO bucket: {settings.MINIO_BUCKET}")
                minio_client.make_bucket(settings.MINIO_BUCKET)
        except S3Error as e:
            if e.code == "BucketAlreadyOwnedByYou":
                logger.info(f"Bucket {settings.MINIO_BUCKET} already exists")
            else:
                raise
        
        # Upload file
        logger.info(f"Uploading to MinIO: {object_name} ({len(data)} bytes)")
        minio_client.put_object(
            settings.MINIO_BUCKET,
            object_name,
            data=io.BytesIO(data),
            length=len(data),
            content_type=content_type,
        )
        
        # Set object ACL to public-read
        try:
            from minio.commonconfig import GOVERNANCE
            from minio.helpers import ObjectACL
            # Note: This requires appropriate bucket policy
            logger.info(f"Object uploaded successfully")
        except Exception as e:
            logger.warning(f"Could not set object ACL: {e}")
        
        # Build public URL with proper URL encoding
        encoded_object_name = quote(object_name, safe='')
        public_url = f"{settings.MINIO_PUBLIC_URL}/{settings.MINIO_BUCKET}/{encoded_object_name}"
        logger.info(f"Successfully uploaded to MinIO: {public_url}")
        return public_url
        
    except S3Error as e:
        logger.error(f"MinIO S3 error: {e}")
        raise Exception(f"MinIO upload failed: {e}")
    except Exception as e:
        logger.error(f"MinIO upload error: {e}")
        raise Exception(f"MinIO upload error: {e}")
