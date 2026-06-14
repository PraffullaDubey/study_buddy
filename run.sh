#!/bin/bash
# ─────────────────────────────────────────────────────────────────
#  Study Buddy — Setup & Run Script (macOS M4)
# ─────────────────────────────────────────────────────────────────

set -e

echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║           STUDY BUDDY — SETUP & LAUNCH              ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

# 1. Check Ollama
echo "▸ Checking Ollama..."
if ! command -v ollama &>/dev/null; then
  echo "  ✗ Ollama not found. Install from https://ollama.com"
  exit 1
fi
echo "  ✓ Ollama found"

# 2. Check llama3.2 model
echo "▸ Checking llama3.2 model..."
if ! ollama list 2>/dev/null | grep -q "llama3.2"; then
  echo "  ↓ Pulling llama3.2 (first time only, ~2 GB)..."
  ollama pull llama3.2
fi
echo "  ✓ llama3.2 ready"

# 3. Start Ollama serve in background if not running
echo "▸ Starting Ollama server..."
if ! curl -s http://localhost:11434/api/tags &>/dev/null; then
  ollama serve &>/dev/null &
  sleep 2
  echo "  ✓ Ollama server started"
else
  echo "  ✓ Ollama server already running"
fi

# 4. Install Python dependencies
echo "▸ Installing Python dependencies..."
pip3 install flask flask-cors faster-whisper sounddevice soundfile numpy requests --break-system-packages -q
echo "  ✓ Dependencies installed"

# 5. Open browser
echo "▸ Launching browser..."
sleep 1
open https://localhost:8080 &

# 6. Start Flask
echo ""
echo "╔══════════════════════════════════════════════════════╗"
echo "║  Study Buddy running at  http://localhost:8080       ║"
echo "║  Press Ctrl+C to stop                               ║"
echo "╚══════════════════════════════════════════════════════╝"
echo ""

python3 app.py