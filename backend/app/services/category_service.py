"""
Meesho Category Service

Parses meesho_subcategory_ids.txt once at startup and serves a flat list of
sub-sub-categories with breadcrumb paths for the frontend category picker.
"""

import json
import logging
from pathlib import Path
from typing import List, Optional
from pydantic import BaseModel

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Schema
# ---------------------------------------------------------------------------

class CategoryItem(BaseModel):
    """A single selectable category (sub-sub-category) with breadcrumb."""
    id: int
    name: str
    breadcrumb: str  # e.g. "Men Fashion > Mens Clothing > Men Top Wear"


# ---------------------------------------------------------------------------
# Singleton cache
# ---------------------------------------------------------------------------

_cached_categories: Optional[List[CategoryItem]] = None


def _build_categories() -> List[CategoryItem]:
    """
    Parse the taxonomy JSON file and return a flat list of sub-sub-categories,
    each annotated with a breadcrumb string built from parent chain:
      super-category > category > sub-category
    """
    # Locate the taxonomy file (project root)
    taxonomy_path = Path(__file__).resolve().parents[3] / "meesho_subcategory_ids.txt"
    if not taxonomy_path.exists():
        # Fallback: look next to backend/
        taxonomy_path = Path(__file__).resolve().parents[2] / "meesho_subcategory_ids.txt"
    
    if not taxonomy_path.exists():
        logger.error(f"Taxonomy file not found at {taxonomy_path}")
        return []

    logger.info(f"Loading Meesho category taxonomy from {taxonomy_path}")
    raw = json.loads(taxonomy_path.read_text(encoding="utf-8"))
    items = raw.get("items", [])

    # Build lookup maps: id → name  for each level
    super_categories: dict[str, str] = {}   # id → name
    categories: dict[str, dict] = {}        # id → {name, parent_id}
    sub_categories: dict[str, dict] = {}    # id → {name, parent_id}

    for group in items:
        t = group.get("type")
        for entry in group.get("data", []):
            eid = entry.get("id", "")
            ename = entry.get("name", "")
            parent_id = entry.get("parent_id", "")

            if t == "super-category":
                super_categories[eid] = ename
            elif t == "category":
                categories[eid] = {"name": ename, "parent_id": parent_id}
            elif t == "sub-category":
                sub_categories[eid] = {"name": ename, "parent_id": parent_id}

    # Now build flat list from sub-sub-categories
    result: List[CategoryItem] = []

    for group in items:
        if group.get("type") != "sub-sub-category":
            continue
        for entry in group.get("data", []):
            sscat_id = entry.get("id", "")
            sscat_name = entry.get("name", "")
            sub_cat_id = entry.get("parent_id", "")

            # Resolve parent chain
            sub_cat = sub_categories.get(sub_cat_id, {})
            sub_cat_name = sub_cat.get("name", entry.get("parent_name", ""))
            cat_id = sub_cat.get("parent_id", "")

            cat = categories.get(cat_id, {})
            cat_name = cat.get("name", "")
            super_cat_id = cat.get("parent_id", "")

            super_cat_name = super_categories.get(super_cat_id, "")

            # Build breadcrumb: only non-empty parts
            parts = [p for p in [super_cat_name, cat_name, sub_cat_name] if p]
            breadcrumb = " > ".join(parts)

            try:
                result.append(CategoryItem(
                    id=int(sscat_id),
                    name=sscat_name,
                    breadcrumb=breadcrumb,
                ))
            except (ValueError, TypeError):
                continue

    # Sort by breadcrumb then name for predictable ordering
    result.sort(key=lambda c: (c.breadcrumb.lower(), c.name.lower()))
    logger.info(f"Loaded {len(result)} Meesho sub-sub-categories")
    return result


def get_categories() -> List[CategoryItem]:
    """Return the cached flat category list (parsed once)."""
    global _cached_categories
    if _cached_categories is None:
        _cached_categories = _build_categories()
    return _cached_categories
