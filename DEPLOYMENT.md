# 🚀 Deployment Guide

Instructions for deploying the Social Media Ad Generator to GitHub.

## 📋 Pre-Deployment Checklist

- ✅ Production folder created without tests
- ✅ Documentation updated (README, QUICKSTART)
- ✅ Correct GitHub repository URL configured
- ✅ Google AI Studio API key instructions updated
- ✅ All dependencies in requirements.txt
- ✅ License and .gitignore files included

## 🔧 GitHub Setup

### 1. Initialize Git Repository

```bash
cd social-media-ad-generator
git init
git add .
git commit -m "Initial release: AI-powered Social Media Ad Generator

🎨 Features:
- Conversational AI agent with Google Gemini 2.5 Flash
- Upload product images and get 4 professional ad variations
- Perfect 9:16 format for Instagram/TikTok Stories
- Real image-to-image generation using uploaded products
- Smart contextual questions based on product category
- FastAPI web interface with real-time progress
- Complete ADK (Agent Development Kit) integration

🚀 Ready for production use!"
```

### 2. Connect to Flin Agency Repository

```bash
git remote add origin git@github.com:flin-agency/social-media-ad-generator.git
git branch -M main
git push -u origin main
```

### 3. Verify Deployment

Visit: https://github.com/flin-agency/social-media-ad-generator

## 🔑 API Key Setup for Users

Users need to:

1. **Get Gemini API Key**: https://aistudio.google.com/apikey
2. **Set Environment Variable**:
   ```bash
   export GEMINI_API_KEY="their-key-here"
   ```
3. **Or create .env file**:
   ```bash
   echo "GEMINI_API_KEY=their-key-here" > .env
   ```

## 🌐 Repository Structure

```
social-media-ad-generator/
├── README.md                    # Main documentation
├── QUICKSTART.md               # 3-minute setup guide
├── DEPLOYMENT.md               # This file
├── LICENSE                     # MIT license
├── .gitignore                  # Python/AI project gitignore
├── requirements.txt            # Dependencies
├── chat_server.py              # Main FastAPI server
├── adk_server.py              # ADK integration
├── demo.py                     # Simple demo script
├── planning.md                 # Architecture planning
├── PRD.md                      # Product requirements
└── src/social_media_ad_generator/  # Core application code
```

## ✅ Post-Deployment

After successful deployment:

1. **Test clone and setup**:
   ```bash
   git clone git@github.com:flin-agency/social-media-ad-generator.git
   cd social-media-ad-generator
   pip install -r requirements.txt
   python demo.py  # Should show setup instructions
   ```

2. **Update repository settings**:
   - Add description: "🎨 AI-powered social media ad generator using Google Gemini"
   - Add topics: `ai`, `gemini`, `social-media`, `ad-generator`, `fastapi`, `python`
   - Enable Issues and Discussions

3. **Create release**:
   - Tag: `v1.0.0`
   - Title: "🎨 Initial Release: Social Media Ad Generator"
   - Include features list and setup instructions

## 🎯 Success Criteria

- ✅ Repository accessible at `git@github.com:flin-agency/social-media-ad-generator.git`
- ✅ Users can clone and run in 3 minutes with API key
- ✅ All documentation links work correctly
- ✅ Demo script provides helpful instructions
- ✅ Production-ready code with no test files

---

🎉 **Ready for the world!** Your AI agent is now available for anyone to use.