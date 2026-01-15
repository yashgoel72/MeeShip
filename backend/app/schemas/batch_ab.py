from typing import Optional, Dict, Any, List
from pydantic import BaseModel, Field

class BatchABMetrics(BaseModel):
    # Accepts any dict, but can be extended with known fields if needed
    __root__: Dict[str, Any]

class BatchABResult(BaseModel):
    model: str = Field(..., description="Model identifier")
    prompt_variant: str = Field(..., description="Prompt variant used")
    metrics: Optional[Dict[str, Any]] = Field(None, description="Metrics dictionary, or None if error")
    optimized_image_b64: Optional[str] = Field(None, description="Base64-encoded optimized image, or None if error")
    error: Optional[str] = Field(None, description="Error message, if any")

class BatchABResponse(BaseModel):
    results: List[BatchABResult]