#!/usr/bin/env python3
"""
Alternative ADK server implementation using FastAPI.
This provides a web API interface for the Social Media Ad Generator Agent.
"""

import asyncio
import sys
import os
import tempfile
import shutil
from pathlib import Path
from typing import Dict, Any, List
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from social_media_ad_generator.adk_wrapper import SocialMediaAdAgentWrapper


# Pydantic models for API
class AnswerModel(BaseModel):
    question_id: str
    question_text: str
    response: str


class AnswersRequest(BaseModel):
    answers: List[AnswerModel]


# Create FastAPI app
app = FastAPI(
    title="Social Media Ad Generator",
    description="AI-powered agent that transforms product images into professional social media advertisements",
    version="1.0.0"
)

# Global agent instance
agent_wrapper = None


@app.on_event("startup")
async def startup_event():
    """Initialize the agent on startup."""
    global agent_wrapper
    agent_wrapper = SocialMediaAdAgentWrapper()
    await agent_wrapper.initialize()
    print("✅ Social Media Ad Generator Agent initialized")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the main web interface."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>Social Media Ad Generator</title>
    <style>
        body { font-family: Arial, sans-serif; max-width: 800px; margin: 0 auto; padding: 20px; }
        .container { background: #f5f5f5; padding: 20px; border-radius: 10px; margin: 20px 0; }
        .upload-area { border: 2px dashed #ccc; padding: 40px; text-align: center; border-radius: 10px; }
        .upload-area.dragover { border-color: #007bff; background: #f0f8ff; }
        button { background: #007bff; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #0056b3; }
        .question { margin: 15px 0; padding: 10px; background: white; border-radius: 5px; }
        .ad-result { margin: 15px 0; padding: 15px; background: white; border-radius: 5px; border-left: 4px solid #007bff; }
        .progress { width: 100%; height: 20px; background: #ddd; border-radius: 10px; overflow: hidden; }
        .progress-bar { height: 100%; background: #007bff; transition: width 0.3s; }
        .status { padding: 10px; margin: 10px 0; border-radius: 5px; }
        .success { background: #d4edda; color: #155724; border: 1px solid #c3e6cb; }
        .error { background: #f8d7da; color: #721c24; border: 1px solid #f5c6cb; }
        .info { background: #d1ecf1; color: #0c5460; border: 1px solid #bee5eb; }
    </style>
</head>
<body>
    <h1>🎨 Social Media Ad Generator</h1>
    <p>Transform your product images into stunning social media advertisements!</p>

    <div class="container">
        <h3>📸 Step 1: Upload Product Image</h3>
        <div class="upload-area" id="uploadArea">
            <input type="file" id="imageInput" accept="image/*" style="display: none;">
            <p>Click to select an image or drag and drop here</p>
            <button onclick="document.getElementById('imageInput').click();">Select Image</button>
        </div>
        <div id="uploadStatus"></div>
    </div>

    <div class="container" id="questionsContainer" style="display: none;">
        <h3>❓ Step 2: Answer Questions</h3>
        <div id="questionsList"></div>
        <button onclick="submitAnswers()" id="submitBtn">Submit Answers</button>
    </div>

    <div class="container" id="generationContainer" style="display: none;">
        <h3>🎨 Step 3: Generate Ads</h3>
        <button onclick="generateAds()" id="generateBtn">Generate 4 Ad Variations</button>
        <div id="generationStatus"></div>
    </div>

    <div class="container" id="resultsContainer" style="display: none;">
        <h3>📱 Generated Social Media Ads</h3>
        <div id="adResults"></div>
    </div>

    <script>
        let currentSession = null;
        let questions = [];

        // File upload handling
        const imageInput = document.getElementById('imageInput');
        const uploadArea = document.getElementById('uploadArea');

        uploadArea.addEventListener('click', () => imageInput.click());
        uploadArea.addEventListener('dragover', (e) => {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        });
        uploadArea.addEventListener('dragleave', () => {
            uploadArea.classList.remove('dragover');
        });
        uploadArea.addEventListener('drop', (e) => {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleImageUpload(files[0]);
            }
        });

        imageInput.addEventListener('change', (e) => {
            if (e.target.files.length > 0) {
                handleImageUpload(e.target.files[0]);
            }
        });

        async function handleImageUpload(file) {
            const formData = new FormData();
            formData.append('image', file);

            document.getElementById('uploadStatus').innerHTML =
                '<div class="status info">📤 Uploading and analyzing image...</div>';

            try {
                const response = await fetch('/upload-image', {
                    method: 'POST',
                    body: formData
                });

                const result = await response.json();

                if (result.error) {
                    document.getElementById('uploadStatus').innerHTML =
                        `<div class="status error">❌ Error: \${result.error}</div>`;
                    return;
                }

                currentSession = result.session_id;
                questions = result.questions;

                document.getElementById('uploadStatus').innerHTML =
                    `<div class="status success">✅ Image analyzed! Category: \${result.analysis.category}</div>`;

                displayQuestions(questions);
                document.getElementById('questionsContainer').style.display = 'block';

            } catch (error) {
                document.getElementById('uploadStatus').innerHTML =
                    `<div class="status error">❌ Upload failed: \${error.message}</div>`;
            }
        }

        function displayQuestions(questions) {
            const container = document.getElementById('questionsList');
            container.innerHTML = '';

            questions.forEach((q, index) => {
                const questionDiv = document.createElement('div');
                questionDiv.className = 'question';
                questionDiv.innerHTML = `
                    <label><strong>Question \${index + 1}:</strong> \${q.template}</label><br>
                    <textarea id="answer_\${q.question_id}" rows="2" style="width: 100%; margin-top: 5px;"
                              placeholder="Enter your answer here..."></textarea>
                `;
                container.appendChild(questionDiv);
            });
        }

        async function submitAnswers() {
            const answers = questions.map(q => ({
                question_id: q.question_id,
                question_text: q.template,
                response: document.getElementById(`answer_\${q.question_id}`).value
            }));

            // Validate answers
            const emptyAnswers = answers.filter(a => !a.response.trim());
            if (emptyAnswers.length > 0) {
                alert('Please answer all questions before proceeding.');
                return;
            }

            document.getElementById('submitBtn').disabled = true;
            document.getElementById('submitBtn').textContent = 'Processing...';

            try {
                const response = await fetch('/submit-answers', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ answers })
                });

                const result = await response.json();

                if (result.error) {
                    alert(`Error: \${result.error}`);
                    return;
                }

                document.getElementById('generationContainer').style.display = 'block';
                document.querySelector('#questionsContainer .status')?.remove();
                document.getElementById('questionsContainer').insertAdjacentHTML('beforeend',
                    '<div class="status success">✅ Answers processed successfully!</div>'
                );

            } catch (error) {
                alert(`Failed to submit answers: \${error.message}`);
            } finally {
                document.getElementById('submitBtn').disabled = false;
                document.getElementById('submitBtn').textContent = 'Submit Answers';
            }
        }

        async function generateAds() {
            document.getElementById('generateBtn').disabled = true;
            document.getElementById('generateBtn').textContent = 'Generating...';

            document.getElementById('generationStatus').innerHTML =
                '<div class="status info">🎨 Generating 4 ad variations... This may take 30-60 seconds.</div>';

            try {
                const response = await fetch('/generate-ads', {
                    method: 'POST'
                });

                const result = await response.json();

                if (result.error) {
                    document.getElementById('generationStatus').innerHTML =
                        `<div class="status error">❌ Error: \${result.error}</div>`;
                    return;
                }

                document.getElementById('generationStatus').innerHTML =
                    `<div class="status success">✅ Generated \${result.ads.length} ads in \${result.generation_time.toFixed(1)}s!</div>`;

                displayResults(result.ads);
                document.getElementById('resultsContainer').style.display = 'block';

            } catch (error) {
                document.getElementById('generationStatus').innerHTML =
                    `<div class="status error">❌ Generation failed: \${error.message}</div>`;
            } finally {
                document.getElementById('generateBtn').disabled = false;
                document.getElementById('generateBtn').textContent = 'Generate 4 Ad Variations';
            }
        }

        function displayResults(ads) {
            const container = document.getElementById('adResults');
            container.innerHTML = '';

            ads.forEach((ad, index) => {
                const adDiv = document.createElement('div');
                adDiv.className = 'ad-result';
                adDiv.innerHTML = `
                    <h4>\${index + 1}. \${ad.variation_type.toUpperCase().replace('_', ' ')} AD</h4>
                    <p><strong>Generation Time:</strong> \${ad.generation_time_seconds.toFixed(1)}s</p>
                    <p><strong>Image:</strong> <a href="\${ad.image_url}" target="_blank">View Generated Ad</a></p>
                    <details>
                        <summary>View Prompt Used</summary>
                        <pre style="background: #f8f9fa; padding: 10px; border-radius: 5px; font-size: 12px; overflow-x: auto;">\${ad.prompt_used}</pre>
                    </details>
                `;
                container.appendChild(adDiv);
            });
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/upload-image")
async def upload_image(image: UploadFile = File(...)):
    """Upload and analyze product image."""
    if not agent_wrapper:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    # Save uploaded file temporarily
    with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(image.filename)[1]) as tmp_file:
        shutil.copyfileobj(image.file, tmp_file)
        tmp_path = tmp_file.name

    try:
        result = await agent_wrapper.process_image(tmp_path)
        return result
    finally:
        # Clean up temp file
        if os.path.exists(tmp_path):
            os.unlink(tmp_path)


@app.post("/submit-answers")
async def submit_answers(request: AnswersRequest):
    """Submit answers to questions."""
    if not agent_wrapper:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    answers_dict = [answer.dict() for answer in request.answers]
    result = await agent_wrapper.submit_answers(answers_dict)
    return result


@app.post("/generate-ads")
async def generate_ads():
    """Generate social media ad variations."""
    if not agent_wrapper:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    result = await agent_wrapper.generate_ads()
    return result


@app.get("/status")
async def get_status():
    """Get current session status."""
    if not agent_wrapper:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    result = await agent_wrapper.get_session_status()
    return result


@app.post("/reset")
async def reset_session():
    """Reset current session."""
    if not agent_wrapper:
        raise HTTPException(status_code=500, detail="Agent not initialized")

    result = await agent_wrapper.reset_session()
    return result


def main():
    """Start the ADK web server."""
    print("🚀 Starting Social Media Ad Generator Web Interface")
    print("=" * 60)
    print("🌐 Web interface will be available at:")
    print("   http://localhost:8080")
    print("\n📱 Features available:")
    print("   • Upload product images")
    print("   • Answer contextual questions")
    print("   • Generate 4 ad variations")
    print("   • View generated ads and prompts")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 60)

    uvicorn.run(app, host="localhost", port=8080, log_level="info")


if __name__ == "__main__":
    main()