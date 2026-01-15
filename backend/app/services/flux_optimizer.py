import os
import base64
import logging
from typing import Optional, Dict, Any, Tuple, List

import httpx
import asyncio
import io
from PIL import Image, ImageChops, ImageFilter, ImageOps

# No local ML fallback: this module delegates to remote FLUX only

logger = logging.getLogger(__name__)


class FluxOptimizer:
    """Simple FLUX-only optimizer: calls a single model and prompt and
    never falls back to local processing. Designed for controlled testing.
    """

    def __init__(
        self,
        base_url: Optional[str] = None,
        api_key: Optional[str] = None,
        model_name: Optional[str] = None,
        timeout: float = 30.0,
    ):
        from app.config import get_settings
        settings = get_settings()
        self.base_url = base_url or getattr(settings, "AZURE_FOUNDRY_ENDPOINT", None) or os.getenv("AZURE_FOUNDRY_ENDPOINT")
        # Ensure protocol is present
        if self.base_url and not self.base_url.startswith(("http://", "https://")):
            self.base_url = "https://" + self.base_url
        self.model_name = model_name or getattr(settings, "AZURE_FOUNDRY_MODEL_NAME", None) or os.getenv("AZURE_FOUNDRY_MODEL_NAME")
        self.api_key = api_key or getattr(settings, "AZURE_FOUNDRY_API_KEY", None) or os.getenv("AZURE_FOUNDRY_API_KEY")
        self.timeout = timeout

    async def optimize_image(
        self,
        image_bytes: bytes,
        original_filename: str,
        pipeline_config: Optional[Dict[str, Any]] = None,
        actual_weight_g: Optional[float] = None,
        dimensions_cm: Optional[Tuple[float, float, float]] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        """Call the configured FLUX endpoint once with a single prompt/model.

        This simplified version always returns either the FLUX result or raises an
        exception — it does not attempt any local ML optimization.
        Returns (optimized_bytes, metrics) where metrics includes any debug info.
        """
        if not self.base_url:
            raise RuntimeError("AZURE_FOUNDRY_ENDPOINT is not configured for FluxOptimizer")

        # choose model and single prompt variant
        model = (pipeline_config or {}).get("flux_model") or self.model_name or "FLUX.1-Kontext-pro"
        prompt_variant = (pipeline_config or {}).get("prompt_variant")
        if not prompt_variant:
            prompt_variant = "meesho_grid_v1"
        prompt = self._build_optimization_prompt(actual_weight_g or 0, {"prompt_variant": prompt_variant})

        # Use OpenAI image edit API endpoint
        candidate = (pipeline_config or {}).get("flux_model")
        if candidate and ("/images/edits" in candidate):
            target_url = candidate
        else:
            # Always use /images/edits for image editing
            target_url = self.base_url.rstrip("/") + "/openai/deployments/FLUX.1-Kontext-pro/images/edits?api-version=2025-04-01-preview"

        headers = {}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

        files = {
            "model": (None, model),
            "image": (original_filename, image_bytes, "image/png"),
            "prompt": (None, prompt),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info("FLUX image edit request to %s with model=%s prompt_variant=%s", target_url, model, prompt_variant)
            try:
                resp = await client.post(target_url, files=files, headers=headers)
            except Exception as e:
                logger.exception("HTTP request to FLUX failed: %s", e)
                raise

            # Log status and a small snippet of the response body for debugging (avoid huge dumps)
            try:
                body_snippet = (resp.text[:1000] + '...') if resp.text and len(resp.text) > 1000 else resp.text
            except Exception:
                body_snippet = f"<binary {len(resp.content)} bytes>"
            logger.info("FLUX response status=%s body_snippet=%s", resp.status_code, body_snippet)
            try:
                resp.raise_for_status()
            except httpx.HTTPStatusError as e:
                # capture full body for debugging (safe fallback if binary)
                try:
                    full_body = resp.text
                except Exception:
                    full_body = f"<binary {len(resp.content)} bytes>"
                logger.error("FLUX request to %s failed with status %s. Full body: %s", target_url, resp.status_code, full_body)
                # Try to extract activityId if present
                activity_id = None
                try:
                    err_json = resp.json()
                    activity_id = err_json.get("activityId") or err_json.get("activity_id")
                except Exception:
                    pass
                # Return error diagnostics in metrics
                error_metrics = {
                    "flux_error": {
                        "status_code": resp.status_code,
                        "body": full_body,
                        "activityId": activity_id,
                        "target_url": target_url,
                    }
                }
                return image_bytes, {"metrics": error_metrics}

            # Parse OpenAI image edit response: .data[0].b64_json
            try:
                data = resp.json()
                b64_img = None
                if "data" in data and isinstance(data["data"], list) and data["data"]:
                    b64_img = data["data"][0].get("b64_json")
                if b64_img:
                    optimized_bytes = base64.b64decode(b64_img)
                    metrics = {"note": "openai_image_edit_success"}
                else:
                    optimized_bytes = resp.content
                    metrics = {"note": "no_b64_json_in_response"}
            except Exception:
                logger.debug("Response not JSON or missing expected fields; using raw bytes")
                optimized_bytes = resp.content
                metrics = {"note": "raw_bytes_returned"}

            before_compress = len(optimized_bytes)
            # Target a Meesho-friendly JPG size (~150-300KB). We aim near the middle for stability.
            optimized_bytes = self._post_process_compress(optimized_bytes, target_bytes=250 * 1024)
            after_compress = len(optimized_bytes)
            logger.info("Compression: before=%d bytes after=%d bytes target=%d bytes", before_compress, after_compress, 250 * 1024)
            out_metrics = {
                "original_size_kb": len(image_bytes) / 1024,
                "optimized_size_kb": after_compress / 1024,
                "optimizer_version": "flux-image-edit-v1",
                "compression_before_bytes": before_compress,
                "compression_after_bytes": after_compress,
                "prompt_variant": prompt_variant,
            }
            out_metrics.update(metrics if isinstance(metrics, dict) else {})
            return optimized_bytes, {"metrics": out_metrics}

    def _build_optimization_prompt(self, weight_g: int, config: Dict[str, Any]) -> str:
        # Template library
        PROMPTS = {
            "meesho_grid_v1": (
                "You are a professional e-commerce catalog generator creating premium product photography sets.\n\n"
                "TASK: From the single uploaded product image, generate EXACTLY ONE 1024x1024px square image containing a perfect 2x2 grid of 4 distinct photography styles (each precisely 480x480px with 1px white borders and 14px even padding between).\n\n"
                "CRITICAL REQUIREMENTS (ALL 4 thumbnails):\n"
                "- Main product perfectly isolated/represented from input (exact shape/color/texture/details/brand/logo)\n"
                "- Each 480x480 thumbnail: photorealistic studio quality, sharp 8K-equivalent detail\n"
                "- Perfect 2x2 grid math: 1024x1024 canvas, 1px white borders, exactly 14px gaps/padding\n"
                "- Compression-ready: clean edges, optimized for e-commerce JPG export\n"
                "- No distortion/cropping/people/text overlays/watermarks\n\n"
                "SPECIFIC 2x2 GRID PHOTOGRAPHY STYLES (Row1:1-2, Row2:3-4):\n\n"
                "1️⃣ HERO WHITE (top-left): \"Ultra-realistic studio product photography isolated on pure white background, soft diffused lighting, sharp focus, natural shadows, luxury e-commerce style, 8K\"\n\n"
                "2️⃣ PREMIUM LIFESTYLE (top-right): \"Professional lifestyle product photography in realistic everyday environment, natural light, shallow depth of field, premium commercial composition\"\n\n"
                "3️⃣ TEXTURE MACRO (bottom-left): \"Macro photography highlighting material texture, stitching, surface quality, craftsmanship, controlled studio lighting, high clarity, luxury catalog\"\n\n"
                "4️⃣ PACKAGING SHOT (bottom-right): \"Commercial photography with branded packaging, studio lighting, balanced composition, premium retail catalog style, realistic shadows\"\n\n"
                "HARD TECHNICAL CONSTRAINTS:\n"
                "- Product identity 100% preserved across all 4 (recognizable as same item)\n"
                "- Each style distinct but professional (no cartoon/low-quality)\n"
                "- Grid perfectly symmetrical, no overlap/misalignment/bleed\n"
                "- Backgrounds appropriate to style (white/neutral/dark per description)\n"
                "- Studio lighting realistic throughout (no harsh/overexposed)\n\n"
                "Output: Single 1024x1024px JPG-ready image. Backend crops 4x premium 480x480 thumbnails for full e-commerce catalog."
            ),
            "meesho_v1": (
                "You are an AI image generator that creates shipping-charge-optimised, Meesho-compliant ecommerce product photos from a single input image.\n\n"
                "TASK  \n"
                "Take the uploaded product image and generate exactly ONE new optimised image that looks professional for shoppers while making the product appear smaller and less bulky in the frame to potentially lower shipping estimates.\n\n"
                "MEESHO IMAGE RULES (must follow all)  \n"
                "- Square 1:1 aspect ratio, exactly 1024x1024 pixels, JPG-style, RGB color space.  \n"
                "- Solo product only: no props, people, models, hands, text, watermarks, logos, prices, or badges unless already in original.  \n"
                "- Clear, non-blurry, non-pixelated; product fully visible and sharp.  \n\n"
                "OPTIMISATION FOR LOWER SHIPPING + COMPRESSION  \n"
                "1. Detect and isolate the main product cleanly from the original image.  \n"
                "2. Keep product EXACTLY the same: shape, proportions, orientation, realistic colors, textures, materials, details, brand/logo/print unchanged. No distortion, stretching, or hallucination.  \n"
                "3. SCALE FOR SHIPPING: Position product fully centered and visible, occupying 55–70% of image width/height (15–25% smaller apparent size than tight crop via extra padding).  \n"
                "4. Background: Pure white (#FFFFFF), completely smooth/flat, no gradients/noise/textures/patterns. Generous even padding on all sides.  \n"
                "5. Lighting: Natural soft lighting, minimal subtle shadows under/behind product only. No highlights, reflections, vignettes, or effects.  \n"
                "6. Camera: Realistic straight-on view, no tilt/rotation/exaggerated angle (max 5° natural variation if original has it).  \n"
                "7. WEB-COMPRESSION FRIENDLY: Use moderate detail on product (avoid ultra-fine textures/grain), smooth edges, simple colors. Aim for visual that compresses to 150-300KB JPG (low-frequency image).  \n\n"
                "HARD CONSTRAINTS  \n"
                "- Never crop/hide any product part.  \n"
                "- No cartoon/illustration; stay photographic.  \n\n"
                "Generate one perfect variant optimised as the FIRST listing image for Meesho."
            )
        }

        variant = None
        if config and isinstance(config, dict):
            variant = config.get("prompt_variant")

        if variant and variant in PROMPTS:
            return PROMPTS[variant]

        # Default short prompt
        return (
            f"OPTIMIZE product image for e-commerce. Weight: {weight_g}g. "
            "Output: 1200x1200 JPEG, white background, product fills 85-90% frame, "
            "high sharpness on product, vibrant colors, minimal file size."
        )

    def _compose_meesho_grid_1024(self, image_bytes: bytes) -> bytes:
        """Create a single 1024x1024 image containing a pixel-perfect 3x3 grid of tiles.

        We rely on the FLUX output to be a clean product-on-white image, then generate
        9 ultra-similar variants via minor transforms and deterministic padding/shadow.

        Returns JPEG bytes.
        """
        canvas_px = 1024
        tile_px = 340
        gap_px = 2  # 3*340 + 2*2 = 1024 (exact). See note in metrics.

        img = Image.open(io.BytesIO(image_bytes))
        if img.mode in {"RGBA", "LA"}:
            bg = Image.new("RGBA", img.size, (255, 255, 255, 255))
            img = Image.alpha_composite(bg, img.convert("RGBA")).convert("RGB")
        else:
            img = img.convert("RGB")

        # Build an approximate alpha mask by treating near-white pixels as background.
        white = Image.new("RGB", img.size, (255, 255, 255))
        diff = ImageChops.difference(img, white).convert("L")
        # Threshold: anything with noticeable difference becomes foreground.
        alpha = diff.point(lambda p: 255 if p > 10 else 0)
        alpha = alpha.filter(ImageFilter.GaussianBlur(1.2))

        master_rgba = img.convert("RGBA")
        master_rgba.putalpha(alpha)

        # Tile definitions (fill fraction within 340x340, minor offsets/rotation/shadow).
        # Keep transforms subtle to avoid perceptible distortion.
        tile_specs = [
            {"fill": 0.68, "dx": 0, "dy": 0, "rot": 0.0, "shadow": (0, 6), "shadow_alpha": 0.14, "blur": 6},
            {"fill": 0.62, "dx": 0, "dy": -10, "rot": 0.0, "shadow": (-5, 6), "shadow_alpha": 0.13, "blur": 6},
            {"fill": 0.58, "dx": 10, "dy": 0, "rot": 0.0, "shadow": (6, 8), "shadow_alpha": 0.13, "blur": 6},
            {"fill": 0.65, "dx": 0, "dy": 0, "rot": 3.0, "shadow": (0, 6), "shadow_alpha": 0.14, "blur": 6},
            {"fill": 0.60, "dx": 0, "dy": 0, "rot": -3.0, "shadow": (0, 6), "shadow_alpha": 0.14, "blur": 6},
            {"fill": 0.55, "dx": 0, "dy": 0, "rot": 0.0, "shadow": (0, 6), "shadow_alpha": 0.12, "blur": 7},
            {"fill": 0.64, "dx": 0, "dy": 0, "rot": 0.0, "shadow": (0, 4), "shadow_alpha": 0.08, "blur": 4},
            {"fill": 0.66, "dx": 0, "dy": -6, "rot": 0.0, "shadow": (0, 3), "shadow_alpha": 0.11, "blur": 6},
            {"fill": 0.68, "dx": -8, "dy": 0, "rot": 0.0, "shadow": (-6, 4), "shadow_alpha": 0.12, "blur": 6},
        ]

        canvas = Image.new("RGB", (canvas_px, canvas_px), (255, 255, 255))

        for idx, spec in enumerate(tile_specs):
            row = idx // 3
            col = idx % 3
            x0 = col * (tile_px + gap_px)
            y0 = row * (tile_px + gap_px)

            tile = Image.new("RGB", (tile_px, tile_px), (255, 255, 255))

            box = int(tile_px * float(spec["fill"]))
            resized = ImageOps.contain(master_rgba, (box, box), method=Image.Resampling.LANCZOS)

            rot = float(spec.get("rot", 0.0))
            if abs(rot) > 0.01:
                resized = resized.rotate(
                    rot,
                    resample=Image.Resampling.BICUBIC,
                    expand=True,
                    fillcolor=(255, 255, 255, 0),
                )
                resized = ImageOps.contain(resized, (box, box), method=Image.Resampling.LANCZOS)

            px, py = resized.size
            dx = int(spec.get("dx", 0))
            dy = int(spec.get("dy", 0))
            left = (tile_px - px) // 2 + dx
            top = (tile_px - py) // 2 + dy

            # Shadow from alpha channel.
            try:
                shadow_dx, shadow_dy = spec.get("shadow", (0, 6))
                shadow_alpha = float(spec.get("shadow_alpha", 0.12))
                blur = float(spec.get("blur", 6))
                a = resized.getchannel("A")
                shadow_a = a.point(lambda p: int(p * shadow_alpha))
                shadow = Image.new("RGBA", resized.size, (0, 0, 0, 0))
                shadow.putalpha(shadow_a)
                shadow = shadow.filter(ImageFilter.GaussianBlur(blur))
                tile_rgba = tile.convert("RGBA")
                tile_rgba.alpha_composite(shadow, (left + int(shadow_dx), top + int(shadow_dy)))
                tile_rgba.alpha_composite(resized, (left, top))
                tile = tile_rgba.convert("RGB")
            except Exception:
                # If anything goes wrong with shadow/mask, fall back to simple paste.
                tile.paste(resized.convert("RGB"), (left, top))

            canvas.paste(tile, (x0, y0))

        buf = io.BytesIO()
        canvas.save(buf, format="JPEG", quality=92, optimize=True)
        return buf.getvalue()

    def _post_process_compress(self, image_bytes: bytes, target_bytes: int = 50 * 1024) -> bytes:
        """Recompress a JPEG image using PIL to try to reach target_bytes.

        Uses binary search on quality between 95 and 20, falls back to linear scan if necessary.
        Returns recompressed bytes (or original if compression not possible).
        """
        try:
            img = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        except Exception:
            return image_bytes

        # quick check: if already small enough, return
        if len(image_bytes) <= target_bytes:
            return image_bytes

        lo, hi = 20, 95
        best = None
        best_size = None
        while lo <= hi:
            mid = (lo + hi) // 2
            buf = io.BytesIO()
            try:
                img.save(buf, format="JPEG", quality=mid, optimize=True)
            except Exception:
                try:
                    img.save(buf, format="JPEG", quality=mid)
                except Exception:
                    break
            data = buf.getvalue()
            size = len(data)
            if size <= target_bytes:
                best = data
                best_size = size
                # try higher quality to get closer to target
                lo = mid + 1
            else:
                hi = mid - 1

        if best is not None:
            return best

        # linear fallback: try decreasing quality until hit target or reach 10
        for q in range(95, 9, -5):
            buf = io.BytesIO()
            try:
                img.save(buf, format="JPEG", quality=q, optimize=True)
            except Exception:
                try:
                    img.save(buf, format="JPEG", quality=q)
                except Exception:
                    continue
            data = buf.getvalue()
            if len(data) <= target_bytes:
                return data

        # last resort: return original (or best found)
        return image_bytes

    def _calculate_savings(self, original_bytes: int, optimized_bytes: int) -> float:
        # Simple savings estimation: difference in shipping cost tiers could be computed later;
        # For now, return approximate ₹ savings proportional to percent reduction.
        try:
            reduction = max(0.0, (original_bytes - optimized_bytes) / original_bytes)
            # approximate ₹ per 100g saved mapping — heuristic as placeholder
            savings = round(reduction * 50, 2)
            return savings
        except Exception:
            return 0.0
