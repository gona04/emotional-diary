# Emotional Diary

Emotional Diary is one of my most passionate projects, blending my background in arts with my enthusiasm for psychology and coding. This innovative app allows users to write daily diary entries, which are then analyzed to identify any cognitive distortions or thinking traps.

Currently, the app is a work in progress, as it is built upon an abstract and evolving concept. I am committed to continuously improving it and welcome any suggestions or feedback to enhance its functionality.

Thank you for your interest in Emotional Diary.

Possible features helping with CBT and DBT way of therapy.

## Getting Started

This project includes two main components:

1. **React frontend** (in `frontend/` directory)
2. **WebSocket streaming server** for speech-to-text and AI chat (in `backend/` directory)

### Requirements

- Node 18+
- Python 3.10+ (virtual environment recommended)
- A [Mistral AI](https://docs.mistral.ai/api/) API key
- (Optional) A Vosk model for on-device transcription. The repo ships with `backend/vosk-model-small-en-us-0.15` as a default.

### Environment variables

Create a `.env` file in the `frontend/` directory with:

```
REACT_APP_STREAMING_WS_URL=ws://localhost:8765
```

Configure the backend via environment variables (e.g. shell export or .env file):

```
MISTRAL_API_KEY=your_mistral_key
MISTRAL_MODEL=mistral-small-latest
MISTRAL_TIMEOUT=30
MISTRAL_SYSTEM_PROMPT="You are a compassionate journaling companion."
```

### Backend setup

```bash
cd backend
python -m venv .venv
source .venv/bin/activate  # On Windows use .venv\Scripts\activate
pip install -r requirements.txt
python streaming_server.py
```

You should see logs like `server listening on 0.0.0.0:8765`. The frontend microphone button connects to this server and streams audio patches for transcription. Final transcripts are dispatched to the chat and forwarded to the Mistral backend.

### Frontend setup

```bash
cd frontend
npm install
npm start
```

The UI opens at http://localhost:3000. The chat panel and microphone now exchange both transcripts and assistant replies directly with the streaming WebSocket server, which relays prompts to Mistral and streams the responses back to the browser.
