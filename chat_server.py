#!/usr/bin/env python3
"""
Conversational Chat Agent Web Interface.

This provides a chat-based interface where the agent dynamically
analyzes responses and guides users through ad generation.
"""

import asyncio
import sys
import os
import tempfile
import shutil
import uuid
from pathlib import Path
from typing import Dict, Any, List, Optional
import uvicorn
from fastapi import FastAPI, File, UploadFile, HTTPException, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
import json

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from social_media_ad_generator.chat_agent import ConversationalAdAgent


# Pydantic models
class ChatMessage(BaseModel):
    message: str
    conversation_id: Optional[str] = None


# Create FastAPI app
app = FastAPI(
    title="Social Media Ad Generator - Chat Agent",
    description="Conversational AI agent that creates social media advertisements through dynamic chat",
    version="2.0.0"
)

# Global agent instance
chat_agent = None
active_connections: Dict[str, WebSocket] = {}


@app.on_event("startup")
async def startup_event():
    """Initialize the chat agent on startup."""
    global chat_agent
    chat_agent = ConversationalAdAgent()
    print("✅ Conversational Social Media Ad Generator Agent initialized")


@app.get("/", response_class=HTMLResponse)
async def root():
    """Serve the conversational chat interface."""
    html_content = """
<!DOCTYPE html>
<html>
<head>
    <title>AI Social Media Ad Generator - Chat</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        * { box-sizing: border-box; margin: 0; padding: 0; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Arial, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            height: 100vh;
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
        }

        .chat-container {
            width: 100%;
            max-width: 800px;
            height: 90vh;
            background: white;
            border-radius: 15px;
            box-shadow: 0 20px 40px rgba(0,0,0,0.1);
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }

        .chat-header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 20px;
            text-align: center;
        }

        .chat-header h1 {
            font-size: 24px;
            margin-bottom: 8px;
        }

        .chat-header p {
            opacity: 0.9;
            font-size: 14px;
        }

        .chat-messages {
            flex: 1;
            padding: 20px;
            overflow-y: auto;
            background: #f8f9fa;
        }

        .message {
            margin-bottom: 20px;
            animation: fadeInUp 0.3s ease-out;
        }

        @keyframes fadeInUp {
            from { opacity: 0; transform: translateY(20px); }
            to { opacity: 1; transform: translateY(0); }
        }

        .message.agent {
            text-align: left;
        }

        .message.user {
            text-align: right;
        }

        .message-bubble {
            display: inline-block;
            max-width: 80%;
            padding: 15px 20px;
            border-radius: 20px;
            position: relative;
            line-height: 1.4;
            word-wrap: break-word;
            white-space: pre-wrap;
        }

        .agent .message-bubble {
            background: #e3f2fd;
            color: #1565c0;
            border-bottom-left-radius: 5px;
        }

        .user .message-bubble {
            background: #667eea;
            color: white;
            border-bottom-right-radius: 5px;
        }

        .message-time {
            font-size: 11px;
            opacity: 0.6;
            margin-top: 5px;
        }

        .input-area {
            padding: 20px;
            background: white;
            border-top: 1px solid #e0e0e0;
        }

        .input-row {
            display: flex;
            gap: 10px;
            align-items: flex-end;
        }

        .message-input {
            flex: 1;
            padding: 15px;
            border: 2px solid #e0e0e0;
            border-radius: 25px;
            font-size: 16px;
            resize: none;
            max-height: 100px;
            outline: none;
            transition: border-color 0.3s;
        }

        .message-input:focus {
            border-color: #667eea;
        }

        .send-button {
            background: #667eea;
            color: white;
            border: none;
            padding: 15px 20px;
            border-radius: 50%;
            cursor: pointer;
            transition: all 0.3s;
            display: flex;
            align-items: center;
            justify-content: center;
            min-width: 50px;
            height: 50px;
        }

        .send-button:hover {
            background: #5a67d8;
            transform: scale(1.05);
        }

        .send-button:disabled {
            background: #ccc;
            cursor: not-allowed;
            transform: none;
        }

        .upload-area {
            margin-bottom: 15px;
            padding: 20px;
            border: 2px dashed #667eea;
            border-radius: 15px;
            text-align: center;
            background: #f8f9ff;
            cursor: pointer;
            transition: all 0.3s;
        }

        .upload-area:hover {
            background: #f0f4ff;
            border-color: #5a67d8;
        }

        .upload-area.hidden {
            display: none;
        }

        .upload-area.dragover {
            background: #e3f2fd;
            border-color: #1565c0;
        }

        .typing-indicator {
            display: none;
            align-items: center;
            gap: 10px;
            color: #666;
            font-style: italic;
            padding: 10px 0;
        }

        .typing-dots {
            display: flex;
            gap: 4px;
        }

        .typing-dots span {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            background: #667eea;
            animation: typing 1.4s infinite;
        }

        .typing-dots span:nth-child(2) { animation-delay: 0.2s; }
        .typing-dots span:nth-child(3) { animation-delay: 0.4s; }

        @keyframes typing {
            0%, 60%, 100% { transform: scale(0.8); opacity: 0.5; }
            30% { transform: scale(1.1); opacity: 1; }
        }

        .action-buttons {
            display: flex;
            gap: 10px;
            margin-top: 15px;
            flex-wrap: wrap;
        }

        .action-button {
            background: #f0f4ff;
            color: #667eea;
            border: 1px solid #667eea;
            padding: 8px 15px;
            border-radius: 20px;
            cursor: pointer;
            font-size: 14px;
            transition: all 0.3s;
        }

        .action-button:hover {
            background: #667eea;
            color: white;
        }

        .status-indicator {
            padding: 10px 15px;
            margin: 10px 0;
            border-radius: 10px;
            font-size: 14px;
            text-align: center;
        }

        .status-success {
            background: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }

        .status-info {
            background: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }

        .status-warning {
            background: #fff3cd;
            color: #856404;
            border: 1px solid #ffeaa7;
        }

        .hidden { display: none !important; }

        .ad-result {
            margin: 15px 0;
            padding: 15px;
            background: #f8f9fa;
            border-radius: 10px;
            border-left: 4px solid #667eea;
        }

        .ad-result h4 {
            color: #667eea;
            margin-bottom: 10px;
        }

        .ad-result a {
            color: #667eea;
            text-decoration: none;
            font-weight: 500;
        }

        .ad-result a:hover {
            text-decoration: underline;
        }

        @media (max-width: 768px) {
            body { padding: 10px; }
            .chat-container { height: 95vh; }
            .message-bubble { max-width: 90%; }
            .input-area { padding: 15px; }
        }
    </style>
</head>
<body>
    <div class="chat-container">
        <div class="chat-header">
            <h1>🎨 AI Social Media Ad Generator</h1>
            <p>Your intelligent assistant for creating stunning social media ads</p>
        </div>

        <div class="chat-messages" id="chatMessages">
            <!-- Messages will be inserted here -->
        </div>

        <div class="typing-indicator" id="typingIndicator">
            <div class="typing-dots">
                <span></span>
                <span></span>
                <span></span>
            </div>
            <span>Agent is thinking...</span>
        </div>

        <div class="input-area">
            <div class="upload-area" id="uploadArea">
                <input type="file" id="imageInput" accept="image/*" style="display: none;">
                <p>📸 <strong>Upload Product Image</strong></p>
                <p>Click here or drag & drop to upload your product image</p>
            </div>

            <div class="input-row">
                <textarea
                    class="message-input"
                    id="messageInput"
                    placeholder="Type your message..."
                    rows="1"
                ></textarea>
                <button class="send-button" id="sendButton" onclick="sendMessage()">
                    <span>➤</span>
                </button>
            </div>
        </div>
    </div>

    <script>
        let conversationId = null;
        let currentStage = 'greeting';
        let isUploading = false;

        // DOM elements
        const chatMessages = document.getElementById('chatMessages');
        const messageInput = document.getElementById('messageInput');
        const sendButton = document.getElementById('sendButton');
        const uploadArea = document.getElementById('uploadArea');
        const imageInput = document.getElementById('imageInput');
        const typingIndicator = document.getElementById('typingIndicator');

        // Initialize chat
        document.addEventListener('DOMContentLoaded', function() {
            startConversation();
            setupEventListeners();
        });

        function setupEventListeners() {
            // Message input
            messageInput.addEventListener('keypress', function(e) {
                if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendMessage();
                }
            });

            messageInput.addEventListener('input', function() {
                this.style.height = 'auto';
                this.style.height = this.scrollHeight + 'px';
            });

            // File upload
            uploadArea.addEventListener('click', () => imageInput.click());
            uploadArea.addEventListener('dragover', handleDragOver);
            uploadArea.addEventListener('dragleave', handleDragLeave);
            uploadArea.addEventListener('drop', handleDrop);

            imageInput.addEventListener('change', function(e) {
                if (e.target.files.length > 0) {
                    handleImageUpload(e.target.files[0]);
                }
            });
        }

        function handleDragOver(e) {
            e.preventDefault();
            uploadArea.classList.add('dragover');
        }

        function handleDragLeave(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
        }

        function handleDrop(e) {
            e.preventDefault();
            uploadArea.classList.remove('dragover');
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                handleImageUpload(files[0]);
            }
        }

        async function startConversation() {
            try {
                showTyping();
                const response = await fetch('/start-conversation', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' }
                });

                const data = await response.json();
                hideTyping();

                if (data.error) {
                    addMessage('agent', 'Sorry, I encountered an error starting our conversation. Please refresh and try again.');
                    return;
                }

                conversationId = data.conversation_id;
                currentStage = data.stage;
                addMessage('agent', data.message);

                updateUI(data);

            } catch (error) {
                hideTyping();
                addMessage('agent', 'Sorry, I cannot connect right now. Please refresh and try again.');
                console.error('Failed to start conversation:', error);
            }
        }

        async function sendMessage() {
            const message = messageInput.value.trim();
            if (!message || isUploading) return;

            // Add user message to chat
            addMessage('user', message);
            messageInput.value = '';
            messageInput.style.height = 'auto';

            // Disable input while processing
            setInputState(false);
            showTyping();

            try {
                const response = await fetch('/chat', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({
                        message: message,
                        conversation_id: conversationId
                    })
                });

                const data = await response.json();
                hideTyping();

                if (data.error) {
                    addMessage('agent', `Sorry, I encountered an error: ${data.error}`);
                } else {
                    addMessage('agent', data.message, data);
                    conversationId = data.conversation_id;
                    currentStage = data.stage;
                    updateUI(data);

                    // If generation started, poll for updates
                    if (data.stage === 'generating' && data.generation_started) {
                        pollGenerationStatus();
                    }
                }

            } catch (error) {
                hideTyping();
                addMessage('agent', 'Sorry, I encountered a connection error. Please try again.');
                console.error('Error sending message:', error);
            } finally {
                setInputState(true);
            }
        }

        async function pollGenerationStatus() {
            let pollCount = 0;
            const maxPolls = 120; // 2 minutes max
            const pollInterval = 3000; // 3 seconds

            const poll = async () => {
                if (pollCount >= maxPolls) {
                    addMessage('agent', 'Generation is taking longer than expected. Please check back in a moment.');
                    return;
                }

                try {
                    const response = await fetch(`/conversation/${conversationId}/status`);
                    const status = await response.json();

                    if (status.stage === 'completed' && status.generation_complete) {
                        // Generation completed, get the results
                        const chatResponse = await fetch('/chat', {
                            method: 'POST',
                            headers: { 'Content-Type': 'application/json' },
                            body: JSON.stringify({
                                message: 'show results',
                                conversation_id: conversationId
                            })
                        });

                        const data = await chatResponse.json();
                        if (data.ads) {
                            addMessage('agent', data.message, data);
                        }
                        return;
                    }

                    if (status.stage === 'generation_failed') {
                        addMessage('agent', 'Sorry, the ad generation failed. Would you like to try again?');
                        return;
                    }

                    // Still generating, continue polling
                    if (status.stage === 'generating') {
                        pollCount++;

                        // Show progress updates
                        if (pollCount === 5) {
                            addMessage('agent', '🎨 Still working on your ads... Creating lifestyle variation...');
                        } else if (pollCount === 10) {
                            addMessage('agent', '🎨 Making great progress... Working on product hero shot...');
                        } else if (pollCount === 15) {
                            addMessage('agent', '🎨 Almost there... Finalizing benefit-focused and social proof ads...');
                        }

                        setTimeout(poll, pollInterval);
                    }

                } catch (error) {
                    console.error('Error polling status:', error);
                    pollCount++;
                    if (pollCount < maxPolls) {
                        setTimeout(poll, pollInterval);
                    }
                }
            };

            // Start polling
            setTimeout(poll, pollInterval);
        }

        async function handleImageUpload(file) {
            if (isUploading) return;

            // Validate file
            if (!file.type.startsWith('image/')) {
                addMessage('agent', 'Please upload a valid image file (JPEG, PNG, or WebP).');
                return;
            }

            if (file.size > 10 * 1024 * 1024) { // 10MB
                addMessage('agent', 'Please upload an image smaller than 10MB.');
                return;
            }

            isUploading = true;
            setInputState(false);
            showTyping();

            // Show upload status
            addMessage('user', `📸 Uploaded: ${file.name}`);

            try {
                const formData = new FormData();
                formData.append('image', file);
                if (conversationId) {
                    formData.append('conversation_id', conversationId);
                }

                const response = await fetch('/upload-image-chat', {
                    method: 'POST',
                    body: formData
                });

                const data = await response.json();
                hideTyping();

                if (data.error) {
                    addMessage('agent', `Sorry, I couldn't process your image: ${data.error}`);
                } else {
                    addMessage('agent', data.message);
                    conversationId = data.conversation_id;
                    currentStage = data.stage;
                    updateUI(data);

                    // Hide upload area after successful upload
                    uploadArea.classList.add('hidden');
                }

            } catch (error) {
                hideTyping();
                addMessage('agent', 'Sorry, the image upload failed. Please try again.');
                console.error('Image upload error:', error);
            } finally {
                isUploading = false;
                setInputState(true);
                imageInput.value = ''; // Reset file input
            }
        }

        function addMessage(role, message, data = null) {
            const messageDiv = document.createElement('div');
            messageDiv.className = `message ${role}`;

            const bubble = document.createElement('div');
            bubble.className = 'message-bubble';
            bubble.textContent = message;

            const time = document.createElement('div');
            time.className = 'message-time';
            time.textContent = new Date().toLocaleTimeString();

            messageDiv.appendChild(bubble);
            messageDiv.appendChild(time);

            // Add action buttons if provided
            if (data && data.actions) {
                const actionsDiv = document.createElement('div');
                actionsDiv.className = 'action-buttons';

                data.actions.forEach(action => {
                    const button = document.createElement('button');
                    button.className = 'action-button';
                    button.textContent = getActionLabel(action);
                    button.onclick = () => handleAction(action);
                    actionsDiv.appendChild(button);
                });

                messageDiv.appendChild(actionsDiv);
            }

            // Add ad results if provided
            if (data && data.ads) {
                const resultsDiv = document.createElement('div');
                data.ads.forEach((ad, index) => {
                    const adDiv = document.createElement('div');
                    adDiv.className = 'ad-result';

                    const filename = ad.download_url ? ad.download_url.split('/').pop() : null;
                    const viewUrl = filename ? `/view-ad/${filename}` : ad.image_url;
                    const downloadUrl = ad.download_url || ad.image_url;

                    adDiv.innerHTML = `
                        <h4>${index + 1}. ${ad.variation_type.replace('_', ' ').toUpperCase()} AD</h4>
                        <p><strong>Generation Time:</strong> ${ad.generation_time_seconds.toFixed(1)}s</p>
                        <div style="margin: 10px 0;">
                            <img src="${viewUrl}" alt="Generated Ad" style="max-width: 200px; max-height: 300px; border-radius: 8px; box-shadow: 0 2px 8px rgba(0,0,0,0.1);" onclick="window.open('${viewUrl}', '_blank')">
                        </div>
                        <div style="display: flex; gap: 10px; margin-top: 10px;">
                            <a href="${viewUrl}" target="_blank" style="color: #667eea; text-decoration: none; padding: 8px 15px; background: #f0f4ff; border-radius: 20px; font-size: 14px;">👁️ View Full Size</a>
                            <a href="${downloadUrl}" download style="color: #667eea; text-decoration: none; padding: 8px 15px; background: #f0f4ff; border-radius: 20px; font-size: 14px;">💾 Download</a>
                        </div>
                    `;
                    resultsDiv.appendChild(adDiv);
                });
                messageDiv.appendChild(resultsDiv);
            }

            chatMessages.appendChild(messageDiv);
            scrollToBottom();
        }

        function getActionLabel(action) {
            const labels = {
                'upload_image': '📸 Upload Image',
                'generate_ads': '🎨 Generate Ads',
                'modify_info': '✏️ Modify Info',
                'new_product': '🔄 New Product',
                'tips': '💡 Get Tips',
                'download': '💾 Download'
            };
            return labels[action] || action;
        }

        function handleAction(action) {
            switch(action) {
                case 'upload_image':
                    imageInput.click();
                    break;
                case 'generate_ads':
                    sendPredefinedMessage('Yes, generate my ads!');
                    break;
                case 'modify_info':
                    sendPredefinedMessage('I want to modify my information');
                    break;
                case 'new_product':
                    sendPredefinedMessage('I want to create ads for a new product');
                    break;
                case 'tips':
                    sendPredefinedMessage('Give me tips for using these ads');
                    break;
                default:
                    console.log('Unknown action:', action);
            }
        }

        function sendPredefinedMessage(message) {
            messageInput.value = message;
            sendMessage();
        }

        function updateUI(data) {
            // Show/hide upload area based on stage
            if (data.stage === 'waiting_for_image') {
                uploadArea.classList.remove('hidden');
            } else if (data.stage !== 'greeting') {
                uploadArea.classList.add('hidden');
            }

            // Update placeholder text
            if (data.stage === 'asking_questions') {
                messageInput.placeholder = 'Type your answer here...';
            } else if (data.stage === 'ready_for_generation') {
                messageInput.placeholder = 'Type "yes" to generate ads...';
            } else {
                messageInput.placeholder = 'Type your message...';
            }
        }

        function setInputState(enabled) {
            messageInput.disabled = !enabled;
            sendButton.disabled = !enabled;
        }

        function showTyping() {
            typingIndicator.style.display = 'flex';
            scrollToBottom();
        }

        function hideTyping() {
            typingIndicator.style.display = 'none';
        }

        function scrollToBottom() {
            setTimeout(() => {
                chatMessages.scrollTop = chatMessages.scrollHeight;
            }, 100);
        }
    </script>
</body>
</html>
    """
    return HTMLResponse(content=html_content)


@app.post("/start-conversation")
async def start_conversation():
    """Start a new conversation with the chat agent."""
    if not chat_agent:
        raise HTTPException(status_code=500, detail="Chat agent not initialized")

    conversation_id, response = await chat_agent.start_conversation()
    return {
        "conversation_id": conversation_id,
        **response
    }


@app.post("/chat")
async def chat(message: ChatMessage):
    """Send a message to the chat agent."""
    if not chat_agent:
        raise HTTPException(status_code=500, detail="Chat agent not initialized")

    if not message.conversation_id:
        raise HTTPException(status_code=400, detail="conversation_id is required")

    response = await chat_agent.process_message(
        message.conversation_id,
        message.message
    )

    # Add download URLs for generated images
    if response.get("ads"):
        for ad in response["ads"]:
            if ad.get("image_url") and ad["image_url"].startswith("file://"):
                # Convert file path to downloadable URL
                file_path = ad["image_url"][7:]  # Remove file:// prefix
                filename = os.path.basename(file_path)
                ad["download_url"] = f"/download-ad/{filename}"

    return response


@app.post("/upload-image-chat")
async def upload_image_chat(image: UploadFile = File(...), conversation_id: str = None):
    """Upload image in chat context."""
    if not chat_agent:
        raise HTTPException(status_code=500, detail="Chat agent not initialized")

    # Read image data
    image_data = await image.read()

    if conversation_id:
        response = await chat_agent.process_message(
            conversation_id,
            f"Uploaded image: {image.filename}",
            image_data=image_data,
            image_filename=image.filename
        )
    else:
        # Start new conversation with image
        conversation_id, _ = await chat_agent.start_conversation()
        response = await chat_agent.process_message(
            conversation_id,
            f"Uploaded image: {image.filename}",
            image_data=image_data,
            image_filename=image.filename
        )

    return response


@app.get("/conversation/{conversation_id}/history")
async def get_conversation_history(conversation_id: str):
    """Get conversation history."""
    if not chat_agent:
        raise HTTPException(status_code=500, detail="Chat agent not initialized")

    history = await chat_agent.get_conversation_history(conversation_id)
    return {"history": history}


@app.get("/conversation/{conversation_id}/status")
async def get_conversation_status(conversation_id: str):
    """Get conversation status."""
    if not chat_agent:
        raise HTTPException(status_code=500, detail="Chat agent not initialized")

    status = await chat_agent.get_conversation_status(conversation_id)
    return status


@app.get("/download-ad/{filename}")
async def download_ad(filename: str):
    """Download a generated ad image."""
    file_path = os.path.join("logs", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Ad image not found")

    return FileResponse(
        path=file_path,
        filename=filename,
        media_type='image/png'
    )


@app.get("/view-ad/{filename}")
async def view_ad(filename: str):
    """View a generated ad image."""
    file_path = os.path.join("logs", filename)

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="Ad image not found")

    return FileResponse(path=file_path, media_type='image/png')


def main():
    """Start the conversational chat server."""
    print("🚀 Starting Conversational Social Media Ad Generator")
    print("=" * 60)
    print("💬 Chat-based AI agent interface")
    print("🌐 Web interface available at: http://localhost:8080")
    print("\n🤖 Features:")
    print("   • Intelligent conversation flow")
    print("   • Dynamic question generation")
    print("   • Context-aware responses")
    print("   • Real-time ad generation")
    print("   • Chat-style user experience")
    print("\n💡 Press Ctrl+C to stop the server")
    print("=" * 60)

    uvicorn.run(app, host="localhost", port=8080, log_level="info")


if __name__ == "__main__":
    main()