import base64
import io
import logging
import os
from typing import Any, Dict, Optional, Tuple

import httpx
from PIL import Image

logger = logging.getLogger(__name__)


class GptImage15Optimizer:
    """Azure OpenAI gpt-image-1.5-based optimizer.

    Generates a single 1024x1536 2x3 grid image from the input image using
    the Images Edits endpoint.
    """

    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: Optional[str] = None,
        images_edits_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        from app.config import get_settings

        settings = get_settings()
        self.endpoint = (
            endpoint
            or getattr(settings, "AZURE_OPENAI_ENDPOINT", None)
            or os.getenv("AZURE_OPENAI_ENDPOINT")
        )
        if self.endpoint and not self.endpoint.startswith(("http://", "https://")):
            self.endpoint = "https://" + self.endpoint

        self.api_key = (
            api_key
            or getattr(settings, "AZURE_OPENAI_API_KEY", None)
            or os.getenv("AZURE_OPENAI_API_KEY")
        )
        self.deployment = (
            deployment
            or getattr(settings, "AZURE_OPENAI_DEPLOYMENT_NAME", None)
            or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            or "gpt-image-1.5"
        )
        self.images_edits_url = (
            images_edits_url
            or getattr(settings, "AZURE_OPENAI_IMAGES_EDITS_URL", None)
            or os.getenv("AZURE_OPENAI_IMAGES_EDITS_URL")
        )
        self.api_version = (
            api_version
            or getattr(settings, "OPENAI_API_VERSION", None)
            or os.getenv("OPENAI_API_VERSION")
            or "2024-02-01"
        )
        self.timeout = timeout

    def _build_images_edits_url(self) -> str:
        """Build the Azure Images Edits URL.

        Supports overriding via AZURE_OPENAI_IMAGES_EDITS_URL (or ctor arg) for cases
        where the base endpoint differs (e.g., services.ai.azure.com vs openai.azure.com).
        The override may include {deployment} and/or {api_version} placeholders.
        """
        if self.images_edits_url:
            url = self.images_edits_url
            try:
                url = url.format(deployment=self.deployment, api_version=self.api_version)
            except Exception:
                # If formatting fails (e.g., literal braces), use as-is.
                pass
            # If api-version wasn't included, append it.
            if "api-version=" not in url:
                sep = "&" if "?" in url else "?"
                url = f"{url}{sep}api-version={self.api_version}"
            return url

        return (
            self.endpoint.rstrip("/")
            + f"/openai/deployments/{self.deployment}/images/edits?api-version={self.api_version}"
        )

    def _auth_headers_for_url(self, url: str) -> Dict[str, str]:
        # Match the sample: use Api-Key header for Azure OpenAI.
        # Header names are case-insensitive, but we keep the sample's casing.
        return {"Api-Key": self.api_key}

    @staticmethod
    def _guess_image_mime_type(image_bytes: bytes) -> str:
        if image_bytes.startswith(b"\x89PNG\r\n\x1a\n"):
            return "image/png"
        if image_bytes.startswith(b"\xff\xd8"):
            return "image/jpeg"
        if image_bytes[:4] == b"RIFF" and image_bytes[8:12] == b"WEBP":
            return "image/webp"
        return "application/octet-stream"

    @staticmethod
    def _grid_prompt_2x3() -> str:
        return (
            "You are a professional e-commerce catalog generator creating premium, visually exciting product photography while keeping products SMALL in frame for lower Meesho shipping estimates.\n\n"
            "TASK:\n"
            "From the single uploaded product image, generate EXACTLY ONE 1024x1536px image containing a perfect 2x3 grid of 6 distinct photography styles.\n"
            "Each tile MUST be exactly 512x512px. No gaps, no padding, no borders, no labels. Tiles must touch edge-to-edge.\n\n"
            "GLOBAL SHIPPING & FRAMING RULES (ALL 6 TILES):\n"
            "- Main product identity 100% preserved (shape, color, texture, proportions, details, branding).\n"
            "- Product size in each tile:\n"
            "  • Preferred: product occupies about 55–65% of tile area\n"
            "  • Hard maximum: product must NEVER exceed 70% of tile area\n"
            "- Always leave clearly visible empty background around the product on all sides.\n"
            "- Product must be fully visible in each tile (do not crop off any part).\n"
            "- Backgrounds, surfaces, and any context must be GENERIC and PRODUCT-AGNOSTIC:\n"
            "  • Use neutral surfaces, gradients, soft abstract shapes, light or dark tones\n"
            "  • Do NOT add category-specific props (no furniture, no food, no books, no tools, etc.)\n"
            "  • Do NOT add people, body parts, logos, text, or watermarks.\n\n"
            "TILE STYLES (Row1: left→right = Tiles 1–2, Row2: 3–4, Row3: 5–6):\n\n"
            "1) HERO WHITE (shipping-optimized, clean)\n"
            "   - Background: pure or near-pure white, completely uncluttered.\n"
            "   - Product: centered, about 55–60% of tile, generous white padding on all sides.\n"
            "   - Lighting: soft diffused studio lighting, very subtle natural shadow under/behind product.\n"
            "   - Mood: clean, minimal, trustworthy. Ideal as first Meesho image.\n\n"
            "2) STYLED NEUTRAL CONTEXT (exciting, generic)\n"
            "   - Background: softly blurred neutral background or gentle gradient; may include very simple abstract shapes or tones that complement product color.\n"
            "   - Surface: simple, neutral, non-reflective surface (no recognizable objects).\n"
            "   - Product: placed slightly off-center for dynamic composition, about 60–65% of tile.\n"
            "   - Lighting: soft but directional, with gentle highlight and shadow for depth.\n"
            "   - Mood: visually interesting, premium, works for ANY product category.\n\n"
            "3) DRAMATIC LIGHT & DETAIL (exciting)\n"
            "   - Background: smooth gradient (e.g., light-to-medium neutral tone) or subtle vignette.\n"
            "   - Product: shown from a dynamic angle that emphasizes form and surface detail, about 60–70% of tile (still not touching edges).\n"
            "   - Lighting: stronger directional light from one side to create contrast, depth, and visible texture, with a clean soft shadow.\n"
            "   - Mood: bold, high-end, “editorial” feel without relying on any specific scene.\n\n"
            "4) SECONDARY CLEAN ANGLE / MULTI-VIEW (shipping-friendly)\n"
            "   - Background: white or very light neutral, uncluttered.\n"
            "   - Product: shown from a different clear angle than Tile 1 (e.g., side or 3/4), centered, about 55–60% of tile.\n"
            "   - Optionally, a VERY simple neutral geometric element (like a plain block or low plinth) may be used under or behind the product purely as a styling shape, not as recognizable packaging.\n"
            "   - Lighting: even studio lighting, minimal shadows.\n"
            "   - Mood: informative catalog angle, still small in frame for shipping.\n\n"
            "5) DARK LUXURY EDITORIAL (exciting)\n"
            "   - Background: dark neutral gradient (charcoal to black) or deep rich tone; no patterns.\n"
            "   - Product: centered or slightly off-center, about 60–65% of tile, clearly separated from background.\n"
            "   - Lighting: dramatic spotlight or rim lighting that creates a halo or strong edge light, with soft falloff into darkness.\n"
            "   - Mood: luxury, cinematic, high-contrast while keeping the product clearly readable.\n\n"
            "6) FLOATING / LIGHTNESS SHOT (exciting)\n"
            "   - Background: light neutral gradient or very soft abstract backdrop.\n"
            "   - Product: appears lightly elevated above surface or subtly “floating”, with a soft, realistic drop shadow below to maintain realism.\n"
            "   - Product size: about 60–65% of tile, centered with ample background breathing room.\n"
            "   - Lighting: clean studio light with gentle reflections and subtle highlight.\n"
            "   - Mood: modern, dynamic, conveys lightness and quality without any category-specific context.\n\n"
            "FINAL OUTPUT:\n"
            "- One single 1024x1536px image only.\n"
            "- Perfect 2x3 grid, tiles are 512x512px each, edge-to-edge.\n"
            "- At least two tiles (Hero White and Secondary Clean Angle) must clearly show the product on very light backgrounds with generous empty space for optimal Meesho shipping estimation.\n"
            "- The remaining tiles must be visually exciting through lighting, angle, gradients, and abstract styling, while still product-agnostic and compliant with all rules above."
        )

    async def optimize_image(
        self,
        image_bytes: bytes,
        original_filename: str,
        pipeline_config: Optional[Dict[str, Any]] = None,
        actual_weight_g: Optional[float] = None,
        dimensions_cm: Optional[Tuple[float, float, float]] = None,
    ) -> Tuple[bytes, Dict[str, Any]]:
        if not self.endpoint:
            raise RuntimeError("AZURE_OPENAI_ENDPOINT is not configured")
        if not self.api_key:
            raise RuntimeError("AZURE_OPENAI_API_KEY is not configured")

        size = "1024x1536"
        quality = "medium"
        n = 1
        prompt = self._grid_prompt_2x3()

        # Best-effort input dimensions for DB fields.
        input_dims = [None, None]
        try:
            img_in = Image.open(io.BytesIO(image_bytes))
            input_dims = [int(img_in.width), int(img_in.height)]
        except Exception:
            pass

        base_metrics: Dict[str, Any] = {
            "input_size_bytes": len(image_bytes),
            "output_size_bytes": None,
            "input_dimensions": input_dims,
            "output_dimensions": None,
            "processing_time_ms": None,
            "size_reduction_percent": None,
            "cost_fields": {},
            "stage_metrics": {},
            "error": None,
            "optimizer_version": "gpt-image-1.5-edit-v1",
            "deployment": self.deployment,
            "api_version": self.api_version,
            "requested_size": size,
            "requested_quality": quality,
        }

        url = self._build_images_edits_url()
        alt_url = None
        # Some Azure configurations use cognitiveservices.azure.com for OpenAI paths.
        # If a services.ai host returns 404, retry against cognitiveservices.
        mime = self._guess_image_mime_type(image_bytes)

        # Match the provided sample:
        # - multipart form-data
        # - form fields in `data` (prompt/n/size/quality)
        # - binary file in `files` (image)
        data_full = {
            "prompt": prompt,
            "n": str(n),
            "size": size,
            "quality": quality,
        }
        data_min = {
            "prompt": prompt,
        }
        files = {
            "image": (original_filename, image_bytes, mime),
        }

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            logger.info(
                "gpt-image-1.5 edit request deployment=%s size=%s quality=%s url=%s",
                self.deployment,
                size,
                quality,
                url,
            )
            headers = self._auth_headers_for_url(url)
            resp = await client.post(url, headers=headers, data=data_full, files=files)

            if resp.status_code >= 400:
                # Retry once with the minimal curl-like form if the service rejects extra fields.
                try:
                    err_text = resp.text or ""
                except Exception:
                    err_text = ""
                if any(k in err_text.lower() for k in ["size", "quality", "n", "unrecognized", "unknown", "invalid"]):
                    logger.info("Retrying gpt-image-1.5 request with minimal multipart fields")
                    resp = await client.post(url, headers=headers, data=data_min, files=files)

            # If endpoint host is wrong, Azure often returns 404 Resource Not Found.
            if resp.status_code == 404 and alt_url:
                logger.info("Retrying gpt-image-1.5 request against alternate host: %s", alt_url)
                headers_alt = self._auth_headers_for_url(alt_url)
                resp = await client.post(alt_url, headers=headers_alt, data=data_full, files=files)
                if resp.status_code >= 400:
                    try:
                        err_text = resp.text or ""
                    except Exception:
                        err_text = ""
                    if any(k in err_text.lower() for k in ["size", "quality", "n", "unrecognized", "unknown", "invalid"]):
                        logger.info("Retrying alternate-host gpt-image-1.5 request with minimal multipart fields")
                        resp = await client.post(alt_url, headers=headers_alt, data=data_min, files=files)
                # Track which URL actually got used.
                url = alt_url

        try:
            body_snippet = (resp.text[:1000] + "...") if resp.text and len(resp.text) > 1000 else resp.text
        except Exception:
            body_snippet = f"<binary {len(resp.content)} bytes>"

        logger.info("gpt-image-1.5 response status=%s body_snippet=%s", resp.status_code, body_snippet)

        if resp.status_code >= 400:
            try:
                err_json = resp.json()
            except Exception:
                err_json = None
            base_metrics["error"] = "gpt_image_request_failed"
            base_metrics["stage_metrics"] = {
                "image_error": {
                    "status_code": resp.status_code,
                    "body": err_json or body_snippet,
                    "target_url": url,
                }
            }
            if alt_url:
                base_metrics["stage_metrics"]["image_error"]["alternate_url"] = alt_url
            return image_bytes, base_metrics

        try:
            data_json = resp.json()
        except Exception:
            # Some deployments may return raw bytes; avoid crashing the API.
            base_metrics["output_size_bytes"] = len(resp.content)
            base_metrics["error"] = "non_json_response"
            base_metrics["stage_metrics"] = {"note": "non_json_response"}
            return resp.content, base_metrics
        b64_img = None
        if isinstance(data_json, dict) and isinstance(data_json.get("data"), list) and data_json["data"]:
            b64_img = data_json["data"][0].get("b64_json")
        if not b64_img:
            base_metrics["output_size_bytes"] = len(resp.content)
            base_metrics["error"] = "no_b64_json_in_response"
            base_metrics["stage_metrics"] = {"note": "no_b64_json_in_response"}
            return resp.content, base_metrics

        raw = base64.b64decode(b64_img)

        # Normalize to PNG bytes (as requested output format), but ensure it decodes.
        try:
            img = Image.open(io.BytesIO(raw)).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="PNG")
            out_bytes = buf.getvalue()
        except Exception:
            out_bytes = raw

        base_metrics["output_size_bytes"] = len(out_bytes)
        base_metrics["output_dimensions"] = [1024, 1536]
        return out_bytes, base_metrics
