@echo off
echo Setting up LLaMA 3 with Ollama...
echo.

echo Step 1: Installing Ollama...
echo Please download and install Ollama from: https://ollama.ai/download
echo.
echo After installation, run these commands in a new terminal:
echo   ollama pull llama3
echo   ollama serve
echo.

echo Step 2: Verifying Ollama installation...
curl -s http://localhost:11434/api/tags > nul 2>&1
if %errorlevel% == 0 (
    echo ✓ Ollama server is running
    echo.
    echo Step 3: Checking available models...
    curl -s http://localhost:11434/api/tags
) else (
    echo ✗ Ollama server is not running
    echo Please start Ollama by running: ollama serve
    echo Then pull the LLaMA 3 model: ollama pull llama3
)

echo.
echo Setup complete! You can now start the backend server.
pause