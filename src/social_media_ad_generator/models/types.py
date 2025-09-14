"""Data models for the Social Media Ad Generator."""

from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field
from enum import Enum


class ProductCategory(str, Enum):
    """Product categories for analysis."""
    FASHION = "fashion"
    ELECTRONICS = "electronics"
    FOOD_BEVERAGE = "food_beverage"
    HOME_GARDEN = "home_garden"
    BEAUTY_PERSONAL_CARE = "beauty_personal_care"
    SPORTS_OUTDOORS = "sports_outdoors"
    AUTOMOTIVE = "automotive"
    BOOKS_MEDIA = "books_media"
    TOYS_GAMES = "toys_games"
    SERVICES = "services"
    OTHER = "other"


class BrandTone(str, Enum):
    """Brand tone options."""
    PROFESSIONAL = "professional"
    PLAYFUL = "playful"
    LUXURY = "luxury"
    MINIMALIST = "minimalist"
    BOLD = "bold"
    FRIENDLY = "friendly"
    SOPHISTICATED = "sophisticated"


class AdVariationType(str, Enum):
    """Types of ad variations to generate."""
    LIFESTYLE = "lifestyle"
    PRODUCT_HERO = "product_hero"
    BENEFIT_FOCUSED = "benefit_focused"
    SOCIAL_PROOF = "social_proof"


class ImageAnalysis(BaseModel):
    """Product image analysis results."""
    category: ProductCategory
    dominant_colors: List[str]
    product_features: List[str]
    background_type: str
    image_quality_score: float = Field(ge=0.0, le=1.0)
    suggested_questions: List[str]


class UserResponse(BaseModel):
    """User response to questions."""
    question_id: str
    question_text: str
    response: str
    processed_response: Optional[Dict[str, Any]] = None


class AdGenerationRequest(BaseModel):
    """Request for generating ads."""
    image_analysis: ImageAnalysis
    user_responses: List[UserResponse]
    target_audience: str
    brand_tone: BrandTone
    key_message: str
    product_image_path: Optional[str] = None


class GeneratedAd(BaseModel):
    """Generated advertisement."""
    variation_type: AdVariationType
    image_url: str
    prompt_used: str
    generation_time_seconds: float
    quality_score: Optional[float] = None


class AdGenerationResult(BaseModel):
    """Complete ad generation result."""
    request_id: str
    ads: List[GeneratedAd]
    total_generation_time_seconds: float
    success: bool
    error_message: Optional[str] = None


class QuestionTemplate(BaseModel):
    """Template for generating questions."""
    question_id: str
    template: str
    category_specific: Optional[List[ProductCategory]] = None
    follow_up_questions: Optional[List[str]] = None