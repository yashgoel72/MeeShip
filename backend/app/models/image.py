from sqlalchemy import Column, String, Float, Boolean, ForeignKey, DateTime, func, Integer, Text
from sqlalchemy.dialects.postgresql import UUID
import uuid
from app.models.user import Base


class ProcessedImage(Base):
    __tablename__ = "processed_images"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id"))

    # Existing fields
    original_filename = Column(String, nullable=True)
    azure_blob_url = Column(String, nullable=True)
    weight_category = Column(String, nullable=True)  # 0-200g, 200-500g, etc
    savings_amount = Column(Float, nullable=True)
    is_trial = Column(Boolean, default=False, nullable=True)

    # Input/output image metadata
    input_size_bytes = Column(Integer, nullable=True)
    output_size_bytes = Column(Integer, nullable=True)
    input_width = Column(Integer, nullable=True)
    input_height = Column(Integer, nullable=True)
    output_width = Column(Integer, nullable=True)
    output_height = Column(Integer, nullable=True)

    # Optimization metrics
    processing_time_ms = Column(Integer, nullable=True)

    # Cost prediction inputs/outputs
    actual_weight_g = Column(Float, nullable=True)
    volumetric_weight_g = Column(Float, nullable=True)
    billable_weight_g = Column(Float, nullable=True)
    shipping_cost_inr = Column(Integer, nullable=True)

    # Status/error info
    status = Column(String, nullable=False, default="success")
    error_message = Column(Text, nullable=True)

    # Versioning / extended metrics (stored as JSON-serialized string)
    optimizer_version = Column(String, nullable=True)
    stage_metrics_json = Column(Text, nullable=True)

    created_at = Column(DateTime(timezone=True), server_default=func.now())