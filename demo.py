#!/usr/bin/env python3
"""
Demo script for Social Media Ad Generator

Usage:
    python demo.py [image_path]

If no image_path is provided, instructions will be shown for getting sample images.
"""

import sys
import os
import asyncio
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger(__name__)

async def demo_workflow(image_path: str = None):
    """Demonstrate the complete ad generation workflow."""

    print("🎨 Social Media Ad Generator Demo")
    print("=" * 50)

    if image_path is None:
        print("📸 No image provided!")
        print("\n📋 To run the demo:")
        print("1. Find a product image (JPG, PNG)")
        print("2. Run: python demo.py /path/to/your/product/image.jpg")
        print("\n🌐 Or start the web interface:")
        print("   python chat_server.py")
        print("   Then open http://localhost:8080")
        return

    if not os.path.exists(image_path):
        print(f"❌ Image not found: {image_path}")
        return

    print(f"📸 Using image: {image_path}")
    print("\n🤖 Initializing AI agent...")

    try:
        from src.social_media_ad_generator.agent import SocialMediaAdAgent

        # Create agent
        agent = SocialMediaAdAgent()

        print("✅ Agent initialized successfully!")
        print("\n🎯 Demo workflow:")
        print("1. Upload and analyze your product image")
        print("2. Answer 2-3 questions about your target audience")
        print("3. Generate 4 professional ad variations")
        print("4. Download your ads!")

        print(f"\n🚀 Start the web interface with:")
        print(f"   python chat_server.py")
        print(f"   Open http://localhost:8080")
        print(f"   Upload: {image_path}")

    except Exception as e:
        logger.error(f"Demo failed: {str(e)}")
        print(f"\n❌ Error: {str(e)}")
        print("\n🔧 Make sure you have:")
        print("1. Installed dependencies: pip install -r requirements.txt")
        print("2. Set your Gemini API key: export GEMINI_API_KEY='your-key'")

if __name__ == "__main__":
    image_path = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        asyncio.run(demo_workflow(image_path))
    except KeyboardInterrupt:
        print("\n👋 Demo cancelled by user")
    except Exception as e:
        logger.error(f"Demo error: {str(e)}")