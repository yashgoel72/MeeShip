"""
Meesho Service

Handles Meesho account linking, credential encryption, and shipping cost API calls.
"""

import logging
import os
import time
from datetime import datetime, timezone
from typing import Optional, Tuple
from dataclasses import dataclass

import httpx
from cryptography.fernet import Fernet, InvalidToken
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.meesho import ShippingCostResponse

logger = logging.getLogger(__name__)
# Dedicated logger for Meesho API calls — grep "MEESHO_API" in logs to see all calls
api_logger = logging.getLogger("meesho_api")


# ============================================================================
# Data Classes
# ============================================================================

@dataclass
class MeeshoCredentials:
    """Meesho seller credentials."""
    supplier_id: str
    identifier: str
    connect_sid: str
    browser_id: Optional[str] = None


@dataclass
class ShippingResult:
    """Result from shipping cost calculation."""
    success: bool
    price: int
    shipping_charges: int
    transfer_price: float
    commission_fees: float = 0
    gst: float = 0
    total_price: int = 0
    duplicate_pid: Optional[int] = None
    error: Optional[str] = None
    error_code: Optional[str] = None


# ============================================================================
# Encryption Utilities
# ============================================================================

class CredentialEncryption:
    """
    Handles encryption/decryption of sensitive Meesho credentials.
    Uses Fernet symmetric encryption.
    """
    
    _instance: Optional['CredentialEncryption'] = None
    _fernet: Optional[Fernet] = None
    
    @classmethod
    def get_instance(cls) -> 'CredentialEncryption':
        if cls._instance is None:
            cls._instance = cls()
        return cls._instance
    
    def __init__(self):
        key = os.environ.get('MEESHO_ENCRYPTION_KEY')
        if not key:
            # Generate a key for development (should be set in production!)
            logger.warning("MEESHO_ENCRYPTION_KEY not set! Generating temporary key.")
            key = Fernet.generate_key().decode()
            os.environ['MEESHO_ENCRYPTION_KEY'] = key
        
        try:
            self._fernet = Fernet(key.encode() if isinstance(key, str) else key)
        except Exception as e:
            logger.error(f"Invalid encryption key: {e}")
            # Generate new key as fallback
            key = Fernet.generate_key()
            self._fernet = Fernet(key)
    
    def encrypt(self, plaintext: str) -> str:
        """Encrypt a string and return base64-encoded ciphertext."""
        if not plaintext:
            return ""
        return self._fernet.encrypt(plaintext.encode()).decode()
    
    def decrypt(self, ciphertext: str) -> str:
        """Decrypt base64-encoded ciphertext and return plaintext."""
        if not ciphertext:
            return ""
        try:
            return self._fernet.decrypt(ciphertext.encode()).decode()
        except InvalidToken:
            logger.error("Failed to decrypt: invalid token")
            raise ValueError("Failed to decrypt credentials. Key may have changed.")


# ============================================================================
# Meesho API Client
# ============================================================================

class MeeshoAPIClient:
    """
    HTTP client for Meesho Supplier APIs.
    
    Based on working POC in scripts/meesho_shipping_poc.py
    """
    
    BASE_URL = "https://supplier.meesho.com/catalogingapi/api"
    
    def __init__(self, credentials: MeeshoCredentials):
        self.credentials = credentials
        self._client: Optional[httpx.AsyncClient] = None
    
    def _get_headers(self) -> dict:
        """Build headers matching what Meesho expects.
        NOTE: content-type is NOT set here — httpx sets it automatically
        (application/json for .post(json=...), multipart for .post(files=...)).
        """
        return {
            "accept": "application/json, text/plain, */*",
            "accept-language": "en-IN,en-GB;q=0.9,en-US;q=0.8,en;q=0.7",
            "browser-id": self.credentials.browser_id or "",
            "cache-control": "no-cache",
            "client-package-version": "1.0.1",
            "client-type": "d-web",
            "identifier": self.credentials.identifier,
            "origin": "https://supplier.meesho.com",
            "pragma": "no-cache",
            "referer": f"https://supplier.meesho.com/panel/v3/new/cataloging/{self.credentials.identifier}/catalogs/single/add",
            "supplier-id": self.credentials.supplier_id,
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/144.0.0.0 Safari/537.36",
        }
    
    def _get_cookies(self) -> dict:
        """Build cookies dict."""
        cookies = {"connect.sid": self.credentials.connect_sid}
        if self.credentials.browser_id:
            cookies["browser_id"] = self.credentials.browser_id
        return cookies
    
    async def __aenter__(self):
        self._client = httpx.AsyncClient(
            base_url=self.BASE_URL,
            headers=self._get_headers(),
            cookies=self._get_cookies(),
            timeout=60.0,
            follow_redirects=True,
        )
        return self
    
    async def __aexit__(self, *args):
        if self._client:
            await self._client.aclose()
    
    async def validate_credentials(self) -> Tuple[bool, Optional[str]]:
        """
        Validate credentials by making a test API call.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        endpoint = "/singleCatalogUpload/getTransferPrice"
        payload = {
            "sscat_id": 12435,
            "gst_percentage": 0,
            "price": 100,
            "supplier_id": int(self.credentials.supplier_id),
            "duplicate_pid": None,
            "gst_type": "GSTIN"
        }
        
        t0 = time.monotonic()
        try:
            response = await self._client.post(endpoint, json=payload)
            duration_ms = (time.monotonic() - t0) * 1000
            
            if response.status_code == 200:
                data = response.json()
                if "transfer_price" in data:
                    api_logger.info("MEESHO_API | %-50s | %s | %3d | %7.0fms | result=valid", endpoint, "POST", response.status_code, duration_ms)
                    return True, None
                api_logger.warning("MEESHO_API | %-50s | %s | %3d | %7.0fms | result=invalid_format", endpoint, "POST", response.status_code, duration_ms)
                return False, "Invalid response format"
            
            error_map = {401: "Unauthorized - invalid credentials", 463: "Session expired - token missing", 403: "Access denied - possible bot detection"}
            error_msg = error_map.get(response.status_code, f"Unexpected status: {response.status_code}")
            api_logger.warning("MEESHO_API | %-50s | %s | %3d | %7.0fms | error=%s", endpoint, "POST", response.status_code, duration_ms, error_msg)
            return False, error_msg
                
        except Exception as e:
            duration_ms = (time.monotonic() - t0) * 1000
            api_logger.error("MEESHO_API | %-50s | %s | ERR | %7.0fms | exception=%s", endpoint, "POST", duration_ms, e)
            return False, str(e)
    
    async def upload_image(self, image_bytes: bytes, filename: str = "image.jpg", content_type: str = "image/jpeg") -> Optional[str]:
        """
        Step 1: Upload image to Meesho CDN.
        
        Endpoint: POST /singleCatalogUpload/uploadSingleCatalogImages
        Returns: Meesho CDN URL for the image, or None on failure
        """
        endpoint = "/singleCatalogUpload/uploadSingleCatalogImages"
        size_kb = len(image_bytes) / 1024
        t0 = time.monotonic()
        try:
            files = {
                "file": (filename, image_bytes, content_type),
            }
            data = {
                "data": "undefined",
            }
            
            response = await self._client.post(
                endpoint,
                files=files,
                data=data,
            )
            duration_ms = (time.monotonic() - t0) * 1000
            
            if response.status_code == 200:
                result = response.json()
                image_url = result.get("image")
                if image_url:
                    api_logger.info("MEESHO_API | %-50s | %s | %3d | %7.0fms | file=%s size=%.0fKB cdn_url=%s", endpoint, "POST", response.status_code, duration_ms, filename, size_kb, image_url[:60])
                    return image_url
            
            api_logger.warning("MEESHO_API | %-50s | %s | %3d | %7.0fms | file=%s size=%.0fKB error=%s", endpoint, "POST", response.status_code, duration_ms, filename, size_kb, response.text[:120])
            return None
            
        except Exception as e:
            duration_ms = (time.monotonic() - t0) * 1000
            api_logger.error("MEESHO_API | %-50s | %s | ERR | %7.0fms | file=%s exception=%s", endpoint, "POST", duration_ms, filename, e)
            return None
    
    async def get_duplicate_pid(self, image_url: str, sscat_id: int = 12435) -> Optional[int]:
        """
        Step 2: Get duplicate product ID via image recognition.
        
        Endpoint: POST /priceRecommendation/fetchDuplicatePid
        Returns: Duplicate PID (or None if no match)
        """
        endpoint = "/priceRecommendation/fetchDuplicatePid"
        payload = {
            "is_old_image_match_enabled": True,
            "sscat_id": sscat_id,
            "image_url": image_url,
        }
        
        t0 = time.monotonic()
        try:
            response = await self._client.post(endpoint, json=payload)
            duration_ms = (time.monotonic() - t0) * 1000
            
            if response.status_code == 200:
                result = response.json()
                duplicate_pid = result.get("data", {}).get("duplicate_pid")
                api_logger.info("MEESHO_API | %-50s | %s | %3d | %7.0fms | sscat_id=%d duplicate_pid=%s", endpoint, "POST", response.status_code, duration_ms, sscat_id, duplicate_pid)
                return duplicate_pid
            
            api_logger.warning("MEESHO_API | %-50s | %s | %3d | %7.0fms | sscat_id=%d error=no_match", endpoint, "POST", response.status_code, duration_ms, sscat_id)
            return None
            
        except Exception as e:
            duration_ms = (time.monotonic() - t0) * 1000
            api_logger.error("MEESHO_API | %-50s | %s | ERR | %7.0fms | exception=%s", endpoint, "POST", duration_ms, e)
            return None
    
    async def get_shipping_cost_for_image(
        self,
        image_bytes: bytes,
        price: int,
        sscat_id: int = 12435,
        filename: str = "variant.jpg"
    ) -> ShippingResult:
        """
        Full POC flow: Upload image → Get duplicate PID → Get shipping cost.
        
        This provides accurate shipping based on image dimensions/recognition.
        """
        t0_flow = time.monotonic()
        
        # Step 1: Upload image to Meesho CDN
        image_url = await self.upload_image(image_bytes, filename)
        if not image_url:
            # Fall back to basic shipping calculation without image
            return await self.get_transfer_price(price=price, sscat_id=sscat_id)
        
        # Step 2: Get duplicate PID via image recognition
        duplicate_pid = await self.get_duplicate_pid(image_url, sscat_id)
        
        # Step 3: Get transfer price with duplicate_pid for accurate shipping
        result = await self.get_transfer_price(
            price=price,
            sscat_id=sscat_id,
            duplicate_pid=duplicate_pid
        )
        
        # Add image_url to result for reference
        result.duplicate_pid = duplicate_pid
        
        total_ms = (time.monotonic() - t0_flow) * 1000
        api_logger.info(
            "MEESHO_API | FLOW_COMPLETE | %s | total=%7.0fms | price=%d dup_pid=%s → shipping=₹%s success=%s",
            filename, total_ms, price, duplicate_pid, result.shipping_charges, result.success
        )
        
        return result
    
    async def get_transfer_price(
        self,
        price: int,
        sscat_id: int = 12435,
        duplicate_pid: Optional[int] = None
    ) -> ShippingResult:
        """
        Get transfer price including shipping charges.
        
        Args:
            price: Product price in INR
            sscat_id: Sub-category ID
            duplicate_pid: Duplicate product ID (for price recommendation)
        """
        endpoint = "/singleCatalogUpload/getTransferPrice"
        payload = {
            "sscat_id": sscat_id,
            "gst_percentage": 0,
            "price": price,
            "supplier_id": int(self.credentials.supplier_id),
            "duplicate_pid": duplicate_pid,
            "gst_type": "GSTIN"
        }
        
        t0 = time.monotonic()
        try:
            response = await self._client.post(endpoint, json=payload)
            duration_ms = (time.monotonic() - t0) * 1000
            
            if response.status_code == 200:
                data = response.json()
                shipping = data.get("shipping_charges", 0)
                transfer = data.get("transfer_price", 0)
                api_logger.info(
                    "MEESHO_API | %-50s | %s | %3d | %7.0fms | price=%d dup_pid=%s → shipping=₹%s transfer=₹%s",
                    endpoint, "POST", response.status_code, duration_ms, price, duplicate_pid, shipping, transfer
                )
                return ShippingResult(
                    success=True,
                    price=price,
                    shipping_charges=shipping,
                    transfer_price=transfer,
                    commission_fees=data.get("commission_fees", 0),
                    gst=data.get("gst_price", 0),
                    total_price=data.get("total_price", price),
                    duplicate_pid=duplicate_pid
                )
            
            elif response.status_code in (401, 463):
                api_logger.warning(
                    "MEESHO_API | %-50s | %s | %3d | %7.0fms | price=%d error=SESSION_EXPIRED",
                    endpoint, "POST", response.status_code, duration_ms, price
                )
                return ShippingResult(
                    success=False,
                    price=price,
                    shipping_charges=0,
                    transfer_price=0,
                    error="Session expired. Please re-link your Meesho account.",
                    error_code="SESSION_EXPIRED"
                )
            
            else:
                api_logger.warning(
                    "MEESHO_API | %-50s | %s | %3d | %7.0fms | price=%d error=API_ERROR",
                    endpoint, "POST", response.status_code, duration_ms, price
                )
                return ShippingResult(
                    success=False,
                    price=price,
                    shipping_charges=0,
                    transfer_price=0,
                    error=f"API error: {response.status_code}",
                    error_code="API_ERROR"
                )
                
        except Exception as e:
            duration_ms = (time.monotonic() - t0) * 1000
            api_logger.error(
                "MEESHO_API | %-50s | %s | ERR | %7.0fms | price=%d exception=%s",
                endpoint, "POST", duration_ms, price, e
            )
            return ShippingResult(
                success=False,
                price=price,
                shipping_charges=0,
                transfer_price=0,
                error=str(e),
                error_code="REQUEST_ERROR"
            )


# ============================================================================
# Meesho Service
# ============================================================================

class MeeshoService:
    """
    Main service for Meesho account operations.
    
    Handles:
    - Linking/unlinking accounts
    - Credential encryption/storage
    - Shipping cost calculations
    """
    
    def __init__(self, db: AsyncSession):
        self.db = db
        self.encryption = CredentialEncryption.get_instance()
    
    async def link_account(
        self,
        user: User,
        supplier_id: str,
        identifier: str,
        connect_sid: str,
        browser_id: Optional[str] = None
    ) -> Tuple[bool, str]:
        """
        Link a Meesho account to a user.
        
        1. Validates credentials with Meesho API
        2. Encrypts connect_sid
        3. Stores in database
        
        Returns:
            Tuple of (success, message)
        """
        # Create credentials object
        credentials = MeeshoCredentials(
            supplier_id=supplier_id,
            identifier=identifier,
            connect_sid=connect_sid,
            browser_id=browser_id
        )
        
        # Validate credentials
        async with MeeshoAPIClient(credentials) as client:
            is_valid, error = await client.validate_credentials()
            
            if not is_valid:
                logger.warning(f"Invalid Meesho credentials for user {user.id}: {error}")
                return False, f"Invalid credentials: {error}"
        
        # Encrypt connect_sid
        encrypted_sid = self.encryption.encrypt(connect_sid)
        
        # Store in database
        user.meesho_supplier_id = supplier_id
        user.meesho_identifier = identifier
        user.meesho_connect_sid_encrypted = encrypted_sid
        user.meesho_browser_id = browser_id
        user.meesho_linked_at = datetime.now(timezone.utc)
        
        await self.db.commit()
        
        logger.info(f"Meesho account linked for user {user.id}, supplier {supplier_id}")
        return True, "Meesho account linked successfully"
    
    async def unlink_account(self, user: User) -> Tuple[bool, str]:
        """
        Unlink Meesho account from user.
        
        Clears all Meesho credentials from database.
        """
        user.meesho_supplier_id = None
        user.meesho_identifier = None
        user.meesho_connect_sid_encrypted = None
        user.meesho_browser_id = None
        user.meesho_linked_at = None
        
        await self.db.commit()
        
        logger.info(f"Meesho account unlinked for user {user.id}")
        return True, "Meesho account unlinked successfully"
    
    def is_linked(self, user: User) -> bool:
        """Check if user has a linked Meesho account."""
        return bool(
            user.meesho_supplier_id and 
            user.meesho_identifier and 
            user.meesho_connect_sid_encrypted
        )
    
    async def validate_session(self, user: User) -> Tuple[bool, Optional[str]]:
        """
        Validate that the user's Meesho session is still active.
        
        Makes a lightweight API call to verify the session token.
        
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self.is_linked(user):
            return False, "Meesho account not linked"
        
        credentials = self._get_credentials(user)
        if not credentials:
            return False, "Failed to retrieve credentials"
        
        async with MeeshoAPIClient(credentials) as client:
            is_valid, error = await client.validate_credentials()
            return is_valid, error
    
    def _get_credentials(self, user: User) -> Optional[MeeshoCredentials]:
        """Get decrypted credentials for user."""
        if not self.is_linked(user):
            return None
        
        try:
            connect_sid = self.encryption.decrypt(user.meesho_connect_sid_encrypted)
            return MeeshoCredentials(
                supplier_id=user.meesho_supplier_id,
                identifier=user.meesho_identifier,
                connect_sid=connect_sid,
                browser_id=user.meesho_browser_id
            )
        except ValueError as e:
            logger.error(f"Failed to decrypt credentials for user {user.id}: {e}")
            return None
    
    async def get_shipping_cost(
        self,
        user: User,
        price: int,
        sscat_id: int = 12435
    ) -> ShippingResult:
        """
        Get shipping cost for a product.
        
        Args:
            user: User with linked Meesho account
            price: Product price in INR
            sscat_id: Sub-category ID
        
        Returns:
            ShippingResult with shipping cost or error
        """
        # Check if linked
        if not self.is_linked(user):
            return ShippingResult(
                success=False,
                price=price,
                shipping_charges=0,
                transfer_price=0,
                error="Meesho account not linked",
                error_code="NOT_LINKED"
            )
        
        # Get credentials
        credentials = self._get_credentials(user)
        if not credentials:
            return ShippingResult(
                success=False,
                price=price,
                shipping_charges=0,
                transfer_price=0,
                error="Failed to retrieve credentials",
                error_code="CREDENTIAL_ERROR"
            )
        
        # Call Meesho API
        async with MeeshoAPIClient(credentials) as client:
            result = await client.get_transfer_price(price=price, sscat_id=sscat_id)
        
        # If session expired, clear credentials
        if result.error_code == "SESSION_EXPIRED":
            logger.warning(f"Meesho session expired for user {user.id}")
            # Don't auto-unlink, let user know to re-link
        
        return result

    async def get_shipping_cost_for_image(
        self,
        user: User,
        image_bytes: bytes,
        price: int,
        sscat_id: int = 12435,
        filename: str = "variant.jpg"
    ) -> ShippingResult:
        """
        Get shipping cost for a specific image using full POC flow.
        
        This uploads the image to Meesho, gets duplicate PID via image recognition,
        and then calculates shipping based on the actual image dimensions.
        
        Args:
            user: User with linked Meesho account
            image_bytes: JPEG image bytes
            price: Product price in INR
            sscat_id: Sub-category ID
            filename: Filename for upload
        
        Returns:
            ShippingResult with shipping cost or error
        """
        # Check if linked
        if not self.is_linked(user):
            return ShippingResult(
                success=False,
                price=price,
                shipping_charges=0,
                transfer_price=0,
                error="Meesho account not linked",
                error_code="NOT_LINKED"
            )
        
        # Get credentials
        credentials = self._get_credentials(user)
        if not credentials:
            return ShippingResult(
                success=False,
                price=price,
                shipping_charges=0,
                transfer_price=0,
                error="Failed to retrieve credentials",
                error_code="CREDENTIAL_ERROR"
            )
        
        # Call Meesho API with full flow
        async with MeeshoAPIClient(credentials) as client:
            result = await client.get_shipping_cost_for_image(
                image_bytes=image_bytes,
                price=price,
                sscat_id=sscat_id,
                filename=filename
            )
        
        # If session expired, log warning
        if result.error_code == "SESSION_EXPIRED":
            logger.warning(f"Meesho session expired for user {user.id}")
        
        return result
