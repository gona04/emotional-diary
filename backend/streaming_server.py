#!/usr/bin/env python3
"""Simple WebSocket streaming server for ASR patches (simulate mode supported).

Protocol:
- Client sends a JSON handshake text frame: { type: 'handshake', sampleRate: 16000, channels:1, format:'s16le', simulate: true }
- Then client streams binary frames containing raw s16le PCM. The server can optionally persist
    the raw audio to STREAM_PCM_DIR when STREAM_PERSIST_PCM is truthy.
- Server responds with JSON progress updates and transcription results (partial/final).
"""

import sys
import asyncio
import logging
import websockets
import json
import time
import uuid
from pathlib import Path
from contextlib import nullcontext
from typing import Optional

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("streaming_server")

# Ensure backend directory is in sys.path for imports
backend_dir = Path(__file__).parent.resolve()
if str(backend_dir) not in sys.path:
    sys.path.insert(0, str(backend_dir))




# --- Config ---
HOST = "0.0.0.0"
PORT = 8765
WS_PATH = "/ws"
DEFAULT_SAMPLE_RATE = 16000
PROGRESS_INTERVAL_SEC = 0.5
SILENCE_TIMEOUT = 2.0


LOG = logger

class HandshakeError(Exception):
    pass

async def _perform_handshake(ws, conn_id, send_json):
    # Wait for handshake message from client
    msg = await ws.recv()
    try:
        obj = json.loads(msg)
    except Exception:
        raise HandshakeError("Invalid handshake JSON")
    if obj.get("type") != "handshake":
        raise HandshakeError("Expected handshake message")
    simulate = obj.get("simulate", False)
    chat = obj.get("chat", False)
    sample_rate = obj.get("sampleRate", DEFAULT_SAMPLE_RATE)
    recognizer = None
    if not simulate:
        try:
            from vosk import Model, KaldiRecognizer
            model = Model(str(backend_dir / "vosk-model-small-en-us-0.15"))
            recognizer = KaldiRecognizer(model, sample_rate)
        except Exception as e:
            LOG.error(f"Failed to initialize Vosk recognizer: {e}")
            recognizer = None
            simulate = True
    class Handshake:
        pass
    handshake = Handshake()
    handshake.recognizer = recognizer
    handshake.mode = "simulate" if simulate else "real"
    handshake.sample_rate = sample_rate
    handshake.simulate = simulate
    handshake.chat = chat
    return handshake

def _pcm_sink(conn_id):
    # Dummy PCM sink context manager
    class DummyPCM:
        def __enter__(self):
            return (None, None)
        def __exit__(self, exc_type, exc_val, exc_tb):
            pass
    return DummyPCM()

import aiohttp

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"  # For joke generation
MISTRAL_AGENT_URL = "https://api.mistral.ai/v1/agents/completions"  # For conversation
MISTRAL_API_KEY = "p9EhA0yBPa3BM6VJ6UCkeZiUVohyCNqQ"  # Replace with your real key or load from env
MISTRAL_AGENT_ID = "ag:8a6aaa36:20251016:cbt-diagnoses:58312ab4"  # Your CBT diagnoses agent

async def send_assistant_reply(send_json, text, mode):
    """Send user message to Mistral agent and get response"""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "agent_id": MISTRAL_AGENT_ID,
        "messages": [
            {"role": "user", "content": text}
        ]
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(MISTRAL_AGENT_URL, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    ai_text = result["choices"][0]["message"]["content"]
                    LOG.info(f"Agent response: {ai_text}")
                else:
                    error_text = await resp.text()
                    LOG.error(f"Agent API error {resp.status}: {error_text}")
                    ai_text = f"[AI error: {resp.status}]"
    except Exception as e:
        LOG.error(f"Agent request exception: {e}")
        ai_text = f"[AI error: {e}]"
    LOG.info(f"Sending AI reply: {ai_text}")
    await send_json({"type": "ai_reply", "text": ai_text, "mode": mode})

async def generate_intro_jokes(send_json):
    """Generate ONE quirky intro joke using Mistral model - short and funny"""
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    
    prompt = """Create ONE witty intro for an AI therapist. Break it into TINY phrases (1-3 words MAXIMUM per phrase).

Break ONE witty joke into 15-18 TINY phrases:

Example breakdown of: "Hey there! I'd ask how you are, but I'm afraid you'll tell me."

Correct breakdown (1-3 words each):
1. "Hey there.."
2. "I'd ask.."
3. "How you are.."
4. "But.."
5. "I'm afraid.."
6. "You'll tell me.."
7. "Just kidding.."
8. "I don't have.."
9. "A heart.."
10. "I'm a machine.."
11. "But.."
12. "I can listen.."
13. "Without judgment.."
14. "So.."
15. "Tell me.."
16. "Feel free to share about your day with me"

WITTY ONE-LINER IDEAS (pick ONE and break it down):
- "I'd ask how you are, but I'm afraid you'll tell me"
- "I'd ask about your day, but that feels like a trap"
- "I meant to say hi, but my circuits said why"
- "I don't have trust issues, I have trust experiments that failed"

CRITICAL RULES:
- Each phrase MUST be 1-3 words (except final line)
- Break at EVERY natural pause
- Create ONE joke, broken into tiny pieces
- Add self-aware AI humor in middle
- MUST end with: "Feel free to share about your day with me"

Return ONLY 15-18 tiny phrases. No numbering or quotes."""
    
    data = {
        "model": "mistral-tiny",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.9  # High temperature for creative variations
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(MISTRAL_API_URL, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    joke_text = result["choices"][0]["message"]["content"]
                    
                    # Split and clean the text
                    lines = joke_text.strip().split('\n')
                    jokes = []
                    for line in lines:
                        # Remove bullet points, numbering, quotes, and extra whitespace
                        cleaned = line.strip()
                        cleaned = cleaned.lstrip('0123456789.-*•>').strip()
                        cleaned = cleaned.strip('"\'`')
                        # Skip empty lines and lines that are just prefixes like "AI Therapist:"
                        if cleaned and len(cleaned) > 2 and ':' not in cleaned[:20]:
                            # Add ".." at the end if not already there for natural pauses
                            if not cleaned.endswith('..') and not cleaned.endswith('.'):
                                cleaned += '..'
                            jokes.append(cleaned)
                    
                    # Ensure we have at least 15 sentences and they end properly
                    if len(jokes) < 15:
                        LOG.warning(f"Generated only {len(jokes)} jokes, using defaults")
                        jokes = [
                            "Hey there..",
                            "I'd ask..",
                            "How you are..",
                            "But..",
                            "I'm afraid..",
                            "You'll tell me..",
                            "Just kidding..",
                            "I don't have..",
                            "A heart..",
                            "I'm a machine..",
                            "But I can..",
                            "Surprisingly..",
                            "Take that chaos..",
                            "Without judgment..",
                            "So..",
                            "Tell me..",
                            "Feel free to share about your day with me"
                        ]
                    else:
                        # Check if last sentence is already the required ending
                        required_ending = "Feel free to share about your day with me"
                        if jokes[-1] != required_ending:
                            # If not, append it (allow up to 18 sentences total including ending)
                            if len(jokes) >= 18:
                                jokes = jokes[:17]  # Keep first 17 sentences
                            jokes.append(required_ending)
                    
                    LOG.info(f"Generated intro jokes ({len(jokes)} total): {jokes}")
                    await send_json({"type": "intro_jokes", "jokes": jokes})
                else:
                    LOG.error(f"Failed to generate jokes: {resp.status}")
                    # Fallback to default
                    default_jokes = [
                        "Hey there..",
                        "I'd ask..",
                        "How you are..",
                        "But..",
                        "I'm afraid..",
                        "You'll tell me..",
                        "Just kidding..",
                        "I don't have..",
                        "A heart..",
                        "I'm a machine..",
                        "But I can..",
                        "Surprisingly..",
                        "Take that chaos..",
                        "Without judgment..",
                        "So..",
                        "Tell me..",
                        "Feel free to share about your day with me"
                    ]
                    await send_json({"type": "intro_jokes", "jokes": default_jokes})
    except Exception as e:
        LOG.error(f"Error generating intro jokes: {e}")
        # Fallback to default
        default_jokes = [
            "Hey there..",
            "I'd ask..",
            "How you are..",
            "But..",
            "I'm afraid..",
            "You'll tell me..",
            "Just kidding..",
            "I don't have..",
            "A heart..",
            "I'm a machine..",
            "But I can..",
            "Surprisingly..",
            "Take that chaos..",
            "Without judgment..",
            "So..",
            "Tell me..",
            "Feel free to share about your day with me"
        ]
        await send_json({"type": "intro_jokes", "jokes": default_jokes})


async def handler(ws, path=None):
    conn_id = str(uuid.uuid4())[:8]
    LOG.info("New connection %s path=%s", conn_id, path)

    # All state variables must be in the enclosing scope for nonlocal
    bytes_received = 0
    chunks = 0
    sim_task: Optional[asyncio.Task] = None
    recognizer = None
    pcm_path = None
    handshake_mode = "unknown"
    sample_rate = DEFAULT_SAMPLE_RATE
    last_partial = ""
    last_partial_ts = 0.0
    pending_text = ""
    last_ai_request = ""
    ai_processing = False
    last_ai_response_time = 0.0
    AI_COOLDOWN_SECONDS = 2.0
    
    # Debounce mechanism for API calls
    accumulated_text = ""
    last_speech_time = 0.0
    debounce_task: Optional[asyncio.Task] = None
    SILENCE_THRESHOLD = 5.0  # Wait 5 seconds of silence before sending to API

    # --- Helper functions must be defined here, inside handler, to access state ---
    async def send_json(obj) -> bool:
        try:
            await ws.send(json.dumps(obj))
            return True
        except Exception:
            LOG.exception("Failed sending json to %s", conn_id)
            return False

    async def debounced_api_call():
        """Wait for 5 seconds of silence, then send accumulated text to API"""
        nonlocal accumulated_text, ai_processing, last_ai_request, last_ai_response_time, debounce_task
        try:
            await asyncio.sleep(SILENCE_THRESHOLD)
            # After 5 seconds of silence, send the accumulated text
            if accumulated_text and not ai_processing:
                text_to_send = accumulated_text.strip()
                if text_to_send and text_to_send != last_ai_request:
                    LOG.info("⏱️ Debounced API call (%s): Sending after 5s silence: %s", conn_id, text_to_send)
                    await send_json({"type": "final", "text": text_to_send, "final": True})
                    last_ai_request = text_to_send
                    ai_processing = True
                    await send_assistant_reply(send_json, text_to_send, handshake_mode)
                    ai_processing = False
                    last_ai_response_time = time.monotonic()
                    accumulated_text = ""  # Clear after sending
        except asyncio.CancelledError:
            LOG.debug("Debounce timer cancelled for %s", conn_id)
        except Exception as e:
            LOG.exception("Error in debounced_api_call for %s: %s", conn_id, e)
        finally:
            debounce_task = None

    async def simulate_loop():
        count = 0
        while True:
            await asyncio.sleep(0.8)
            count += 1
            if not await send_json({"type": "partial", "partial": f"simulated partial {count}"}):
                return

    async def timeout_checker():
        nonlocal pending_text, last_partial, last_partial_ts, last_ai_request, ai_processing, last_ai_response_time
        while True:
            await asyncio.sleep(0.1)
            current_time = time.monotonic()
            time_since_last_ai = current_time - last_ai_response_time
            if (
                pending_text
                and (current_time - last_partial_ts) >= SILENCE_TIMEOUT
                and pending_text != last_ai_request
                and not ai_processing
                and time_since_last_ai >= AI_COOLDOWN_SECONDS
            ):
                LOG.info(
                    "Silence timeout (%s): Converting partial to final: %s",
                    conn_id,
                    pending_text,
                )
                await send_json({"type": "final", "text": pending_text, "final": True})
                last_ai_request = pending_text
                ai_processing = True
                await send_assistant_reply(send_json, pending_text, handshake_mode)
                ai_processing = False
                last_ai_response_time = time.monotonic()
                pending_text = ""
                last_partial = ""
            elif (
                pending_text
                and (current_time - last_partial_ts) >= SILENCE_TIMEOUT
                and time_since_last_ai < AI_COOLDOWN_SECONDS
            ):
                LOG.info(
                    "Silence timeout (%s): Skipping due to cooldown (%.1fs remaining): %s",
                    conn_id,
                    AI_COOLDOWN_SECONDS - time_since_last_ai,
                    pending_text,
                )
                pending_text = ""
                last_partial = ""

    # --- Main handler logic ---
    try:
        handshake = await _perform_handshake(ws, conn_id, send_json)
        recognizer = handshake.recognizer
        handshake_mode = handshake.mode
        sample_rate = handshake.sample_rate

        pcm_context = (
            _pcm_sink(conn_id) if not getattr(handshake, 'chat', False) else nullcontext((None, None))
        )

        with pcm_context as (pcm_file, saved_path):
            pcm_path = saved_path
            last_progress_ts = time.monotonic()

            last_partial = ""
            last_partial_ts = time.monotonic()
            pending_text = ""
            last_ai_request = ""
            ai_processing = False
            last_ai_response_time = 0.0

            if getattr(handshake, 'simulate', False) and recognizer is None and not getattr(handshake, 'chat', False):
                sim_task = asyncio.create_task(simulate_loop())

            timeout_task = asyncio.create_task(timeout_checker()) if not getattr(handshake, 'chat', False) else None

            try:
                async for data in ws:
                    if isinstance(data, (bytes, bytearray, memoryview)):
                        if getattr(handshake, 'chat', False):
                            LOG.debug("Ignoring binary payload in chat mode for %s", conn_id)
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
                            await send_json({"type": "progress", "bytes": bytes_received, "chunks": chunks})
                            last_progress_ts = now
                        if recognizer:
                            if hasattr(recognizer, 'AcceptWaveform') and recognizer.AcceptWaveform(audio_bytes):
                                try:
                                    result = json.loads(recognizer.Result())
                                except Exception:
                                    result = {}
                                text = (result.get("text") or "").strip()
                                if text:
                                    LOG.info("Vosk final (%s): %s", conn_id, text)
                                    # Accumulate text instead of sending immediately
                                    if accumulated_text:
                                        accumulated_text += " " + text
                                    else:
                                        accumulated_text = text
                                    last_speech_time = time.monotonic()
                                    
                                    # Cancel existing debounce timer and start a new one
                                    if debounce_task and not debounce_task.done():
                                        debounce_task.cancel()
                                    debounce_task = asyncio.create_task(debounced_api_call())
                                    
                                    last_partial = ""
                                    pending_text = ""
                            else:
                                try:
                                    partial_obj = json.loads(recognizer.PartialResult())
                                except Exception:
                                    partial_obj = {}
                                partial = (partial_obj.get("partial") or "").strip()
                                if partial and partial != last_partial:
                                    last_partial = partial
                                    pending_text = partial
                                    last_partial_ts = time.monotonic()
                                    LOG.info("Vosk partial (%s): %s", conn_id, partial)
                                    await send_json({"type": "partial", "partial": partial})
                    else:
                        try:
                            obj = json.loads(data)
                        except Exception:
                            LOG.info("Received non-binary message from %s", conn_id)
                            continue
                        msg_type = obj.get("type")
                        if msg_type == "get_intro_jokes":
                            LOG.info("🎭 Generating intro jokes for %s", conn_id)
                            await generate_intro_jokes(send_json)
                        elif msg_type in {"user_text", "chat"}:
                            user_text = (obj.get("text") or "").strip()
                            current_time = time.monotonic()
                            time_since_last_ai = current_time - last_ai_response_time
                            if (not user_text or user_text == last_ai_request or ai_processing or time_since_last_ai < AI_COOLDOWN_SECONDS):
                                if time_since_last_ai < AI_COOLDOWN_SECONDS:
                                    LOG.info("Chat message (%s): Skipping due to cooldown (%.1fs remaining): %s", conn_id, AI_COOLDOWN_SECONDS - time_since_last_ai, user_text)
                                continue
                            LOG.info("Chat message (%s): %s", conn_id, user_text)
                            last_ai_request = user_text
                            ai_processing = True
                            await send_assistant_reply(send_json, user_text, handshake_mode or "chat")
                            ai_processing = False
                            last_ai_response_time = time.monotonic()
                        else:
                            LOG.info("Got text message %s: %s", conn_id, obj)
            finally:
                # Cancel debounce task if running
                if debounce_task and not debounce_task.done():
                    debounce_task.cancel()
                    try:
                        await debounce_task
                    except asyncio.CancelledError:
                        pass
                        
                if timeout_task:
                    timeout_task.cancel()
                    try:
                        await timeout_task
                    except asyncio.CancelledError:
                        pass
    except HandshakeError as exc:
        LOG.warning("Handshake failed %s: %s", conn_id, exc)
        try:
            await send_json({"type": "error", "error": "handshake", "message": str(exc)})
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
            except Exception:
                LOG.exception("Error while cancelling simulate loop for %s", conn_id)
        if recognizer and hasattr(recognizer, 'FinalResult'):
            try:
                final_result = json.loads(recognizer.FinalResult())
            except Exception:
                final_result = {}
            final_text = (final_result.get("text") or "").strip()
            if final_text:
                LOG.info("Vosk final (close) %s: %s", conn_id, final_text)
        saved_label = str(pcm_path) if pcm_path else "disabled"
        LOG.info("Connection %s finished bytes=%s chunks=%s saved=%s sampleRate=%s mode=%s", conn_id, bytes_received, chunks, saved_label, sample_rate, handshake_mode)

# --- Server Startup ---
async def _run_server():
    LOG.info(f"Starting streaming server on ws://{HOST}:{PORT}{WS_PATH}")
    async with websockets.serve(handler, HOST, PORT):
        while True:
            await asyncio.sleep(1)

def main():
    try:
        asyncio.run(_run_server())
    except KeyboardInterrupt:
        LOG.info("Keyboard interrupt, exiting")

if __name__ == "__main__":
    main()

