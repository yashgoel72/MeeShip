"""S3-compatible object storage service for Backblaze B2"""
import boto3
from botocore.config import Config
from botocore.exceptions import ClientError
import uuid
import logging
import re
from datetime import datetime, timedelta, timezone
from ..config import get_settings

logger = logging.getLogger(__name__)


def _extract_region_from_endpoint(endpoint_url: str) -> str:
    """
    Extract region from S3 endpoint URL.
    Example: https://s3.us-east-005.backblazeb2.com -> us-east-005
    """
    match = re.search(r's3\.([a-z]+-[a-z]+-\d+)', endpoint_url)
    if match:
        return match.group(1)
    # Default fallback
    return "us-west-000"


def _get_s3_client():
    """
    Create and return configured boto3 S3 client for Backblaze B2
    """
    settings = get_settings()
    
    if not settings.S3_ENABLED:
        raise Exception("S3 storage is not enabled")
    
    region = _extract_region_from_endpoint(settings.S3_ENDPOINT)
    
    try:
        client = boto3.client(
            's3',
            endpoint_url=settings.S3_ENDPOINT,
            aws_access_key_id=settings.S3_ACCESS_KEY,
            aws_secret_access_key=settings.S3_SECRET_KEY,
            config=Config(signature_version='s3v4'),
            region_name=region
        )
        return client
    except Exception as e:
        logger.error(f"Failed to initialize S3 client: {e}")
        raise Exception(f"S3 client initialization failed: {e}")


async def upload_to_s3(
    data: bytes,
    filename: str = None,
    content_type: str = "image/jpeg"
) -> str:
    """
    Upload bytes to S3 and return the object key
    
    Args:
        data: Bytes to upload
        filename: Optional filename (will be auto-generated if not provided)
        content_type: MIME type of the file
    
    Returns:
        Object key of the uploaded file (e.g., "user123/optimized.jpg")
    
    Raises:
        Exception: If upload fails
    """
    settings = get_settings()
    s3_client = _get_s3_client()
    
    # Generate and sanitize filename
    if filename:
        # Remove/replace special characters to avoid URL encoding issues
        object_name = re.sub(r'[^\w\-./]', '_', filename)
    else:
        object_name = f"{uuid.uuid4().hex}.jpg"
    
    try:
        # Upload file
        logger.info(f"Uploading to S3: {object_name} ({len(data)} bytes)")
        s3_client.put_object(
            Bucket=settings.S3_BUCKET,
            Key=object_name,
            Body=data,
            ContentType=content_type,
        )
        
        logger.info(f"Successfully uploaded to S3: {object_name}")
        return object_name
        
    except ClientError as e:
        logger.error(f"S3 ClientError: {e}")
        raise Exception(f"S3 upload failed: {e}")
    except Exception as e:
        logger.error(f"S3 upload error: {e}")
        raise Exception(f"S3 upload error: {e}")


async def generate_presigned_url(
    object_key: str,
    expires_in: int = None
) -> dict:
    """
    Generate a presigned URL for temporary access to a private S3 object
    
    Args:
        object_key: The S3 object key (e.g., "user123/optimized.jpg")
        expires_in: Expiry time in seconds (defaults to S3_PRESIGNED_URL_EXPIRY from settings)
    
    Returns:
        Dictionary with signed_url and expires_at timestamp
        {
            "signed_url": "https://...",
            "expires_at": "2026-01-16T12:30:00Z"
        }
    
    Raises:
        Exception: If URL generation fails
    """
    settings = get_settings()
    s3_client = _get_s3_client()
    
    if expires_in is None:
        expires_in = settings.S3_PRESIGNED_URL_EXPIRY
    
    try:
        logger.info(f"Generating presigned URL for: {object_key} (expires in {expires_in}s)")
        
        signed_url = s3_client.generate_presigned_url(
            'get_object',
            Params={
                'Bucket': settings.S3_BUCKET,
                'Key': object_key
            },
            ExpiresIn=expires_in
        )
        
        # Calculate expiration timestamp
        expires_at = datetime.now(timezone.utc) + timedelta(seconds=expires_in)
        
        logger.info(f"Generated presigned URL for {object_key}, expires at {expires_at.isoformat()}")
        
        return {
            "signed_url": signed_url,
            "expires_at": expires_at.isoformat()
        }
        
    except ClientError as e:
        logger.error(f"S3 ClientError generating presigned URL: {e}")
        raise Exception(f"Failed to generate presigned URL: {e}")
    except Exception as e:
        logger.error(f"Error generating presigned URL: {e}")
        raise Exception(f"Error generating presigned URL: {e}")


async def get_object(object_key: str) -> bytes:
    """
    Download an object from S3
    
    Args:
        object_key: The S3 object key to download
    
    Returns:
        File contents as bytes
    
    Raises:
        Exception: If download fails
    """
    settings = get_settings()
    s3_client = _get_s3_client()
    
    try:
        logger.info(f"Downloading from S3: {object_key}")
        
        response = s3_client.get_object(
            Bucket=settings.S3_BUCKET,
            Key=object_key
        )
        
        data = response['Body'].read()
        logger.info(f"Successfully downloaded {len(data)} bytes from S3")
        return data
        
    except ClientError as e:
        logger.error(f"S3 ClientError downloading object: {e}")
        raise Exception(f"S3 download failed: {e}")
    except Exception as e:
        logger.error(f"S3 download error: {e}")
        raise Exception(f"S3 download error: {e}")


# Backwards compatibility alias
upload_to_minio = upload_to_s3
