"""Question generation and response processing engine."""

from __future__ import annotations

import re
from typing import Any, Dict, List, Optional

from pydantic import Field

from ..models import (
    BrandTone,
    ImageAnalysis,
    ProductCategory,
    QuestionTemplate,
    UserResponse,
)
from ..prompts.question_templates import get_questions_for_category
from .base import AgentTool, ToolInput, ToolOutput


class QuestionEngineInput(ToolInput):
    """Input payload for the question engine."""

    operation: str = Field(
        default="generate_questions",
        description="Action to perform: generate_questions or process_response",
    )
    analysis: Optional[ImageAnalysis] = None
    num_questions: int = 3
    response: Optional[UserResponse] = None


class QuestionEngineOutput(ToolOutput):
    """Output payload returned by the question engine."""

    questions: Optional[List[QuestionTemplate]] = None
    processed_response: Optional[Dict[str, Any]] = None


class QuestionEngine(AgentTool):
    """Engine for generating contextual questions and processing responses."""

    name = "question_engine"
    description = "Crafts follow-up questions and structures user responses."
    args_model = QuestionEngineInput
    return_model = QuestionEngineOutput

    def __init__(self) -> None:
        super().__init__()

    async def generate_questions(self, analysis: ImageAnalysis, num_questions: int = 3) -> List[QuestionTemplate]:
        """Generate contextual questions based on image analysis."""

        result = await self.ainvoke(analysis=analysis, num_questions=num_questions, operation="generate_questions")
        return result.questions or []

    async def process_response(self, response: UserResponse) -> Dict[str, Any]:
        """Process and extract structured information from user response."""

        result = await self.ainvoke(response=response, operation="process_response")
        return result.processed_response or {}

    async def _arun(self, params: QuestionEngineInput) -> QuestionEngineOutput:
        """Dispatch the correct operation based on the provided parameters."""

        operation = params.operation
        if operation == "generate_questions":
            if not params.analysis:
                raise ValueError("analysis is required to generate questions")
            questions = await self._generate_questions_internal(params.analysis, params.num_questions)
            return QuestionEngineOutput(questions=questions)

        if operation == "process_response":
            if not params.response:
                raise ValueError("response is required to process answers")
            processed = await self._process_response_internal(params.response)
            return QuestionEngineOutput(processed_response=processed)

        raise ValueError(f"Unsupported question engine operation: {operation}")

    async def _generate_questions_internal(
        self, analysis: ImageAnalysis, num_questions: int = 3
    ) -> List[QuestionTemplate]:
        """Generate contextual questions based on image analysis."""

        self.logger.info(f"Generating {num_questions} questions for category: {analysis.category}")

        # Get questions appropriate for the product category
        questions = get_questions_for_category(analysis.category, num_questions)

        # If we have suggested questions from analysis, consider incorporating them
        if analysis.suggested_questions and len(questions) < num_questions:
            remaining_slots = num_questions - len(questions)
            for i, suggested in enumerate(analysis.suggested_questions[:remaining_slots]):
                questions.append(
                    QuestionTemplate(
                        question_id=f"suggested_{i+1}",
                        template=suggested,
                        category_specific=[analysis.category],
                    )
                )

        self.logger.info(f"Generated {len(questions)} questions")
        return questions[:num_questions]

    async def _process_response_internal(self, response: UserResponse) -> Dict[str, Any]:
        """Process and extract structured information from user response."""

        self.logger.info(f"Processing response for question: {response.question_id}")

        processed_data: Dict[str, Any] = {}
        response_text = response.response.lower().strip()

        # Process based on question type
        if response.question_id == "target_audience":
            processed_data["target_audience"] = response.response.strip()
            processed_data["demographics"] = await self._extract_demographics(response_text)

        elif response.question_id == "brand_tone":
            processed_data["brand_tone"] = await self._extract_brand_tone(response_text)
            processed_data["tone_keywords"] = await self._extract_tone_keywords(response_text)

        elif response.question_id == "key_message":
            processed_data["key_message"] = response.response.strip()
            processed_data["call_to_action"] = await self._extract_call_to_action(response_text)
            processed_data["unique_selling_points"] = await self._extract_selling_points(response_text)

        # Category-specific processing
        elif response.question_id.startswith("fashion_"):
            processed_data.update(await self._process_fashion_response(response.question_id, response_text))

        elif response.question_id.startswith("tech_"):
            processed_data.update(await self._process_tech_response(response.question_id, response_text))

        elif response.question_id.startswith("food_"):
            processed_data.update(await self._process_food_response(response.question_id, response_text))

        elif response.question_id.startswith("beauty_"):
            processed_data.update(await self._process_beauty_response(response.question_id, response_text))

        elif response.question_id.startswith("home_"):
            processed_data.update(await self._process_home_response(response.question_id, response_text))

        elif response.question_id.startswith("sports_"):
            processed_data.update(await self._process_sports_response(response.question_id, response_text))

        elif response.question_id.startswith("service_"):
            processed_data.update(await self._process_service_response(response.question_id, response_text))

        # Generic processing for any remaining responses
        else:
            processed_data["raw_response"] = response.response.strip()
            processed_data["keywords"] = await self._extract_keywords(response_text)

        self.logger.info(f"Response processing completed for {response.question_id}")
        return processed_data

    async def _extract_demographics(self, response_text: str) -> Dict[str, Any]:
        """Extract demographic information from target audience response."""
        demographics = {}

        # Age extraction
        age_patterns = [
            r'(\d+)[-\s]*(?:to|-)?\s*(\d+)?\s*(?:year|yr)s?\s*old',
            r'(?:age|aged)\s*(\d+)[-\s]*(?:to|-)?\s*(\d+)?',
            r'(teen|teenager|young|adult|senior|elderly|millennial|gen\s*z|boomer)'
        ]

        for pattern in age_patterns:
            match = re.search(pattern, response_text)
            if match:
                demographics["age_info"] = match.group(0)
                break

        # Gender extraction - order matters! Longer/more specific terms first
        gender_keywords = ["women", "female", "men", "male", "unisex", "all genders", "everyone"]
        for keyword in gender_keywords:
            if keyword in response_text:
                demographics["gender"] = keyword
                break

        # Interest extraction
        interest_keywords = ["fitness", "fashion", "tech", "business", "family", "travel", "food", "music", "sports"]
        interests = [keyword for keyword in interest_keywords if keyword in response_text]
        if interests:
            demographics["interests"] = interests

        return demographics

    async def _extract_brand_tone(self, response_text: str) -> str:
        """Extract brand tone from response."""
        tone_mapping = {
            "professional": ["professional", "business", "corporate", "formal", "serious"],
            "playful": ["playful", "fun", "energetic", "casual", "vibrant", "colorful"],
            "luxury": ["luxury", "premium", "high-end", "exclusive", "sophisticated", "elegant"],
            "minimalist": ["minimalist", "simple", "clean", "minimal", "understated"],
            "bold": ["bold", "strong", "dramatic", "striking", "powerful", "intense"],
            "friendly": ["friendly", "warm", "approachable", "welcoming", "kind", "caring"],
            "sophisticated": ["sophisticated", "refined", "cultured", "tasteful", "classy"]
        }

        for tone, keywords in tone_mapping.items():
            if any(keyword in response_text for keyword in keywords):
                return tone

        return "professional"  # Default tone

    async def _extract_tone_keywords(self, response_text: str) -> List[str]:
        """Extract tone-related keywords from response."""
        tone_keywords = [
            "professional", "playful", "luxury", "minimalist", "bold", "friendly",
            "sophisticated", "casual", "formal", "elegant", "modern", "traditional",
            "vibrant", "subtle", "energetic", "calm"
        ]

        found_keywords = [keyword for keyword in tone_keywords if keyword in response_text]
        return found_keywords

    async def _extract_call_to_action(self, response_text: str) -> Optional[str]:
        """Extract call-to-action from response."""
        cta_patterns = [
            r'(buy\s+now|shop\s+now|get\s+yours|order\s+today)',
            r'(learn\s+more|find\s+out|discover)',
            r'(sign\s+up|register|subscribe)',
            r'(contact\s+us|call\s+now|book\s+now)',
            r'(try\s+it|test\s+it|experience)'
        ]

        for pattern in cta_patterns:
            match = re.search(pattern, response_text, re.IGNORECASE)
            if match:
                return match.group(0)

        return None

    async def _extract_selling_points(self, response_text: str) -> List[str]:
        """Extract unique selling points from response."""
        selling_point_keywords = [
            "unique", "different", "special", "innovative", "exclusive", "premium",
            "quality", "best", "leading", "advanced", "superior", "excellent",
            "affordable", "cheap", "value", "efficient", "fast", "easy"
        ]

        words = response_text.split()
        selling_points = []

        for i, word in enumerate(words):
            if word in selling_point_keywords:
                # Include context around the keyword
                start = max(0, i-2)
                end = min(len(words), i+3)
                context = " ".join(words[start:end])
                selling_points.append(context)

        return selling_points

    async def _extract_keywords(self, response_text: str) -> List[str]:
        """Extract general keywords from response."""
        # Remove common stop words and extract meaningful terms
        stop_words = {
            "the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for",
            "of", "with", "by", "is", "are", "was", "were", "be", "been", "being",
            "have", "has", "had", "do", "does", "did", "will", "would", "should",
            "could", "may", "might", "must", "shall", "can", "this", "that",
            "these", "those", "i", "you", "he", "she", "it", "we", "they"
        }

        words = re.findall(r'\b\w+\b', response_text.lower())
        keywords = [word for word in words if word not in stop_words and len(word) > 2]

        # Return unique keywords, limited to top 10
        return list(dict.fromkeys(keywords))[:10]

    async def _process_fashion_response(self, question_id: str, response_text: str) -> Dict[str, Any]:
        """Process fashion-specific responses."""
        data = {}

        if question_id == "fashion_style":
            style_keywords = ["minimalist", "bohemian", "streetwear", "classic", "trendy", "vintage", "modern"]
            for keyword in style_keywords:
                if keyword in response_text:
                    data["style"] = keyword
                    break

        elif question_id == "fashion_occasion":
            occasion_keywords = ["everyday", "work", "casual", "formal", "party", "wedding", "summer", "winter"]
            occasions = [keyword for keyword in occasion_keywords if keyword in response_text]
            if occasions:
                data["occasions"] = occasions

        elif question_id == "fashion_demographics":
            data.update(await self._extract_demographics(response_text))

        return data

    async def _process_tech_response(self, question_id: str, response_text: str) -> Dict[str, Any]:
        """Process technology-specific responses."""
        data = {}

        if question_id == "tech_benefits":
            tech_keywords = ["performance", "speed", "efficiency", "innovation", "convenience", "reliability"]
            benefits = [keyword for keyword in tech_keywords if keyword in response_text]
            if benefits:
                data["tech_benefits"] = benefits

        elif question_id == "tech_audience":
            if "enthusiast" in response_text:
                data["tech_level"] = "enthusiast"
            elif "professional" in response_text:
                data["tech_level"] = "professional"
            else:
                data["tech_level"] = "general"

        return data

    async def _process_food_response(self, question_id: str, response_text: str) -> Dict[str, Any]:
        """Process food/beverage-specific responses."""
        data = {}

        if question_id == "food_occasion":
            meal_keywords = ["breakfast", "lunch", "dinner", "snack", "dessert", "drink"]
            occasions = [keyword for keyword in meal_keywords if keyword in response_text]
            if occasions:
                data["meal_occasions"] = occasions

        elif question_id == "food_appeal":
            appeal_keywords = ["taste", "health", "convenience", "tradition", "organic", "fresh"]
            appeals = [keyword for keyword in appeal_keywords if keyword in response_text]
            if appeals:
                data["food_appeals"] = appeals

        return data

    async def _process_beauty_response(self, question_id: str, response_text: str) -> Dict[str, Any]:
        """Process beauty/personal care-specific responses."""
        data = {}

        if question_id == "beauty_concerns":
            concern_keywords = ["anti-aging", "hydration", "acne", "glow", "sensitive", "oily", "dry"]
            concerns = [keyword for keyword in concern_keywords if keyword in response_text]
            if concerns:
                data["beauty_concerns"] = concerns

        return data

    async def _process_home_response(self, question_id: str, response_text: str) -> Dict[str, Any]:
        """Process home/garden-specific responses."""
        data = {}

        if question_id == "home_space":
            space_keywords = ["living room", "kitchen", "bedroom", "bathroom", "garden", "outdoor"]
            spaces = [keyword for keyword in space_keywords if keyword in response_text]
            if spaces:
                data["home_spaces"] = spaces

        return data

    async def _process_sports_response(self, question_id: str, response_text: str) -> Dict[str, Any]:
        """Process sports/outdoors-specific responses."""
        data = {}

        if question_id == "sports_activity":
            activity_keywords = ["running", "yoga", "hiking", "gym", "cycling", "swimming", "fitness"]
            activities = [keyword for keyword in activity_keywords if keyword in response_text]
            if activities:
                data["activities"] = activities

        return data

    async def _process_service_response(self, question_id: str, response_text: str) -> Dict[str, Any]:
        """Process service-specific responses."""
        data = {}

        if question_id == "service_clients":
            client_keywords = ["individual", "business", "enterprise", "small business", "startup"]
            clients = [keyword for keyword in client_keywords if keyword in response_text]
            if clients:
                data["client_types"] = clients

        return data