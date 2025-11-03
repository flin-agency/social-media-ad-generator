"""Ad generation tool using Google Gemini API for text-to-image generation."""

from __future__ import annotations

import asyncio
import time
import uuid
from typing import Any, Dict, Literal, Optional

import os

import requests
from google import genai
from google.genai import types
from PIL import Image
from pydantic import Field

from ..config import config
from ..models import (
    AdGenerationRequest,
    AdGenerationResult,
    AdVariationType,
    GeneratedAd,
)
from ..prompts.ad_generation_prompts import (
    enhance_prompt_with_colors,
    generate_ad_prompt,
    get_quality_enhancement_suffix,
)
from .base import AgentTool, ToolInput, ToolOutput


class AdGeneratorInput(ToolInput):
    """Input payload for the ad generator tool."""

    operation: Literal["generate_ads", "validate_image", "download_image"] = Field(
        default="generate_ads",
        description="Action the tool should execute.",
    )
    request: Optional[AdGenerationRequest] = None
    image_url: Optional[str] = None
    image_path: Optional[str] = None
    request_id: Optional[str] = None
    index: int = 0


class AdGeneratorOutput(ToolOutput):
    """Output payload returned by the ad generator tool."""

    generation: Optional[AdGenerationResult] = None
    validation: Optional[Dict[str, Any]] = None
    saved_path: Optional[str] = Field(
        default=None,
        description="Local path where the image was saved.",
    )


class AdGenerator(AgentTool):
    """Tool for generating social media ads using Gemini API."""

    name = "ad_generator"
    description = "Creates polished ad creatives from analysis insights and brand data."
    args_model = AdGeneratorInput
    return_model = AdGeneratorOutput

    def __init__(self) -> None:
        super().__init__()
        self._configure_gemini()

    def _configure_gemini(self):
        """Configure Gemini API client."""
        try:
            if config.gemini_api_key:
                # Configure the new genai client
                import os
                os.environ['GEMINI_API_KEY'] = config.gemini_api_key
                self.client = genai.Client(api_key=config.gemini_api_key)
                self.model_name = 'gemini-2.5-flash-image-preview'
                self.logger.info("Gemini API configured successfully")
            else:
                self.logger.warning("Gemini API key not found - using mock mode")
                self.client = None
        except Exception as e:
            self.logger.error(f"Failed to configure Gemini API: {str(e)}")
            self.client = None

    async def generate_ads(self, request: AdGenerationRequest) -> AdGenerationResult:
        """Generate 4 ad variations based on the request."""

        result = await self.ainvoke(request=request, operation="generate_ads")
        if not result.generation:
            raise ValueError("Ad generation failed to produce a result")
        return result.generation

    async def _arun(self, params: AdGeneratorInput) -> AdGeneratorOutput:
        """Dispatch operations supported by the ad generator tool."""

        operation = params.operation

        if operation == "generate_ads":
            if not params.request:
                raise ValueError("request is required for ad generation")
            generation = await self._generate_ads_internal(params.request)
            return AdGeneratorOutput(generation=generation)

        if operation == "validate_image":
            if not params.image_path:
                raise ValueError("image_path is required for validation")
            validation = self.validate_generated_image(params.image_path)
            return AdGeneratorOutput(validation=validation)

        if operation == "download_image":
            if not params.image_url or not params.request_id:
                raise ValueError("image_url and request_id are required to download an image")
            saved_path = await self.download_and_save_image(
                params.image_url,
                params.request_id,
                params.index,
            )
            return AdGeneratorOutput(saved_path=saved_path)

        raise ValueError(f"Unsupported ad generator operation: {operation}")

    async def _generate_ads_internal(self, request: AdGenerationRequest) -> AdGenerationResult:
        """Internal implementation for generating ad variations."""

        self.logger.info("Starting ad generation for request")
        start_time = time.time()

        request_id = str(uuid.uuid4())
        generated_ads = []

        # Define the 4 variations to generate
        variations = [
            AdVariationType.LIFESTYLE,
            AdVariationType.PRODUCT_HERO,
            AdVariationType.BENEFIT_FOCUSED,
            AdVariationType.SOCIAL_PROOF,
        ]

        try:
            # Generate ads concurrently for better performance
            if config.concurrent_generations > 1:
                tasks = [
                    self._generate_single_ad(request, variation, request_id, i)
                    for i, variation in enumerate(variations)
                ]
                generated_ads = await asyncio.gather(*tasks, return_exceptions=True)

                # Filter out exceptions and log errors
                valid_ads = []
                for i, result in enumerate(generated_ads):
                    if isinstance(result, Exception):
                        self.logger.error(f"Failed to generate {variations[i]} ad: {str(result)}")
                    else:
                        valid_ads.append(result)
                generated_ads = valid_ads
            else:
                # Generate ads sequentially
                for i, variation in enumerate(variations):
                    try:
                        ad = await self._generate_single_ad(request, variation, request_id, i)
                        generated_ads.append(ad)
                    except Exception as e:
                        self.logger.error(f"Failed to generate {variation} ad: {str(e)}")

            total_time = time.time() - start_time

            result = AdGenerationResult(
                request_id=request_id,
                ads=generated_ads,
                total_generation_time_seconds=total_time,
                success=len(generated_ads) > 0,
                error_message=None if len(generated_ads) > 0 else "Failed to generate any ads",
            )

            self.logger.info(f"Ad generation completed: {len(generated_ads)} ads in {total_time:.1f}s")
            return result

        except Exception as e:
            total_time = time.time() - start_time
            self.logger.error(f"Ad generation failed: {str(e)}")

            return AdGenerationResult(
                request_id=request_id,
                ads=[],
                total_generation_time_seconds=total_time,
                success=False,
                error_message=str(e),
            )

    async def _generate_single_ad(
        self,
        request: AdGenerationRequest,
        variation_type: AdVariationType,
        request_id: str,
        index: int
    ) -> GeneratedAd:
        """Generate a single ad variation."""
        start_time = time.time()

        self.logger.info(f"Generating {variation_type} ad (index {index})")

        # Extract product features from analysis
        product_features = ", ".join(request.image_analysis.product_features)

        # Generate the prompt for this variation
        base_prompt = generate_ad_prompt(
            variation_type=variation_type,
            product_features=product_features,
            target_audience=request.target_audience,
            brand_tone=request.brand_tone,
            key_message=request.key_message,
            product_category=request.image_analysis.category
        )

        # Enhance prompt with color information
        enhanced_prompt = enhance_prompt_with_colors(
            base_prompt,
            request.image_analysis.dominant_colors
        )

        # Add quality enhancement suffix
        final_prompt = enhanced_prompt + get_quality_enhancement_suffix()

        # Generate the image with product reference
        image_url = await self._call_gemini_api(final_prompt, request_id, index, request.product_image_path)

        generation_time = time.time() - start_time

        ad = GeneratedAd(
            variation_type=variation_type,
            image_url=image_url,
            prompt_used=final_prompt,
            generation_time_seconds=generation_time,
            quality_score=None  # Could be implemented with additional analysis
        )

        self.logger.info(f"Generated {variation_type} ad in {generation_time:.1f}s")
        return ad

    async def _call_gemini_api(self, prompt: str, request_id: str, index: int, product_image_path: Optional[str] = None) -> str:
        """Call Gemini API to generate image using new google.genai library."""
        if not self.client:
            # Mock mode - return placeholder
            return await self._generate_mock_image(request_id, index)

        try:
            # Use new Gemini API for image generation
            self.logger.info(f"Generating image with Gemini API: {prompt[:100]}...")

            # Prepare contents - include product image if provided
            contents = [prompt]

            if product_image_path and os.path.exists(product_image_path):
                self.logger.info(f"Including product image: {product_image_path}")
                # Read and include the product image
                with open(product_image_path, 'rb') as f:
                    image_data = f.read()

                # Add the image to contents
                image_part = types.Part.from_bytes(
                    data=image_data,
                    mime_type="image/jpeg" if product_image_path.lower().endswith(('.jpg', '.jpeg')) else "image/png"
                )

                # Enhanced prompt for image-to-image generation
                enhanced_prompt = f"Using the product shown in the uploaded image as the main subject, {prompt}"
                contents = [enhanced_prompt, image_part]
            else:
                self.logger.warning(f"Product image not found or not provided: {product_image_path}")

            response = await asyncio.to_thread(
                self.client.models.generate_content,
                model=self.model_name,
                contents=contents
            )

            self.logger.info(f"Gemini API response received: {type(response)}")

            # Extract image data using new API format
            if response.candidates and len(response.candidates) > 0:
                candidate = response.candidates[0]
                self.logger.info(f"Processing candidate with parts: {len(candidate.content.parts)}")

                for i, part in enumerate(candidate.content.parts):
                    self.logger.info(f"Part {i}: {type(part)}, has inline_data: {hasattr(part, 'inline_data')}")

                    # Handle inline image data (new API format)
                    if hasattr(part, 'inline_data') and part.inline_data:
                        self.logger.info("Found inline_data, extracting image")
                        image_data = part.inline_data.data
                        if image_data:
                            return await self._save_generated_image(image_data, request_id, index)

                    # Log text content if present
                    if hasattr(part, 'text') and part.text:
                        self.logger.info(f"Text part: {part.text[:200]}...")

            # Log detailed response structure for debugging
            self.logger.warning("No image data found in response, using mock")
            if hasattr(response, 'candidates') and response.candidates:
                candidate = response.candidates[0]
                self.logger.info(f"Candidate content parts: {[type(p) for p in candidate.content.parts]}")
                for i, part in enumerate(candidate.content.parts):
                    self.logger.info(f"Part {i} attributes: {dir(part)}")

            # Fallback to mock if API doesn't return expected format
            return await self._generate_mock_image(request_id, index)

        except Exception as e:
            self.logger.error(f"Gemini API call failed: {str(e)}")
            import traceback
            self.logger.error(f"Full traceback: {traceback.format_exc()}")
            # Fallback to mock on API failure
            return await self._generate_mock_image(request_id, index)

    async def _generate_mock_image(self, request_id: str, index: int) -> str:
        """Generate a mock image placeholder for testing."""
        self.logger.info(f"Generating mock image for request {request_id}, index {index}")

        # Create a simple colored rectangle as placeholder
        from PIL import Image, ImageDraw, ImageFont
        import os

        # Create image with 9:16 aspect ratio
        width, height = config.output_width_height
        image = Image.new('RGB', (width, height), color=(100 + index * 30, 150, 200))

        # Add some text
        draw = ImageDraw.Draw(image)
        try:
            # Try to use a default font
            font = ImageFont.load_default()
        except:
            font = None

        text = f"Mock Ad #{index + 1}\n{request_id[:8]}"
        if font:
            # Calculate text position
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (width - text_width) // 2
            y = (height - text_height) // 2
            draw.text((x, y), text, fill=(255, 255, 255), font=font)

        # Save mock image
        mock_filename = f"mock_ad_{request_id[:8]}_{index}.png"
        mock_path = os.path.join("logs", mock_filename)

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        image.save(mock_path)
        self.logger.info(f"Mock image saved: {mock_path}")

        # Return file path as URL (in real implementation, this would be uploaded to cloud storage)
        return f"file://{os.path.abspath(mock_path)}"

    async def _save_generated_image(self, file_data: bytes, request_id: str, index: int) -> str:
        """Save generated image data to file."""
        filename = f"generated_ad_{request_id[:8]}_{index}.png"
        filepath = os.path.join("logs", filename)

        # Ensure logs directory exists
        os.makedirs("logs", exist_ok=True)

        # Save image data
        with open(filepath, 'wb') as f:
            f.write(file_data)

        self.logger.info(f"Generated image saved: {filepath}")
        return f"file://{os.path.abspath(filepath)}"

    async def download_and_save_image(self, image_url: str, request_id: str, index: int) -> str:
        """Download image from URL and save locally."""
        if image_url.startswith("file://"):
            # Already a local file
            return image_url

        try:
            response = requests.get(image_url, timeout=30)
            response.raise_for_status()

            # Create filename
            filename = f"downloaded_ad_{request_id[:8]}_{index}.png"
            filepath = os.path.join("logs", filename)

            # Ensure logs directory exists
            os.makedirs("logs", exist_ok=True)

            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)

            self.logger.info(f"Image downloaded and saved: {filepath}")
            return f"file://{os.path.abspath(filepath)}"

        except Exception as e:
            self.logger.error(f"Failed to download image from {image_url}: {str(e)}")
            raise

    def validate_generated_image(self, image_path: str) -> Dict[str, Any]:
        """Validate that generated image meets requirements."""
        try:
            if image_path.startswith("file://"):
                image_path = image_path[7:]  # Remove file:// prefix

            if not os.path.exists(image_path):
                return {"valid": False, "error": "Image file not found"}

            with Image.open(image_path) as img:
                width, height = img.size
                aspect_ratio = width / height

                # Check aspect ratio (9:16 = 0.5625)
                target_ratio = 9 / 16
                ratio_tolerance = 0.05

                validation_result = {
                    "valid": True,
                    "width": width,
                    "height": height,
                    "aspect_ratio": aspect_ratio,
                    "correct_aspect_ratio": abs(aspect_ratio - target_ratio) <= ratio_tolerance,
                    "file_size_mb": os.path.getsize(image_path) / (1024 * 1024)
                }

                if not validation_result["correct_aspect_ratio"]:
                    validation_result["valid"] = False
                    validation_result["error"] = f"Incorrect aspect ratio: {aspect_ratio:.3f}, expected: {target_ratio:.3f}"

                return validation_result

        except Exception as e:
            return {"valid": False, "error": f"Validation failed: {str(e)}"}