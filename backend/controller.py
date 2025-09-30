import asyncio
import json
import logging
import time
from contextlib import contextmanager, nullcontext
from models.handshake import HandshakeResult, HandshakeError
from services.speech_service import SpeechService
from services.ai_service import AIService
from services.session_service import SessionService
import config

logger = logging.getLogger("controller")

speech_service = SpeechService()
ai_service = AIService()
session_service = SessionService()

@contextmanager
def _pcm_sink(conn_id: str):
    if not config.PERSIST_PCM:
        yield None, None
        return
    config.PCM_DIR.mkdir(parents=True, exist_ok=True)
    pcm_path = config.PCM_DIR / f"stream_{conn_id}.pcm"
    f = open(pcm_path, "wb")
    try:
        yield f, pcm_path
    finally:
        try:
            f.close()
        except Exception:
            logger.exception("Failed closing PCM file for %s", conn_id)

async def _perform_handshake(ws, conn_id: str, send_json) -> HandshakeResult:
    try:
        raw_msg = await asyncio.wait_for(ws.recv(), config.HANDSHAKE_TIMEOUT)
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
    sample_rate = int(obj.get("sampleRate", config.DEFAULT_SAMPLE_RATE))
    simulate = bool(obj.get("simulate", False)) or chat_mode
    recognizer = None
    if chat_mode:
        mode = "chat"
        await send_json({"type": "handshake_ack", "ok": True, "mode": mode, "chat": chat_mode})
        logger.info(f"Handshake {conn_id} sampleRate={sample_rate} simulate={simulate} chat={chat_mode} mode={mode}")
        return HandshakeResult(sample_rate, simulate, None, mode, chat_mode)
    elif not simulate:
        try:
            recognizer = speech_service.create_recognizer(sample_rate)
        except Exception as exc:
            logger.exception("Failed to initialise Vosk recognizer; falling back to simulate mode")
            await send_json({"type": "warning", "warning": "vosk_unavailable", "message": str(exc)})
            recognizer = None
            simulate = True
        mode = "simulate" if simulate else "vosk"
        await send_json({"type": "handshake_ack", "ok": True, "mode": mode, "chat": chat_mode})
        logger.info(f"Handshake {conn_id} sampleRate={sample_rate} simulate={simulate} chat={chat_mode} mode={mode}")
        return HandshakeResult(sample_rate, simulate, recognizer, mode, chat_mode)

async def send_assistant_reply(send_json, user_text: str, mode: str):
    reply = await ai_service.call_mistral(user_text)
    if reply:
        await send_json({"type": "assistant", "text": reply, "mode": mode})
        await asyncio.sleep(0.5)
    else:
        await send_json({"type": "assistant", "text": "I'm here and listening.", "mode": mode, "error": True})

async def handler(ws, path=None):
    conn_id = str(id(ws))
    logger.info(f"New connection {conn_id} path={path}")
    bytes_received = 0
    chunks = 0
    sim_task = None
    recognizer = None
    pcm_path = None
    handshake_mode = "unknown"
    sample_rate = config.DEFAULT_SAMPLE_RATE
    async def send_json(obj) -> bool:
        try:
            await ws.send(json.dumps(obj))
            return True
        except Exception:
            logger.exception(f"Failed sending json to {conn_id}")
            return False
    async def simulate_loop():
        count = 0
        while True:
            await asyncio.sleep(0.8)
            count += 1
            if not await send_json({"type": "partial", "partial": f"simulated partial {count}"}):
                return
    try:
        handshake = await _perform_handshake(ws, conn_id, send_json)
        recognizer = handshake.recognizer
        handshake_mode = handshake.mode
        sample_rate = handshake.sample_rate
        pcm_context = _pcm_sink(conn_id) if not handshake.chat else nullcontext((None, None))
        with pcm_context as (pcm_file, saved_path):
            pcm_path = saved_path
            session = session_service.get(conn_id)
            if handshake.simulate and recognizer is None and not handshake.chat:
                sim_task = asyncio.create_task(simulate_loop())
            async def timeout_checker():
                while True:
                    await asyncio.sleep(0.1)
                    current_time = time.monotonic()
                    time_since_last_ai = current_time - session["last_ai_response_time"]
                    if (session["pending_text"] and (current_time - session["last_partial_ts"]) >= config.SILENCE_TIMEOUT and session["pending_text"] != session["last_ai_request"] and not session["ai_processing"] and time_since_last_ai >= 2.0):
                        logger.info(f"Silence timeout ({conn_id}): Converting partial to final: {session['pending_text']}")
                        await send_json({"type": "final", "text": session["pending_text"], "final": True})
                        session["last_ai_request"] = session["pending_text"]
                        session["ai_processing"] = True
                        await send_assistant_reply(send_json, session["pending_text"], handshake_mode)
                        session["ai_processing"] = False
                        session["last_ai_response_time"] = time.monotonic()
                        session["pending_text"] = ""
                        session["last_partial"] = ""
                    elif (session["pending_text"] and (current_time - session["last_partial_ts"]) >= config.SILENCE_TIMEOUT and time_since_last_ai < 2.0):
                        logger.info(f"Silence timeout ({conn_id}): Skipping due to cooldown ({2.0 - time_since_last_ai:.1f}s remaining): {session['pending_text']}")
                        session["pending_text"] = ""
                        session["last_partial"] = ""
            timeout_task = asyncio.create_task(timeout_checker()) if not handshake.chat else None
            try:
                async for data in ws:
                    if isinstance(data, (bytes, bytearray, memoryview)):
                        if handshake.chat:
                            logger.debug(f"Ignoring binary payload in chat mode for {conn_id}")
                            continue
                        audio_bytes = data if isinstance(data, (bytes, bytearray)) else bytes(data)
                        if pcm_file is not None:
                            pcm_file.write(audio_bytes)
                        bytes_received += len(audio_bytes)
                        chunks += 1
                        now = time.monotonic()
                        if now - session["last_progress_ts"] >= config.PROGRESS_INTERVAL_SEC:
                            await send_json({"type": "progress", "bytes": bytes_received, "chunks": chunks})
                            session["last_progress_ts"] = now
                        if recognizer:
                            if recognizer.AcceptWaveform(audio_bytes):
                                try:
                                    result = json.loads(recognizer.Result())
                                except json.JSONDecodeError:
                                    result = {}
                                text = (result.get("text") or "").strip()
                                current_time = time.monotonic()
                                time_since_last_ai = current_time - session["last_ai_response_time"]
                                if (text and text != session["last_ai_request"] and not session["ai_processing"] and time_since_last_ai >= 2.0):
                                    logger.info(f"Vosk final ({conn_id}): {text}")
                                    await send_json({"type": "final", "text": text, "final": True})
                                    session["last_partial"] = ""
                                    session["pending_text"] = ""
                                    session["last_ai_request"] = text
                                    session["ai_processing"] = True
                                    await send_assistant_reply(send_json, text, handshake_mode)
                                    session["ai_processing"] = False
                                    session["last_ai_response_time"] = time.monotonic()
                                elif text == session["last_ai_request"]:
                                    logger.info(f"Vosk final ({conn_id}): Skipping duplicate text: {text}")
                                elif time_since_last_ai < 2.0:
                                    logger.info(f"Vosk final ({conn_id}): Skipping due to cooldown ({2.0 - time_since_last_ai:.1f}s remaining): {text}")
                            else:
                                try:
                                    partial_obj = json.loads(recognizer.PartialResult())
                                except json.JSONDecodeError:
                                    partial_obj = {}
                                partial = (partial_obj.get("partial") or "").strip()
                                if partial and partial != session["last_partial"]:
                                    session["last_partial"] = partial
                                    session["pending_text"] = partial
                                    session["last_partial_ts"] = time.monotonic()
                                    logger.info(f"Vosk partial ({conn_id}): {partial}")
                                    await send_json({"type": "partial", "partial": partial})
                    else:
                        try:
                            obj = json.loads(data)
                        except Exception:
                            logger.info(f"Received non-binary message from {conn_id}")
                            continue
                        msg_type = obj.get("type")
                        if msg_type in {"user_text", "chat"}:
                            user_text = (obj.get("text") or "").strip()
                            current_time = time.monotonic()
                            time_since_last_ai = current_time - session["last_ai_response_time"]
                            if (not user_text or user_text == session["last_ai_request"] or session["ai_processing"] or time_since_last_ai < 2.0):
                                if time_since_last_ai < 2.0:
                                    logger.info(f"Chat message ({conn_id}): Skipping due to cooldown ({2.0 - time_since_last_ai:.1f}s remaining): {user_text}")
                                continue
                            logger.info(f"Chat message ({conn_id}): {user_text}")
                            session["last_ai_request"] = user_text
                            session["ai_processing"] = True
                            await send_assistant_reply(send_json, user_text, handshake_mode or "chat")
                            session["ai_processing"] = False
                            session["last_ai_response_time"] = time.monotonic()
                        else:
                            logger.info(f"Got text message {conn_id}: {obj}")
            finally:
                if timeout_task:
                    timeout_task.cancel()
                    try:
                        await timeout_task
                    except asyncio.CancelledError:
                        pass
    except HandshakeError as exc:
        logger.warning(f"Handshake failed {conn_id}: {exc}")
        try:
            await send_json({"type": "error", "error": "handshake", "message": str(exc)})
        except Exception:
            pass
    except Exception:
        logger.exception(f"Connection handler failed {conn_id}")
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
        session_service.cleanup(conn_id)
        saved_label = str(pcm_path) if pcm_path else "disabled"
        logger.info(f"Connection {conn_id} finished bytes={bytes_received} chunks={chunks} saved={saved_label} sampleRate={sample_rate} mode={handshake_mode}")
