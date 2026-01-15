import io
import time
import asyncio
from typing import Optional, Dict, Any, Tuple

import numpy as np
from PIL import Image
import cv2
from sklearn.cluster import KMeans
import logging

logger = logging.getLogger(__name__)


async def optimize_image(
    image_bytes: bytes,
    original_filename: str,
    pipeline_config: Optional[Dict[str, Any]] = None,
    actual_weight_g: Optional[float] = None,
    dimensions_cm: Optional[Tuple[float, float, float]] = None,
) -> Tuple[bytes, Dict[str, Any]]:
    """
    Optimize an image for e-commerce product listing using ML-enhanced techniques.
    
    Features:
    - ML product detection with GrabCut + KMeans clustering
    - Already-optimized image detection (skips unnecessary processing)
    - Intelligent cropping to product area
    - Product-only white background application
    - Selective sharpening on product edges
    - Aggressive compression targeting <180KB
    
    Args:
        image_bytes (bytes): Input image in bytes.
        original_filename (str): Original filename for reference.
        pipeline_config (dict, optional): Per-call config/overrides for pipeline stages.
        actual_weight_g (float, optional): Actual weight in grams, if known.
        dimensions_cm (tuple, optional): (W, H, D) in centimeters, if known.

    Returns:
        Tuple[bytes, dict]: (optimized_image_bytes, metrics_dict)
    
    Raises:
        Exception: If pipeline fails, exception message is included in metrics_dict['error'].

    """
    start_time = time.time()
    metrics = {
        'input_size_bytes': len(image_bytes),
        'output_size_bytes': None,
        'input_dimensions': None,
        'output_dimensions': (1200, 1200),
        'processing_time_ms': None,
        'size_reduction_percent': None,
        'cost_fields': {},
        'optimizer_version': '2.0.0-ml',
        'stage_metrics': {},
        'error': None
    }
    try:
        # Load image
        image_cv = cv2.imdecode(np.frombuffer(image_bytes, np.uint8), cv2.IMREAD_COLOR)
        if image_cv is None:
            raise ValueError("Failed to decode image")
        
        h, w = image_cv.shape[:2]
        metrics['input_dimensions'] = (w, h)
        logger.info(f"Loaded image: {w}x{h}, {len(image_bytes)/1024:.2f}KB")
        
        # 1. Check if already optimized - SKIP if perfect
        if is_already_optimized(image_cv, image_bytes):
            logger.info("Image already optimized, skipping processing")
            metrics['stage_metrics']['optimization_skipped'] = True
            metrics['output_size_bytes'] = len(image_bytes)
            metrics['size_reduction_percent'] = 0
            metrics['cost_fields'] = _predict_cost(w, h, actual_weight_g)
            metrics['processing_time_ms'] = (time.time() - start_time) * 1000
            return image_bytes, metrics
        
        # 2. ML Product Detection
        logger.info("Starting ML product detection...")
        product_mask = detect_product_ml(image_cv)
        
        if product_mask is None:
            logger.info("ML detection failed, using edge detection fallback")
            product_mask = simple_crop(image_cv)
        else:
            logger.info("Product detected via GrabCut + KMeans")
        
        metrics['stage_metrics']['product_detected'] = product_mask is not None
        
        # 3. Crop to product (90% fill - aggressive)
        image_cropped = crop_to_product(image_cv, product_mask, target_fill=0.90)
        if image_cropped is None or image_cropped.size == 0:
            image_cropped = image_cv
            logger.warning("Crop failed, using original image")
        
        # 4. Resize to 1200x1200 with Lanczos interpolation
        image_resized = cv2.resize(image_cropped, (1200, 1200), interpolation=cv2.INTER_LANCZOS4)
        
        # Resize mask to match resized image dimensions
        if product_mask is not None:
            product_mask = cv2.resize(product_mask, (1200, 1200), interpolation=cv2.INTER_NEAREST)
        
        logger.info("Resized to 1200x1200")
        
        # 5. Product-only white background
        image_bg_clean = apply_white_bg_product_only(image_resized, product_mask)
        logger.info("Applied product-only white background")
        
        # 6. Selective sharpening
        image_sharpened = selective_sharpen(image_bg_clean, product_mask)
        logger.info("Applied selective sharpening")
        
        # 7. Aggressive compression to <180KB
        optimized_bytes = aggressive_compress(image_sharpened)
        logger.info(f"Compressed to {len(optimized_bytes)/1024:.2f}KB")
        
        # Calculate metrics
        metrics['output_size_bytes'] = len(optimized_bytes)
        metrics['size_reduction_percent'] = ((len(image_bytes) - len(optimized_bytes)) / len(image_bytes)) * 100
        metrics['cost_fields'] = _predict_cost(1200, 1200, actual_weight_g)
        metrics['processing_time_ms'] = (time.time() - start_time) * 1000
        
        logger.info(f"Optimization complete: {len(image_bytes)/1024:.2f}KB → {len(optimized_bytes)/1024:.2f}KB "
                   f"({metrics['size_reduction_percent']:.1f}% reduction)")
        
        return optimized_bytes, metrics

    except Exception as e:
        logger.error(f"Image optimization failed: {str(e)}")
        metrics['error'] = str(e)
        metrics['processing_time_ms'] = (time.time() - start_time) * 1000
        raise Exception(f"Image optimization failed: {e}")


# ============================================================================
# ML-ENHANCED OPTIMIZATION FUNCTIONS
# ============================================================================

def is_already_optimized(image, image_bytes):
    """Check if image is already perfectly optimized"""
    h, w = image.shape[:2]
    size_kb = len(image_bytes) / 1024
    
    # Already good if: 1200x1200, <200KB, mostly white background
    if size_kb < 200 and h == 1200 and w == 1200:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        white_ratio = np.sum(gray > 240) / gray.size
        if white_ratio > 0.6:  # 60% white bg threshold
            logger.info("Image already optimized: 1200x1200, <200KB, 60%+ white background")
            return True
    return False


def detect_product_ml(image):
    """ML Product Detection using GrabCut + KMeans clustering"""
    try:
        h, w = image.shape[:2]
        mask = np.zeros((h, w), np.uint8)
        
        # GrabCut initialization with center rectangle
        rect = (w // 4, h // 4, w // 2, h // 2)
        bgd_model = np.zeros((1, 65), np.float64)
        fgd_model = np.zeros((1, 65), np.float64)
        
        cv2.grabCut(image, mask, rect, bgd_model, fgd_model, 5, cv2.GC_INIT_WITH_RECT)
        
        # Extract probable foreground pixels
        probable_fg = np.where((mask == cv2.GC_FGD) | (mask == cv2.GC_PR_FGD), 255, 0).astype(np.uint8)
        
        # Refine with KMeans clustering
        product_pixels = image[probable_fg == 255]
        if len(product_pixels) > 100:
            try:
                kmeans = KMeans(n_clusters=3, n_init=10, random_state=42)
                kmeans.fit(product_pixels.reshape(-1, 3))
                dominant_color = kmeans.cluster_centers_[np.argmax(np.bincount(kmeans.labels_))]
                
                # Create mask for dominant color with tolerance
                product_mask = create_color_mask(image, dominant_color, tolerance=30)
                return product_mask
            except Exception as e:
                logger.warning(f"KMeans clustering failed: {str(e)}")
                return probable_fg if np.sum(probable_fg) > 0 else None
        
        return probable_fg if np.sum(probable_fg) > 0 else None
    
    except Exception as e:
        logger.warning(f"ML product detection failed: {str(e)}")
        return None


def create_color_mask(image, color, tolerance=30):
    """Create mask for pixels similar to given color"""
    lower = np.array([max(0, c - tolerance) for c in color], dtype=np.uint8)
    upper = np.array([min(255, c + tolerance) for c in color], dtype=np.uint8)
    mask = cv2.inRange(image, lower, upper)
    
    # Dilate to expand mask
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
    mask = cv2.dilate(mask, kernel, iterations=2)
    
    return mask


def simple_crop(image):
    """Fallback: Edge detection-based crop"""
    try:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            margin = int(min(w, h) * 0.1)
            
            # Create mask from bounding box with margin
            mask = np.zeros(image.shape[:2], np.uint8)
            mask[max(0, y - margin):min(image.shape[0], y + h + margin),
                 max(0, x - margin):min(image.shape[1], x + w + margin)] = 255
            return mask
        
        return None
    except Exception as e:
        logger.warning(f"Edge detection crop failed: {str(e)}")
        return None


def crop_to_product(image, product_mask, target_fill=0.90):
    """Crop image to product area based on mask"""
    if product_mask is None:
        return image
    
    try:
        contours, _ = cv2.findContours(product_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        if contours:
            largest = max(contours, key=cv2.contourArea)
            x, y, w, h = cv2.boundingRect(largest)
            
            # Calculate margin to reach target fill percentage
            margin = int(min(w, h) * (1 - target_fill) / 2)
            
            # Apply margins with bounds checking
            x1 = max(0, x - margin)
            y1 = max(0, y - margin)
            x2 = min(image.shape[1], x + w + margin)
            y2 = min(image.shape[0], y + h + margin)
            
            cropped = image[y1:y2, x1:x2]
            return cropped if cropped.size > 0 else image
        
        return image
    except Exception as e:
        logger.warning(f"Crop to product failed: {str(e)}")
        return image


def apply_white_bg_product_only(image, product_mask):
    """Replace background with white, keep product as-is"""
    if product_mask is None:
        return image
    
    try:
        # Invert mask to get background areas
        bg_mask = cv2.bitwise_not(product_mask)
        
        # Create white background
        white_bg = np.full_like(image, 255)
        
        # Replace background only (keep product pixels)
        result = np.where(bg_mask[:, :, None] == 255, white_bg, image)
        return result.astype(np.uint8)
    except Exception as e:
        logger.warning(f"White background application failed: {str(e)}")
        return image


def selective_sharpen(image, product_mask):
    """Sharpen only product area, keep background as-is"""
    try:
        # Sharpening kernel
        kernel = np.array([[-1, -1, -1],
                          [-1,  9, -1],
                          [-1, -1, -1]], dtype=np.float32)
        
        if product_mask is None:
            # Apply to whole image if no mask
            return cv2.filter2D(image, -1, kernel)
        
        # Sharpen product only
        sharpened = cv2.filter2D(image, -1, kernel)
        
        # Expand mask to 3 channels
        mask_expanded = np.dstack([product_mask, product_mask, product_mask])
        
        # Blend: use sharpened where mask is 255, original elsewhere
        result = np.where(mask_expanded == 255, sharpened, image)
        return result.astype(np.uint8)
    except Exception as e:
        logger.warning(f"Selective sharpening failed: {str(e)}")
        return image


def aggressive_compress(image):
    """Binary search for compression <180KB with best quality"""
    try:
        pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
        
        # Try quality levels from 95 down to 20, targeting <180KB
        for quality in range(95, 19, -1):
            buffer = io.BytesIO()
            pil_image.save(buffer, 'JPEG', quality=quality, optimize=True)
            buffer.seek(0)
            compressed_bytes = buffer.getvalue()
            
            if len(compressed_bytes) <= 180 * 1024:
                logger.info(f"Compressed to {len(compressed_bytes)/1024:.2f}KB at quality {quality}")
                return compressed_bytes
        
        # If still too large at quality 20, return best effort
        logger.warning(f"Could not compress below 180KB, best effort: {len(compressed_bytes)/1024:.2f}KB")
        return compressed_bytes
    except Exception as e:
        logger.error(f"Compression failed: {str(e)}")
        # Return original encoded as JPEG if PIL compression fails
        success, encoded = cv2.imencode('.jpg', image, [cv2.IMWRITE_JPEG_QUALITY, 80])
        return encoded.tobytes() if success else None


def _predict_cost(width: int, height: int, actual_weight_g: Optional[float]) -> Dict[str, Any]:
    """Predict shipping cost based on image dimensions and weight"""
    # Estimate dimensions (assume 2cm thick, pixel to cm ratio 20cm/1200px)
    px_to_cm = 20 / 1200
    W = width * px_to_cm
    H = height * px_to_cm
    D = 2.0
    
    # Volumetric weight formula: (L × W × H) / 5000
    volumetric_weight = (W * H * D) / 5000
    
    # Use actual weight if provided, otherwise volumetric
    billable_weight = max(actual_weight_g or volumetric_weight, volumetric_weight)
    
    # Meesho shipping tiers
    if billable_weight <= 500:
        cost = 45
    elif billable_weight <= 1000:
        cost = 65
    elif billable_weight <= 2000:
        cost = 85
    else:
        cost = 110
    
    return {
        'actual_weight_g': actual_weight_g or volumetric_weight,
        'volumetric_weight_g': volumetric_weight,
        'billable_weight_g': billable_weight,
        'shipping_cost_inr': cost
    }