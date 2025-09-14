"""Ad generation prompts for different variation types."""

from typing import Dict
from ..models import AdVariationType, BrandTone, ProductCategory

AD_GENERATION_PROMPTS: Dict[AdVariationType, str] = {
    AdVariationType.LIFESTYLE: """
Create a vertical 9:16 social media advertisement showing {product_features} in a real-world lifestyle context.
The image should feature the product being used by {target_audience} in a {lifestyle_setting}.
Style: {brand_tone} tone with natural lighting and authentic scenario.
The scene should convey {key_message} through the lifestyle integration.
Include space for text overlay in the upper or lower third of the image.
High-quality, Instagram/TikTok Stories optimized, professional photography aesthetic.
""",

    AdVariationType.PRODUCT_HERO: """
Create a vertical 9:16 social media advertisement featuring {product_features} as the hero element.
Clean, minimal background with professional product photography lighting.
Style: {brand_tone} aesthetic with focus on product details and quality.
The product should be prominently displayed with {key_message} clearly communicated.
Include negative space for text overlay and call-to-action elements.
High-resolution, crisp product shot optimized for social media platforms.
""",

    AdVariationType.BENEFIT_FOCUSED: """
Create a vertical 9:16 social media advertisement that visually represents the benefits of {product_features}.
Show the transformation, solution, or positive outcome the product provides to {target_audience}.
Style: {brand_tone} tone with before/after concept or benefit visualization.
The image should clearly communicate {key_message} through visual storytelling.
Include areas for benefit-focused text and compelling call-to-action.
Engaging, results-oriented design optimized for social media engagement.
""",

    AdVariationType.SOCIAL_PROOF: """
Create a vertical 9:16 social media advertisement with a testimonial or review aesthetic featuring {product_features}.
Include visual elements that suggest customer satisfaction, ratings, or social validation.
Style: {brand_tone} tone with trustworthy, authentic social proof indicators.
The design should reinforce {key_message} through credibility and customer success.
Include space for testimonial text, star ratings, or customer quote overlays.
Professional yet approachable design that builds trust and social validation.
"""
}

BRAND_TONE_MODIFIERS: Dict[BrandTone, str] = {
    BrandTone.PROFESSIONAL: "clean, sophisticated, business-like",
    BrandTone.PLAYFUL: "fun, colorful, energetic, whimsical",
    BrandTone.LUXURY: "premium, elegant, high-end, exclusive",
    BrandTone.MINIMALIST: "simple, clean lines, lots of white space, understated",
    BrandTone.BOLD: "vibrant colors, strong contrast, eye-catching, dramatic",
    BrandTone.FRIENDLY: "warm, approachable, welcoming, casual",
    BrandTone.SOPHISTICATED: "refined, cultured, tasteful, mature"
}

LIFESTYLE_SETTINGS: Dict[ProductCategory, str] = {
    ProductCategory.FASHION: "trendy urban environment, stylish cafe, or fashion-forward setting",
    ProductCategory.ELECTRONICS: "modern workspace, tech-savvy environment, or contemporary home",
    ProductCategory.FOOD_BEVERAGE: "inviting kitchen, cozy dining space, or social gathering",
    ProductCategory.BEAUTY_PERSONAL_CARE: "elegant bathroom, vanity area, or spa-like setting",
    ProductCategory.HOME_GARDEN: "beautifully designed home interior or lush garden space",
    ProductCategory.SPORTS_OUTDOORS: "active outdoor setting, gym environment, or athletic venue",
    ProductCategory.AUTOMOTIVE: "scenic road, modern city street, or premium garage",
    ProductCategory.SERVICES: "professional office, consultation space, or client meeting area",
    ProductCategory.OTHER: "appropriate real-world context for product usage"
}


def generate_ad_prompt(
    variation_type: AdVariationType,
    product_features: str,
    target_audience: str,
    brand_tone: BrandTone,
    key_message: str,
    product_category: ProductCategory = ProductCategory.OTHER
) -> str:
    """Generate a specific ad prompt based on parameters."""

    base_prompt = AD_GENERATION_PROMPTS[variation_type]

    # Get lifestyle setting for the category
    lifestyle_setting = LIFESTYLE_SETTINGS.get(product_category, LIFESTYLE_SETTINGS[ProductCategory.OTHER])

    # Get brand tone modifier
    tone_modifier = BRAND_TONE_MODIFIERS.get(brand_tone, "professional")

    # Format the prompt with provided parameters
    formatted_prompt = base_prompt.format(
        product_features=product_features,
        target_audience=target_audience,
        brand_tone=tone_modifier,
        key_message=key_message,
        lifestyle_setting=lifestyle_setting
    )

    return formatted_prompt.strip()


def get_quality_enhancement_suffix() -> str:
    """Get standard quality enhancement suffix for all prompts."""
    return """
Additional requirements:
- Aspect ratio: exactly 9:16 (vertical)
- Resolution: minimum 1080x1920 pixels
- Professional photography quality
- Optimized for mobile viewing
- Include SynthID watermark as required
- Ensure text overlay areas are clear and readable
- Use appropriate lighting for product visibility
- Maintain brand consistency throughout
"""


def enhance_prompt_with_colors(prompt: str, dominant_colors: list) -> str:
    """Enhance prompt with dominant color information."""
    if dominant_colors and len(dominant_colors) > 0:
        color_guidance = f"\nColor palette: Incorporate or complement these dominant colors from the original product image: {', '.join(dominant_colors[:3])}."
        return prompt + color_guidance
    return prompt