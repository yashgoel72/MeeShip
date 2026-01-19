"""Azure Blob Storage service using native SDK with Account Key for SAS tokens"""
from azure.storage.blob import BlobServiceClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from azure.core.exceptions import ResourceNotFoundError, AzureError
import uuid
import logging
import re
from datetime import datetime, timedelta, timezone
from ..config import get_settings

logger = logging.getLogger(__name__)


def _extract_region_from_endpoint(endpoint_url: str) -> str:
    """
    Kept for backward compatibility (not used in Azure Blob Storage)
    Azure Blob URLs don't contain region information
    """
    return "not-applicable"


def _get_blob_service_client():
    """
    Create and return configured BlobServiceClient for Azure Blob Storage
    Uses account key authentication for SAS token generation
    """
    settings = get_settings()
    
    if not settings.S3_ENABLED:
        raise Exception("Storage is not enabled")
    
    try:
        # Construct connection string from account name and key
        # S3_ACCESS_KEY = account name, S3_SECRET_KEY = account key
        account_name = settings.S3_ACCESS_KEY
        account_key = settings.S3_SECRET_KEY
        
        # Create BlobServiceClient with account key
        client = BlobServiceClient(
            account_url=settings.S3_ENDPOINT,
            credential=account_key
        )
        return client, account_name, account_key
    except Exception as e:
        logger.error(f"Failed to initialize Azure Blob client: {e}")
        raise Exception(f"Azure Blob client initialization failed: {e}")


async def upload_to_s3(
    data: bytes,
    filename: str = None,
    content_type: str = "image/jpeg"
) -> str:
    """
    Upload bytes to Azure Blob Storage and return the blob name
    
    Args:
        data: Bytes to upload
        filename: Optional filename (will be auto-generated if not provided)
        content_type: MIME type of the file
    
    Returns:
        Blob name of the uploaded file (e.g., "user123/optimized.jpg")
    
    Raises:
        Exception: If upload fails
    """
    settings = get_settings()
    blob_service_client, account_name, account_key = _get_blob_service_client()
    
    # Generate and sanitize filename
    if filename:
        # Remove/replace special characters to avoid URL encoding issues
        object_name = re.sub(r'[^\w\-./]', '_', filename)
    else:
        object_name = f"{uuid.uuid4().hex}.jpg"
    
    try:
        # Get container client (hardcoded to meeship-images)
        container_name = "meeship-images"
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=object_name
        )
        
        # Upload file
        logger.info(f"Uploading to Azure Blob: {object_name} ({len(data)} bytes)")
        blob_client.upload_blob(
            data,
            overwrite=True,
            content_settings=ContentSettings(content_type=content_type)
        )
        
        logger.info(f"Successfully uploaded to Azure Blob: {object_name}")
        return object_name
        
    except AzureError as e:
        logger.error(f"Azure Blob upload error: {e}")
        raise Exception(f"Azure Blob upload failed: {e}")
    except Exception as e:
        logger.error(f"Blob upload error: {e}")
        raise Exception(f"Blob upload error: {e}")


async def generate_presigned_url(
    object_key: str,
    expires_in: int = None
) -> dict:
    """
    Generate a SAS URL for temporary access to a private Azure blob
    
    Args:
        object_key: The blob name (e.g., "user123/optimized.jpg")
        expires_in: Expiry time in seconds (defaults to S3_PRESIGNED_URL_EXPIRY from settings)
    
    Returns:
        Dictionary with signed_url and expires_at timestamp
        {
            "signed_url": "https://...?sv=...&sig=...",
            "expires_at": "2026-01-17T12:30:00Z"
        }
    
    Raises:
        Exception: If URL generation fails
    """
    settings = get_settings()
    blob_service_client, account_name, account_key = _get_blob_service_client()
    
    if expires_in is None:
        expires_in = settings.S3_PRESIGNED_URL_EXPIRY
    
    try:
        logger.info(f"Generating SAS URL for: {object_key} (expires in {expires_in}s)")
        
        # Get container and blob info
        container_name = "meeship-images"
        
        # Calculate expiration time
        start_time = datetime.now(timezone.utc)
        expiry_time = start_time + timedelta(seconds=expires_in)
        
        # Get blob client
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=object_key
        )
        
        # Generate SAS token using account key (simpler than user delegation key)
        sas_token = generate_blob_sas(
            account_name=account_name,
            container_name=container_name,
            blob_name=object_key,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
        )
        
        # Construct full URL with SAS token (remove any existing query params from blob_client.url)
        base_url = blob_client.url.split('?')[0]  # Remove any existing SAS token
        signed_url = f"{base_url}?{sas_token}"
        
        logger.info(f"Generated SAS URL for {object_key}, expires at {expiry_time.isoformat()}")
        
        return {
            "signed_url": signed_url,
            "expires_at": expiry_time.isoformat()
        }
        
    except AzureError as e:
        logger.error(f"Azure error generating SAS URL: {e}")
        raise Exception(f"Failed to generate SAS URL: {e}")
    except Exception as e:
        logger.error(f"Error generating SAS URL: {e}")
        raise Exception(f"Error generating SAS URL: {e}")


async def get_object(object_key: str) -> bytes:
    """
    Download a blob from Azure Blob Storage
    
    Args:
        object_key: The blob name to download
    
    Returns:
        File contents as bytes
    
    Raises:
        Exception: If download fails
    """
    settings = get_settings()
    blob_service_client, account_name, account_key = _get_blob_service_client()
    
    try:
        logger.info(f"Downloading from Azure Blob: {object_key}")
        
        # Get container client
        container_name = "meeship-images"
        blob_client = blob_service_client.get_blob_client(
            container=container_name,
            blob=object_key
        )
        
        # Download blob
        download_stream = blob_client.download_blob()
        data = download_stream.readall()
        
        logger.info(f"Successfully downloaded {len(data)} bytes from Azure Blob")
        return data
        
    except ResourceNotFoundError as e:
        logger.error(f"Azure Blob not found: {e}")
        raise Exception(f"Blob download failed - not found: {e}")
    except AzureError as e:
        logger.error(f"Azure error downloading blob: {e}")
        raise Exception(f"Blob download failed: {e}")
    except Exception as e:
        logger.error(f"Blob download error: {e}")
        raise Exception(f"Blob download error: {e}")


# Backwards compatibility alias
upload_to_minio = upload_to_s3
