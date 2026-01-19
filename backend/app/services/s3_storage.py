"""Azure Blob Storage service using native SDK with Container SAS token"""
from azure.storage.blob import BlobServiceClient, ContainerClient, generate_blob_sas, BlobSasPermissions, ContentSettings
from azure.core.exceptions import ResourceNotFoundError, AzureError
import uuid
import logging
import re
from datetime import datetime, timedelta, timezone
from ..config import get_settings

logger = logging.getLogger(__name__)

# Container name - hardcoded for this application
CONTAINER_NAME = "meeship-images"


def _extract_region_from_endpoint(endpoint_url: str) -> str:
    """
    Kept for backward compatibility (not used in Azure Blob Storage)
    Azure Blob URLs don't contain region information
    """
    return "not-applicable"


def _get_container_client():
    """
    Create and return configured ContainerClient for Azure Blob Storage
    Uses container SAS token authentication directly
    
    Returns:
        tuple: (container_client, account_name, account_key, sas_token)
               account_key is None when using SAS token mode
    """
    settings = get_settings()
    
    if not settings.S3_ENABLED:
        raise Exception("Storage is not enabled")
    
    try:
        # S3_ACCESS_KEY = account name, S3_SECRET_KEY = SAS token (starting with sp=...)
        account_name = settings.S3_ACCESS_KEY
        sas_token = settings.S3_SECRET_KEY
        
        # Check if it's a SAS token (starts with sp= or sv=) vs account key
        is_sas_token = sas_token.startswith('sp=') or sas_token.startswith('sv=') or '&sig=' in sas_token
        
        if is_sas_token:
            # Use ContainerClient with SAS URL directly - this is the correct way to use container SAS tokens
            container_sas_url = f"{settings.S3_ENDPOINT}/{CONTAINER_NAME}?{sas_token}"
            container_client = ContainerClient.from_container_url(container_sas_url)
            logger.info(f"Using container SAS token authentication")
            # Return None for account_key to indicate SAS mode
            return container_client, account_name, None, sas_token
        else:
            # Use account key via BlobServiceClient
            blob_service_client = BlobServiceClient(
                account_url=settings.S3_ENDPOINT,
                credential=sas_token
            )
            container_client = blob_service_client.get_container_client(CONTAINER_NAME)
            return container_client, account_name, sas_token, None
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
    container_client, account_name, account_key, sas_token = _get_container_client()
    
    # Generate and sanitize filename
    if filename:
        # Remove/replace special characters to avoid URL encoding issues
        object_name = re.sub(r'[^\w\-./]', '_', filename)
    else:
        object_name = f"{uuid.uuid4().hex}.jpg"
    
    try:
        # Get blob client from container client
        blob_client = container_client.get_blob_client(blob=object_name)
        
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
    container_client, account_name, account_key, sas_token = _get_container_client()
    
    if expires_in is None:
        expires_in = settings.S3_PRESIGNED_URL_EXPIRY
    
    try:
        logger.info(f"Generating SAS URL for: {object_key} (expires in {expires_in}s)")
        
        # Calculate expiration time
        start_time = datetime.now(timezone.utc)
        expiry_time = start_time + timedelta(seconds=expires_in)
        
        # If using SAS token (no account key), use the container SAS token directly
        if account_key is None and sas_token:
            # Use the container-level SAS token for read access
            base_url = f"{settings.S3_ENDPOINT}/{CONTAINER_NAME}/{object_key}"
            signed_url = f"{base_url}?{sas_token}"
            
            logger.info(f"Generated URL using container SAS for {object_key}")
            
            return {
                "signed_url": signed_url,
                "expires_at": expiry_time.isoformat()
            }
        
        # Get blob client from container
        blob_client = container_client.get_blob_client(blob=object_key)
        
        # Generate SAS token using account key
        generated_sas = generate_blob_sas(
            account_name=account_name,
            container_name=CONTAINER_NAME,
            blob_name=object_key,
            account_key=account_key,
            permission=BlobSasPermissions(read=True),
            expiry=expiry_time,
            start=start_time
        )
        
        # Construct full URL with SAS token (remove any existing query params from blob_client.url)
        base_url = blob_client.url.split('?')[0]  # Remove any existing SAS token
        signed_url = f"{base_url}?{generated_sas}"
        
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
    container_client, account_name, account_key, sas_token = _get_container_client()
    
    try:
        logger.info(f"Downloading from Azure Blob: {object_key}")
        
        # Get blob client from container
        blob_client = container_client.get_blob_client(blob=object_key)
        
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
