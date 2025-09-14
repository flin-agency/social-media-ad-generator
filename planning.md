# Social Media Ad Generator Agent - Planning Document

## Project Overview
Create an intelligent agent using Google's Agent Development Kit (ADK) that transforms product images into compelling social media advertisements with 9:16 aspect ratio.

## Agent Workflow

### 1. Image Upload & Analysis
- **Input**: Product image from user
- **Process**: Analyze product characteristics, style, colors, and category
- **Tools**: Image analysis capabilities, product classification

### 2. Interactive Questioning (2-3 Questions)
- **Target Audience**: "Who is your target customer? (e.g., age group, interests)"
- **Brand Tone**: "What tone should the ad convey? (e.g., professional, playful, luxury)"
- **Key Message**: "What's the main selling point or call-to-action?"

### 3. Ad Generation
- **Output**: 4 unique social media ads in 9:16 format
- **Variations**: Different styles, copy approaches, and visual compositions
- **Model**: Gemini 2.5 Flash Image Preview

## Technical Architecture

### ADK Agent Structure
```
SocialMediaAdAgent/
├── agent.py              # Main agent orchestration
├── tools/
│   ├── image_analyzer.py  # Product image analysis
│   ├── question_engine.py # Interactive questioning logic
│   └── ad_generator.py    # Image generation with Gemini API
└── prompts/
    ├── analysis_prompts.py
    ├── question_templates.py
    └── ad_generation_prompts.py
```

### Core Components

#### 1. Image Analysis Tool
- Extract product features, colors, style
- Identify product category and context
- Generate initial creative brief

#### 2. Question Engine
- Dynamic question generation based on product analysis
- Conversation flow management
- Response validation and processing

#### 3. Ad Generation Tool
- Gemini API integration for text-to-image
- 9:16 aspect ratio enforcement
- Style variation logic for 4 different approaches

## Prompt Engineering Strategy

### Image Generation Prompts Template
```
A vertical 9:16 social media advertisement image of [PRODUCT],
featuring [PRODUCT_FEATURES], designed for [TARGET_AUDIENCE].
The ad should convey a [BRAND_TONE] tone with [KEY_MESSAGE].
Style: [VARIATION_STYLE], with professional lighting and
composition optimized for Instagram/TikTok stories.
```

### Ad Variations
1. **Lifestyle Context**: Product in real-world usage
2. **Clean Product Focus**: Minimal background, product hero shot
3. **Benefit-Driven**: Visual representation of product benefits
4. **Social Proof**: Testimonial or review integration style

## Implementation Plan

### Phase 1: Core Agent Setup
- Initialize ADK agent framework
- Implement basic image upload handling
- Create product analysis pipeline

### Phase 2: Question System
- Design adaptive questioning logic
- Implement conversation state management
- Create response processing system

### Phase 3: Generation Engine
- Integrate Gemini image generation API
- Implement 4-variation generation logic
- Add 9:16 aspect ratio optimization

### Phase 4: Testing & Refinement
- Test with various product categories
- Optimize prompt engineering
- Refine question effectiveness

## Technical Requirements

### Dependencies
- `google-adk` - Agent Development Kit
- `google-generativeai` - Gemini API access
- `PIL/Pillow` - Image processing
- `asyncio` - Async operations for parallel generation

### API Configuration
- Gemini 2.5 Flash Image Preview model
- Image generation endpoint configuration
- Token management for cost optimization

### Input/Output Specifications
- **Input**: Image file (JPEG, PNG, WebP)
- **Output**: 4 images in 9:16 ratio (1080x1920 recommended)
- **Format**: High-quality social media ready files

## Success Metrics
- Generation time < 60 seconds for all 4 ads
- User satisfaction with question relevance
- Ad quality suitable for immediate social media use
- Cost efficiency per generation cycle

## Deployment Strategy
- Local development and testing
- Cloud deployment via Vertex AI Agent Engine
- API endpoint for integration with web/mobile apps