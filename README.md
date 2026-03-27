# 🎙️ AI Meeting Assistant

Transform your meetings with AI-powered transcription, summarization, and intelligent action item extraction using NVIDIA Qwen 3.5.

## ✨ Features

- **🎯 Real-time Audio Transcription** - High-accuracy speech-to-text using Faster Whisper
- **🤖 AI-Powered Summarization** - NVIDIA Qwen 3.5 for intelligent meeting analysis
- **📋 Structured Extraction** - Automatically extract action items, decisions, and summaries
- **📤 File Upload Support** - Analyze PDF, TXT, and DOCX files
- **📊 Interactive Dashboard** - Beautiful React interface with real-time updates
- ** Chrome Extension** - Seamless browser integration for web meetings
- **� Export Capabilities** - Download transcripts as CSV or TXT

## 🚀 Quick Start

### Prerequisites
- Python 3.11+
- Node.js 16+
- NVIDIA API Key (get from https://build.nvidia.com)

### Installation

1. **Clone and setup backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   cp .env.example .env
   # Edit .env and add your NVIDIA_API_KEY
   ```

2. **Setup frontend**
   ```bash
   cd dashboard
   npm install
   ```

### Running

1. **Start backend**
   ```bash
   cd backend
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

2. **Start frontend**
   ```bash
   cd dashboard
   npm run dev
   ```

3. **Access**
   - Dashboard: http://localhost:5173
   - API Docs: http://127.0.0.1:8000/docs

## 🏗️ Architecture

```
Chrome Extension / File Upload
         ↓
    FastAPI Backend
         ↓
  NVIDIA Qwen 3.5 API
         ↓
React Dashboard
```

## 🔧 Configuration

Create `.env` in `backend/`:

```env
NVIDIA_API_KEY=your_key_here
NVIDIA_MODEL=qwen/qwen3.5-397b-a17b
NVIDIA_MAX_TOKENS=16384
NVIDIA_TEMPERATURE=0.60
NVIDIA_TOP_P=0.95
NVIDIA_TOP_K=20
NVIDIA_ENABLE_FALLBACK=true
NVIDIA_REQUEST_TIMEOUT=0
NVIDIA_MAX_RETRIES=3
NVIDIA_MAX_TRANSCRIPT_CHARS=50000
```

## 📡 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/transcript` | GET | Get current transcript |
| `/summary` | GET | Get AI summary |
| `/action-items` | GET | Get action items |
| `/decisions` | GET | Get decisions |
| `/audio` | POST | Upload audio |
| `/upload-transcript` | POST | Upload file (PDF/TXT/DOCX) |
| `/health/nvidia` | GET | NVIDIA API status |

## 📁 Project Structure

```
ai-meeting-assistant/
├── backend/
│   ├── main.py                 # FastAPI server
│   ├── nvidia_summarizer.py    # NVIDIA integration
│   ├── file_extractor.py       # File parsing
│   ├── meeting_analysis.py     # Fallback extraction
│   └── requirements.txt        # Dependencies
├── dashboard/
│   ├── src/
│   │   ├── App.jsx
│   │   ├── api.js
│   │   └── components/
│   └── package.json
└── extension/
    ├── manifest.json
    ├── popup.html
    └── popup.js
```

## 🤖 How It Works

1. **Audio/File Input** - Record meeting or upload file
2. **Transcription** - Convert audio to text using Faster Whisper
3. **AI Analysis** - Send to NVIDIA Qwen 3.5 for:
   - Summary generation
   - Decision extraction
   - Action item identification
4. **Display** - Show results in dashboard with owner/deadline info

## 🔒 Privacy

- All transcripts stored locally
- No data retention on servers
- Optional local processing with fallback mode
- Secure API communication

## 📊 System Requirements

**Minimum:**
- RAM: 512MB
- CPU: Dual-core
- Storage: 1GB

**Recommended:**
- RAM: 2GB+
- CPU: Quad-core
- Storage: 5GB

## 🐛 Troubleshooting

**Backend won't start?**
- Check Python version: `python --version` (need 3.11+)
- Verify NVIDIA_API_KEY is set in .env
- Check port 8000 is available

**Dashboard not loading?**
- Ensure backend is running on http://127.0.0.1:8000
- Check browser console for errors
- Try clearing cache and reloading

**No decisions/action items?**
- Ensure transcript has clear commitments or tasks
- Check NVIDIA API is responding: http://127.0.0.1:8000/health/nvidia
- Fallback extraction will activate if API fails

## 📄 License

MIT License - see LICENSE file for details

## 🙏 Acknowledgments

- [NVIDIA Qwen 3.5](https://build.nvidia.com) - AI model
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) - Transcription
- [FastAPI](https://fastapi.tiangolo.com) - Backend framework
- [React](https://reactjs.org) - Frontend framework

---

**Made with ❤️ for better meetings**
