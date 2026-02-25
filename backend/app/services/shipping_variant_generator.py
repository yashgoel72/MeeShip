"""Shipping-optimized variant generator.

Generates 5 purposeful variants per base tile from the GPT-generated grid,
each designed to help sellers understand how visual size impacts perceived weight/shipping cost.
"""

import io
import logging
import random
from dataclasses import dataclass
from enum import Enum
from typing import Generator, List, Tuple

from PIL import Image, ImageDraw, ImageEnhance, ImageFilter, ImageFont

logger = logging.getLogger(__name__)


class VariantType(str, Enum):
    """Types of shipping-optimized variants."""
    HERO_COMPACT = "hero_compact"      # 20% zoom-out, max whitespace
    STANDARD = "standard"              # Original framing from model
    DETAIL_FOCUS = "detail_focus"      # Cool tone variant
    WARM_MINIMAL = "warm_minimal"      # Warm tone variant
    STICKER = "sticker"                # Promotional badge overlay


@dataclass
class VariantInfo:
    """Information about a generated variant."""
    tile_index: int           # 0-3, which base tile this came from
    variant_type: VariantType # Which variant transformation
    variant_index: int        # 0-4, position within the tile's variants
    global_index: int         # 0-19, position in the full 20-variant list
    tile_name: str           # Human-readable tile name
    variant_label: str       # Human-readable variant label


# Tile names from the GPT 2x2 prompt (0-indexed)
TILE_NAMES = [
    "Hero White Front",
    "3/4 Angle",
    "Lifestyle Scene",
    "Dark Luxury",
]

VARIANT_LABELS = {
    VariantType.HERO_COMPACT: "Zoom Out",
    VariantType.STANDARD: "Standard",
    VariantType.DETAIL_FOCUS: "Cool Minimal",
    VariantType.WARM_MINIMAL: "Warm Minimal",
    VariantType.STICKER: "Sticker Badge",
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
    
    # Boost contrast noticeably
    enhancer = ImageEnhance.Contrast(img)
    img = enhancer.enhance(1.18)  # 18% contrast boost
    
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
    
# Noticeable saturation boost
    enhancer = ImageEnhance.Color(img)
    img = enhancer.enhance(1.15)  # 15% saturation boost
    
    return img


# --- Sticker / Badge overlay ---
# Elaborate e-commerce promotional badges: circular seals, starburst shapes,
# ribbon banners — matching the style used by Indian marketplace sellers.

_BADGE_CONFIGS = [
    # Each config: text, primary color, accent color, style, corner
    # Corners ONLY — never center or mid positions to avoid covering the product
    {"text": "BEST\nSELLER", "bg": (199, 144, 38), "accent": (160, 110, 20), "fg": (255, 255, 255), "style": "seal", "corner": "bottom-left"},
    {"text": "BIG\nSALE", "bg": (200, 30, 120), "accent": (255, 210, 50), "fg": (255, 255, 255), "style": "starburst", "corner": "bottom-right"},
    {"text": "LIMITED\nOFFER", "bg": (120, 50, 180), "accent": (255, 200, 50), "fg": (255, 255, 255), "style": "seal", "corner": "top-right"},
    {"text": "BEST\nQUALITY", "bg": (210, 40, 40), "accent": (255, 215, 0), "fg": (255, 255, 255), "style": "seal", "corner": "top-left"},
    {"text": "TOP\nRATED", "bg": (22, 140, 60), "accent": (255, 215, 0), "fg": (255, 255, 255), "style": "seal", "corner": "bottom-left"},
    {"text": "BEST\nCHOICE", "bg": (218, 165, 32), "accent": (22, 120, 50), "fg": (255, 255, 255), "style": "starburst", "corner": "bottom-right"},
    {"text": "PREMIUM\nPICK", "bg": (50, 50, 150), "accent": (255, 215, 0), "fg": (255, 255, 255), "style": "seal", "corner": "top-right"},
    {"text": "HOT\nDEAL", "bg": (220, 50, 30), "accent": (255, 165, 0), "fg": (255, 255, 255), "style": "starburst", "corner": "top-left"},
]


def _draw_serrated_circle(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int,
                          teeth: int, tooth_depth: int, fill: tuple, outline: tuple):
    """Draw a serrated / wavy circle (seal shape) centred at (cx, cy)."""
    import math as _math
    points = []
    for i in range(teeth * 2):
        angle = _math.pi * 2 * i / (teeth * 2) - _math.pi / 2
        r = radius if i % 2 == 0 else radius - tooth_depth
        points.append((cx + r * _math.cos(angle), cy + r * _math.sin(angle)))
    draw.polygon(points, fill=fill, outline=outline)


def _draw_starburst(draw: ImageDraw.ImageDraw, cx: int, cy: int, radius: int,
                    points_count: int, inner_ratio: float, fill: tuple, outline: tuple):
    """Draw a starburst / explosion shape centred at (cx, cy)."""
    import math as _math
    points = []
    for i in range(points_count * 2):
        angle = _math.pi * 2 * i / (points_count * 2) - _math.pi / 2
        r = radius if i % 2 == 0 else int(radius * inner_ratio)
        points.append((cx + r * _math.cos(angle), cy + r * _math.sin(angle)))
    draw.polygon(points, fill=fill, outline=outline)


def _get_font(size: int) -> ImageFont.FreeTypeFont:
    """Try to load a bold TTF font; fall back to default."""
    for path in [
        "arialbd.ttf", "arial.ttf", "Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
    ]:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            continue
    return ImageFont.load_default()


def _render_badge(badge_size: int, config: dict) -> Image.Image:
    """Render a single badge as an RGBA image.

    ``badge_size`` is the bounding-box dimension (square) of the badge.
    ``config`` is one of the ``_BADGE_CONFIGS`` dicts.
    """
    img = Image.new("RGBA", (badge_size, badge_size), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    cx = cy = badge_size // 2
    radius = badge_size // 2 - 4  # small safety margin
    bg = config["bg"]
    accent = config["accent"]
    fg = config["fg"]
    style = config["style"]
    text = config["text"]

    # --- Draw the shape ---
    if style == "seal":
        teeth = random.randint(18, 24)
        tooth_depth = max(4, radius // 8)
        # Outer serrated ring (accent colour)
        _draw_serrated_circle(draw, cx, cy, radius, teeth, tooth_depth,
                              fill=(*accent, 240), outline=(*accent, 255))
        # Inner filled circle
        inner_r = radius - tooth_depth - 2
        draw.ellipse(
            [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
            fill=(*bg, 240), outline=(*accent, 255), width=2,
        )
        # Decorative thin ring
        ring_r = inner_r - max(3, inner_r // 8)
        draw.ellipse(
            [cx - ring_r, cy - ring_r, cx + ring_r, cy + ring_r],
            outline=(*fg, 180), width=1,
        )
    elif style == "starburst":
        pts = random.randint(12, 18)
        _draw_starburst(draw, cx, cy, radius, pts, 0.65,
                        fill=(*bg, 240), outline=(*accent, 255))
        # Inner circle highlight
        inner_r = int(radius * 0.55)
        draw.ellipse(
            [cx - inner_r, cy - inner_r, cx + inner_r, cy + inner_r],
            fill=(*bg, 200), outline=(*accent, 200), width=2,
        )

    # --- Draw text ---
    lines = text.split("\n")
    # Size font to fit ~60% of badge width
    target_w = int(badge_size * 0.55)
    font_size = max(10, badge_size // (3 if len(lines) == 1 else 4))
    font = _get_font(font_size)

    # Measure and centre each line
    line_bboxes = [draw.textbbox((0, 0), line, font=font) for line in lines]
    line_heights = [bb[3] - bb[1] for bb in line_bboxes]
    line_widths = [bb[2] - bb[0] for bb in line_bboxes]
    total_text_h = sum(line_heights) + max(0, (len(lines) - 1) * 2)
    y_start = cy - total_text_h // 2

    for i, line in enumerate(lines):
        lw = line_widths[i]
        lh = line_heights[i]
        lx = cx - lw // 2
        # Subtle shadow
        draw.text((lx + 1, y_start + 1), line, fill=(0, 0, 0, 100), font=font)
        draw.text((lx, y_start), line, fill=(*fg, 255), font=font)
        y_start += lh + 2

    # Small star decorations for seals
    if style == "seal":
        star_char = "★"
        star_font = _get_font(max(8, font_size // 2))
        # Stars above and below text
        sb = draw.textbbox((0, 0), star_char, font=star_font)
        sw = sb[2] - sb[0]
        draw.text((cx - sw // 2, cy - total_text_h // 2 - (sb[3] - sb[1]) - 2),
                  star_char, fill=(*accent, 255), font=star_font)
        draw.text((cx - sw // 2, cy + total_text_h // 2 + 2),
                  star_char, fill=(*accent, 255), font=star_font)

    return img


def apply_sticker_overlay(img: Image.Image) -> Image.Image:
    """Overlay 1–2 elaborate promotional badges on the product image.

    Renders large, colorful e-commerce style badges (circular seals, starburst
    shapes) similar to those used by Indian marketplace sellers — "Best Seller",
    "Big Sale", "Limited Offer", etc.

    Badges occupy ~20-28% of the tile width each and are placed in different
    corners so they don't cover the product centre.

    Args:
        img: Source PIL Image (RGB)

    Returns:
        New image with sticker badge(s) composited.
    """
    if img.mode != "RGB":
        img = img.convert("RGB")
    result = img.copy()

    w, h = result.size

    # Pick 1 or 2 badges (never the same)
    num_badges = random.choice([1, 2, 2])  # bias towards 2
    chosen = random.sample(_BADGE_CONFIGS, k=min(num_badges, len(_BADGE_CONFIGS)))

    result_rgba = result.convert("RGBA")

    for cfg in chosen:
        # Smaller badges when placing 2 so they don't overwhelm the product
        if len(chosen) == 1:
            badge_size = random.randint(int(w * 0.22), int(w * 0.28))
        else:
            badge_size = random.randint(int(w * 0.15), int(w * 0.20))
        badge_img = _render_badge(badge_size, cfg)

        # Slight random rotation for dynamism
        angle = random.uniform(-15, 15)
        badge_rot = badge_img.rotate(angle, expand=True, resample=Image.Resampling.BICUBIC)

        # Position in strict corners only — never near center
        margin = int(w * 0.03)
        bw, bh = badge_rot.size
        corner = cfg["corner"]

        if corner == "top-left":
            px, py = margin, margin
        elif corner == "top-right":
            px, py = w - bw - margin, margin
        elif corner == "bottom-left":
            px, py = margin, h - bh - margin
        else:  # bottom-right (default)
            px, py = w - bw - margin, h - bh - margin

        result_rgba.paste(badge_rot, (px, py), badge_rot)

    return result_rgba.convert("RGB")


def generate_shipping_variants(tile_img: Image.Image, tile_index: int = 0) -> Generator[Tuple[Image.Image, VariantInfo], None, None]:
    """Generate 5 shipping-optimized variants for a single base tile.
    
    Args:
        tile_img: Source 512x512 (or similar) PIL Image from grid
        tile_index: 0-3, which tile this is from
    
    Yields:
        Tuple of (variant_image, variant_info) for each of the 5 variants.
    """
    tile_name = TILE_NAMES[tile_index] if tile_index < len(TILE_NAMES) else f"Tile {tile_index + 1}"
    
    # Ensure RGB mode
    if tile_img.mode != "RGB":
        tile_img = tile_img.convert("RGB")
    
    # All 5 variants for each tile: Standard, Cool, Warm, Zoom Out, Sticker
    variants = [
        (VariantType.STANDARD, lambda img: img.copy()),  # Original unchanged
        (VariantType.DETAIL_FOCUS, lambda img: adjust_background_tone(img, warmth=-20)),  # Cool tone
        (VariantType.WARM_MINIMAL, lambda img: adjust_background_tone(img, warmth=25)),  # Warm tone
        (VariantType.HERO_COMPACT, lambda img: zoom_out(img, factor=0.80)),  # 20% zoomed out
        (VariantType.STICKER, lambda img: apply_sticker_overlay(img)),  # Promotional badge
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
    """Generate all 20 shipping-optimized variants from a 1024x1024 grid image.
    
    This is a generator that yields variants one at a time for streaming.
    
    Args:
        grid_image_bytes: PNG/JPEG bytes of the 1024x1024 grid
        tile_px: Expected tile size (512px for standard grid)
    
    Yields:
        Tuple of (jpeg_bytes, variant_info) for each variant.
    """
    img = Image.open(io.BytesIO(grid_image_bytes)).convert("RGB")
    
    # Resize to expected dimensions if needed
    if img.size != (1024, 1024):
        img = img.resize((1024, 1024), resample=Image.Resampling.LANCZOS)
    
    cols, rows = 2, 2
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
    target_kb_range: Tuple[int, int] = (100, 200),
) -> bytes:
    """Encode a variant image to JPEG with size optimization.
    
    Args:
        img: Source PIL Image
        output_size: Target output dimension (square) - 1200px for high quality
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
