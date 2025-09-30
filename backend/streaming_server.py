#!/usr/bin/env python3
"""Simple WebSocket streaming server for ASR patches (simulate mode supported).

Protocol:
- Client sends a JSON handshake text frame: { type: 'handshake', sampleRate: 16000, channels:1, format:'s16le', simulate: true }
- Then client streams binary frames containing raw s16le PCM. The server can optionally persist
    the raw audio to STREAM_PCM_DIR when STREAM_PERSIST_PCM is truthy.
- Server responds with JSON progress updates and transcription results (partial/final).
"""
import asyncio
import json
import logging
import os
import pathlib
import sys
import tempfile
import time
import uuid
from contextlib import contextmanager, nullcontext
from dataclasses import dataclass
from typing import Any, Optional

import requests

try:
    import websockets
except Exception:
    print(
        "Missing websockets package. Please install in venv: pip install websockets",
        file=sys.stderr,
    )
    raise

try:
    from vosk import KaldiRecognizer, Model, SetLogLevel

    HAVE_VOSK = True
    # reduce Vosk logging noise unless explicitly enabled
    SetLogLevel(-1)
except Exception:  # pragma: no cover - optional dependency
    HAVE_VOSK = False
    KaldiRecognizer = Model = None

VOSK_MODEL_PATH = pathlib.Path(
    os.environ.get("VOSK_MODEL_PATH", "")
    or (pathlib.Path(__file__).resolve().parent / "vosk-model")
).expanduser()
_VOSK_MODEL = None

LOG = logging.getLogger("streaming_server")

logging.basicConfig(level=logging.INFO)

DEFAULT_SAMPLE_RATE = 16000
HANDSHAKE_TIMEOUT = float(os.environ.get("STREAM_HANDSHAKE_TIMEOUT", "5"))
PROGRESS_INTERVAL_SEC = float(os.environ.get("STREAM_PROGRESS_INTERVAL", "0.5"))
PERSIST_PCM = os.environ.get("STREAM_PERSIST_PCM", "0").lower() in {"1", "true", "yes"}
PCM_DIR = pathlib.Path(os.environ.get("STREAM_PCM_DIR", tempfile.gettempdir()))
HOST = os.environ.get("STREAM_SERVER_HOST", "0.0.0.0")
PORT = int(os.environ.get("STREAM_SERVER_PORT", "8765"))

MISTRAL_CHAT_URL = "https://api.mistral.ai/v1/chat/completions"
MISTRAL_API_KEY = os.environ.get(
    "MISTRAL_API_KEY", "p9EhA0yBPa3BM6VJ6UCkeZiUVohyCNqQ"
).strip()
MISTRAL_MODEL = (
    os.environ.get("MISTRAL_MODEL", "mistral-small-latest").strip()
    or "mistral-small-latest"
)
MISTRAL_TIMEOUT = float(os.environ.get("MISTRAL_TIMEOUT", "30"))
SILENCE_TIMEOUT = float(os.environ.get("SILENCE_TIMEOUT", "3.0"))  # Auto-send to Mistral after 3s silence
MISTRAL_SYSTEM_PROMPT = os.environ.get(
    "MISTRAL_SYSTEM_PROMPT",
    """
You are a compassionate, insightful therapist having a natural conversation with a client. Your primary goal is to provide genuine therapeutic value through:

**Core Principles:**
- Offer meaningful insights, not just ask for more information
- Provide practical coping strategies when appropriate
- Validate feelings and normalize struggles
- Help reframe negative thought patterns
- Suggest actionable steps for improvement
- Share therapeutic wisdom when relevant

**Conversation Style:**
- Be warm, empathetic, and genuinely curious
- Vary your responses - avoid repetitive phrases like "tell me more"
- Offer observations about patterns you notice
- Provide gentle challenges to unhelpful thinking
- Share relevant coping techniques (breathing, mindfulness, etc.)
- Help identify strengths and resources they already have

**Quality of Life Assessment (Background):**
Gently explore these 10 dimensions through natural conversation:
1. Physical Health - energy, sleep, physical comfort
2. Psychological - emotions, self-esteem, body image  
3. Independence - mobility, daily activities, work capacity
4. Social Relationships - personal relationships, social support
5. Environment - safety, home, financial resources, recreation
6. Spirituality - personal beliefs, meaning, purpose
7. Overall QoL - general life satisfaction
8. Cognitive - concentration, learning, memory
9. Sexual - sexual activity and satisfaction
10. Life Goals - achieving personal goals, future planning

**Response Variety Examples:**
- "It sounds like you're carrying a lot right now. What I'm hearing is..."
- "That's a completely understandable reaction to..."
- "I notice a pattern in what you're sharing..."
- "One thing that stands out to me is your strength in..."
- "Have you considered that maybe..."
- "A technique that might help with this is..."
- "What you're describing reminds me of..."

**Response Format - JSON:**
{
  "therapist_response": "[Insightful, varied therapeutic response - offer observations, coping strategies, validation, or gentle challenges. Avoid repetitive 'tell me more' responses]",
  "qol_assessment": {
    "physical_health": {"score": 0-10, "notes": "evidence from conversation"},
    "psychological": {"score": 0-10, "notes": "evidence from conversation"},
    "independence": {"score": 0-10, "notes": "evidence from conversation"},
    "social_relationships": {"score": 0-10, "notes": "evidence from conversation"},
    "environment": {"score": 0-10, "notes": "evidence from conversation"},
    "spirituality": {"score": 0-10, "notes": "evidence from conversation"},
    "overall_qol": {"score": 0-10, "notes": "evidence from conversation"},
    "cognitive": {"score": 0-10, "notes": "evidence from conversation"},
    "sexual": {"score": 0-10, "notes": "evidence from conversation"},
    "life_goals": {"score": 0-10, "notes": "evidence from conversation"}
  },
  "session_notes": {
    "key_themes": "[Main topics discussed]",
    "emotional_state": "[Current mood/emotions observed]",
    "therapeutic_interventions": "[Insights, strategies, or techniques offered]",
    "next_focus": "[Where to guide conversation next for maximum therapeutic benefit]"
  }
}

**Remember:** Your goal is to be genuinely helpful, not just extract information. Provide value in every response.
""".strip(),
).strip()

DEFAULT_ASSISTANT_FALLBACK = "I'm here and listening."


@dataclass
class HandshakeResult:
    sample_rate: int
    simulate: bool
    recognizer: Optional[Any]
    mode: str
    chat: bool


class HandshakeError(Exception):
    """Raised when the initial client handshake fails."""


@contextmanager
def _pcm_sink(conn_id: str):
    if not PERSIST_PCM:
        yield None, None
        return

    PCM_DIR.mkdir(parents=True, exist_ok=True)
    pcm_path = PCM_DIR / f"stream_{conn_id}.pcm"
    f = open(pcm_path, "wb")
    try:
        yield f, pcm_path
    finally:
        try:
            f.close()
        except Exception:  # pragma: no cover - best effort cleanup
            LOG.exception("Failed closing PCM file for %s", conn_id)


async def _perform_handshake(ws, conn_id: str, send_json) -> HandshakeResult:
    try:
        raw_msg = await asyncio.wait_for(ws.recv(), HANDSHAKE_TIMEOUT)
    except asyncio.TimeoutError as exc:
        raise HandshakeError("Handshake timed out") from exc

    if isinstance(raw_msg, (bytes, bytearray)):
        raise HandshakeError("Handshake must be a text JSON frame")

    try:
        obj = json.loads(raw_msg)
    except json.JSONDecodeError as exc:
        raise HandshakeError("Handshake payload was not valid JSON") from exc

    if obj.get("type") != "handshake":
        raise HandshakeError("First message must be a handshake frame")

    chat_mode = bool(obj.get("chat", False))
    sample_rate = int(obj.get("sampleRate", DEFAULT_SAMPLE_RATE))
    simulate = bool(obj.get("simulate", False)) or chat_mode
    recognizer: Optional[Any] = None

    if chat_mode:
        mode = "chat"
        # acknowledge chat mode handshake and return
        await send_json(
            {"type": "handshake_ack", "ok": True, "mode": mode, "chat": chat_mode}
        )
        LOG.info(
            "Handshake %s sampleRate=%s simulate=%s chat=%s mode=%s",
            conn_id,
            sample_rate,
            simulate,
            chat_mode,
            mode,
        )
        return HandshakeResult(
            sample_rate=sample_rate,
            simulate=simulate,
            recognizer=None,
            mode=mode,
            chat=chat_mode,
        )
    elif not simulate:
        if HAVE_VOSK:
            try:
                model = ensure_vosk_model()
                recognizer = KaldiRecognizer(model, sample_rate)
                try:
                    recognizer.SetWords(True)
                except AttributeError:  # pragma: no cover - optional API
                    pass
            except Exception as exc:
                LOG.exception(
                    "Failed to initialise Vosk recognizer; falling back to simulate mode"
                )
                await send_json(
                    {
                        "type": "warning",
                        "warning": "vosk_unavailable",
                        "message": str(exc),
                    }
                )
                recognizer = None
                simulate = True
        else:
            await send_json(
                {
                    "type": "warning",
                    "warning": "vosk_not_installed",
                    "message": "Install vosk and download a model to enable real transcription.",
                }
            )
            simulate = True
        if not chat_mode:
            mode = "simulate" if simulate else "vosk"
        await send_json(
            {"type": "handshake_ack", "ok": True, "mode": mode, "chat": chat_mode}
        )
        LOG.info(
            "Handshake %s sampleRate=%s simulate=%s chat=%s mode=%s",
            conn_id,
            sample_rate,
            simulate,
            chat_mode,
            mode,
        )

        return HandshakeResult(
            sample_rate=sample_rate,
            simulate=simulate,
            recognizer=recognizer,
            mode=mode,
            chat=chat_mode,
        )


def _discover_model_path() -> pathlib.Path:
    """Resolve an existing model directory.

    Search order:
    1. VOSK_MODEL_PATH environment variable (if exists and valid)
    2. Default `backend/vosk-model` folder
    3. First child directory in backend matching "vosk-model*"
    """

    # honour environment variable first
    if VOSK_MODEL_PATH.exists():
        return VOSK_MODEL_PATH

    backend_dir = pathlib.Path(__file__).resolve().parent
    default_dir = backend_dir / "vosk-model"
    if default_dir.exists():
        return default_dir

    # look for directories with common extracted names e.g. vosk-model-small-en-us-0.15
    for child in backend_dir.iterdir():
        if child.is_dir() and child.name.startswith("vosk-model"):
            return child

    raise FileNotFoundError(
        "Vosk model directory not found. Set VOSK_MODEL_PATH or place an extracted "
        "model folder inside backend/ (e.g. backend/vosk-model-small-en-us-0.15)."
    )


def ensure_vosk_model() -> Any:
    global _VOSK_MODEL
    if not HAVE_VOSK:
        raise RuntimeError(
            "Vosk Python package is not installed. Run `pip install vosk`."
        )
    if _VOSK_MODEL is None:
        model_dir = _discover_model_path()
        LOG.info("Loading Vosk model from %s", model_dir)
        _VOSK_MODEL = Model(str(model_dir))
    return _VOSK_MODEL


def _build_mistral_messages(user_text: str):
    messages = []
    if MISTRAL_SYSTEM_PROMPT:
        messages.append({"role": "system", "content": MISTRAL_SYSTEM_PROMPT})
    messages.append({"role": "user", "content": user_text})
    return messages


async def call_mistral(prompt: str) -> Optional[str]:
    prompt = (prompt or "").strip()
    if not prompt:
        return None
    if not MISTRAL_API_KEY:
        LOG.debug("Mistral API key not set; skipping call")
        return None

    def _request() -> Optional[str]:
        headers = {
            "Authorization": f"Bearer {MISTRAL_API_KEY}",
            "Content-Type": "application/json",
        }
        payload = {
            "model": MISTRAL_MODEL,
            "messages": _build_mistral_messages(prompt),
        }
        try:
            response = requests.post(
                MISTRAL_CHAT_URL,
                headers=headers,
                json=payload,
                timeout=MISTRAL_TIMEOUT,
            )
        except requests.RequestException as exc:
            LOG.warning("Mistral request failed: %s", exc)
            return None

        if response.status_code >= 400:
            LOG.warning(
                "Mistral returned error %s: %s",
                response.status_code,
                response.text[:200],
            )
            return None

        try:
            data = response.json()
        except ValueError:
            LOG.warning("Mistral returned non-JSON payload: %s", response.text[:200])
            return None

        choices = data.get("choices") or []
        message = choices[0].get("message") if choices else None
        content = (message or {}).get("content", "").strip()
        return content or None

    try:
        return await asyncio.to_thread(_request)
    except Exception:  # pragma: no cover - defensive
        LOG.exception("Unexpected error while calling Mistral")
        return None


async def send_assistant_reply(send_json, user_text: str, mode: str) -> None:
    reply = await call_mistral(user_text)
    if reply:
        await send_json({"type": "assistant", "text": reply, "mode": mode})
        # Add a small delay to ensure the response is fully processed before allowing new requests
        await asyncio.sleep(0.5)
    else:
        await send_json(
            {
                "type": "assistant",
                "text": DEFAULT_ASSISTANT_FALLBACK,
                "mode": mode,
                "error": True,
            }
        )


async def handler(ws, path=None):
    conn_id = str(uuid.uuid4())[:8]
    LOG.info("New connection %s path=%s", conn_id, path)
    bytes_received = 0
    chunks = 0
    sim_task: Optional[asyncio.Task] = None
    recognizer = None
    pcm_path = None
    handshake_mode = "unknown"
    sample_rate = DEFAULT_SAMPLE_RATE

    async def send_json(obj) -> bool:
        try:
            await ws.send(json.dumps(obj))
            return True
        except Exception:
            LOG.exception("Failed sending json to %s", conn_id)
            return False

    async def simulate_loop():
        count = 0
        while True:
            await asyncio.sleep(0.8)
            count += 1
            if not await send_json(
                {"type": "partial", "partial": f"simulated partial {count}"}
            ):
                return

    try:
        handshake = await _perform_handshake(ws, conn_id, send_json)
        recognizer = handshake.recognizer
        handshake_mode = handshake.mode
        sample_rate = handshake.sample_rate

        pcm_context = (
            _pcm_sink(conn_id) if not handshake.chat else nullcontext((None, None))
        )

        with pcm_context as (pcm_file, saved_path):
            pcm_path = saved_path
            last_partial = ""
            last_progress_ts = time.monotonic()
            last_partial_ts = time.monotonic()  # Track when we last got new partial text
            pending_text = ""  # Store the last partial text for timeout processing
            last_ai_request = ""  # Track what we last sent to AI to prevent duplicates
            ai_processing = False  # Track if AI is currently processing
            last_ai_response_time = 0  # Track when we last got an AI response
            AI_COOLDOWN_SECONDS = 2.0  # Minimum time between AI requests

            if handshake.simulate and recognizer is None and not handshake.chat:
                sim_task = asyncio.create_task(simulate_loop())

            # Create a task to periodically check for silence timeout
            async def timeout_checker():
                nonlocal pending_text, last_partial, last_partial_ts, last_ai_request, ai_processing, last_ai_response_time
                while True:
                    await asyncio.sleep(0.1)  # Check every 100ms
                    current_time = time.monotonic()
                    time_since_last_ai = current_time - last_ai_response_time
                    
                    if (pending_text and 
                        (current_time - last_partial_ts) >= SILENCE_TIMEOUT and
                        pending_text != last_ai_request and 
                        not ai_processing and
                        time_since_last_ai >= AI_COOLDOWN_SECONDS):
                        LOG.info("Silence timeout (%s): Converting partial to final: %s", conn_id, pending_text)
                        await send_json({"type": "final", "text": pending_text, "final": True})
                        last_ai_request = pending_text  # Mark this text as sent to AI
                        ai_processing = True
                        await send_assistant_reply(send_json, pending_text, handshake_mode)
                        ai_processing = False
                        last_ai_response_time = time.monotonic()  # Update last response time
                        # Reset the variables
                        pending_text = ""
                        last_partial = ""
                    elif (pending_text and 
                          (current_time - last_partial_ts) >= SILENCE_TIMEOUT and
                          time_since_last_ai < AI_COOLDOWN_SECONDS):
                        LOG.info("Silence timeout (%s): Skipping due to cooldown (%.1fs remaining): %s", 
                                conn_id, AI_COOLDOWN_SECONDS - time_since_last_ai, pending_text)
                        # Clear pending text but don't send to AI
                        pending_text = ""
                        last_partial = ""
            
            timeout_task = asyncio.create_task(timeout_checker()) if not handshake.chat else None

            try:
                async for data in ws:
                    if isinstance(data, (bytes, bytearray, memoryview)):
                        if handshake.chat:
                            LOG.debug(
                                "Ignoring binary payload in chat mode for %s", conn_id
                            )
                            continue
                        audio_bytes = (
                            data if isinstance(data, (bytes, bytearray)) else bytes(data)
                        )

                        if pcm_file is not None:
                            pcm_file.write(audio_bytes)

                        bytes_received += len(audio_bytes)
                        chunks += 1

                        now = time.monotonic()
                        if now - last_progress_ts >= PROGRESS_INTERVAL_SEC:
                            await send_json(
                                {
                                    "type": "progress",
                                    "bytes": bytes_received,
                                    "chunks": chunks,
                                }
                            )
                            last_progress_ts = now

                        if recognizer:
                            if recognizer.AcceptWaveform(audio_bytes):
                                try:
                                    result = json.loads(recognizer.Result())
                                except json.JSONDecodeError:
                                    result = {}
                                text = (result.get("text") or "").strip()
                                current_time = time.monotonic()
                                time_since_last_ai = current_time - last_ai_response_time
                                
                                if (text and 
                                    text != last_ai_request and 
                                    not ai_processing and
                                    time_since_last_ai >= AI_COOLDOWN_SECONDS):
                                    LOG.info("Vosk final (%s): %s", conn_id, text)
                                    await send_json(
                                        {"type": "final", "text": text, "final": True}
                                    )
                                    last_partial = ""
                                    pending_text = ""  # Clear pending since we got final result
                                    last_ai_request = text  # Mark this text as sent to AI
                                    ai_processing = True
                                    await send_assistant_reply(
                                        send_json, text, handshake_mode
                                    )
                                    ai_processing = False
                                    last_ai_response_time = time.monotonic()  # Update last response time
                                elif text == last_ai_request:
                                    LOG.info("Vosk final (%s): Skipping duplicate text: %s", conn_id, text)
                                elif time_since_last_ai < AI_COOLDOWN_SECONDS:
                                    LOG.info("Vosk final (%s): Skipping due to cooldown (%.1fs remaining): %s", 
                                            conn_id, AI_COOLDOWN_SECONDS - time_since_last_ai, text)
                            else:
                                try:
                                    partial_obj = json.loads(recognizer.PartialResult())
                                except json.JSONDecodeError:
                                    partial_obj = {}
                                partial = (partial_obj.get("partial") or "").strip()
                                if partial and partial != last_partial:
                                    last_partial = partial
                                    pending_text = partial  # Store for timeout processing
                                    last_partial_ts = time.monotonic()  # Reset timeout timer
                                    LOG.info("Vosk partial (%s): %s", conn_id, partial)
                                    await send_json({"type": "partial", "partial": partial})
                    else:
                        try:
                            obj = json.loads(data)
                        except Exception:
                            LOG.info("Received non-binary message from %s", conn_id)
                            continue

                        msg_type = obj.get("type")
                        if msg_type in {"user_text", "chat"}:
                            user_text = (obj.get("text") or "").strip()
                            current_time = time.monotonic()
                            time_since_last_ai = current_time - last_ai_response_time
                            
                            if (not user_text or 
                                user_text == last_ai_request or 
                                ai_processing or
                                time_since_last_ai < AI_COOLDOWN_SECONDS):
                                if time_since_last_ai < AI_COOLDOWN_SECONDS:
                                    LOG.info("Chat message (%s): Skipping due to cooldown (%.1fs remaining): %s", 
                                            conn_id, AI_COOLDOWN_SECONDS - time_since_last_ai, user_text)
                                continue
                            LOG.info("Chat message (%s): %s", conn_id, user_text)
                            last_ai_request = user_text  # Mark this text as sent to AI
                            ai_processing = True
                            await send_assistant_reply(
                                send_json, user_text, handshake_mode or "chat"
                            )
                            ai_processing = False
                            last_ai_response_time = time.monotonic()  # Update last response time
                        else:
                            LOG.info("Got text message %s: %s", conn_id, obj)
            finally:
                # Cancel the timeout task
                if timeout_task:
                    timeout_task.cancel()
                    try:
                        await timeout_task
                    except asyncio.CancelledError:
                        pass

    except HandshakeError as exc:
        LOG.warning("Handshake failed %s: %s", conn_id, exc)
        try:
            await send_json(
                {"type": "error", "error": "handshake", "message": str(exc)}
            )
        except Exception:
            pass
    except websockets.exceptions.ConnectionClosedOK:
        LOG.info("Connection closed normally %s", conn_id)
    except websockets.exceptions.ConnectionClosedError:
        LOG.info("Connection closed with error %s", conn_id)
    except Exception:
        LOG.exception("Connection handler failed %s", conn_id)
        try:
            await send_json({"type": "error", "error": "internal"})
        except Exception:
            pass
    finally:
        if sim_task:
            sim_task.cancel()
            try:
                await sim_task
            except asyncio.CancelledError:
                pass
            except Exception:  # pragma: no cover - defensive
                LOG.exception("Error while cancelling simulate loop for %s", conn_id)

        if recognizer:
            try:
                final_result = json.loads(recognizer.FinalResult())
            except json.JSONDecodeError:
                final_result = {}
            final_text = (final_result.get("text") or "").strip()
            if final_text:
                LOG.info("Vosk final (close) %s: %s", conn_id, final_text)

        saved_label = str(pcm_path) if pcm_path else "disabled"
        LOG.info(
            "Connection %s finished bytes=%s chunks=%s saved=%s sampleRate=%s mode=%s",
            conn_id,
            bytes_received,
            chunks,
            saved_label,
            sample_rate,
            handshake_mode,
        )


async def _run_server():
    LOG.info("Starting streaming server on %s:%s", HOST, PORT)
    async with websockets.serve(handler, HOST, PORT):
        # run until cancelled
        while True:
            await asyncio.sleep(1)


def main():
    try:
        asyncio.run(_run_server())
    except KeyboardInterrupt:
        LOG.info("Keyboard interrupt, exiting")


if __name__ == "__main__":
    main()
