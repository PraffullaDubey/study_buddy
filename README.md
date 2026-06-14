# Study Buddy — Voice Learning Assistant

A voice-first conversational AI tutor for visually impaired and blind students.
Powered by **Ollama + llama3.2**, **faster-whisper** (speech-to-text), and
**macOS native TTS** (`say` command).

---

## Quick Start (macOS M4)

```bash
# 1. Place this folder anywhere, then:
cd study_buddy

# 2. One command to install everything and launch:
chmod +x run.sh && ./run.sh
```

The browser opens automatically at http://localhost:8080

---

## Manual Start

```bash
# Terminal 1 — Ollama
ollama serve

# Terminal 2 — Study Buddy
pip3 install -r requirements.txt --break-system-packages
python3 app.py
```

---

## How It Works

```
Student speaks
      │
      ▼
[Browser captures audio via Web MediaRecorder API]
      │
      ▼
[POST /api/transcribe]
[faster-whisper Whisper base model → text transcript]
      │
      ▼
[POST /api/chat]
[Ollama llama3.2 with Study Buddy system prompt → response text]
      │
      ▼
[POST /api/speak]
[macOS `say` command → device speakers]
      │
      ▼
Student hears the answer → asks follow-up
```

---

## Keyboard Shortcuts

| Key       | Action                              |
|-----------|-------------------------------------|
| Space     | Start / stop recording              |
| Enter     | Send typed question                 |

---

## Configuration

Edit `app.py` top section:

| Variable              | Default       | Options                            |
|-----------------------|---------------|------------------------------------|
| `OLLAMA_MODEL`        | `llama3.2`    | Any model you've pulled in Ollama  |
| `WHISPER_MODEL_SIZE`  | `base`        | `tiny` (faster) / `small` (accurate) |
| Voice                 | `Aman`    | Any macOS voice (see Voice dropdown) |

---

## Voices available on macOS

Run `say -v ?` in Terminal to see all installed voices.
Popular English ones: Samantha, Alex, Karen, Daniel, Moira, Tessa

---

## Troubleshooting

**"Cannot connect to Ollama"**
→ Run `ollama serve` in a terminal first

**"No speech detected"**
→ Allow microphone access in System Settings → Privacy → Microphone → Browser

**Whisper downloads taking long**
→ First run downloads ~150 MB. Subsequent runs are instant.

**Audio not playing**
→ Check System Settings → Sound → Output is set to your speakers
