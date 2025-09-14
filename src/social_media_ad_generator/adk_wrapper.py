"""ADK wrapper for Social Media Ad Generator Agent."""

import asyncio
import logging
import os
from typing import Dict, Any, Optional, List
from pathlib import Path

# Import the main agent
from .agent import SocialMediaAdAgent


class SocialMediaAdAgentWrapper:
    """ADK wrapper for the Social Media Ad Generator Agent."""

    def __init__(self):
        """Initialize the ADK wrapper."""
        self.logger = logging.getLogger(__name__)
        self.agent = SocialMediaAdAgent()
        self.current_session: Optional[str] = None

    async def initialize(self) -> Dict[str, Any]:
        """Initialize the agent for ADK."""
        self.logger.info("Initializing Social Media Ad Generator Agent for ADK")

        return {
            "status": "ready",
            "capabilities": [
                "image_analysis",
                "question_generation",
                "ad_generation",
                "multi_format_support"
            ],
            "supported_categories": [
                "fashion", "electronics", "food_beverage",
                "beauty_personal_care", "home_garden", "sports_outdoors",
                "automotive", "books_media", "toys_games", "services"
            ],
            "output_formats": ["9:16 vertical ads for Instagram/TikTok Stories"]
        }

    async def process_image(self, image_path: str) -> Dict[str, Any]:
        """Process uploaded image and start new session."""
        try:
            # Start new session
            self.current_session = await self.agent.start_session()

            # Upload and analyze image
            result = await self.agent.upload_image(self.current_session, image_path)

            if result["success"]:
                return {
                    "session_id": self.current_session,
                    "stage": "questions",
                    "analysis": result["analysis"],
                    "questions": result["questions"],
                    "message": f"Image analyzed successfully! Category: {result['analysis']['category']}"
                }
            else:
                return {
                    "error": result.get("error", "Image processing failed"),
                    "stage": "error"
                }

        except Exception as e:
            self.logger.error(f"Image processing failed: {str(e)}")
            return {
                "error": f"Image processing failed: {str(e)}",
                "stage": "error"
            }

    async def submit_answers(self, answers: List[Dict[str, str]]) -> Dict[str, Any]:
        """Submit user answers to questions."""
        if not self.current_session:
            return {"error": "No active session. Please upload an image first."}

        try:
            result = await self.agent.submit_answers(self.current_session, answers)

            if result["success"]:
                return {
                    "session_id": self.current_session,
                    "stage": "ready_for_generation",
                    "processed_responses": result["processed_responses"],
                    "message": "Answers processed successfully! Ready to generate ads."
                }
            else:
                return {
                    "error": result.get("error", "Answer processing failed"),
                    "stage": "error"
                }

        except Exception as e:
            self.logger.error(f"Answer processing failed: {str(e)}")
            return {
                "error": f"Answer processing failed: {str(e)}",
                "stage": "error"
            }

    async def generate_ads(self) -> Dict[str, Any]:
        """Generate social media ad variations."""
        if not self.current_session:
            return {"error": "No active session. Please upload an image first."}

        try:
            result = await self.agent.generate_ads(self.current_session)

            if result["success"]:
                ads_data = result["result"]
                return {
                    "session_id": self.current_session,
                    "stage": "completed",
                    "ads": ads_data["ads"],
                    "generation_time": ads_data["total_generation_time_seconds"],
                    "message": f"Successfully generated {len(ads_data['ads'])} ad variations!"
                }
            else:
                return {
                    "error": result.get("error", "Ad generation failed"),
                    "stage": "error"
                }

        except Exception as e:
            self.logger.error(f"Ad generation failed: {str(e)}")
            return {
                "error": f"Ad generation failed: {str(e)}",
                "stage": "error"
            }

    async def get_session_status(self) -> Dict[str, Any]:
        """Get current session status."""
        if not self.current_session:
            return {
                "stage": "no_session",
                "message": "No active session"
            }

        try:
            status = await self.agent.get_session_status(self.current_session)
            return status
        except Exception as e:
            self.logger.error(f"Failed to get session status: {str(e)}")
            return {
                "error": f"Failed to get session status: {str(e)}",
                "stage": "error"
            }

    async def reset_session(self) -> Dict[str, Any]:
        """Reset current session."""
        if self.current_session:
            self.agent.cleanup_session(self.current_session)
            self.current_session = None

        return {
            "stage": "reset",
            "message": "Session reset successfully"
        }

    async def execute(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Main execution method for ADK."""
        action = input_data.get("action", "process_image")

        try:
            if action == "initialize":
                return await self.initialize()

            elif action == "process_image":
                image_path = input_data.get("image_path")
                if not image_path:
                    return {"error": "image_path is required"}
                return await self.process_image(image_path)

            elif action == "submit_answers":
                answers = input_data.get("answers", [])
                return await self.submit_answers(answers)

            elif action == "generate_ads":
                return await self.generate_ads()

            elif action == "get_status":
                return await self.get_session_status()

            elif action == "reset":
                return await self.reset_session()

            else:
                return {"error": f"Unknown action: {action}"}

        except Exception as e:
            self.logger.error(f"Execution failed: {str(e)}")
            return {
                "error": f"Execution failed: {str(e)}",
                "stage": "error"
            }


# ADK entry point
async def create_agent() -> SocialMediaAdAgentWrapper:
    """Create and initialize the agent for ADK."""
    agent = SocialMediaAdAgentWrapper()
    await agent.initialize()
    return agent