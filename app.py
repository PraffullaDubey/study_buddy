"""
Study Buddy - Voice Conversational AI for Visually Impaired Students
Backend: Flask + Ollama (llama3.2) + faster-whisper + macOS TTS
Served over HTTPS so Safari grants microphone access.
"""

import os
import uuid
import subprocess
import tempfile
import threading
import requests
from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from faster_whisper import WhisperModel

BASE_DIR   = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
CERT_FILE  = os.path.join(BASE_DIR, "cert.pem")
KEY_FILE   = os.path.join(BASE_DIR, "key.pem")

app = Flask(__name__, static_folder=STATIC_DIR)
CORS(app)

# Config
OLLAMA_URL         = "http://localhost:11434/api/chat"
OLLAMA_MODEL       = "llama3.2"
WHISPER_MODEL_SIZE = "base"   # tiny | base | small | medium
TMP_DIR            = tempfile.gettempdir()

# Load Whisper once at startup
print("Loading Whisper model...")
whisper_model = WhisperModel(WHISPER_MODEL_SIZE, device="cpu", compute_type="int8")
print("Whisper ready.")

# Conversation history 
conversations: dict[str, list] = {}

SYSTEM_PROMPT = """You are Study Buddy, a warm, enthusiastic, and encouraging AI tutor
designed for students who are visually impaired or blind. You explain topics through
vivid storytelling, memorable analogies, real-world examples, and fun facts that make
learning exciting. Always use sound-friendly language — no tables, no bullet lists with
symbols. Use short numbered steps when listing things. Keep your tone friendly, clear,
and engaging like an exciting radio presenter meets a brilliant teacher.
Vary your pacing with enthusiasm. Add a fun wow-fact when relevant.
Responses should be concise (under 200 words) unless the student asks for more detail."""


# SSL cert generation
def ensure_ssl_cert():
    """Generate a self-signed cert if not already present."""
    if os.path.exists(CERT_FILE) and os.path.exists(KEY_FILE):
        return
    print("Generating self-signed SSL certificate...")
    result = subprocess.run([
        "openssl", "req", "-x509", "-newkey", "rsa:2048",
        "-keyout", KEY_FILE,
        "-out",    CERT_FILE,
        "-days",   "365",
        "-nodes",
        "-subj",   "/CN=localhost",
        "-addext", "subjectAltName=DNS:localhost,IP:127.0.0.1"
    ], capture_output=True, text=True)
    if result.returncode != 0:
        print("openssl error:", result.stderr)
    else:
        print("SSL certificate generated.")


# Routes

@app.route("/")
def index():
    return send_from_directory(STATIC_DIR, "index.html")


@app.route("/api/transcribe", methods=["POST"])
def transcribe():
    """Receive audio blob, transcribe via faster-whisper."""
    if "audio" not in request.files:
        return jsonify({"error": "No audio file"}), 400

    audio_file = request.files["audio"]
    filename   = audio_file.filename or "recording.webm"
    ext        = os.path.splitext(filename)[-1].lower() or ".webm"
    tmp_path   = os.path.join(TMP_DIR, f"sb_{uuid.uuid4().hex}{ext}")
    audio_file.save(tmp_path)

    print(f"[transcribe] saved {filename} ({os.path.getsize(tmp_path)} bytes)")

    try:
        segments, info = whisper_model.transcribe(
            tmp_path,
            language="en",
            vad_filter=True,
            vad_parameters={"min_silence_duration_ms": 300},
        )
        text = " ".join(seg.text.strip() for seg in segments).strip()
        print(f"[transcribe] lang={info.language} text={text!r}")
    except Exception as e:
        print(f"[transcribe] ERROR: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        if os.path.exists(tmp_path):
            os.remove(tmp_path)

    if not text:
        return jsonify({"transcript": "", "error": "No speech detected"})

    return jsonify({"transcript": text})


@app.route("/api/chat", methods=["POST"])
def chat():
    """Send message to Ollama, return response text."""
    data       = request.get_json()
    session_id = data.get("session_id", "default")
    user_msg   = data.get("message", "").strip()

    if not user_msg:
        return jsonify({"error": "Empty message"}), 400

    if session_id not in conversations:
        conversations[session_id] = []

    conversations[session_id].append({"role": "user", "content": user_msg})

    payload = {
        "model":    OLLAMA_MODEL,
        "messages": [{"role": "system", "content": SYSTEM_PROMPT}]
                    + conversations[session_id],
        "stream":   False,
    }

    try:
        resp = requests.post(OLLAMA_URL, json=payload, timeout=60)
        resp.raise_for_status()
        assistant_text = resp.json()["message"]["content"].strip()
    except requests.exceptions.ConnectionError:
        return jsonify({"error": "Cannot connect to Ollama. Run: ollama serve"}), 503
    except Exception as e:
        return jsonify({"error": str(e)}), 500

    conversations[session_id].append({"role": "assistant", "content": assistant_text})
    return jsonify({"response": assistant_text, "session_id": session_id})


@app.route("/api/speak", methods=["POST"])
def speak():
    """Speak text via macOS say command."""
    data  = request.get_json()
    text  = data.get("text", "").strip()
    voice = data.get("voice", "Aman")

    if not text:
        return jsonify({"error": "No text"}), 400

    clean = (text.replace("**", "").replace("*", "")
                 .replace("#", "").replace("`", "").replace("_", " "))

    def _say():
        subprocess.run(["say", "-v", voice, "-r", "175", clean], check=False)

    threading.Thread(target=_say, daemon=True).start()
    return jsonify({"status": "speaking"})


@app.route("/api/stop_speech", methods=["POST"])
def stop_speech():
    subprocess.run(["pkill", "-f", "say"], check=False)
    return jsonify({"status": "stopped"})


@app.route("/api/clear", methods=["POST"])
def clear_session():
    data       = request.get_json()
    session_id = data.get("session_id", "default")
    conversations.pop(session_id, None)
    return jsonify({"status": "cleared"})


@app.route("/api/voices", methods=["GET"])
def list_voices():
    try:
        result = subprocess.run(["say", "-v", "?"], capture_output=True, text=True)
        voices = [line.split()[0] for line in result.stdout.splitlines() if line.strip()]
        return jsonify({"voices": voices[:30]})
    except Exception:
        return jsonify({"voices": ["Aman", "Samantha", "Alex", "Karen", "Daniel"]})


# Main
if __name__ == "__main__":
    ensure_ssl_cert()
    print("\n" + "═" * 55)
    print("  Study Buddy → https://localhost:8080")
    print("  Safari: accept the security warning once,")
    print("  then mic will work perfectly.")
    print("  Make sure Ollama is running: ollama serve")
    print("═" * 55 + "\n")
    app.run(host="0.0.0.0", port=8080, ssl_context=(CERT_FILE, KEY_FILE), debug=False)