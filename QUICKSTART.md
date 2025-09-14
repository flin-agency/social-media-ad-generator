# 🚀 Quick Start Guide

Get your Social Media Ad Generator running in 3 minutes!

## 1. Prerequisites

- Python 3.8+
- Google Gemini API key ([Get one here](https://aistudio.google.com/apikey))

## 2. Installation

```bash
git clone git@github.com:flin-agency/social-media-ad-generator.git
cd social-media-ad-generator
pip install -r requirements.txt
```

## 3. Configuration

Set your Gemini API key:

**Option A: Environment Variable**
```bash
export GEMINI_API_KEY="your-api-key-here"
```

**Option B: .env File**
```bash
echo "GEMINI_API_KEY=your-api-key-here" > .env
```

## 4. Run the Application

```bash
python chat_server.py
```

Open http://localhost:8080 in your browser.

## 5. Generate Your First Ad

1. **Upload** your product image (JPG, PNG)
2. **Chat** with the AI agent about your product
3. **Answer** 2-3 questions about your target audience
4. **Download** 4 professional ad variations!

## 🎯 Example Workflow

```
🤖 Agent: "Hi! I can help create social media ads. Upload your product image to get started!"

📸 You: [Upload smartphone image]

🤖 Agent: "Great! I see this is a smartphone with advanced camera features.
         Who is your target audience?"

💬 You: "Tech enthusiasts and professionals aged 25-40"

🤖 Agent: "Perfect! What's your key message?"

💬 You: "Capture life in stunning detail"

🤖 Agent: "Generating your 4 ad variations... ⏱️ 30-60 seconds"

✨ Result: 4 professional ads ready for Instagram/TikTok Stories!
```

## 🔧 Troubleshooting

**Server won't start?**
- Check Python version: `python --version` (needs 3.8+)
- Install dependencies: `pip install -r requirements.txt`

**API errors?**
- Verify API key is set: `echo $GEMINI_API_KEY`
- Check key is valid at [Google AI Studio](https://aistudio.google.com/apikey)

**Need help?**
- Check the [README.md](README.md) for full documentation
- Review [planning.md](planning.md) for architecture details

---

🎨 **Ready to create amazing ads!** Start with any product image and let the AI do the work!