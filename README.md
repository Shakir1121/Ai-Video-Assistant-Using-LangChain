# AI Video Assistant Using LangChain

An AI-powered video analysis system that transcribes, summarizes, and extracts insights from videos. Supports both YouTube URLs and local file uploads.

## Features

- 🎬 Takes any YouTube URL or audio/video file as input
- 🎙 Transcribes audio using local Whisper AI
- 📝 Generates a descriptive video title
- 📄 Shows full transcript
- 📋 Summarises the video content in bullet points
- ❓ Extracts open questions and follow-ups
- 💬 Lets you ask questions about the video with ChromaDB RAG
- 📥 Export full detailed report as PDF or TXT

## Tech Stack

- **Frontend:** Streamlit
- **Transcription:** OpenAI Whisper (local)
- **LLM:** Mistral AI via LangChain
- **Vector Store:** ChromaDB with HuggingFace embeddings (`all-MiniLM-L6-v2`)
- **Video Download:** yt-dlp
- **Audio Processing:** FFmpeg

## Setup

### 1. Clone & Navigate
```bash
cd ai-video-intelligence-system
```

### 2. Create Virtual Environment
```bash
python -m venv env
```

### 3. Activate Environment
**Windows:**
```bash
.\env\Scripts\activate
```
**Mac/Linux:**
```bash
source env/bin/activate
```

### 4. Install Dependencies
```bash
pip install -r requirements.txt
```

### 5. Set Environment Variables
Create a `.env` file:
```
MISTRAL_API_KEY=your_mistral_api_key_here
```

### 6. Run the App
```bash
streamlit run streamlit_app/app.py
```

## Deploy to Streamlit Community Cloud (Free)

This project is ready to deploy on Streamlit Cloud (free tier).

### Step 1: Push to GitHub
```bash
git add .
git commit -m "Prepare for Streamlit Cloud deployment"
git push origin main
```

### Step 2: Deploy on Streamlit Cloud
1. Go to **https://share.streamlit.io** and sign in with GitHub
2. Click **"Create app"** → **"Deploy from a repo"**
3. Select your repo: `Shakir1121/Ai-Video-Assistant-Using-LangChain`
4. Set:
   - **Branch:** `main`
   - **Main file path:** `streamlit_app/app.py`
5. Click **"Advanced settings"** and set the secret:
   - `MISTRAL_API_KEY = "your_mistral_api_key_here"`
6. Click **"Deploy"** 🚀

Your app will build automatically (may take 5-10 min on first deploy).

### Deployment Config Files
- `.streamlit/config.toml` — Blue theme + server settings (max upload 200MB)
- `packages.txt` — Installs `ffmpeg` via apt on the cloud server
- `.streamlit/secrets.example.toml` — Template for your API keys

### ⚠️ Free Tier Notes
- Streamlit Cloud free tier has **1GB RAM** — Whisper "base" model works but is memory-heavy
- Cold starts (first load after inactivity) can take **5-10 minutes** as the model loads
- After ~10 min of inactivity the app sleeps; it wakes automatically on next visit

## Project Structure

```
ai-video-intelligence-system/
├── app/
│   ├── agents/          # AI agents (summarizer, QA)
│   ├── memory/          # ChromaDB vector store
│   └── tools/           # Utilities (youtube, whisper, pipeline)
├── streamlit_app/       # Streamlit UI
├── ffmpeg/              # FFmpeg binaries
├── audio/               # Downloaded/extracted audio files
├── chroma_db/           # Vector store persistence
└── generated_notes/     # Generated PDF reports
```

## Usage

1. Enter a YouTube URL OR upload a video/audio file
2. Click "Process" to start analysis
3. View results: Transcript, Summary, Open Questions
4. Ask questions using the RAG-powered chat
5. Export report as PDF or TXT
