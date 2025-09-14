# 🎨 Social Media Ad Generator

An intelligent AI agent that transforms product images into professional social media advertisements using Google's Gemini API and Agent Development Kit (ADK).

![Demo](https://via.placeholder.com/800x400/4285f4/ffffff?text=Social+Media+Ad+Generator)

## ✨ Features

- 🤖 **Conversational AI Agent** - Chat-based interface with dynamic questioning
- 📸 **Product Image Analysis** - Automatic categorization and feature extraction
- 🎯 **4 Ad Variations** - Lifestyle, Product Hero, Benefit-Focused, and Social Proof styles
- 📱 **Perfect Format** - 9:16 aspect ratio optimized for Instagram/TikTok Stories
- 🌟 **Real AI Generation** - Powered by Google Gemini 2.5 Flash Image Preview
- 💬 **Smart Questions** - Context-aware follow-up questions based on product category
- 🎨 **Professional Quality** - High-resolution ads with your actual product images
- ⚡ **Fast Generation** - ~30-60 seconds for all 4 variations
- 🔗 **Easy Download** - Direct download links and web preview

## 🚀 Quick Start

### 1. Installation

```bash
git clone git@github.com:flin-agency/social-media-ad-generator.git
cd social-media-ad-generator
pip install -r requirements.txt
```

### 2. Configuration

Get your Google Gemini API key from [Google AI Studio](https://aistudio.google.com/apikey) and set it:

```bash
export GEMINI_API_KEY="your-api-key-here"
```

Or create a `.env` file:
```
GEMINI_API_KEY=your-api-key-here
```

### 3. Run the Application

**Option A: Chat Interface (Recommended)**
```bash
python chat_server.py
```
Then open http://localhost:8080 in your browser.

**Option B: ADK Server**
```bash
python adk_server.py
```

## 🎯 How It Works

1. **Upload Product Image** - Drop your product photo
2. **AI Analysis** - Automatic category detection and feature extraction
3. **Smart Questions** - 2-3 contextual questions about your target audience and brand
4. **Ad Generation** - Creates 4 professional ad variations using your product
5. **Download & Use** - Get your ads ready for social media

## 🏗️ Architecture

```
social-media-ad-generator/
├── src/social_media_ad_generator/
│   ├── agent.py              # Core agent orchestration
│   ├── chat_agent.py         # Conversational interface
│   ├── models/               # Pydantic data models
│   ├── tools/
│   │   ├── ad_generator.py   # Gemini API integration
│   │   ├── image_analyzer.py # Product analysis
│   │   └── question_engine.py # Dynamic questions
│   └── prompts/              # AI prompt templates
├── chat_server.py            # FastAPI web server
├── adk_server.py            # ADK integration server
└── requirements.txt         # Dependencies
```

## 🛠️ Technology Stack

- **AI/ML**: Google Gemini 2.5 Flash Image Preview API
- **Framework**: Google Agent Development Kit (ADK)
- **Backend**: FastAPI, asyncio
- **Frontend**: HTML5, CSS3, JavaScript
- **Image Processing**: PIL/Pillow
- **Data Validation**: Pydantic v2

## 📋 API Endpoints

**Chat Interface:**
- `GET /` - Web interface
- `POST /start-conversation` - Initialize chat session
- `POST /upload-image-chat` - Upload product image
- `POST /chat` - Send message to agent
- `GET /conversation/{id}/status` - Check generation status

**File Management:**
- `GET /view-ad/{filename}` - View generated ad
- `GET /download-ad/{filename}` - Download ad image

## 🎨 Ad Variations Generated

1. **Lifestyle** - Product in real-world usage scenarios
2. **Product Hero** - Clean, professional product shots
3. **Benefit-Focused** - Before/after or feature comparisons
4. **Social Proof** - Testimonials and review-style layouts

## ⚙️ Configuration

Key settings in `src/social_media_ad_generator/config.py`:

```python
class Config(BaseSettings):
    gemini_api_key: str = ""
    concurrent_generations: int = 4
    output_width_height: Tuple[int, int] = (576, 1024)  # 9:16 ratio
    max_file_size_mb: float = 10.0
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🔗 Links

- [Google Gemini API Documentation](https://ai.google.dev/gemini-api/docs)
- [Agent Development Kit](https://developers.google.com/agent-development-kit)
- [Project Planning](planning.md)
- [Product Requirements](PRD.md)

## 🙏 Acknowledgments

- Google for the Gemini 2.5 Flash Image Preview API
- The Agent Development Kit team
- FastAPI and Pydantic communities

---

Made with ❤️ using Google's Gemini AI and Agent Development Kit