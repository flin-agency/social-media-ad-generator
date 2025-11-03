"""Main Social Media Ad Generator Agent using Google ADK."""

import asyncio
import logging
import uuid
from typing import Any, Dict, List, Optional, cast
from datetime import datetime

# Note: google-adk might not be available yet, so we'll create a mock structure
# that can be easily replaced when the actual ADK becomes available

from .models import (
    AdGenerationRequest,
    AdGenerationResult,
    BrandTone,
    ImageAnalysis,
    ProductCategory,
    UserResponse,
)
from .tools import (
    AdGenerator,
    ImageAnalyzer,
    QuestionEngine,
    ToolManager,
    ToolSpec,
    ToolOutput,
)
from .config import config


class SocialMediaAdAgent:
    """Main agent class for generating social media ads."""

    def __init__(self, tool_manager: Optional[ToolManager] = None):
        """Initialize the agent with tools."""

        self.logger = logging.getLogger(__name__)
        self.tool_manager = tool_manager or ToolManager.default()
        self.image_analyzer = cast(ImageAnalyzer, self.tool_manager.get("image_analyzer"))
        self.question_engine = cast(QuestionEngine, self.tool_manager.get("question_engine"))
        self.ad_generator = cast(AdGenerator, self.tool_manager.get("ad_generator"))
        self.sessions: Dict[str, Dict[str, Any]] = {}

    async def start_session(self, session_id: str = None) -> str:
        """Start a new agent session."""
        if session_id is None:
            session_id = str(uuid.uuid4())

        self.sessions[session_id] = {
            "created_at": datetime.now(),
            "stage": "upload",
            "image_analysis": None,
            "questions": [],
            "responses": [],
            "generation_result": None
        }

        self.logger.info(f"Started new session: {session_id}")
        return session_id

    async def upload_image(self, session_id: str, image_path: str) -> Dict[str, Any]:
        """Process uploaded image and analyze it."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        if session["stage"] != "upload":
            raise ValueError(f"Session {session_id} is not in upload stage")

        try:
            # Analyze the uploaded image
            analysis = await self.image_analyzer.analyze_image(image_path)
            session["image_analysis"] = analysis
            session["product_image_path"] = image_path  # Store path for ad generation
            session["stage"] = "questions"

            # Generate questions based on analysis
            questions = await self.question_engine.generate_questions(analysis)
            session["questions"] = questions

            self.logger.info(f"Image analyzed for session {session_id}")

            return {
                "success": True,
                "analysis": analysis.model_dump(),
                "questions": [q.model_dump() for q in questions],
                "next_stage": "questions"
            }

        except Exception as e:
            self.logger.error(f"Error analyzing image for session {session_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def submit_answers(self, session_id: str, answers: List[Dict[str, str]]) -> Dict[str, Any]:
        """Submit answers to questions."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        if session["stage"] != "questions":
            raise ValueError(f"Session {session_id} is not in questions stage")

        try:
            # Process user responses
            responses = []
            for answer in answers:
                response = UserResponse(
                    question_id=answer["question_id"],
                    question_text=answer["question_text"],
                    response=answer["response"]
                )
                processed = await self.question_engine.process_response(response)
                response.processed_response = processed
                responses.append(response)

            session["responses"] = responses
            session["stage"] = "generation"

            self.logger.info(f"Answers submitted for session {session_id}")

            return {
                "success": True,
                "processed_responses": [r.model_dump() for r in responses],
                "next_stage": "generation"
            }

        except Exception as e:
            self.logger.error(f"Error processing answers for session {session_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def generate_ads(self, session_id: str) -> Dict[str, Any]:
        """Generate social media ads based on analysis and responses."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        if session["stage"] != "generation":
            raise ValueError(f"Session {session_id} is not in generation stage")

        if not session["image_analysis"] or not session["responses"]:
            raise ValueError("Missing image analysis or responses")

        try:
            # Extract key information from responses
            target_audience = ""
            brand_tone = BrandTone.PROFESSIONAL
            key_message = ""

            for response in session["responses"]:
                if response.processed_response:
                    if "target_audience" in response.processed_response:
                        target_audience = response.processed_response["target_audience"]
                    if "brand_tone" in response.processed_response:
                        brand_tone = BrandTone(response.processed_response["brand_tone"])
                    if "key_message" in response.processed_response:
                        key_message = response.processed_response["key_message"]

            # Create generation request
            generation_request = AdGenerationRequest(
                image_analysis=session["image_analysis"],
                user_responses=session["responses"],
                target_audience=target_audience,
                brand_tone=brand_tone,
                key_message=key_message,
                product_image_path=session.get("product_image_path")
            )

            # Generate ads
            result = await self.ad_generator.generate_ads(generation_request)
            session["generation_result"] = result
            session["stage"] = "completed"

            self.logger.info(f"Ads generated for session {session_id}")

            return {
                "success": True,
                "result": result.model_dump(),
                "next_stage": "completed"
            }

        except Exception as e:
            self.logger.error(f"Error generating ads for session {session_id}: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    async def get_session_status(self, session_id: str) -> Dict[str, Any]:
        """Get current session status."""
        if session_id not in self.sessions:
            raise ValueError(f"Session {session_id} not found")

        session = self.sessions[session_id]
        return {
            "session_id": session_id,
            "stage": session["stage"],
            "created_at": session["created_at"].isoformat(),
            "has_analysis": session["image_analysis"] is not None,
            "questions_count": len(session["questions"]),
            "responses_count": len(session["responses"]),
            "generation_complete": session["generation_result"] is not None
        }

    def get_tool_specs(self) -> List[ToolSpec]:
        """Expose tool specifications for external agent frameworks."""

        return self.tool_manager.specs()

    async def invoke_tool(self, tool_name: str, **kwargs: Any) -> ToolOutput:
        """Invoke a registered tool directly via the tool manager."""

        return await self.tool_manager.ainvoke(tool_name, **kwargs)

    def cleanup_session(self, session_id: str) -> bool:
        """Clean up session data."""
        if session_id in self.sessions:
            del self.sessions[session_id]
            self.logger.info(f"Cleaned up session: {session_id}")
            return True
        return False