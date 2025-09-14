"""
Conversational Chat Agent for Social Media Ad Generation.

This module provides a chat-based interface where the agent dynamically
asks questions, analyzes responses, and guides users through the ad generation process.
"""

import asyncio
import logging
import uuid
import json
from typing import Dict, Any, List, Optional, Tuple
from datetime import datetime

from .agent import SocialMediaAdAgent
from .models import ProductCategory, BrandTone


class ConversationalAdAgent:
    """A conversational agent that guides users through ad generation via chat."""

    def __init__(self):
        """Initialize the conversational agent."""
        self.logger = logging.getLogger(__name__)
        self.core_agent = SocialMediaAdAgent()
        self.conversations: Dict[str, Dict[str, Any]] = {}

    async def start_conversation(self, conversation_id: str = None) -> Tuple[str, Dict[str, Any]]:
        """Start a new conversation."""
        if conversation_id is None:
            conversation_id = str(uuid.uuid4())

        # Initialize conversation state
        self.conversations[conversation_id] = {
            "id": conversation_id,
            "created_at": datetime.now(),
            "stage": "greeting",
            "session_id": None,
            "image_uploaded": False,
            "image_analysis": None,
            "conversation_history": [],
            "collected_info": {
                "target_audience": None,
                "brand_tone": None,
                "key_message": None,
                "additional_context": {}
            },
            "current_question": None,
            "questions_asked": 0,
            "max_questions": 3,
            "ready_for_generation": False
        }

        self.logger.info(f"Started conversation: {conversation_id}")

        # Send greeting message
        response = await self._generate_greeting()
        await self._add_to_history(conversation_id, "agent", response["message"])

        return conversation_id, response

    async def process_message(self, conversation_id: str, user_message: str,
                            image_data: Optional[bytes] = None,
                            image_filename: Optional[str] = None) -> Dict[str, Any]:
        """Process a user message and generate appropriate response."""
        if conversation_id not in self.conversations:
            return {"error": "Conversation not found. Please start a new conversation."}

        conv = self.conversations[conversation_id]
        await self._add_to_history(conversation_id, "user", user_message)

        try:
            # Handle image upload
            if image_data and not conv["image_uploaded"]:
                return await self._handle_image_upload(conversation_id, image_data, image_filename)

            # Process message based on current stage
            stage = conv["stage"]

            if stage == "greeting":
                return await self._handle_greeting_response(conversation_id, user_message)
            elif stage == "waiting_for_image":
                return await self._handle_waiting_for_image(conversation_id, user_message)
            elif stage == "analyzing_image":
                return await self._handle_image_analysis_complete(conversation_id)
            elif stage == "asking_questions":
                return await self._handle_question_response(conversation_id, user_message)
            elif stage == "ready_for_generation":
                return await self._handle_generation_request(conversation_id, user_message)
            elif stage == "generating":
                return await self._handle_generation_status(conversation_id)
            elif stage == "completed":
                return await self._handle_completion_chat(conversation_id, user_message)
            else:
                return await self._handle_unknown_stage(conversation_id, user_message)

        except Exception as e:
            self.logger.error(f"Error processing message: {str(e)}")
            response = {
                "message": "I'm sorry, I encountered an error processing your message. Could you please try again?",
                "stage": conv["stage"],
                "conversation_id": conversation_id,
                "error": str(e)
            }
            await self._add_to_history(conversation_id, "agent", response["message"])
            return response

    async def _generate_greeting(self) -> Dict[str, Any]:
        """Generate initial greeting message."""
        return {
            "message": "Hello! I'm your AI Social Media Ad Generator assistant. 🎨\n\n"
                      "I'll help you create 4 stunning social media advertisements from your product images! "
                      "These ads will be optimized for Instagram and TikTok Stories (9:16 format).\n\n"
                      "To get started, please upload a product image, and I'll analyze it and ask you a few "
                      "smart questions to create the perfect ads for your audience.\n\n"
                      "What product would you like to create ads for today?",
            "stage": "waiting_for_image",
            "actions": ["upload_image"],
            "examples": [
                "Fashion items (clothing, accessories)",
                "Electronics (phones, laptops, gadgets)",
                "Food & beverages",
                "Beauty products",
                "Home & garden items"
            ]
        }

    async def _handle_image_upload(self, conversation_id: str, image_data: bytes,
                                 image_filename: str) -> Dict[str, Any]:
        """Handle image upload and analysis."""
        conv = self.conversations[conversation_id]

        # Start core agent session
        session_id = await self.core_agent.start_session()
        conv["session_id"] = session_id
        conv["stage"] = "analyzing_image"

        try:
            # Save image permanently for ad generation
            import os
            import uuid

            # Create permanent uploads directory
            uploads_dir = "uploads"
            os.makedirs(uploads_dir, exist_ok=True)

            # Generate unique filename for the uploaded image
            file_extension = os.path.splitext(image_filename or 'image.jpg')[1]
            unique_filename = f"product_{conversation_id}_{uuid.uuid4().hex[:8]}{file_extension}"
            permanent_path = os.path.join(uploads_dir, unique_filename)

            # Save the image permanently
            with open(permanent_path, 'wb') as f:
                f.write(image_data)

            # Store the path in conversation state for ad generation
            conv["product_image_path"] = permanent_path

            result = await self.core_agent.upload_image(session_id, permanent_path)

            if not result["success"]:
                response = {
                    "message": f"I'm sorry, I had trouble analyzing your image: {result.get('error', 'Unknown error')}. "
                              "Could you try uploading a different image?",
                    "stage": "waiting_for_image",
                    "conversation_id": conversation_id
                }
                await self._add_to_history(conversation_id, "agent", response["message"])
                return response

            # Store analysis results
            conv["image_uploaded"] = True
            conv["image_analysis"] = result["analysis"]
            conv["stage"] = "asking_questions"

            # Generate contextual first question
            analysis = result["analysis"]
            category = analysis["category"]

            response = await self._generate_first_question(conversation_id, analysis)
            await self._add_to_history(conversation_id, "agent", response["message"])

            return response

        except Exception as e:
            self.logger.error(f"Image upload failed: {str(e)}")
            response = {
                "message": "I'm sorry, I couldn't process your image. Please make sure it's a valid image file "
                          "(JPEG, PNG, or WebP) under 10MB and try again.",
                "stage": "waiting_for_image",
                "conversation_id": conversation_id,
                "error": str(e)
            }
            await self._add_to_history(conversation_id, "agent", response["message"])
            return response

    async def _generate_first_question(self, conversation_id: str, analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate the first contextual question based on image analysis."""
        conv = self.conversations[conversation_id]
        category = analysis["category"]

        # Create personalized message based on analysis
        category_messages = {
            "ProductCategory.FASHION": "I can see this is a fashion item! It looks stylish with those colors.",
            "ProductCategory.ELECTRONICS": "I can see this is an electronic device! It looks sleek and modern.",
            "ProductCategory.FOOD_BEVERAGE": "I can see this is a food or beverage product! It looks appetizing.",
            "ProductCategory.BEAUTY_PERSONAL_CARE": "I can see this is a beauty product! It looks elegant and premium.",
            "ProductCategory.HOME_GARDEN": "I can see this is a home or garden item! It looks practical and stylish.",
            "ProductCategory.SPORTS_OUTDOORS": "I can see this is sports or outdoor equipment! It looks durable and functional."
        }

        category_msg = category_messages.get(category, "I've analyzed your product image!")

        # Generate first question based on category
        first_questions = {
            "ProductCategory.FASHION": "Who do you imagine wearing this? Are you targeting young trendsetters, working professionals, or perhaps a different style-conscious group?",
            "ProductCategory.ELECTRONICS": "Who's your ideal customer for this device? Tech enthusiasts who love the latest gadgets, or everyday users who value reliability and simplicity?",
            "ProductCategory.FOOD_BEVERAGE": "Who do you see enjoying this? Busy professionals looking for convenience, food lovers seeking premium quality, or health-conscious consumers?",
            "ProductCategory.BEAUTY_PERSONAL_CARE": "Who's your target customer? People focused on anti-aging, those who love trying new beauty trends, or perhaps those seeking natural/organic solutions?",
            "ProductCategory.HOME_GARDEN": "Who would be most interested in this? New homeowners setting up their space, design enthusiasts, or practical people looking for functional solutions?",
            "ProductCategory.SPORTS_OUTDOORS": "Who's your target market? Serious athletes training for performance, weekend warriors staying active, or outdoor adventure enthusiasts?"
        }

        question = first_questions.get(category, "Who is your ideal customer for this product?")

        # Store current question context
        conv["current_question"] = {
            "type": "target_audience",
            "question": question,
            "category_context": category
        }
        conv["questions_asked"] = 1

        quality_comment = ""
        if analysis.get("image_quality_score", 0) > 0.8:
            quality_comment = " The image quality looks great for ad creation!"

        message = f"Perfect! {category_msg}{quality_comment}\n\n{question}\n\n" \
                 "💡 The more specific you are, the better I can tailor your ads!"

        return {
            "message": message,
            "stage": "asking_questions",
            "conversation_id": conversation_id,
            "question_context": {
                "type": "target_audience",
                "category": category,
                "question_number": 1,
                "total_questions": conv["max_questions"]
            },
            "analysis_summary": {
                "category": category,
                "colors": analysis.get("dominant_colors", [])[:3],
                "quality": analysis.get("image_quality_score", 0)
            }
        }

    async def _handle_question_response(self, conversation_id: str, user_response: str) -> Dict[str, Any]:
        """Handle user's response to a question and generate follow-up."""
        conv = self.conversations[conversation_id]
        current_q = conv["current_question"]

        if not current_q:
            return {"error": "No active question found"}

        # Process the response
        await self._process_user_response(conversation_id, current_q, user_response)

        # Check if we need more questions
        if conv["questions_asked"] < conv["max_questions"]:
            return await self._generate_next_question(conversation_id)
        else:
            # Ready for generation
            conv["stage"] = "ready_for_generation"
            conv["ready_for_generation"] = True

            # Generate summary and ask for confirmation
            summary = await self._generate_info_summary(conversation_id)

            message = f"Perfect! I have everything I need to create your ads. Here's what I understand:\n\n" \
                     f"{summary}\n\n" \
                     f"I'm ready to generate 4 unique social media ad variations for you! " \
                     f"This will take about 30-60 seconds.\n\n" \
                     f"Should I start creating your ads now? 🎨"

            response = {
                "message": message,
                "stage": "ready_for_generation",
                "conversation_id": conversation_id,
                "actions": ["generate_ads", "modify_info"],
                "info_summary": summary
            }

            await self._add_to_history(conversation_id, "agent", message)
            return response

    async def _process_user_response(self, conversation_id: str, current_question: Dict[str, Any], response: str):
        """Process and store user's response to the current question."""
        conv = self.conversations[conversation_id]
        question_type = current_question["type"]

        # Use the core agent's question engine to process the response
        from .models import UserResponse

        user_resp = UserResponse(
            question_id=question_type,
            question_text=current_question["question"],
            response=response
        )

        processed = await self.core_agent.question_engine.process_response(user_resp)

        # Store processed information
        if question_type == "target_audience":
            conv["collected_info"]["target_audience"] = response
            if processed.get("demographics"):
                conv["collected_info"]["additional_context"]["demographics"] = processed["demographics"]

        elif question_type == "brand_tone":
            conv["collected_info"]["brand_tone"] = processed.get("brand_tone", "professional")
            if processed.get("tone_keywords"):
                conv["collected_info"]["additional_context"]["tone_keywords"] = processed["tone_keywords"]

        elif question_type == "key_message":
            conv["collected_info"]["key_message"] = response
            if processed.get("call_to_action"):
                conv["collected_info"]["additional_context"]["call_to_action"] = processed["call_to_action"]

    async def _generate_next_question(self, conversation_id: str) -> Dict[str, Any]:
        """Generate the next contextual question."""
        conv = self.conversations[conversation_id]
        question_num = conv["questions_asked"] + 1

        # Determine next question based on what we've collected and product category
        collected = conv["collected_info"]
        category = conv["image_analysis"]["category"]

        if question_num == 2:
            # Second question: Brand tone
            question = await self._generate_tone_question(category, collected)
            conv["current_question"] = {
                "type": "brand_tone",
                "question": question["question"],
                "category_context": category
            }

        elif question_num == 3:
            # Third question: Key message/CTA
            question = await self._generate_message_question(category, collected)
            conv["current_question"] = {
                "type": "key_message",
                "question": question["question"],
                "category_context": category
            }

        conv["questions_asked"] = question_num

        response = {
            "message": f"{question['message']}\n\n💡 {question['tip']}",
            "stage": "asking_questions",
            "conversation_id": conversation_id,
            "question_context": {
                "type": conv["current_question"]["type"],
                "category": category,
                "question_number": question_num,
                "total_questions": conv["max_questions"]
            }
        }

        await self._add_to_history(conversation_id, "agent", response["message"])
        return response

    async def _generate_tone_question(self, category: str, collected_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate brand tone question based on context."""
        audience = collected_info.get("target_audience", "your customers")

        tone_questions = {
            "ProductCategory.FASHION": {
                "question": f"What vibe should your fashion ads have for {audience}? Should they feel trendy and bold, elegant and sophisticated, or casual and approachable?",
                "message": f"Great! Now let's talk about the tone and feeling of your ads.",
                "tip": "The tone should match both your brand personality and what appeals to your target audience."
            },
            "ProductCategory.ELECTRONICS": {
                "question": f"How should your tech ads feel to {audience}? Professional and trustworthy, innovative and cutting-edge, or simple and user-friendly?",
                "message": f"Excellent! Now, what tone should your tech ads convey?",
                "tip": "Tech ads can emphasize reliability, innovation, or ease-of-use depending on your audience."
            },
            "ProductCategory.FOOD_BEVERAGE": {
                "question": f"What mood should your food ads create for {audience}? Indulgent and premium, healthy and fresh, or cozy and comforting?",
                "message": f"Perfect! Now let's determine the right mood for your food ads.",
                "tip": "Food ads work best when they evoke the right emotions and appetite appeal."
            }
        }

        return tone_questions.get(category, {
            "question": f"What tone should your ads have for {audience}? Professional, playful, luxury, or something else?",
            "message": "Great! Now let's talk about your brand tone.",
            "tip": "Your tone should reflect your brand personality and resonate with your target audience."
        })

    async def _generate_message_question(self, category: str, collected_info: Dict[str, Any]) -> Dict[str, Any]:
        """Generate key message question based on context."""
        audience = collected_info.get("target_audience", "your customers")
        tone = collected_info.get("brand_tone", "professional")

        message_questions = {
            "ProductCategory.FASHION": {
                "question": f"What's the key message you want {audience} to remember? Is it about style, quality, affordability, or a special offer? What should they do next?",
                "message": f"Almost done! What's the most important message for your fashion ads?",
                "tip": "Include your unique selling point and a clear call-to-action like 'Shop Now' or 'Get 20% Off'."
            },
            "ProductCategory.ELECTRONICS": {
                "question": f"What's the main benefit you want {audience} to know about? Superior performance, latest features, great value, or reliability? What action should they take?",
                "message": f"Last question! What's the key message for your tech ads?",
                "tip": "Focus on the problem you solve or the benefit you provide, with a clear next step."
            },
            "ProductCategory.FOOD_BEVERAGE": {
                "question": f"What should {audience} know most about your product? Amazing taste, health benefits, premium ingredients, or special pricing? What's your call-to-action?",
                "message": f"Final question! What's your main message for these food ads?",
                "tip": "Food ads work well with sensory language and urgency like 'Try Today' or 'Limited Time'."
            }
        }

        return message_questions.get(category, {
            "question": f"What's the most important message for {audience}? What makes your product special and what should they do next?",
            "message": "Final question! What's your key message?",
            "tip": "Combine your unique value proposition with a clear call-to-action."
        })

    async def _generate_info_summary(self, conversation_id: str) -> str:
        """Generate a summary of collected information."""
        conv = self.conversations[conversation_id]
        info = conv["collected_info"]
        analysis = conv["image_analysis"]

        category = analysis["category"].replace("ProductCategory.", "").replace("_", " ").title()
        colors = ", ".join(analysis.get("dominant_colors", [])[:3])

        summary = f"🎯 **Target Audience:** {info['target_audience']}\n" \
                 f"🎨 **Brand Tone:** {info['brand_tone']}\n" \
                 f"💬 **Key Message:** {info['key_message']}\n" \
                 f"📂 **Product Category:** {category}\n" \
                 f"🌈 **Main Colors:** {colors}"

        return summary

    async def _handle_generation_request(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle request to generate ads."""
        if "yes" in user_message.lower() or "generate" in user_message.lower() or "start" in user_message.lower() or "create" in user_message.lower():
            return await self._start_ad_generation(conversation_id)
        elif "no" in user_message.lower() or "modify" in user_message.lower() or "change" in user_message.lower():
            return await self._handle_modification_request(conversation_id, user_message)
        else:
            response = {
                "message": "Should I go ahead and generate your 4 ad variations now? Just say 'yes' to start, or 'modify' if you'd like to change any information.",
                "stage": "ready_for_generation",
                "conversation_id": conversation_id,
                "actions": ["generate_ads", "modify_info"]
            }
            await self._add_to_history(conversation_id, "agent", response["message"])
            return response

    async def _start_ad_generation(self, conversation_id: str) -> Dict[str, Any]:
        """Start the ad generation process."""
        conv = self.conversations[conversation_id]
        conv["stage"] = "generating"

        # Prepare responses for the core agent
        info = conv["collected_info"]

        answers = [
            {
                "question_id": "target_audience",
                "question_text": "Who is your target customer?",
                "response": info["target_audience"]
            },
            {
                "question_id": "brand_tone",
                "question_text": "What tone should your ad convey?",
                "response": info["brand_tone"]
            },
            {
                "question_id": "key_message",
                "question_text": "What's your main selling point?",
                "response": info["key_message"]
            }
        ]

        try:
            # Submit answers to core agent
            session_id = conv["session_id"]
            await self.core_agent.submit_answers(session_id, answers)

            # Start generation (this will run in background)
            asyncio.create_task(self._generate_ads_background(conversation_id))

            response = {
                "message": "🎨 Perfect! I'm now generating your 4 social media ad variations...\n\n"
                          "⏱️ This usually takes 30-60 seconds\n"
                          "🎯 Creating: Lifestyle, Product Hero, Benefit-Focused, and Social Proof styles\n"
                          "📱 Format: 9:16 vertical for Instagram/TikTok Stories\n\n"
                          "I'll let you know as soon as they're ready! ✨",
                "stage": "generating",
                "conversation_id": conversation_id,
                "generation_started": True
            }

            await self._add_to_history(conversation_id, "agent", response["message"])
            return response

        except Exception as e:
            self.logger.error(f"Failed to start generation: {str(e)}")
            conv["stage"] = "ready_for_generation"

            response = {
                "message": "I'm sorry, I encountered an issue starting the ad generation. Could you try again?",
                "stage": "ready_for_generation",
                "conversation_id": conversation_id,
                "error": str(e)
            }
            await self._add_to_history(conversation_id, "agent", response["message"])
            return response

    async def _generate_ads_background(self, conversation_id: str):
        """Generate ads in background and update conversation when complete."""
        conv = self.conversations[conversation_id]

        try:
            session_id = conv["session_id"]
            result = await self.core_agent.generate_ads(session_id)

            if result["success"]:
                conv["stage"] = "completed"
                conv["generation_result"] = result["result"]

                # The main chat loop will pick this up when the user next sends a message
                # or we could implement WebSocket for real-time updates

        except Exception as e:
            self.logger.error(f"Background generation failed: {str(e)}")
            conv["stage"] = "generation_failed"
            conv["generation_error"] = str(e)

    async def _handle_completion_chat(self, conversation_id: str, user_message: str) -> Dict[str, Any]:
        """Handle chat after ads are generated."""
        conv = self.conversations[conversation_id]

        if "generation_result" not in conv:
            # Check if generation completed
            if conv["stage"] == "completed":
                return await self._present_results(conversation_id)
            elif conv["stage"] == "generation_failed":
                error = conv.get("generation_error", "Unknown error")
                response = {
                    "message": f"I'm sorry, the ad generation failed: {error}\n\nWould you like to try again?",
                    "stage": "ready_for_generation",
                    "conversation_id": conversation_id
                }
                conv["stage"] = "ready_for_generation"
                await self._add_to_history(conversation_id, "agent", response["message"])
                return response
            else:
                # Still generating
                response = {
                    "message": "🎨 Your ads are still being generated... Please wait a moment longer!",
                    "stage": "generating",
                    "conversation_id": conversation_id
                }
                await self._add_to_history(conversation_id, "agent", response["message"])
                return response

        # Results are ready - present them
        return await self._present_results(conversation_id)

    async def _present_results(self, conversation_id: str) -> Dict[str, Any]:
        """Present the generated ad results."""
        conv = self.conversations[conversation_id]
        result = conv["generation_result"]

        ads = result["ads"]
        generation_time = result["total_generation_time_seconds"]

        message = f"🎉 Amazing! Your 4 social media ads are ready! Generated in {generation_time:.1f} seconds.\n\n"

        for i, ad in enumerate(ads, 1):
            variation_name = ad["variation_type"].replace("_", " ").title()
            message += f"**{i}. {variation_name} Ad** - {ad['generation_time_seconds']:.1f}s\n"

        message += f"\n📱 All ads are optimized for Instagram/TikTok Stories (9:16 format)\n" \
                  f"💾 Ready for download and immediate use!\n\n" \
                  f"Would you like to:\n" \
                  f"• Create ads for another product? 🔄\n" \
                  f"• Ask about ad customization? ✏️\n" \
                  f"• Get tips for using these ads? 💡"

        response = {
            "message": message,
            "stage": "completed",
            "conversation_id": conversation_id,
            "ads": ads,
            "generation_time": generation_time,
            "actions": ["new_product", "customize", "tips", "download"]
        }

        await self._add_to_history(conversation_id, "agent", message)
        return response

    async def _add_to_history(self, conversation_id: str, role: str, message: str):
        """Add message to conversation history."""
        if conversation_id in self.conversations:
            self.conversations[conversation_id]["conversation_history"].append({
                "role": role,
                "message": message,
                "timestamp": datetime.now().isoformat()
            })

    async def get_conversation_history(self, conversation_id: str) -> List[Dict[str, Any]]:
        """Get conversation history."""
        if conversation_id not in self.conversations:
            return []
        return self.conversations[conversation_id]["conversation_history"]

    async def get_conversation_status(self, conversation_id: str) -> Dict[str, Any]:
        """Get current conversation status."""
        if conversation_id not in self.conversations:
            return {"error": "Conversation not found"}

        conv = self.conversations[conversation_id]

        # Check if generation completed in background
        if conv["stage"] == "generating" and "generation_result" in conv:
            conv["stage"] = "completed"

        return {
            "conversation_id": conversation_id,
            "stage": conv["stage"],
            "questions_asked": conv["questions_asked"],
            "ready_for_generation": conv.get("ready_for_generation", False),
            "image_uploaded": conv["image_uploaded"],
            "generation_complete": "generation_result" in conv,
            "created_at": conv["created_at"].isoformat()
        }

    # Placeholder methods for other handlers
    async def _handle_greeting_response(self, conversation_id: str, user_message: str):
        conv = self.conversations[conversation_id]
        conv["stage"] = "waiting_for_image"
        response = {
            "message": "Great! Please upload your product image and I'll analyze it to create the perfect ads for you. 📸",
            "stage": "waiting_for_image",
            "conversation_id": conversation_id,
            "actions": ["upload_image"]
        }
        await self._add_to_history(conversation_id, "agent", response["message"])
        return response

    async def _handle_waiting_for_image(self, conversation_id: str, user_message: str):
        response = {
            "message": "I'm ready for your product image! Please upload it and I'll get started with the analysis. 📸✨",
            "stage": "waiting_for_image",
            "conversation_id": conversation_id,
            "actions": ["upload_image"]
        }
        await self._add_to_history(conversation_id, "agent", response["message"])
        return response

    async def _handle_image_analysis_complete(self, conversation_id: str):
        # This should already be handled in _handle_image_upload
        return {"message": "Analysis complete!", "stage": "asking_questions", "conversation_id": conversation_id}

    async def _handle_generation_status(self, conversation_id: str):
        response = {
            "message": "🎨 Still working on your ads... Almost there! ⏱️",
            "stage": "generating",
            "conversation_id": conversation_id
        }
        await self._add_to_history(conversation_id, "agent", response["message"])
        return response

    async def _handle_unknown_stage(self, conversation_id: str, user_message: str):
        response = {
            "message": "I'm not sure how to help with that right now. Would you like to start over with a new product image?",
            "stage": "waiting_for_image",
            "conversation_id": conversation_id
        }
        await self._add_to_history(conversation_id, "agent", response["message"])
        return response

    async def _handle_modification_request(self, conversation_id: str, user_message: str):
        response = {
            "message": "What would you like to modify? I can adjust your target audience, brand tone, or key message.",
            "stage": "ready_for_generation",
            "conversation_id": conversation_id,
            "actions": ["modify_audience", "modify_tone", "modify_message"]
        }
        await self._add_to_history(conversation_id, "agent", response["message"])
        return response