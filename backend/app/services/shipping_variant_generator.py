"""Shipping-optimized variant generator.

Generates 5 purposeful variants per base tile from the GPT-generated grid,
each designed to help sellers understand how visual size impacts perceived weight/shipping cost.
"""

import io
import logging
from dataclasses import dataclass
from enum import Enum
from typing import Generator, List, Tuple

from PIL import Image, ImageEnhance, ImageFilter

logger = logging.getLogger(__name__)


class VariantType(str, Enum):
    """Types of shipping-optimized variants."""
    HERO_COMPACT = "hero_compact"      # 85% zoom-out, max whitespace
    STANDARD = "standard"              # Original framing from model
    DETAIL_FOCUS = "detail_focus"      # 110% zoom-in for texture detail
    DYNAMIC_ANGLE = "dynamic_angle"    # Micro-rotate 3° for visual interest
    WARM_MINIMAL = "warm_minimal"      # Original size + warm tone + high contrast


@dataclass
class VariantInfo:
    """Information about a generated variant."""
    tile_index: int           # 0-5, which base tile this came from
    variant_type: VariantType # Which variant transformation
    variant_index: int        # 0-4, position within the tile's variants
    global_index: int         # 0-29, position in the full 30-variant list
    tile_name: str           # Human-readable tile name
    variant_label: str       # Human-readable variant label


# Tile names from the GPT prompt (0-indexed)
TILE_NAMES = [
    "Hero White",
    "Styled Neutral Context", 
    "Dramatic Light & Detail",
    "Secondary Clean Angle",
    "Dark Luxury Editorial",
    "Floating / Lightness Shot",
]

VARIANT_LABELS = {
    VariantType.HERO_COMPACT: "Hero Compact",
    VariantType.STANDARD: "Standard Frame",
    VariantType.DETAIL_FOCUS: "Detail Focus",
    VariantType.DYNAMIC_ANGLE: "Dynamic Angle",
    VariantType.WARM_MINIMAL: "Warm Minimal",
}


def _detect_dominant_background_color(img: Image.Image) -> Tuple[int, int, int]:
    """Detect the dominant background color by sampling edges.
    
    Returns RGB tuple for padding/fill operations.
    """
    w, h = img.size
    edge_pixels = []
    
    # Sample from edges (top, bottom, left, right)
    for x in range(0, w, max(1, w // 20)):
        edge_pixels.append(img.getpixel((x, 0)))
        edge_pixels.append(img.getpixel((x, h - 1)))
    for y in range(0, h, max(1, h // 20)):
        edge_pixels.append(img.getpixel((0, y)))
        edge_pixels.append(img.getpixel((w - 1, y)))
    
    # Average the edge pixels
    if not edge_pixels:
        return (255, 255, 255)  # Default to white
    
    # Handle both RGB and RGBA
    r_sum = sum(p[0] for p in edge_pixels)
    g_sum = sum(p[1] for p in edge_pixels)
    b_sum = sum(p[2] for p in edge_pixels)
    n = len(edge_pixels)
    
    return (r_sum // n, g_sum // n, b_sum // n)


def zoom_out(img: Image.Image, factor: float = 0.85, pad_color: Tuple[int, int, int] = None) -> Image.Image:
    """Zoom out (shrink product) to maximize whitespace for shipping optimization.
    
    Args:
        img: Source PIL Image
        factor: Scale factor (0.85 = 85% of original, more whitespace)
        pad_color: RGB tuple for padding, or None to auto-detect
    
    Returns:
        New image with product scaled down and centered with padding.
    """
    w, h = img.size
    
    # Auto-detect background color if not provided
    if pad_color is None:
        pad_color = _detect_dominant_background_color(img)
    
    # Calculate new dimensions
    new_w = int(w * factor)
    new_h = int(h * factor)
    
    # Resize the image (shrink)
    resized = img.resize((new_w, new_h), resample=Image.Resampling.LANCZOS)
    
    # Create new canvas with padding color
    result = Image.new("RGB", (w, h), pad_color)
    
    # Center the resized image
    paste_x = (w - new_w) // 2
    paste_y = (h - new_h) // 2
    result.paste(resized, (paste_x, paste_y))
    
    return result


def zoom_in_safe(img: Image.Image, factor: float = 1.10, max_product_area: float = 0.70) -> Image.Image:
    """Zoom in (crop center) to show detail while keeping edge safety margin.
    
    Args:
        img: Source PIL Image
        factor: Zoom factor (1.10 = 110% zoom, center crop)
        max_product_area: Not used currently, kept for API compatibility
    
    Returns:
        Center-cropped and resized image.
    """
    w, h = img.size
    
    # Calculate crop dimensions (smaller than original to simulate zoom)
    crop_w = int(w / factor)
    crop_h = int(h / factor)
    
    # Center crop coordinates
    left = (w - crop_w) // 2
    top = (h - crop_h) // 2
    right = left + crop_w
    bottom = top + crop_h
    
    # Crop and resize back to original dimensions
    cropped = img.crop((left, top, right, bottom))
    return cropped.resize((w, h), resample=Image.Resampling.LANCZOS)


def micro_rotate(img: Image.Image, angle: float = 3.0) -> Image.Image:
    """Apply subtle rotation for dynamic visual interest.
    
    Args:
        img: Source PIL Image
        angle: Rotation angle in degrees (positive = counter-clockwise)
    
    Returns:
        Rotated image with background fill.
    """
    # Detect background color for fill
    bg_color = _detect_dominant_background_color(img)
    
    # Rotate with expand=False to keep dimensions, fill gaps with background color
    rotated = img.rotate(
        angle, 
        resample=Image.Resampling.BICUBIC,
        expand=False,
        fillcolor=bg_color
    )
    
    return rotated


def adjust_background_tone(img: Image.Image, warmth: int = 10) -> Image.Image:
    """Apply warm tone shift and contrast boost for premium minimal look.
    
    Args:
        img: Source PIL Image
        warmth: Warmth adjustment (positive = warmer, negative = cooler)
    
    Returns:
        Color-adjusted image.
    """
    # Convert to RGB if needed
    if img.mode != "RGB":
        img = img.convert("RGB")
    
    # Boost contrast slightly
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.08)  # 8% contrast boost
    
    # Apply warmth via color channel adjustment
    if warmth != 0:
        r, g, b = img.split()
        
        # Warm = boost red/yellow, reduce blue
        if warmth > 0:
            # Subtle warm shift
            r = r.point(lambda x: min(255, x + warmth // 2))
            b = b.point(lambda x: max(0, x - warmth // 3))
        else:
            # Cool shift
            r = r.point(lambda x: max(0, x + warmth // 2))
            b = b.point(lambda x: min(255, x - warmth // 3))
        
        img = Image.merge("RGB", (r, g, b))
    
    # Slight saturation boost
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.05)  # 5% saturation boost
    
    return img


def generate_shipping_variants(tile_img: Image.Image, tile_index: int = 0) -> Generator[Tuple[Image.Image, VariantInfo], None, None]:
    """Generate 5 shipping-optimized variants for a single base tile.
    
    Args:
        tile_img: Source 512x512 (or similar) PIL Image from grid
        tile_index: 0-5, which tile this is from
    
    Yields:
        Tuple of (variant_image, variant_info) for each of the 5 variants.
    """
    tile_name = TILE_NAMES[tile_index] if tile_index < len(TILE_NAMES) else f"Tile {tile_index + 1}"
    
    # Ensure RGB mode
    if tile_img.mode != "RGB":
        tile_img = tile_img.convert("RGB")
    
    variants = [
        (VariantType.HERO_COMPACT, lambda img: zoom_out(img, factor=0.85)),
        (VariantType.STANDARD, lambda img: img.copy()),  # Original unchanged
        (VariantType.DETAIL_FOCUS, lambda img: zoom_in_safe(img, factor=1.10)),
        (VariantType.DYNAMIC_ANGLE, lambda img: micro_rotate(img, angle=3.0)),
        (VariantType.WARM_MINIMAL, lambda img: adjust_background_tone(img, warmth=10)),
    ]
    
    for variant_idx, (variant_type, transform_fn) in enumerate(variants):
        try:
            variant_img = transform_fn(tile_img)
            info = VariantInfo(
                tile_index=tile_index,
                variant_type=variant_type,
                variant_index=variant_idx,
                global_index=tile_index * 5 + variant_idx,
                tile_name=tile_name,
                variant_label=VARIANT_LABELS[variant_type],
            )
            yield (variant_img, info)
        except Exception as e:
            logger.warning(f"Failed to generate variant {variant_type} for tile {tile_index}: {e}")
            # Skip failed variants rather than failing entire pipeline
            continue


def generate_all_shipping_variants(grid_image_bytes: bytes, tile_px: int = 512) -> Generator[Tuple[bytes, VariantInfo], None, None]:
    """Generate all 30 shipping-optimized variants from a 1024x1536 grid image.
    
    This is a generator that yields variants one at a time for streaming.
    
    Args:
        grid_image_bytes: PNG/JPEG bytes of the 1024x1536 grid
        tile_px: Expected tile size (512px for standard grid)
    
    Yields:
        Tuple of (jpeg_bytes, variant_info) for each variant.
    """
    img = Image.open(io.BytesIO(grid_image_bytes)).convert("RGB")
    
    # Resize to expected dimensions if needed
    if img.size != (1024, 1536):
        img = img.resize((1024, 1536), resample=Image.Resampling.LANCZOS)
    
    cols, rows = 2, 3
    tile_w = img.size[0] // cols
    tile_h = img.size[1] // rows
    
    # Process each tile
    for tile_idx in range(cols * rows):
        row = tile_idx // cols
        col = tile_idx % cols
        x0 = col * tile_w
        y0 = row * tile_h
        
        tile = img.crop((x0, y0, x0 + tile_w, y0 + tile_h)).convert("RGB")
        
        # Generate 5 variants for this tile
        for variant_img, info in generate_shipping_variants(tile, tile_idx):
            # Encode as JPEG
            buf = io.BytesIO()
            variant_img.save(buf, format="JPEG", quality=92, optimize=True)
            yield (buf.getvalue(), info)


def encode_variant_jpeg(
    img: Image.Image,
    output_size: int = 1200,
    target_kb_range: Tuple[int, int] = (150, 300),
) -> bytes:
    """Encode a variant image to JPEG with size optimization.
    
    Args:
        img: Source PIL Image
        output_size: Target output dimension (square)
        target_kb_range: Target file size range in KB
    
    Returns:
        JPEG bytes optimized for size.
    """
    # Resize to output dimension
    resized = img.resize((output_size, output_size), resample=Image.Resampling.LANCZOS)
    
    min_bytes = target_kb_range[0] * 1024
    max_bytes = target_kb_range[1] * 1024
    
    # Try different quality levels to hit target size
    for quality in (95, 93, 92, 90, 88, 86, 84, 82, 80):
        buf = io.BytesIO()
        resized.save(buf, format="JPEG", quality=quality, optimize=True, progressive=True)
        data = buf.getvalue()
        
        if min_bytes <= len(data) <= max_bytes:
            return data
        if len(data) < min_bytes:
            return data  # Can't make it bigger, return best we have
    
    # Fallback
    buf = io.BytesIO()
    resized.save(buf, format="JPEG", quality=85, optimize=True)
    return buf.getvalue()
