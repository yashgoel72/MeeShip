"""
This file is deprecated. Authentication is now handled by Kinde OAuth.
See app/routers/kinde_auth.py for the OAuth implementation.
"""

from sendgrid.helpers.mail import Mail
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import get_settings
from app.models.user import User
from app.models.subscription import Subscription

settings = get_settings()
logger = logging.getLogger(__name__)

# Password hashing context using bcrypt
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# In-memory rate limiting store (use Redis in production)
_rate_limit_store: dict[str, list[datetime]] = {}

# In-memory OTP store (use Redis in production)
_otp_store: dict[str, Tuple[str, datetime]] = {}


class AuthService:
    """Authentication service handling all auth-related operations."""
    
    def __init__(self, db: AsyncSession):
        self.db = db
    
    # ==================== Password Hashing ====================
    
    @staticmethod
    def hash_password(password: str) -> str:
        """Hash a password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            Hashed password string
        """
        return pwd_context.hash(password)
    
    @staticmethod
    def verify_password(plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash.
        
        Args:
            plain_password: Plain text password to verify
            hashed_password: Stored hashed password
            
        Returns:
            True if password matches, False otherwise
        """
        return pwd_context.verify(plain_password, hashed_password)
    
    # ==================== JWT Token Operations ====================
    
    @staticmethod
    def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
        """Create a JWT access token.
        
        Args:
            data: Payload data to encode in token
            expires_delta: Optional custom expiration time
            
        Returns:
            Encoded JWT access token
        """
        to_encode = data.copy()
        if expires_delta:
            expire = datetime.utcnow() + expires_delta
        else:
            expire = datetime.utcnow() + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        to_encode.update({
            "exp": expire,
            "type": "access"
        })
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def create_refresh_token(data: dict) -> str:
        """Create a JWT refresh token.
        
        Args:
            data: Payload data to encode in token
            
        Returns:
            Encoded JWT refresh token
        """
        to_encode = data.copy()
        expire = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
        to_encode.update({
            "exp": expire,
            "type": "refresh"
        })
        encoded_jwt = jwt.encode(
            to_encode, 
            settings.JWT_SECRET_KEY, 
            algorithm=settings.JWT_ALGORITHM
        )
        return encoded_jwt
    
    @staticmethod
    def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
        """Verify and decode a JWT token.
        
        Args:
            token: JWT token to verify
            token_type: Expected token type ("access" or "refresh")
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token, 
                settings.JWT_SECRET_KEY, 
                algorithms=[settings.JWT_ALGORITHM]
            )
            # Verify token type
            if payload.get("type") != token_type:
                logger.warning(f"Token type mismatch: expected {token_type}, got {payload.get('type')}")
                return None
            return payload
        except JWTError as e:
            logger.warning(f"JWT verification failed: {e}")
            return None
    
    @staticmethod
    def create_email_verification_token(user_id: str, email: str) -> str:
        """Create a token for email verification.
        
        Args:
            user_id: User's ID
            email: User's email address
            
        Returns:
            Encoded verification token
        """
        data = {
            "sub": str(user_id),
            "email": email,
            "type": "email_verification"
        }
        expire = datetime.utcnow() + timedelta(hours=24)
        data["exp"] = expire
        return jwt.encode(data, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)
    
    @staticmethod
    def verify_email_token(token: str) -> Optional[dict]:
        """Verify an email verification token.
        
        Args:
            token: Email verification token
            
        Returns:
            Decoded payload if valid, None otherwise
        """
        try:
            payload = jwt.decode(
                token,
                settings.JWT_SECRET_KEY,
                algorithms=[settings.JWT_ALGORITHM]
            )
            if payload.get("type") != "email_verification":
                return None
            return payload
        except JWTError:
            return None
    
    # ==================== Rate Limiting ====================
    
    @staticmethod
    def check_rate_limit(identifier: str) -> Tuple[bool, int]:
        """Check if an identifier (IP/email) has exceeded rate limits.
        
        Args:
            identifier: Unique identifier (IP address or email)
            
        Returns:
            Tuple of (is_allowed, remaining_attempts)
        """
        now = datetime.utcnow()
        window_start = now - timedelta(minutes=settings.RATE_LIMIT_WINDOW_MINUTES)
        
        # Clean up old entries
        if identifier in _rate_limit_store:
            _rate_limit_store[identifier] = [
                ts for ts in _rate_limit_store[identifier] 
                if ts > window_start
            ]
        else:
            _rate_limit_store[identifier] = []
        
        attempts = len(_rate_limit_store[identifier])
        remaining = max(0, settings.RATE_LIMIT_ATTEMPTS - attempts)
        
        if attempts >= settings.RATE_LIMIT_ATTEMPTS:
            logger.warning(f"Rate limit exceeded for {identifier}")
            return False, 0
        
        return True, remaining
    
    @staticmethod
    def record_login_attempt(identifier: str) -> None:
        """Record a login attempt for rate limiting.
        
        Args:
            identifier: Unique identifier (IP address or email)
        """
        if identifier not in _rate_limit_store:
            _rate_limit_store[identifier] = []
        _rate_limit_store[identifier].append(datetime.utcnow())
    
    @staticmethod
    def clear_rate_limit(identifier: str) -> None:
        """Clear rate limit entries for an identifier after successful login.
        
        Args:
            identifier: Unique identifier (IP address or email)
        """
        if identifier in _rate_limit_store:
            del _rate_limit_store[identifier]
    
    # ==================== OTP Operations ====================
    
    @staticmethod
    def generate_otp(email: str, length: int = 6) -> str:
        """Generate a one-time password for email verification.
        
        Args:
            email: Email address to associate with OTP
            length: Length of OTP (default 6)
            
        Returns:
            Generated OTP string
        """
        otp = ''.join([str(secrets.randbelow(10)) for _ in range(length)])
        expiry = datetime.utcnow() + timedelta(minutes=15)
        _otp_store[email] = (otp, expiry)
        logger.info(f"Generated OTP for {email}")
        return otp
    
    @staticmethod
    def verify_otp(email: str, otp: str) -> bool:
        """Verify an OTP for an email address.
        
        Args:
            email: Email address
            otp: OTP to verify
            
        Returns:
            True if OTP is valid, False otherwise
        """
        if email not in _otp_store:
            return False
        
        stored_otp, expiry = _otp_store[email]
        
        if datetime.utcnow() > expiry:
            del _otp_store[email]
            return False
        
        if stored_otp == otp:
            del _otp_store[email]
            return True
        
        return False
    
    # ==================== Email Operations ====================
    
    @staticmethod
    async def send_verification_email(email: str, otp: str) -> bool:
        """Send email verification OTP via SendGrid.
        
        Args:
            email: Recipient email address
            otp: OTP to include in email
            
        Returns:
            True if email sent successfully, False otherwise
        """
        if not settings.SENDGRID_API_KEY:
            logger.warning("SendGrid API key not configured, skipping email send")
            # In development, log the OTP
            logger.info(f"[DEV] Verification OTP for {email}: {otp}")
            return True
        
        try:
            message = Mail(
                from_email=settings.EMAIL_FROM,
                to_emails=email,
                subject=f"Verify your {settings.APP_NAME} account",
                html_content=f"""
                <html>
                <body style="font-family: Arial, sans-serif; max-width: 600px; margin: 0 auto;">
                    <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 30px; text-align: center;">
                        <h1 style="color: white; margin: 0;">Welcome to {settings.APP_NAME}!</h1>
                    </div>
                    <div style="padding: 30px; background-color: #f9fafb;">
                        <p style="font-size: 16px; color: #374151;">
                            Thank you for signing up! Please use the following OTP to verify your email address:
                        </p>
                        <div style="background-color: #4f46e5; color: white; font-size: 32px; font-weight: bold; 
                                    padding: 20px; text-align: center; border-radius: 8px; margin: 20px 0;
                                    letter-spacing: 8px;">
                            {otp}
                        </div>
                        <p style="font-size: 14px; color: #6b7280;">
                            This OTP will expire in 15 minutes. If you didn't create an account, please ignore this email.
                        </p>
                    </div>
                    <div style="padding: 20px; text-align: center; color: #9ca3af; font-size: 12px;">
                        © 2024 {settings.APP_NAME}. All rights reserved.
                    </div>
                </body>
                </html>
                """
            )
            
            sg = SendGridAPIClient(settings.SENDGRID_API_KEY)
            response = sg.send(message)
            
            if response.status_code in [200, 201, 202]:
                logger.info(f"Verification email sent to {email}")
                return True
            else:
                logger.error(f"Failed to send email: {response.status_code}")
                if settings.DEBUG:
                    logger.warning("SendGrid send failed; DEBUG=true so falling back to logging OTP")
                    logger.info(f"[DEV] Verification OTP for {email}: {otp}")
                    return True
                return False
                
        except Exception as e:
            logger.error(f"Error sending verification email: {e}")
            if settings.DEBUG:
                logger.warning("SendGrid error; DEBUG=true so falling back to logging OTP")
                logger.info(f"[DEV] Verification OTP for {email}: {otp}")
                return True
            return False
    
    # ==================== User Operations ====================
    
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address.
        
        Args:
            email: User's email address
            
        Returns:
            User object if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.email == email)
        )
        return result.scalar_one_or_none()
    
    async def get_user_by_id(self, user_id: UUID) -> Optional[User]:
        """Get a user by ID.
        
        Args:
            user_id: User's UUID
            
        Returns:
            User object if found, None otherwise
        """
        result = await self.db.execute(
            select(User).where(User.id == user_id)
        )
        return result.scalar_one_or_none()
    
    async def create_user(
        self, 
        email: str, 
        password: str, 
        full_name: Optional[str] = None
    ) -> User:
        """Create a new user with hashed password.
        
        Args:
            email: User's email address
            password: Plain text password (will be hashed)
            full_name: Optional user's full name
            
        Returns:
            Created User object
        """
        hashed_password = self.hash_password(password)
        
        user = User(
            email=email,
            hashed_password=hashed_password,
            full_name=full_name,
            is_active=True,
            email_verified=False
        )
        
        self.db.add(user)
        await self.db.flush()
        
        logger.info(f"Created new user: {email}")
        return user
    
    async def create_trial_subscription(self, user_id: UUID) -> Subscription:
        """Create a trial subscription for a new user.
        
        Args:
            user_id: User's UUID
            
        Returns:
            Created Subscription object
        """
        subscription = Subscription(
            user_id=user_id,
            tier="trial",
            trial_uploads_remaining=3
        )
        
        self.db.add(subscription)
        await self.db.flush()
        
        logger.info(f"Created trial subscription for user: {user_id}")
        return subscription
    
    async def verify_user_email(self, user_id: UUID) -> bool:
        """Mark a user's email as verified.
        
        Args:
            user_id: User's UUID
            
        Returns:
            True if successful, False otherwise
        """
        user = await self.get_user_by_id(user_id)
        if not user:
            return False
        
        user.email_verified = True
        await self.db.flush()
        
        logger.info(f"Email verified for user: {user_id}")
        return True
    
    async def authenticate_user(self, email: str, password: str) -> Optional[User]:
        """Authenticate a user by email and password.
        
        Args:
            email: User's email address
            password: Plain text password
            
        Returns:
            User object if authentication successful, None otherwise
        """
        user = await self.get_user_by_email(email)
        if not user:
            return None
        
        if not self.verify_password(password, user.hashed_password):
            return None
        
        if not user.is_active:
            return None
        
        return user


# Helper functions for backward compatibility
def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """Create access token (standalone function for backward compatibility)."""
    return AuthService.create_access_token(data, expires_delta)


def create_refresh_token(data: dict) -> str:
    """Create refresh token (standalone function for backward compatibility)."""
    return AuthService.create_refresh_token(data)


def verify_token(token: str, token_type: str = "access") -> Optional[dict]:
    """Verify token (standalone function for backward compatibility)."""
    return AuthService.verify_token(token, token_type)


def hash_password(password: str) -> str:
    """Hash password (standalone function for backward compatibility)."""
    return AuthService.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password (standalone function for backward compatibility)."""
    return AuthService.verify_password(plain_password, hashed_password)