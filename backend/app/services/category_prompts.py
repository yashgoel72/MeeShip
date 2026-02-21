"""
Category → Photography Style Mapping

Maps Meesho super-categories to prompt fragments that guide the AI model
to generate category-appropriate product photography.

Lookup: O(1) dict access — zero computational cost.
Memory: ~15 entries, <3KB.
"""

from typing import Optional

# ---------------------------------------------------------------------------
# Prompt fragment per super-category
# ---------------------------------------------------------------------------

class CategoryStyle:
    """Photography style hints for a product super-category."""
    __slots__ = ("product_descriptor", "shipping_hint", "lifestyle_hint")

    def __init__(self, product_descriptor: str, shipping_hint: str, lifestyle_hint: str):
        self.product_descriptor = product_descriptor
        self.shipping_hint = shipping_hint
        self.lifestyle_hint = lifestyle_hint


# Keyed by LOWERCASE super-category name (first part of breadcrumb)
CATEGORY_STYLES: dict[str, CategoryStyle] = {
    "men fashion": CategoryStyle(
        product_descriptor="men's garment",
        shipping_hint=(
            "Show the garment NEATLY FOLDED/STACKED, NOT on mannequin or spread out. "
            "Fold reveals front design/print. Ultra compact footprint on white surface."
        ),
        lifestyle_hint=(
            "Styled on male model or crisp flat-lay with minimal accessories (watch, belt). "
            "Casual or smart-casual setting. Clean, masculine aesthetic."
        ),
    ),
    "women fashion": CategoryStyle(
        product_descriptor="women's garment",
        shipping_hint=(
            "Show the garment NEATLY FOLDED, NOT draped, NOT on hanger. "
            "Compact stack showing front print/embroidery. Minimal footprint."
        ),
        lifestyle_hint=(
            "On female model or elegant hanger/mannequin shot. "
            "Styled with complementary accessories. Aspirational, fashion-forward setting."
        ),
    ),
    "home & living": CategoryStyle(
        product_descriptor="home product",
        shipping_hint=(
            "Show product ONLY, isolated on white. NO room context, NO furniture nearby. "
            "Tight crop, compact centered placement. Remove all scale references."
        ),
        lifestyle_hint=(
            "Product in styled room vignette — on shelf, table, or bed. "
            "Cozy, aspirational home setting with warm lighting and soft textures."
        ),
    ),
    "home & kitchen": CategoryStyle(
        product_descriptor="kitchen/home product",
        shipping_hint=(
            "Product only on white, NO food or ingredients around. "
            "Compact centered shot. If appliance, show it closed/folded."
        ),
        lifestyle_hint=(
            "Product on kitchen counter or in-use cooking scene. "
            "Homely, practical setting with warm tones. Clean, organized kitchen context."
        ),
    ),
    "kids & toys": CategoryStyle(
        product_descriptor="kids' product",
        shipping_hint=(
            "Product folded/compact if clothing, or centered tight if toy. "
            "Bright white background. No child in frame."
        ),
        lifestyle_hint=(
            "Child using/wearing product in fun, colorful setting. "
            "Playful props, age-appropriate context. Bright, cheerful mood."
        ),
    ),
    "consumer electronics": CategoryStyle(
        product_descriptor="electronic device",
        shipping_hint=(
            "Device only, NO packaging, box, or cables. Clean white background. "
            "Product at slight angle showing front face. Compact, precise placement."
        ),
        lifestyle_hint=(
            "Device on modern desk or being held in hand. "
            "Tech-lifestyle context, clean workspace or on-the-go usage. Sleek aesthetic."
        ),
    ),
    "appliances": CategoryStyle(
        product_descriptor="appliance",
        shipping_hint=(
            "Appliance closed/compact on white. No accessories, no food, no utensils around. "
            "Front-facing angle, tight framing."
        ),
        lifestyle_hint=(
            "Appliance on kitchen counter or in modern home setting. "
            "In-use or styled context. Clean, aspirational kitchen."
        ),
    ),
    "beauty & personal care": CategoryStyle(
        product_descriptor="beauty product",
        shipping_hint=(
            "Bottle/tube/compact standing upright or at slight angle. "
            "Label facing camera. Tight framing on white. Single item only."
        ),
        lifestyle_hint=(
            "Product on marble vanity or styled surface with soft florals, texture swatches, "
            "or fabric backdrop. Aspirational self-care mood. Warm, feminine lighting."
        ),
    ),
    "beauty & makeup": CategoryStyle(
        product_descriptor="beauty/makeup product",
        shipping_hint=(
            "Product standing upright, label/logo visible. Clean white background. "
            "Compact single-item presentation."
        ),
        lifestyle_hint=(
            "On vanity with mirror, brushes, or swatch display. "
            "Glamorous yet approachable. Soft studio lighting."
        ),
    ),
    "personal care": CategoryStyle(
        product_descriptor="personal care product",
        shipping_hint=(
            "Product standing upright, label visible. Clinical clean white background. "
            "Compact, centered placement."
        ),
        lifestyle_hint=(
            "Product in bathroom/self-care setting. "
            "Clean, trustworthy, health-focused context. Fresh, soothing mood."
        ),
    ),
    "personal care & wellness": CategoryStyle(
        product_descriptor="personal care product",
        shipping_hint=(
            "Product standing upright, label visible. Clean white background. "
            "Tight compact framing."
        ),
        lifestyle_hint=(
            "In bathroom or wellness setting with natural textures. "
            "Fresh, clean, health-conscious aesthetic."
        ),
    ),
    "health & wellness": CategoryStyle(
        product_descriptor="health/wellness product",
        shipping_hint=(
            "Product standing upright, label visible. Clean clinical white background. "
            "Compact single-item presentation."
        ),
        lifestyle_hint=(
            "Product in bathroom or gym/wellness setting. "
            "Clean, trustworthy, health-focused context. Professional feel."
        ),
    ),
    "bags, luggage & travel accessories": CategoryStyle(
        product_descriptor="bag",
        shipping_hint=(
            "Bag standing upright, handles folded down/tucked. Compact frontal view. "
            "No items inside to puff it up. Minimal shadow."
        ),
        lifestyle_hint=(
            "Bag being carried or styled with travel/outfit context. "
            "Aspirational lifestyle — airport, cafe, urban street. On-the-go mood."
        ),
    ),
    "sports & fitness": CategoryStyle(
        product_descriptor="sports equipment",
        shipping_hint=(
            "Compact product shot on white. If ball/racket, show at rest. "
            "Equipment folded/collapsed if possible. Tight framing."
        ),
        lifestyle_hint=(
            "Product in-use at gym, sports field, or outdoor setting. "
            "Active, energetic mood. Dynamic angle. Aspirational fitness context."
        ),
    ),
    "automotive": CategoryStyle(
        product_descriptor="automotive accessory",
        shipping_hint=(
            "Product only, compact on white. No vehicle in frame. "
            "Clean isolated shot showing product details."
        ),
        lifestyle_hint=(
            "Product installed on or near vehicle. "
            "Practical context showing actual use case. Garage or road setting."
        ),
    ),
    "automotive accessories": CategoryStyle(
        product_descriptor="automotive accessory",
        shipping_hint=(
            "Product only, compact on white. No vehicle in frame. "
            "Clean isolated product shot."
        ),
        lifestyle_hint=(
            "Product installed on or near vehicle. "
            "Practical context showing use case."
        ),
    ),
    "grocery": CategoryStyle(
        product_descriptor="food/grocery item",
        shipping_hint=(
            "Single package/bottle/pouch, label facing front. "
            "Tight compact framing on white background."
        ),
        lifestyle_hint=(
            "Product on kitchen counter or table with styled ingredients/meal context. "
            "Fresh, appetizing, homely mood. Warm natural lighting."
        ),
    ),
    "books": CategoryStyle(
        product_descriptor="book",
        shipping_hint=(
            "Book standing upright or flat at slight angle. Cover facing camera. "
            "Tight crop, compact placement on white."
        ),
        lifestyle_hint=(
            "Book on reading nook, desk, or coffee table with warm lighting. "
            "Intellectual, cozy atmosphere. Cup of tea/coffee as prop."
        ),
    ),
    "pet supplies": CategoryStyle(
        product_descriptor="pet product",
        shipping_hint=(
            "Product only on white, no pet in frame. "
            "Compact, centered placement. Label/design visible."
        ),
        lifestyle_hint=(
            "Product being used by/with pet. "
            "Cute, heartwarming context. Happy pet in comfortable home setting."
        ),
    ),
    "jewellery": CategoryStyle(
        product_descriptor="jewellery piece",
        shipping_hint=(
            "Macro-style close-up showing craftsmanship and detail. "
            "Product is inherently small — center it with generous padding. Light sparkle."
        ),
        lifestyle_hint=(
            "On model (hand, wrist, neck, or ear). Elegant warm lighting. "
            "Aspirational styling. Soft bokeh background."
        ),
    ),
    "mobiles & tablets": CategoryStyle(
        product_descriptor="mobile device",
        shipping_hint=(
            "Device front-facing at slight angle. Screen on or off. "
            "Clean white background, compact placement. No box or accessories."
        ),
        lifestyle_hint=(
            "Device being held or on modern surface. "
            "Tech-lifestyle context — workspace, cafe, commute. Sleek, premium feel."
        ),
    ),
    "men's grooming": CategoryStyle(
        product_descriptor="men's grooming product",
        shipping_hint=(
            "Product standing upright, label visible. Clean white background. "
            "Compact, minimal presentation."
        ),
        lifestyle_hint=(
            "Product on bathroom counter or grooming setup. "
            "Masculine, clean aesthetic. Modern bathroom context."
        ),
    ),
    "mens personal care & grooming": CategoryStyle(
        product_descriptor="men's grooming product",
        shipping_hint=(
            "Product standing upright, label visible. Clean white background. "
            "Compact placement."
        ),
        lifestyle_hint=(
            "Bathroom counter or grooming setup. "
            "Masculine, modern aesthetic."
        ),
    ),
    "office supplies & stationery": CategoryStyle(
        product_descriptor="stationery item",
        shipping_hint=(
            "Product centered on white. Pens capped, notebooks closed. "
            "Compact, organized single-item shot."
        ),
        lifestyle_hint=(
            "On organized desk with workspace context. "
            "Productive, creative atmosphere. Warm desk lamp lighting."
        ),
    ),
    "craft & office supplies": CategoryStyle(
        product_descriptor="stationery/craft item",
        shipping_hint=(
            "Product centered on white. Compact, tidy presentation. "
            "Single item only."
        ),
        lifestyle_hint=(
            "On creative workspace or desk. "
            "Artistic, organized, productive mood."
        ),
    ),
    "musical instruments": CategoryStyle(
        product_descriptor="musical instrument",
        shipping_hint=(
            "Instrument in rest position, case closed if applicable. "
            "Compact placement on white, no accessories."
        ),
        lifestyle_hint=(
            "Instrument being played or on stand in music room/studio. "
            "Artistic, passionate mood. Warm dramatic lighting."
        ),
    ),
    "eye utility": CategoryStyle(
        product_descriptor="eyewear/eye care product",
        shipping_hint=(
            "Product centered on white. Sunglasses folded, eye drops upright. "
            "Compact, label-visible presentation."
        ),
        lifestyle_hint=(
            "Worn on face or styled on surface with sunlight/outdoor context. "
            "Fresh, stylish, health-conscious aesthetic."
        ),
    ),
    "home utility": CategoryStyle(
        product_descriptor="home utility product",
        shipping_hint=(
            "Product only, compact on white. No room context. "
            "Tight crop, isolated product shot."
        ),
        lifestyle_hint=(
            "Product in-use in home setting — kitchen, bathroom, or storage area. "
            "Practical, organized, functional context."
        ),
    ),
    "kids": CategoryStyle(
        product_descriptor="kids' product",
        shipping_hint=(
            "Product folded/compact if clothing, or centered tight if toy/accessory. "
            "Bright white background. No child in frame."
        ),
        lifestyle_hint=(
            "Child using/wearing product in fun, colorful setting. "
            "Playful props, age-appropriate context. Bright, cheerful mood."
        ),
    ),
    "women": CategoryStyle(
        product_descriptor="women's product",
        shipping_hint=(
            "Show product NEATLY FOLDED/compact, NOT draped. "
            "Compact presentation on white. Minimal footprint."
        ),
        lifestyle_hint=(
            "On female model or elegant styled shot. "
            "Aspirational, fashion-forward or lifestyle-appropriate setting."
        ),
    ),
    "industrial & scientific products": CategoryStyle(
        product_descriptor="industrial product",
        shipping_hint=(
            "Product only on white, compact centered placement. "
            "No tools or accessories around. Clean, precise."
        ),
        lifestyle_hint=(
            "Product in workshop or lab context. "
            "Professional, industrial setting. Practical, trustworthy feel."
        ),
    ),
}


def get_category_prompt_fragment(
    category_name: Optional[str] = None,
    breadcrumb: Optional[str] = None,
) -> Optional[str]:
    """
    Build a prompt fragment for the given product category.

    Returns None if the category doesn't match any known super-category
    (in which case the generic prompt is used as-is).
    """
    if not breadcrumb and not category_name:
        return None

    # Extract super-category from breadcrumb ("Men Fashion > Mens Clothing > …")
    super_cat = ""
    if breadcrumb:
        super_cat = breadcrumb.split(" > ")[0].strip()

    style = CATEGORY_STYLES.get(super_cat.lower())
    if not style:
        return None

    display_name = category_name or super_cat
    crumb = breadcrumb or super_cat

    return (
        f"📦 PRODUCT CONTEXT:\n"
        f"This is a {display_name} ({crumb}).\n"
        f"Product type: {style.product_descriptor}.\n"
        f"SHIPPING TILES 1-4: {style.shipping_hint}\n"
        f"LIFESTYLE TILES 5-6: {style.lifestyle_hint}\n"
    )
