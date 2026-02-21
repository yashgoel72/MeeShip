from sqlalchemy import Column, String, Boolean, DateTime, Integer, Text, func
from sqlalchemy.dialects.postgresql import UUID
import uuid
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class User(Base):
    __tablename__ = "users"
    
    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=True)  # Nullable for Kinde users
    kinde_id = Column(String, unique=True, index=True, nullable=True)  # Kinde user ID (sub claim)
    full_name = Column(String)
    is_active = Column(Boolean, default=True)
    email_verified = Column(Boolean, default=False)
    credits = Column(Integer, default=1, nullable=False)  # New users get 1 free credit
    credits_expires_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    
    # Meesho account linking fields
    meesho_supplier_id = Column(String, nullable=True)
    meesho_identifier = Column(String, nullable=True)
    meesho_connect_sid_encrypted = Column(Text, nullable=True)  # Fernet encrypted
    meesho_browser_id = Column(String, nullable=True)
    meesho_linked_at = Column(DateTime(timezone=True), nullable=True)