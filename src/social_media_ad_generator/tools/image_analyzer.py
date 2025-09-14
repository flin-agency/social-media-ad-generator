"""Image analysis tool for product categorization and feature extraction."""

import asyncio
import logging
from typing import List, Dict, Any
from PIL import Image
import os
import colorsys
from collections import Counter

from ..models import ImageAnalysis, ProductCategory
from ..config import config


class ImageAnalyzer:
    """Tool for analyzing product images."""

    def __init__(self):
        """Initialize the image analyzer."""
        self.logger = logging.getLogger(__name__)

    async def analyze_image(self, image_path: str) -> ImageAnalysis:
        """Analyze a product image and extract features."""
        self.logger.info(f"Analyzing image: {image_path}")

        # Validate image
        await self._validate_image(image_path)

        # Load and process image
        image = Image.open(image_path)
        if image.mode != "RGB":
            image = image.convert("RGB")

        # Extract features
        dominant_colors = await self._extract_dominant_colors(image)
        category = await self._classify_product(image, image_path)
        product_features = await self._extract_product_features(image, category)
        background_type = await self._analyze_background(image)
        quality_score = await self._assess_image_quality(image)
        suggested_questions = await self._generate_suggested_questions(category, product_features)

        analysis = ImageAnalysis(
            category=category,
            dominant_colors=dominant_colors,
            product_features=product_features,
            background_type=background_type,
            image_quality_score=quality_score,
            suggested_questions=suggested_questions
        )

        self.logger.info(f"Image analysis completed for {image_path}")
        return analysis

    async def _validate_image(self, image_path: str) -> None:
        """Validate image file."""
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Image file not found: {image_path}")

        # Check file size
        file_size_mb = os.path.getsize(image_path) / (1024 * 1024)
        if file_size_mb > config.max_image_size_mb:
            raise ValueError(f"Image too large: {file_size_mb:.1f}MB > {config.max_image_size_mb}MB")

        # Check file format
        try:
            with Image.open(image_path) as img:
                if img.format.upper() not in config.supported_formats_list:
                    raise ValueError(f"Unsupported format: {img.format}")
        except Exception as e:
            raise ValueError(f"Invalid image file: {str(e)}")

    async def _extract_dominant_colors(self, image: Image.Image) -> List[str]:
        """Extract dominant colors from the image."""
        # Resize image for faster processing
        image_small = image.resize((100, 100))
        pixels = list(image_small.getdata())

        # Count color frequencies
        color_counts = Counter(pixels)
        most_common = color_counts.most_common(5)

        # Convert to hex colors
        hex_colors = []
        for (r, g, b), count in most_common:
            hex_color = f"#{r:02x}{g:02x}{b:02x}"
            hex_colors.append(hex_color)

        return hex_colors

    async def _classify_product(self, image: Image.Image, image_path: str) -> ProductCategory:
        """Classify the product category based on image analysis."""
        # This is a simplified classification based on filename and basic analysis
        # In a real implementation, this would use a trained ML model

        filename = os.path.basename(image_path).lower()

        # Simple keyword-based classification
        if any(word in filename for word in ['fashion', 'clothing', 'shirt', 'dress', 'shoe', 'bag']):
            return ProductCategory.FASHION
        elif any(word in filename for word in ['electronic', 'phone', 'laptop', 'camera', 'tech']):
            return ProductCategory.ELECTRONICS
        elif any(word in filename for word in ['food', 'drink', 'coffee', 'cake', 'restaurant']):
            return ProductCategory.FOOD_BEVERAGE
        elif any(word in filename for word in ['home', 'furniture', 'decor', 'kitchen', 'garden']):
            return ProductCategory.HOME_GARDEN
        elif any(word in filename for word in ['beauty', 'cosmetic', 'skincare', 'makeup']):
            return ProductCategory.BEAUTY_PERSONAL_CARE
        elif any(word in filename for word in ['sport', 'fitness', 'outdoor', 'gym']):
            return ProductCategory.SPORTS_OUTDOORS
        elif any(word in filename for word in ['car', 'auto', 'vehicle']):
            return ProductCategory.AUTOMOTIVE
        elif any(word in filename for word in ['book', 'media', 'music', 'movie']):
            return ProductCategory.BOOKS_MEDIA
        elif any(word in filename for word in ['toy', 'game', 'play']):
            return ProductCategory.TOYS_GAMES
        elif any(word in filename for word in ['service', 'consulting', 'business']):
            return ProductCategory.SERVICES
        else:
            # Analyze image properties for additional clues
            width, height = image.size
            dominant_colors = await self._extract_dominant_colors(image)

            # Basic heuristics based on image properties
            if width > height * 1.5:  # Wide aspect ratio might be electronics
                return ProductCategory.ELECTRONICS
            elif len(dominant_colors) > 3:  # Colorful might be fashion or toys
                return ProductCategory.FASHION
            else:
                return ProductCategory.OTHER

    async def _extract_product_features(self, image: Image.Image, category: ProductCategory) -> List[str]:
        """Extract product features based on category and image analysis."""
        features = []
        width, height = image.size

        # Basic features based on image properties
        if width > height:
            features.append("landscape orientation")
        elif height > width:
            features.append("portrait orientation")
        else:
            features.append("square format")

        # Category-specific features
        if category == ProductCategory.FASHION:
            features.extend(["stylish design", "wearable", "trendy"])
        elif category == ProductCategory.ELECTRONICS:
            features.extend(["modern design", "high-tech", "functional"])
        elif category == ProductCategory.FOOD_BEVERAGE:
            features.extend(["appetizing", "fresh", "delicious"])
        elif category == ProductCategory.BEAUTY_PERSONAL_CARE:
            features.extend(["premium quality", "skin-friendly", "beautiful"])
        else:
            features.extend(["quality product", "reliable", "useful"])

        return features

    async def _analyze_background(self, image: Image.Image) -> str:
        """Analyze the background type of the image."""
        # Convert to grayscale for edge detection
        gray = image.convert('L')
        width, height = gray.size

        # Sample pixels from edges to determine background complexity
        edge_pixels = []

        # Sample from edges
        for i in range(0, width, max(1, width // 20)):
            edge_pixels.extend([gray.getpixel((i, 0)), gray.getpixel((i, height-1))])

        for i in range(0, height, max(1, height // 20)):
            edge_pixels.extend([gray.getpixel((0, i)), gray.getpixel((width-1, i))])

        # Calculate variance to determine background complexity
        if len(edge_pixels) > 0:
            mean_pixel = sum(edge_pixels) / len(edge_pixels)
            variance = sum((p - mean_pixel) ** 2 for p in edge_pixels) / len(edge_pixels)

            if variance < 100:
                return "clean background"
            elif variance < 1000:
                return "simple background"
            else:
                return "complex background"

        return "unknown background"

    async def _assess_image_quality(self, image: Image.Image) -> float:
        """Assess the quality of the image."""
        width, height = image.size
        total_pixels = width * height

        # Basic quality assessment based on resolution and sharpness
        quality_score = 0.0

        # Resolution score (0-0.4)
        if total_pixels >= 1920 * 1080:  # HD or higher
            quality_score += 0.4
        elif total_pixels >= 1280 * 720:  # HD ready
            quality_score += 0.3
        elif total_pixels >= 640 * 480:  # VGA
            quality_score += 0.2
        else:
            quality_score += 0.1

        # Aspect ratio score (0-0.2)
        aspect_ratio = width / height
        if 0.5 <= aspect_ratio <= 2.0:  # Reasonable aspect ratio
            quality_score += 0.2
        else:
            quality_score += 0.1

        # Color distribution score (0-0.4)
        colors = await self._extract_dominant_colors(image)
        if len(colors) >= 3:  # Good color variety
            quality_score += 0.4
        elif len(colors) >= 2:
            quality_score += 0.3
        else:
            quality_score += 0.2

        return min(quality_score, 1.0)

    async def _generate_suggested_questions(self, category: ProductCategory, features: List[str]) -> List[str]:
        """Generate suggested questions based on analysis."""
        base_questions = [
            "Who is your target audience?",
            "What tone should the ad convey?",
            "What's your main selling point?"
        ]

        category_questions = {
            ProductCategory.FASHION: [
                "What style aesthetic appeals to your customers?",
                "Is this for a specific season or occasion?",
                "What age group are you targeting?"
            ],
            ProductCategory.ELECTRONICS: [
                "What technical benefits should we highlight?",
                "Are you targeting tech enthusiasts or general consumers?",
                "What problem does this product solve?"
            ],
            ProductCategory.FOOD_BEVERAGE: [
                "What eating occasion is this for?",
                "Should we emphasize taste, health, or convenience?",
                "What dietary preferences should we consider?"
            ]
        }

        suggested = base_questions.copy()
        if category in category_questions:
            suggested.extend(category_questions[category][:2])  # Add 2 category-specific questions

        return suggested[:5]  # Return max 5 questions