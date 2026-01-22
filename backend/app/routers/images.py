from urllib.parse import urlparse, unquote

# ...existing code...

import asyncio
import io
import json
import logging
import time
import uuid
from typing import Optional, List, Tuple, AsyncGenerator

from fastapi import APIRouter, UploadFile, File, Form, Depends, HTTPException, status, Query, Request
from fastapi.responses import JSONResponse
from sse_starlette.sse import EventSourceResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from sqlalchemy.orm import selectinload
from sqlalchemy.exc import SQLAlchemyError

from app.database import get_db
from app.models.image import ProcessedImage
from app.services.image_optimizer import optimize_image as local_optimize_image
from app.services.s3_storage import upload_to_s3, generate_presigned_url, get_object
from app.services.shipping_variant_generator import (
    generate_all_shipping_variants,
    encode_variant_jpeg,
    VariantInfo,
    TILE_NAMES,
    VARIANT_LABELS,
)

# Import GPT image optimizer lazily
try:
    from app.services.gpt_image_optimizer import GptImage15Optimizer
except Exception:
    GptImage15Optimizer = None
# Import FluxOptimizer lazily (module may be missing in some envs)
try:
    from app.services.flux_optimizer import FluxOptimizer
except Exception:
    FluxOptimizer = None
from app.config import get_settings
from app.services.trial_service import is_trial_upload_allowed
from app.middlewares.auth import get_current_user, get_current_user_optional

router = APIRouter(prefix="/api/images", tags=["Images"])
logger = logging.getLogger(__name__)


def _encode_jpeg_target_size(
    img,
    target_range_bytes: Tuple[int, int],
    qualities: Tuple[int, ...] = (95, 93, 92, 90, 88, 86, 84, 82, 80, 78, 76, 74),
) -> bytes:
    """Encode an RGB PIL image to JPEG aiming to land in a byte-size window.

    Best-effort: if it can't hit the window, returns the closest <= max (or the
    largest quality result if everything is < min).
    """
    min_bytes, max_bytes = target_range_bytes
    best_under_max: Optional[bytes] = None
    best_under_max_len: int = -1
    best_over_min: Optional[bytes] = None
    best_over_min_len: int = 10**18

    for q in qualities:
        buf = io.BytesIO()
        # Use progressive+optimize for consistent web/JPG delivery
        img.save(
            buf,
            format="JPEG",
            quality=q,
            optimize=True,
            progressive=True,
            subsampling=2,
        )
        data = buf.getvalue()
        n = len(data)

        if min_bytes <= n <= max_bytes:
            return data

        if n <= max_bytes and n > best_under_max_len:
            best_under_max = data
            best_under_max_len = n

        if n >= min_bytes and n < best_over_min_len:
            best_over_min = data
            best_over_min_len = n

    # Prefer <= max if we can, otherwise fall back to smallest >= min.
    if best_under_max is not None:
        return best_under_max
    if best_over_min is not None:
        return best_over_min

    # Last resort: return something reasonable
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92, optimize=True, progressive=True, subsampling=2)
    return buf.getvalue()


def _crop_grid_variants(
    grid_jpeg_bytes: bytes,
    tile_px: int = 512,
    output_px_candidates: Tuple[int, ...] = (1200,1400),
    target_kb_range: Tuple[int, int] = (150, 300),
) -> List[bytes]:
    """Crop a 1024x1536 grid image into 6 variants.

    Assumes a perfect 2x3 grid (6 tiles) covering the full canvas.
    - Crops 6 square tiles from the 2x3 grid (tile_px source crop)
    - Upscales each tile into the 1000–2000px band
    - Encodes each variant as JPEG targeting ~150–300KB (best-effort)
    """
    from PIL import Image

    img = Image.open(io.BytesIO(grid_jpeg_bytes)).convert("RGB")
    if img.size != (1024, 1536):
        img = img.resize((1024, 1536), resample=Image.Resampling.LANCZOS)

    cols, rows = 2, 3
    tile_px = min(img.size[0] // cols, img.size[1] // rows)

    min_bytes = target_kb_range[0] * 1024
    max_bytes = target_kb_range[1] * 1024

    variants: List[bytes] = []
    for idx in range(cols * rows):
        row = idx // cols
        col = idx % cols
        x0 = col * tile_px
        y0 = row * tile_px
        tile = img.crop((x0, y0, x0 + tile_px, y0 + tile_px)).convert("RGB")

        chosen: Optional[bytes] = None
        for out_px in output_px_candidates:
            resized = tile.resize((out_px, out_px), resample=Image.Resampling.LANCZOS)
            encoded = _encode_jpeg_target_size(resized, target_range_bytes=(min_bytes, max_bytes))
            chosen = encoded
            # If we hit (or exceed) the minimum size, stop; otherwise try a larger output size.
            if len(encoded) >= min_bytes:
                break

        if chosen is None:
            # Defensive fallback
            buf = io.BytesIO()
            tile.save(buf, format="JPEG", quality=92, optimize=True)
            chosen = buf.getvalue()

        variants.append(chosen)

    return variants


@router.get("/signed-url/{object_key:path}")
async def get_signed_url(object_key: str, expires_in: Optional[int] = Query(900, description="Expiry time in seconds")):
    """
    Generate a presigned URL for temporary access to a private S3 object.
    
    Args:
        object_key: The S3 object key (e.g., "optimized_grid_abc123.png")
        expires_in: Expiry time in seconds (default: 900 = 15 minutes)
    
    Returns:
        JSON with signed_url and expires_at timestamp
    """
    try:
        result = await generate_presigned_url(object_key, expires_in=expires_in)
        return {
            "signed_url": result["signed_url"],
            "expires_at": result["expires_at"],
            "object_key": object_key
        }
    except Exception as e:
        logger.error(f"Failed to generate presigned URL for {object_key}: {e}")
        raise HTTPException(
            status_code=500, 
            detail=f"Failed to generate signed URL: {str(e)}"
        )


# Place the /proxy/ endpoint after router is defined
@router.get("/proxy/")
async def proxy_image_query(url: str = Query(...), download: bool = Query(False)):
    """Proxy endpoint to serve images from S3 using a ?url=... query param (for frontend compatibility)."""
    try:
        from fastapi.responses import StreamingResponse
        import io

        settings = get_settings()

        # Parse the URL to extract bucket and object name
        parsed = urlparse(unquote(url))
        # Example: https://s3.us-east-005.backblazeb2.com/meeship-images/optimized_test_3.jpg
        # path: /meeship-images/optimized_test_3.jpg
        path = parsed.path.lstrip('/')
        parts = path.split('/', 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid S3 URL format")
        bucket_name = parts[0]
        object_name = parts[1]

        # Get object from S3
        data = await get_object(object_name)
        
        headers = {"Access-Control-Allow-Origin": "*"}
        if download:
            headers["Content-Disposition"] = f"attachment; filename={object_name}"
        return StreamingResponse(io.BytesIO(data), headers=headers)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Proxy error: {e}")

@router.post("/batch_ab_optimize")
async def batch_ab_optimize_endpoint(
    file: UploadFile = File(...),
    prompts: Optional[str] = Form(None),  # JSON array or comma-separated
    models: Optional[str] = Form(None),   # JSON array or comma-separated
    pipeline_config: Optional[str] = Form(None),  # JSON dict or None
    actual_weight_g: Optional[float] = Form(None),
    dimensions_cm: Optional[str] = Form(None),  # JSON array or comma-separated
    delay_seconds: Optional[int] = Form(15),
    current_user=Depends(get_current_user),
):
    """
    Batch A/B optimization endpoint for dashboard grid.
    Accepts an image and triggers 10 batch optimizations (5 prompts × 2 models).
    Returns a list of result dicts, each with metrics and base64 image.
    """
    try:
        image_bytes = await file.read()
        dims = None
        if dimensions_cm:
            try:
                if dimensions_cm.strip().startswith("[") or dimensions_cm.strip().startswith("{"):
                    dims = tuple(json.loads(dimensions_cm))
                else:
                    dims = tuple(float(x) for x in dimensions_cm.split(","))
                if len(dims) != 3:
                    raise ValueError
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid dimensions_cm format. Use JSON array or 'w,h,d'.")
        # Parse prompts and models
        prompt_list = None
        if prompts:
            try:
                if prompts.strip().startswith("["):
                    prompt_list = json.loads(prompts)
                else:
                    prompt_list = [p.strip() for p in prompts.split(",") if p.strip()]
            except Exception:
                prompt_list = None
        model_list = None
        if models:
            try:
                if models.strip().startswith("["):
                    model_list = json.loads(models)
                else:
                    model_list = [m.strip() for m in models.split(",") if m.strip()]
            except Exception:
                model_list = None
        config_dict = None
        if pipeline_config:
            try:
                config_dict = json.loads(pipeline_config)
            except Exception:
                config_dict = None

        settings = get_settings()
        if getattr(settings, "AZURE_FOUNDRY_ENDPOINT", None) and FluxOptimizer is not None:
            flux = FluxOptimizer(
                base_url=getattr(settings, "AZURE_FOUNDRY_ENDPOINT", None),
                api_key=getattr(settings, "AZURE_FOUNDRY_API_KEY", None),
                model_name=getattr(settings, "AZURE_FOUNDRY_MODEL_NAME", None),
            )
            results = await flux.batch_optimize_ab_test(
                image_bytes=image_bytes,
                original_filename=file.filename,
                prompts=prompt_list,
                models=model_list,
                pipeline_config=config_dict,
                actual_weight_g=actual_weight_g,
                dimensions_cm=dims,
                delay_seconds=delay_seconds if delay_seconds is not None else 15,
            )
        else:
            raise HTTPException(status_code=503, detail="Batch A/B optimization requires FLUX remote optimizer.")

        return {"results": results}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Batch A/B optimization failed: {e}")
        raise HTTPException(status_code=500, detail=f"Batch A/B optimization failed: {e}")

# Dependency for MinIO storage upload (returns True if enabled)
def get_minio_enabled():
    """Check if S3 storage is enabled (backwards compatible function name)"""
    settings = get_settings()
    return settings.S3_ENABLED

@router.post("/optimize")
async def optimize_image_endpoint(
    file: UploadFile = File(...),
    actual_weight_g: Optional[float] = Form(None),
    dimensions_cm: Optional[str] = Form(None),  # Expecting JSON string or comma-separated
    prompt_variant: Optional[str] = Form(None),
    prompt_variants: Optional[str] = Form(None),  # JSON array or comma-separated
    flux_models: Optional[str] = Form(None),  # JSON array or comma-separated model endpoints
    delay_between_calls: Optional[int] = Form(None),
    disable_fallback: Optional[bool] = Form(False),
    db: AsyncSession = Depends(get_db),
    minio_enabled: bool = Depends(get_minio_enabled),
    current_user=Depends(get_current_user_optional),
):
    # --- Credits enforcement ---
    is_trial_user = False
    if current_user is not None:
        if current_user.credits <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No credits remaining. Please purchase credits to continue."
            )
        # Deduct 1 credit
        current_user.credits -= 1
        await db.commit()
    try:
        image_bytes = await file.read()
        dims = None
        if dimensions_cm:
            try:
                # Accepts either JSON string or "w,h,d"
                if dimensions_cm.strip().startswith("[") or dimensions_cm.strip().startswith("{"):
                    dims = tuple(json.loads(dimensions_cm))
                else:
                    dims = tuple(float(x) for x in dimensions_cm.split(","))
                if len(dims) != 3:
                    raise ValueError
            except Exception:
                raise HTTPException(status_code=400, detail="Invalid dimensions_cm format. Use JSON array or 'w,h,d'.")
        # Run optimizer — prefer Azure OpenAI gpt-image-1.5 if configured
        settings = get_settings()
        if (
            getattr(settings, "AZURE_OPENAI_ENDPOINT", None)
            and getattr(settings, "AZURE_OPENAI_API_KEY", None)
            and GptImage15Optimizer is not None
        ):
            gpt = GptImage15Optimizer(
                endpoint=getattr(settings, "AZURE_OPENAI_ENDPOINT", None),
                api_key=getattr(settings, "AZURE_OPENAI_API_KEY", None),
                deployment=getattr(settings, "AZURE_OPENAI_DEPLOYMENT_NAME", None),
                api_version=getattr(settings, "OPENAI_API_VERSION", None),
            )

            pipeline_config = {}
            if prompt_variant:
                # allow overriding prompt variant text if needed via pipeline_config in future
                pipeline_config["prompt_variant"] = prompt_variant

            optimized_bytes, metrics = await gpt.optimize_image(
                image_bytes=image_bytes,
                original_filename=file.filename,
                pipeline_config=pipeline_config,
                actual_weight_g=actual_weight_g,
                dimensions_cm=dims,
            )
        elif getattr(settings, "AZURE_FOUNDRY_ENDPOINT", None) and FluxOptimizer is not None:
            flux = FluxOptimizer(
                base_url=getattr(settings, "AZURE_FOUNDRY_ENDPOINT", None),
                api_key=getattr(settings, "AZURE_FOUNDRY_API_KEY", None),
                model_name=getattr(settings, "AZURE_FOUNDRY_MODEL_NAME", None),
            )
            pipeline_config = {}
            # parse prompt_variants if provided (JSON array or CSV)
            if prompt_variants:
                try:
                    if prompt_variants.strip().startswith("["):
                        pipeline_config["prompt_variants"] = json.loads(prompt_variants)
                    else:
                        pipeline_config["prompt_variants"] = [p.strip() for p in prompt_variants.split(",") if p.strip()]
                except Exception:
                    pipeline_config["prompt_variants"] = [prompt_variant] if prompt_variant else None
            elif prompt_variant:
                pipeline_config["prompt_variant"] = prompt_variant

            # parse flux_models if provided
            if flux_models:
                try:
                    if flux_models.strip().startswith("["):
                        pipeline_config["flux_models"] = json.loads(flux_models)
                    else:
                        pipeline_config["flux_models"] = [m.strip() for m in flux_models.split(",") if m.strip()]
                except Exception:
                    pipeline_config["flux_models"] = [flux.model_name] if getattr(flux, "model_name", None) else [getattr(settings, "AZURE_FOUNDRY_MODEL_NAME", "FLUX.1-Kontext-pro")]

            if delay_between_calls is not None:
                pipeline_config["delay_between_calls"] = int(delay_between_calls)

            if disable_fallback:
                pipeline_config["disable_local_fallback"] = True

            optimized_bytes, metrics = await flux.optimize_image(
                image_bytes=image_bytes,
                original_filename=file.filename,
                pipeline_config=pipeline_config,
                actual_weight_g=actual_weight_g,
                dimensions_cm=dims,
            )
        else:
            optimized_bytes, metrics = await local_optimize_image(
                image_bytes=image_bytes,
                original_filename=file.filename,
                pipeline_config=None,
                actual_weight_g=actual_weight_g,
                dimensions_cm=dims,
            )
        # Prepare DB record
        cost_fields = metrics.get("cost_fields", {})
        stage_metrics = metrics.get("stage_metrics", {})
        error = metrics.get("error")
        status_str = "error" if error else "success"

        input_dims = metrics.get("input_dimensions") or [None, None]
        if not isinstance(input_dims, (list, tuple)) or len(input_dims) < 2:
            input_dims = [None, None]
        output_dims = metrics.get("output_dimensions") or [None, None]
        if not isinstance(output_dims, (list, tuple)) or len(output_dims) < 2:
            output_dims = [None, None]

        processed = ProcessedImage(
            original_filename=file.filename,
            input_size_bytes=metrics.get("input_size_bytes"),
            output_size_bytes=metrics.get("output_size_bytes"),
            input_width=input_dims[0],
            input_height=input_dims[1],
            output_width=output_dims[0],
            output_height=output_dims[1],
            processing_time_ms=metrics.get("processing_time_ms"),
            actual_weight_g=cost_fields.get("actual_weight_g"),
            volumetric_weight_g=cost_fields.get("volumetric_weight_g"),
            billable_weight_g=cost_fields.get("billable_weight_g"),
            shipping_cost_inr=cost_fields.get("shipping_cost_inr"),
            optimizer_version=metrics.get("optimizer_version"),
            stage_metrics_json=json.dumps(stage_metrics),
            status=status_str,
            error_message=error,
            is_trial=is_trial_user,
            user_id=current_user.id if current_user is not None else None,
        )

        # If the remote optimizer failed, persist the record but return a clear upstream error.
        if error:
            db.add(processed)
            await db.commit()
            await db.refresh(processed)
            raise HTTPException(
                status_code=502,
                detail={
                    "id": str(processed.id),
                    "error": error,
                    "stage_metrics": stage_metrics,
                    "metrics": metrics,
                },
            )
        # Upload to S3 if enabled
        blob_url = None
        original_blob_url = None
        variant_blob_urls: Optional[List[str]] = None
        if minio_enabled:
            try:
                # Use a unique run id for all outputs in this request
                run_id = uuid.uuid4().hex
                # Upload optimized grid image with randomization
                object_key = await upload_to_s3(
                    optimized_bytes,
                    filename=f"optimized_grid_{run_id}.png",
                    content_type="image/png",
                )
                # Generate presigned URL for the uploaded object
                presigned_result = await generate_presigned_url(object_key)
                blob_url = presigned_result["signed_url"]
                processed.azure_blob_url = blob_url

                # Crop and upload 6 variants from the generated grid, each with unique name
                # Use parallel upload for better performance
                try:
                    import asyncio
                    variant_bytes_list = _crop_grid_variants(optimized_bytes)
                    
                    async def upload_variant(idx: int, variant_bytes: bytes) -> str:
                        """Upload a single variant and return its presigned URL."""
                        variant_id = uuid.uuid4().hex[:8]
                        variant_key = await upload_to_s3(
                            variant_bytes,
                            filename=f"optimized_variant_{idx+1}_{variant_id}_{run_id}.jpg",
                            content_type="image/jpeg",
                        )
                        variant_presigned = await generate_presigned_url(variant_key)
                        return variant_presigned["signed_url"]
                    
                    # Upload all 6 variants in parallel
                    upload_tasks = [
                        upload_variant(i, vb) 
                        for i, vb in enumerate(variant_bytes_list)
                    ]
                    variant_blob_urls = await asyncio.gather(*upload_tasks)
                    variant_blob_urls = list(variant_blob_urls)  # Convert tuple to list
                except Exception as e:
                    logger.warning("Variant crop/upload failed: %s", e)

                # Upload original image for comparison with randomization
                orig_id = uuid.uuid4().hex[:8]
                original_key = await upload_to_s3(
                    image_bytes,
                    filename=f"original_{orig_id}_{run_id}.{file.filename.split('.')[-1] if '.' in file.filename else 'jpg'}",
                    content_type=file.content_type or "image/jpeg",
                )
                original_presigned = await generate_presigned_url(original_key)
                original_blob_url = original_presigned["signed_url"]
            except Exception as e:
                processed.status = "error"
                processed.error_message = f"S3 upload failed: {e}"
        # Persist to DB
        db.add(processed)
        await db.commit()
        await db.refresh(processed)
        # Response
        response = {
            "id": str(processed.id),
            "metrics": metrics,
            "cost": cost_fields,
            "blob_url": processed.azure_blob_url,
            "original_blob_url": original_blob_url,
            "variant_blob_urls": variant_blob_urls,
            "status": processed.status,
            "error_message": processed.error_message,
        }
        # If optimizer returned FLUX attempts, include them for the frontend
        if isinstance(metrics, dict) and metrics.get("flux_attempts"):
            response["flux_attempts"] = metrics.get("flux_attempts")
        return response
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Image optimization failed: {e}")


@router.post("/optimize-stream")
async def optimize_image_stream(
    request: Request,
    file: UploadFile = File(...),
    actual_weight_g: Optional[float] = Form(None),
    dimensions_cm: Optional[str] = Form(None),
    prompt_variant: Optional[str] = Form(None),
    db: AsyncSession = Depends(get_db),
    minio_enabled: bool = Depends(get_minio_enabled),
    current_user=Depends(get_current_user_optional),
):
    """Streaming optimization endpoint that yields variants via Server-Sent Events.
    
    Returns SSE events:
    - status: {stage: "generating"|"processing"|"uploading", progress: 0-100, message: str}
    - variant: {index: int, tile_index: int, variant_type: str, url: str, tile_name: str, variant_label: str}
    - error: {message: str, recoverable: bool}
    - complete: {total: int, successful: int, failed: int}
    """
    # Pre-validate and read image before starting SSE
    image_bytes = await file.read()
    original_filename = file.filename
    content_type = file.content_type or "image/jpeg"
    
    # Parse dimensions
    dims = None
    if dimensions_cm:
        try:
            if dimensions_cm.strip().startswith("[") or dimensions_cm.strip().startswith("{"):
                dims = tuple(json.loads(dimensions_cm))
            else:
                dims = tuple(float(x) for x in dimensions_cm.split(","))
            if len(dims) != 3:
                raise ValueError
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid dimensions_cm format.")

    # --- Credits enforcement ---
    is_trial_user = False
    if current_user is not None:
        if current_user.credits <= 0:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="No credits remaining. Please purchase credits to continue."
            )
        # Deduct 1 credit
        current_user.credits -= 1
        await db.commit()

    async def event_generator() -> AsyncGenerator[dict, None]:
        """Generate SSE events as variants are created and uploaded."""
        run_id = uuid.uuid4().hex
        start_time = time.time()
        
        successful_variants = 0
        failed_variants = 0
        total_variants = 30  # 6 tiles × 5 variants
        variant_urls: List[str] = []
        grid_url = None
        original_url = None
        metrics = {}
        
        try:
            # === Stage 1: Generate grid with GPT ===
            yield {
                "event": "status",
                "data": json.dumps({
                    "stage": "generating",
                    "progress": 0,
                    "message": "Generating your product images with AI..."
                })
            }
            
            settings = get_settings()
            optimized_bytes = None
            
            if (
                getattr(settings, "AZURE_OPENAI_ENDPOINT", None)
                and getattr(settings, "AZURE_OPENAI_API_KEY", None)
                and GptImage15Optimizer is not None
            ):
                gpt = GptImage15Optimizer(
                    endpoint=getattr(settings, "AZURE_OPENAI_ENDPOINT", None),
                    api_key=getattr(settings, "AZURE_OPENAI_API_KEY", None),
                    deployment=getattr(settings, "AZURE_OPENAI_DEPLOYMENT_NAME", None),
                    api_version=getattr(settings, "OPENAI_API_VERSION", None),
                )
                
                pipeline_config = {}
                if prompt_variant:
                    pipeline_config["prompt_variant"] = prompt_variant
                
                optimized_bytes, metrics = await gpt.optimize_image(
                    image_bytes=image_bytes,
                    original_filename=original_filename,
                    pipeline_config=pipeline_config,
                    actual_weight_g=actual_weight_g,
                    dimensions_cm=dims,
                )
            elif getattr(settings, "AZURE_FOUNDRY_ENDPOINT", None) and FluxOptimizer is not None:
                flux = FluxOptimizer(
                    base_url=getattr(settings, "AZURE_FOUNDRY_ENDPOINT", None),
                    api_key=getattr(settings, "AZURE_FOUNDRY_API_KEY", None),
                    model_name=getattr(settings, "AZURE_FOUNDRY_MODEL_NAME", None),
                )
                optimized_bytes, metrics = await flux.optimize_image(
                    image_bytes=image_bytes,
                    original_filename=original_filename,
                    actual_weight_g=actual_weight_g,
                    dimensions_cm=dims,
                )
            else:
                optimized_bytes, metrics = await local_optimize_image(
                    image_bytes=image_bytes,
                    original_filename=original_filename,
                    actual_weight_g=actual_weight_g,
                    dimensions_cm=dims,
                )
            
            # Check for generation errors
            if metrics.get("error"):
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "message": f"Image generation failed: {metrics.get('error')}",
                        "recoverable": False,
                        "stage_metrics": metrics.get("stage_metrics", {})
                    })
                }
                return
            
            yield {
                "event": "status",
                "data": json.dumps({
                    "stage": "processing",
                    "progress": 15,
                    "message": "AI generation complete. Creating shipping variants..."
                })
            }
            
            # === Stage 2: Upload grid and original ===
            if minio_enabled:
                try:
                    # Upload grid
                    grid_key = await upload_to_s3(
                        optimized_bytes,
                        filename=f"optimized_grid_{run_id}.png",
                        content_type="image/png",
                    )
                    grid_presigned = await generate_presigned_url(grid_key)
                    grid_url = grid_presigned["signed_url"]
                    
                    # Upload original
                    ext = original_filename.split('.')[-1] if '.' in original_filename else 'jpg'
                    orig_key = await upload_to_s3(
                        image_bytes,
                        filename=f"original_{uuid.uuid4().hex[:8]}_{run_id}.{ext}",
                        content_type=content_type,
                    )
                    orig_presigned = await generate_presigned_url(orig_key)
                    original_url = orig_presigned["signed_url"]
                except Exception as e:
                    logger.warning(f"Grid/original upload failed: {e}")
            
            yield {
                "event": "status",
                "data": json.dumps({
                    "stage": "uploading",
                    "progress": 20,
                    "message": "Generating and uploading 30 shipping-optimized variants..."
                })
            }
            
            # === Stage 3: Generate and stream variants ===
            from PIL import Image as PILImage
            
            for variant_bytes, info in generate_all_shipping_variants(optimized_bytes):
                # Check if client disconnected
                if await request.is_disconnected():
                    logger.info("Client disconnected, stopping variant generation")
                    break
                
                try:
                    # Upscale and encode - 800px optimized for Meesho shipping estimates
                    variant_img = PILImage.open(io.BytesIO(variant_bytes)).convert("RGB")
                    final_bytes = encode_variant_jpeg(variant_img, output_size=1200)
                    
                    # Upload variant
                    if minio_enabled:
                        variant_id = uuid.uuid4().hex[:8]
                        variant_key = await upload_to_s3(
                            final_bytes,
                            filename=f"optimized_variant_{info.tile_index}_{info.variant_index}_{variant_id}_{run_id}.jpg",
                            content_type="image/jpeg",
                        )
                        variant_presigned = await generate_presigned_url(variant_key)
                        variant_url = variant_presigned["signed_url"]
                        variant_urls.append(variant_url)
                        
                        successful_variants += 1
                        progress = 20 + int((successful_variants / total_variants) * 75)
                        
                        yield {
                            "event": "variant",
                            "data": json.dumps({
                                "index": info.global_index,
                                "tile_index": info.tile_index,
                                "variant_index": info.variant_index,
                                "variant_type": info.variant_type.value,
                                "url": variant_url,
                                "tile_name": info.tile_name,
                                "variant_label": info.variant_label,
                                "completed": successful_variants,
                                "total": total_variants,
                                "progress": progress,
                            })
                        }
                except Exception as e:
                    failed_variants += 1
                    logger.warning(f"Variant {info.global_index} failed: {e}")
                    yield {
                        "event": "error",
                        "data": json.dumps({
                            "message": f"Variant {info.global_index + 1} failed: {str(e)}",
                            "recoverable": True,
                            "variant_index": info.global_index,
                        })
                    }
            
            # === Stage 4: Save to database ===
            cost_fields = metrics.get("cost_fields", {})
            stage_metrics = metrics.get("stage_metrics", {})
            input_dims = metrics.get("input_dimensions") or [None, None]
            output_dims = metrics.get("output_dimensions") or [None, None]
            
            processing_time_ms = int((time.time() - start_time) * 1000)
            
            processed = ProcessedImage(
                original_filename=original_filename,
                azure_blob_url=grid_url,
                input_size_bytes=metrics.get("input_size_bytes"),
                output_size_bytes=metrics.get("output_size_bytes"),
                input_width=input_dims[0] if len(input_dims) > 0 else None,
                input_height=input_dims[1] if len(input_dims) > 1 else None,
                output_width=output_dims[0] if len(output_dims) > 0 else None,
                output_height=output_dims[1] if len(output_dims) > 1 else None,
                processing_time_ms=processing_time_ms,
                actual_weight_g=cost_fields.get("actual_weight_g"),
                volumetric_weight_g=cost_fields.get("volumetric_weight_g"),
                billable_weight_g=cost_fields.get("billable_weight_g"),
                shipping_cost_inr=cost_fields.get("shipping_cost_inr"),
                optimizer_version=metrics.get("optimizer_version", "gpt-image-stream-v1"),
                stage_metrics_json=json.dumps({
                    **stage_metrics,
                    "variant_count": successful_variants,
                    "variant_failures": failed_variants,
                }),
                status="success" if successful_variants > 0 else "error",
                error_message=None if successful_variants > 0 else "All variants failed",
                is_trial=is_trial_user,
                user_id=current_user.id if current_user is not None else None,
            )
            
            db.add(processed)
            await db.commit()
            await db.refresh(processed)
            
            # === Final: Complete event ===
            yield {
                "event": "complete",
                "data": json.dumps({
                    "id": str(processed.id),
                    "total": total_variants,
                    "successful": successful_variants,
                    "failed": failed_variants,
                    "grid_url": grid_url,
                    "original_url": original_url,
                    "variant_urls": variant_urls,
                    "processing_time_ms": processing_time_ms,
                    "metrics": metrics,
                })
            }
            
        except Exception as e:
            logger.exception(f"Streaming optimization failed: {e}")
            yield {
                "event": "error",
                "data": json.dumps({
                    "message": f"Optimization failed: {str(e)}",
                    "recoverable": False,
                })
            }
    
    return EventSourceResponse(event_generator())

@router.get("/{image_id}/results")
async def get_image_results(
    image_id: str,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Get optimization results for a specific image by ID"""
    try:
        from uuid import UUID
        try:
            image_uuid = UUID(image_id)
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid image ID format")
        
        q = await db.execute(
            select(ProcessedImage).where(ProcessedImage.id == image_uuid)
        )
        img = q.scalar_one_or_none()
        
        if not img:
            raise HTTPException(status_code=404, detail="Image not found")
        
        # Verify ownership
        if img.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Access denied")
        
        try:
            stage_metrics = json.loads(img.stage_metrics_json) if img.stage_metrics_json else {}
        except Exception:
            stage_metrics = {}
        
        return {
            "id": str(img.id),
            "created_at": img.created_at.isoformat() if img.created_at else None,
            "original_filename": img.original_filename,
            "azure_blob_url": img.azure_blob_url,
            "blob_url": img.azure_blob_url,  # Alias for frontend
            "original_blob_url": None,  # TODO: Store original image URL in DB column
            "weight_category": img.weight_category,
            "savings_amount": img.savings_amount,
            "is_trial": img.is_trial,
            "input_size_bytes": img.input_size_bytes,
            "output_size_bytes": img.output_size_bytes,
            "input_width": img.input_width,
            "input_height": img.input_height,
            "output_width": img.output_width,
            "output_height": img.output_height,
            "processing_time_ms": img.processing_time_ms,
            "actual_weight_g": img.actual_weight_g,
            "volumetric_weight_g": img.volumetric_weight_g,
            "billable_weight_g": img.billable_weight_g,
            "shipping_cost_inr": img.shipping_cost_inr,
            "status": img.status,
            "error_message": img.error_message,
            "optimizer_version": img.optimizer_version,
            "stage_metrics": stage_metrics,
            "metrics": {
                "input_size_bytes": img.input_size_bytes,
                "output_size_bytes": img.output_size_bytes,
                "size_reduction_percent": round(((img.input_size_bytes - img.output_size_bytes) / img.input_size_bytes * 100), 2) if img.input_size_bytes else 0,
                "processing_time_ms": img.processing_time_ms,
            },
            "cost": {
                "actual_weight_g": img.actual_weight_g,
                "volumetric_weight_g": img.volumetric_weight_g,
                "billable_weight_g": img.billable_weight_g,
                "shipping_cost_inr": img.shipping_cost_inr,
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch image results: {e}")

@router.get("/history")
async def get_image_history(
    db: AsyncSession = Depends(get_db),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
):
    try:
        q = await db.execute(
            select(ProcessedImage)
            .order_by(ProcessedImage.created_at.desc())
            .offset(skip)
            .limit(limit)
        )
        results = q.scalars().all()
        items = []
        for img in results:
            try:
                stage_metrics = json.loads(img.stage_metrics_json) if img.stage_metrics_json else {}
            except Exception:
                stage_metrics = {}
            items.append({
                "id": str(img.id),
                "created_at": img.created_at.isoformat() if img.created_at else None,
                "original_filename": img.original_filename,
                "azure_blob_url": img.azure_blob_url,
                "weight_category": img.weight_category,
                "savings_amount": img.savings_amount,
                "is_trial": img.is_trial,
                "input_size_bytes": img.input_size_bytes,
                "output_size_bytes": img.output_size_bytes,
                "input_width": img.input_width,
                "input_height": img.input_height,
                "output_width": img.output_width,
                "output_height": img.output_height,
                "processing_time_ms": img.processing_time_ms,
                "actual_weight_g": img.actual_weight_g,
                "volumetric_weight_g": img.volumetric_weight_g,
                "billable_weight_g": img.billable_weight_g,
                "shipping_cost_inr": img.shipping_cost_inr,
                "status": img.status,
                "error_message": img.error_message,
                "optimizer_version": img.optimizer_version,
                "stage_metrics": stage_metrics,
            })
        return {
            "count": len(items),
            "results": items,
            "skip": skip,
            "limit": limit,
        }
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Database error: {e}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to fetch history: {e}")

@router.get("/proxy/{path:path}")
async def proxy_image(path: str, download: bool = Query(False)):
    """Proxy endpoint to serve images from S3 with CORS headers. If download=1, set Content-Disposition for download."""
    try:
        from fastapi.responses import StreamingResponse
        import io
        
        settings = get_settings()
        
        # Extract bucket and object name from path
        # path format: meeship-images/optimized_Screenshot_2026-01-09_150004.png
        parts = path.split('/', 1)
        if len(parts) != 2:
            raise HTTPException(status_code=400, detail="Invalid path format")
        
        bucket_name = parts[0]
        object_name = parts[1]
        
        # Get the object from S3
        data = await get_object(object_name)
        
        headers = {
            "Access-Control-Allow-Origin": "*",
            "Cache-Control": "public, max-age=3600",
        }
        if download:
            # Use the object name as filename
            filename = object_name.split("/")[-1]
            headers["Content-Disposition"] = f"attachment; filename={filename}"
        return StreamingResponse(
            iter([data]),
            media_type="image/jpeg",
            headers=headers
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Proxy image error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to fetch image: {str(e)}")