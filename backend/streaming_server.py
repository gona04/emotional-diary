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

MISTRAL_API_URL = "https://api.mistral.ai/v1/chat/completions"  # Update if needed
MISTRAL_API_KEY = "p9EhA0yBPa3BM6VJ6UCkeZiUVohyCNqQ"  # Replace with your real key or load from env

async def send_assistant_reply(send_json, text, mode):
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json",
    }
    data = {
        "model": "mistral-tiny",  # Or your preferred model
        "messages": [
            {"role": "user", "content": text}
        ],
        "temperature": 0.7
    }
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(MISTRAL_API_URL, headers=headers, json=data, timeout=30) as resp:
                if resp.status == 200:
                    result = await resp.json()
                    ai_text = result["choices"][0]["message"]["content"]
                else:
                    ai_text = f"[AI error: {resp.status}]"
    except Exception as e:
        ai_text = f"[AI error: {e}]"
    LOG.info(f"Sending AI reply: {ai_text}")
    await send_json({"type": "ai_reply", "text": ai_text, "mode": mode})




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

    # --- Helper functions must be defined here, inside handler, to access state ---
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
                                current_time = time.monotonic()
                                time_since_last_ai = current_time - last_ai_response_time
                                if (text and text != last_ai_request and not ai_processing and time_since_last_ai >= AI_COOLDOWN_SECONDS):
                                    LOG.info("Vosk final (%s): %s", conn_id, text)
                                    await send_json({"type": "final", "text": text, "final": True})
                                    last_partial = ""
                                    pending_text = ""
                                    last_ai_request = text
                                    ai_processing = True
                                    await send_assistant_reply(send_json, text, handshake_mode)
                                    ai_processing = False
                                    last_ai_response_time = time.monotonic()
                                elif text == last_ai_request:
                                    LOG.info("Vosk final (%s): Skipping duplicate text: %s", conn_id, text)
                                elif time_since_last_ai < AI_COOLDOWN_SECONDS:
                                    LOG.info("Vosk final (%s): Skipping due to cooldown (%.1fs remaining): %s", conn_id, AI_COOLDOWN_SECONDS - time_since_last_ai, text)
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
                        if msg_type in {"user_text", "chat"}:
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

