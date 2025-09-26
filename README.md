# Emotional Diary

Emotional Diary is one of my most passionate projects, blending my background in arts with my enthusiasm for psychology and coding. This innovative app allows users to write daily diary entries, which are then analyzed to identify any cognitive distortions or thinking traps.

Currently, the app is a work in progress, as it is built upon an abstract and evolving concept. I am committed to continuously improving it and welcome any suggestions or feedback to enhance its functionality.

Thank you for your interest in Emotional Diary.

Possible features helping with CBT and DBT way of therapy.

## Getting Started

This project includes three processes:

1. **React frontend** (`npm start` from the repo root)
2. **Django API** (`python manage.py runserver` inside `backend/helpfuldiary`)
3. **WebSocket streaming server** for speech-to-text (`python streaming_server.py` inside `backend`)

### Requirements

- Node 18+
- Python 3.10+ (virtual environment recommended)
- A [Mistral AI](https://docs.mistral.ai/api/) API key
- (Optional) A Vosk model for on-device transcription. The repo ships with `backend/vosk-model-small-en-us-0.15` as a default.

### Environment variables

Create a `.env` file for the frontend with:

```
REACT_APP_BACKEND_URL=http://localhost:8000
REACT_APP_STREAMING_WS_URL=ws://localhost:8765
```

Configure the backend via environment variables (e.g. `.env` + `python-dotenv` or shell export):

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
cd helpfuldiary
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

### Streaming server

```bash
cd backend
source .venv/bin/activate
python streaming_server.py
```

You should see logs like `server listening on 0.0.0.0:8765`. The frontend microphone button connects to this server and streams audio patches for transcription. Final transcripts are dispatched to the chat and forwarded to the Mistral backend.

### Frontend setup

```bash
npm install
npm start
```

The UI opens at http://localhost:3000. The chat panel calls the Django proxy (`/api/mistral/chat/`) which relays prompts to Mistral and returns the assistant response.
