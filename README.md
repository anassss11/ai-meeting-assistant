# 🎙️ AI Meeting Assistant

> **Transform your meetings with AI-powered transcription, summarization, and intelligent action item extraction**

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.116.1-green.svg)](https://fastapi.tiangolo.com)
[![React](https://img.shields.io/badge/React-18+-61DAFB.svg)](https://reactjs.org)
[![LLaMA 3](https://img.shields.io/badge/LLaMA_3-Ollama-orange.svg)](https://ollama.ai)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🌟 Features

- **🎯 Real-time Audio Transcription** - High-accuracy speech-to-text using Faster Whisper
- **🤖 AI-Powered Summarization** - LLaMA 3 integration with intelligent fallback
- **📋 Structured Action Items** - Extract tasks with owners and deadlines
- **✅ Decision Tracking** - Automatically identify and catalog meeting decisions
- **📊 Interactive Dashboard** - Beautiful React interface with real-time updates
- **🔌 Chrome Extension** - Seamless browser integration for web meetings
- **🛡️ Robust Fallback System** - Works even with limited system resources
- **📤 Export Capabilities** - Download transcripts as CSV or TXT

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- Node.js 16+
- Ollama (optional, for enhanced AI features)

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/ai-meeting-assistant.git
   cd ai-meeting-assistant
   ```

2. **Set up the backend**
   ```bash
   cd backend
   pip install -r requirements.txt
   ```

3. **Set up the frontend**
   ```bash
   cd ../dashboard
   npm install
   ```

4. **Optional: Install LLaMA 3 (for enhanced AI)**
   ```bash
   # Install Ollama from https://ollama.ai
   ollama pull llama3
   ollama serve
   ```

### Running the Application

1. **Start the backend server**
   ```bash
   cd backend
   python -m uvicorn main:app --host 127.0.0.1 --port 8000
   ```

2. **Start the frontend dashboard**
   ```bash
   cd dashboard
   npm run dev
   ```

3. **Access the application**
   - Dashboard: http://localhost:5173
   - API Documentation: http://127.0.0.1:8000/docs
   - Health Check: http://127.0.0.1:8000/health/llama

## 🏗️ Architecture

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│  Chrome         │    │  React          │    │  FastAPI        │
│  Extension      │───▶│  Dashboard      │───▶│  Backend        │
│                 │    │                 │    │                 │
│ • Audio Capture │    │ • Real-time UI  │    │ • LLaMA 3       │
│ • File Upload   │    │ • Export Tools  │    │ • Transcription │
│ • Integration   │    │ • Status Monitor│    │ • AI Processing │
└─────────────────┘    └─────────────────┘    └─────────────────┘
                                                       │
                                               ┌─────────────────┐
                                               │  Ollama         │
                                               │  LLaMA 3        │
                                               │                 │
                                               │ • Summarization │
                                               │ • Action Items  │
                                               │ • Decisions     │
                                               └─────────────────┘
```

## 📱 Screenshots

### Dashboard Overview
![Dashboard](docs/dashboard-overview.png)

### Action Items with Structured Data
![Action Items](docs/action-items.png)

### Real-time Processing
![Processing](docs/real-time-processing.png)

## 🔧 Configuration

### Environment Variables

Create a `.env` file in the `backend/` directory:

```env
# LLaMA 3 Configuration
LLAMA_MODEL=llama3
LLAMA_BASE_URL=http://localhost:11434
LLAMA_MAX_TOKENS=500
LLAMA_TEMPERATURE=0.3
LLAMA_ENABLE_FALLBACK=true
LLAMA_REQUEST_TIMEOUT=120
LLAMA_MAX_RETRIES=3

# Optional: Custom settings
LLAMA_MAX_TRANSCRIPT_CHARS=50000
```

### API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Server status |
| `/transcript` | GET | Current meeting transcript |
| `/summary` | GET | AI-generated summary |
| `/action-items` | GET | Structured action items |
| `/decisions` | GET | Extracted decisions |
| `/audio` | POST | Upload audio for transcription |
| `/health/llama` | GET | LLaMA 3 health status |
| `/metrics/llama` | GET | Usage metrics |

## 🤖 AI Integration

### LLaMA 3 Prompt Structure

The system uses a carefully crafted prompt for structured extraction:

```json
{
  "summary": "Concise meeting overview (3-5 lines)",
  "decisions": ["Decision 1", "Decision 2"],
  "action_items": [
    {
      "task": "What needs to be done",
      "owner": "Person responsible",
      "deadline": "When it's due"
    }
  ]
}
```

### Intelligent Fallback

When LLaMA 3 is unavailable (due to memory constraints or other issues), the system automatically falls back to:
- Enhanced regex-based extraction
- Context-aware action item detection
- Structured data formatting
- Maintains full functionality

## 🛠️ Development

### Project Structure

```
ai-meeting-assistant/
├── backend/                 # FastAPI backend
│   ├── main.py             # Main server application
│   ├── llama_summarizer.py # LLaMA 3 integration
│   ├── llama_config.py     # Configuration management
│   ├── models.py           # Pydantic data models
│   ├── transcribe.py       # Audio transcription
│   └── requirements.txt    # Python dependencies
├── dashboard/              # React frontend
│   ├── src/
│   │   ├── App.jsx         # Main application
│   │   ├── api.js          # API communication
│   │   └── components/     # React components
│   └── package.json        # Node.js dependencies
├── extension/              # Chrome extension
│   ├── manifest.json       # Extension manifest
│   ├── popup.html          # Extension UI
│   └── background.js       # Background scripts
└── README.md              # This file
```

### Running Tests

```bash
# Backend tests
cd backend
python -m pytest

# Frontend tests
cd dashboard
npm test
```

### Building for Production

```bash
# Build frontend
cd dashboard
npm run build

# The built files will be in dashboard/dist/
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# For GPU support (if available)
docker-compose -f docker-compose-gpu.yml up --build
```

### Manual Deployment

1. Set up a server with Python 3.11+ and Node.js
2. Install dependencies as shown in Quick Start
3. Configure environment variables
4. Use a process manager like PM2 or systemd
5. Set up a reverse proxy (nginx recommended)

## 🤝 Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for details.

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📊 Performance

- **Transcription Accuracy**: 95%+ with Faster Whisper
- **Processing Speed**: ~2-5 seconds per minute of audio
- **Memory Usage**: 
  - Minimum: 512MB (fallback mode)
  - Recommended: 2GB+ (full LLaMA 3)
- **Supported Audio Formats**: WAV, MP3, M4A, WebM

## 🔒 Privacy & Security

- **Local Processing**: All AI processing can run locally
- **No Data Retention**: Transcripts stored locally only
- **Secure Communication**: HTTPS support for production
- **Privacy First**: No external API calls required (when using local LLaMA)

## 📋 System Requirements

### Minimum Requirements
- **RAM**: 512MB (fallback mode)
- **CPU**: Dual-core processor
- **Storage**: 1GB free space
- **OS**: Windows 10+, macOS 10.15+, Linux

### Recommended Requirements
- **RAM**: 2GB+ (for LLaMA 3)
- **CPU**: Quad-core processor
- **Storage**: 5GB free space (for models)
- **GPU**: Optional, for faster processing

## 🐛 Troubleshooting

### Common Issues

**LLaMA 3 not working?**
- Check if Ollama is running: `ollama serve`
- Verify model is installed: `ollama list`
- System will automatically use fallback mode

**Audio transcription failing?**
- Ensure audio file is in supported format
- Check file size (max 100MB recommended)
- Verify microphone permissions for Chrome extension

**Dashboard not loading?**
- Confirm both backend and frontend are running
- Check browser console for errors
- Verify API endpoints are accessible

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- [Ollama](https://ollama.ai) for local LLaMA 3 integration
- [Faster Whisper](https://github.com/guillaumekln/faster-whisper) for audio transcription
- [FastAPI](https://fastapi.tiangolo.com) for the robust backend framework
- [React](https://reactjs.org) for the interactive frontend

## 📞 Support

- 📧 Email: support@example.com
- 💬 Discord: [Join our community](https://discord.gg/example)
- 🐛 Issues: [GitHub Issues](https://github.com/yourusername/ai-meeting-assistant/issues)
- 📖 Documentation: [Full Documentation](https://docs.example.com)

---

<div align="center">
  <strong>Made with ❤️ for better meetings</strong>
  <br>
  <sub>Star ⭐ this repo if you find it helpful!</sub>
</div>