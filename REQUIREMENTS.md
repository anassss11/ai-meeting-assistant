# System Requirements

## Software Requirements

### Backend
- **Python**: 3.11 or higher
- **pip**: Latest version
- **Virtual Environment**: Recommended (venv or conda)

### Frontend
- **Node.js**: 16 or higher
- **npm**: 8 or higher (comes with Node.js)

### API
- **NVIDIA API Key**: Required (get from https://build.nvidia.com)
- **Internet Connection**: Required for NVIDIA Qwen 3.5 API

## Hardware Requirements

### Minimum (Fallback Mode)
- **RAM**: 512 MB
- **CPU**: Dual-core processor
- **Storage**: 1 GB free space
- **Network**: Stable internet connection

### Recommended (Full Features)
- **RAM**: 2 GB or more
- **CPU**: Quad-core processor or better
- **Storage**: 5 GB free space
- **Network**: Stable, high-speed internet connection
- **GPU**: Optional (for faster processing)

## Operating System Support

- **Windows**: 10 or later
- **macOS**: 10.15 (Catalina) or later
- **Linux**: Ubuntu 18.04 or later (or equivalent)

## Browser Requirements (Chrome Extension)

- **Chrome**: Version 90 or later
- **Brave**: Version 1.20 or later
- **Edge**: Version 90 or later

## Python Dependencies

See `backend/requirements.txt` for complete list:

### Core
- fastapi==0.116.1
- uvicorn==0.35.0
- pydantic==2.11.7
- python-multipart==0.0.20
- python-dotenv==1.0.0
- requests>=2.32,<3

### Audio Processing
- faster-whisper==1.1.1

### File Processing
- PyPDF2==4.0.1
- python-docx==0.8.11
- pandas==2.2.0

## Node.js Dependencies

See `dashboard/package.json` for complete list:

### Core
- react@18+
- react-dom@18+
- vite (dev server)

## Network Requirements

- **Outbound HTTPS**: Required for NVIDIA API (https://integrate.api.nvidia.com)
- **Port 8000**: Backend API (configurable)
- **Port 5173**: Frontend dev server (configurable)
- **Bandwidth**: Minimum 1 Mbps for API calls

## Optional Requirements

### For Development
- **Git**: For version control
- **VS Code**: Recommended editor
- **Postman**: For API testing

### For Production Deployment
- **Docker**: For containerization
- **nginx**: For reverse proxy
- **PM2**: For process management
- **SSL Certificate**: For HTTPS

## Installation Verification

### Check Python
```bash
python --version  # Should be 3.11+
pip --version     # Should be latest
```

### Check Node.js
```bash
node --version    # Should be 16+
npm --version     # Should be 8+
```

### Check NVIDIA API Access
```bash
# Test with curl (replace YOUR_KEY)
curl -X GET "https://integrate.api.nvidia.com/v1/models" \
  -H "Authorization: Bearer YOUR_KEY"
```

## Troubleshooting

### Python Version Issues
```bash
# If python3 is needed
python3 --version
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### Port Already in Use
```bash
# Change port in backend
python -m uvicorn main:app --port 8001

# Change port in frontend
npm run dev -- --port 5174
```

### NVIDIA API Key Issues
- Verify key is correctly set in `.env`
- Check key has not expired
- Ensure key has API access enabled
- Test connectivity to https://integrate.api.nvidia.com

### Memory Issues
- Close unnecessary applications
- Increase available RAM
- Use fallback mode (automatic if API fails)
- Process shorter audio files

## Performance Tips

1. **Use SSD** for faster file operations
2. **Stable Internet** for consistent API performance
3. **Close Background Apps** to free up RAM
4. **Use Latest Drivers** for GPU acceleration (if available)
5. **Regular Cleanup** of old transcripts and logs

## Security Considerations

- Keep NVIDIA API key private (never commit to git)
- Use `.env` file for sensitive configuration
- Enable HTTPS in production
- Regularly update dependencies
- Use firewall to restrict API access

## Support

For issues or questions about requirements:
- Check the main README.md
- Review troubleshooting section
- Check GitHub issues
- Contact support team
