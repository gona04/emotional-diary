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
from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Optional

try:
    import websockets
except Exception:
    print('Missing websockets package. Please install in venv: pip install websockets', file=sys.stderr)
    raise

try:
    from vosk import KaldiRecognizer, Model, SetLogLevel
    HAVE_VOSK = True
    # reduce Vosk logging noise unless explicitly enabled
    SetLogLevel(-1)
except Exception:  # pragma: no cover - optional dependency
    HAVE_VOSK = False
    KaldiRecognizer = Model = None

VOSK_MODEL_PATH = pathlib.Path(os.environ.get('VOSK_MODEL_PATH', '') or (pathlib.Path(__file__).resolve().parent / 'vosk-model')).expanduser()
_VOSK_MODEL = None

LOG = logging.getLogger('streaming_server')
logging.basicConfig(level=logging.INFO)

DEFAULT_SAMPLE_RATE = 16000
HANDSHAKE_TIMEOUT = float(os.environ.get('STREAM_HANDSHAKE_TIMEOUT', '5'))
PROGRESS_INTERVAL_SEC = float(os.environ.get('STREAM_PROGRESS_INTERVAL', '0.5'))
PERSIST_PCM = os.environ.get('STREAM_PERSIST_PCM', '0').lower() in {'1', 'true', 'yes'}
PCM_DIR = pathlib.Path(os.environ.get('STREAM_PCM_DIR', tempfile.gettempdir()))
HOST = os.environ.get('STREAM_SERVER_HOST', '0.0.0.0')
PORT = int(os.environ.get('STREAM_SERVER_PORT', '8765'))


@dataclass
class HandshakeResult:
    sample_rate: int
    simulate: bool
    recognizer: Optional[Any]
    mode: str


class HandshakeError(Exception):
    """Raised when the initial client handshake fails."""


@contextmanager
def _pcm_sink(conn_id: str):
    if not PERSIST_PCM:
        yield None, None
        return

    PCM_DIR.mkdir(parents=True, exist_ok=True)
    pcm_path = PCM_DIR / f'stream_{conn_id}.pcm'
    f = open(pcm_path, 'wb')
    try:
        yield f, pcm_path
    finally:
        try:
            f.close()
        except Exception:  # pragma: no cover - best effort cleanup
            LOG.exception('Failed closing PCM file for %s', conn_id)


async def _perform_handshake(ws, conn_id: str, send_json) -> HandshakeResult:
    try:
        raw_msg = await asyncio.wait_for(ws.recv(), HANDSHAKE_TIMEOUT)
    except asyncio.TimeoutError as exc:
        raise HandshakeError('Handshake timed out') from exc

    if isinstance(raw_msg, (bytes, bytearray)):
        raise HandshakeError('Handshake must be a text JSON frame')

    try:
        obj = json.loads(raw_msg)
    except json.JSONDecodeError as exc:
        raise HandshakeError('Handshake payload was not valid JSON') from exc

    if obj.get('type') != 'handshake':
        raise HandshakeError('First message must be a handshake frame')

    sample_rate = int(obj.get('sampleRate', DEFAULT_SAMPLE_RATE))
    simulate = bool(obj.get('simulate', False))
    recognizer: Optional[Any] = None

    if not simulate:
        if HAVE_VOSK:
            try:
                model = ensure_vosk_model()
                recognizer = KaldiRecognizer(model, sample_rate)
                try:
                    recognizer.SetWords(True)
                except AttributeError:  # pragma: no cover - optional API
                    pass
            except Exception as exc:
                LOG.exception('Failed to initialise Vosk recognizer; falling back to simulate mode')
                await send_json({
                    'type': 'warning',
                    'warning': 'vosk_unavailable',
                    'message': str(exc),
                })
                recognizer = None
                simulate = True
        else:
            await send_json({
                'type': 'warning',
                'warning': 'vosk_not_installed',
                'message': 'Install vosk and download a model to enable real transcription.'
            })
            simulate = True

    mode = 'simulate' if simulate else 'vosk'
    await send_json({'type': 'handshake_ack', 'ok': True, 'mode': mode})
    LOG.info('Handshake %s sampleRate=%s simulate=%s mode=%s', conn_id, sample_rate, simulate, mode)

    return HandshakeResult(sample_rate=sample_rate, simulate=simulate, recognizer=recognizer, mode=mode)


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
    default_dir = backend_dir / 'vosk-model'
    if default_dir.exists():
        return default_dir

    # look for directories with common extracted names e.g. vosk-model-small-en-us-0.15
    for child in backend_dir.iterdir():
        if child.is_dir() and child.name.startswith('vosk-model'):
            return child

    raise FileNotFoundError(
        'Vosk model directory not found. Set VOSK_MODEL_PATH or place an extracted '
        'model folder inside backend/ (e.g. backend/vosk-model-small-en-us-0.15).'
    )


def ensure_vosk_model() -> Any:
    global _VOSK_MODEL
    if not HAVE_VOSK:
        raise RuntimeError('Vosk Python package is not installed. Run `pip install vosk`.')
    if _VOSK_MODEL is None:
        model_dir = _discover_model_path()
        LOG.info('Loading Vosk model from %s', model_dir)
        _VOSK_MODEL = Model(str(model_dir))
    return _VOSK_MODEL


async def handler(ws, path=None):
    conn_id = str(uuid.uuid4())[:8]
    LOG.info('New connection %s path=%s', conn_id, path)
    bytes_received = 0
    chunks = 0
    sim_task: Optional[asyncio.Task] = None
    recognizer = None
    pcm_path = None
    handshake_mode = 'unknown'
    sample_rate = DEFAULT_SAMPLE_RATE

    async def send_json(obj) -> bool:
        try:
            await ws.send(json.dumps(obj))
            return True
        except Exception:
            LOG.exception('Failed sending json to %s', conn_id)
            return False

    async def simulate_loop():
        count = 0
        while True:
            await asyncio.sleep(0.8)
            count += 1
            if not await send_json({'type': 'partial', 'partial': f'simulated partial {count}'}):
                return

    try:
        handshake = await _perform_handshake(ws, conn_id, send_json)
        recognizer = handshake.recognizer
        handshake_mode = handshake.mode
        sample_rate = handshake.sample_rate

        with _pcm_sink(conn_id) as (pcm_file, saved_path):
            pcm_path = saved_path
            last_partial = ''
            last_progress_ts = time.monotonic()

            if handshake.simulate and recognizer is None:
                sim_task = asyncio.create_task(simulate_loop())

            async for data in ws:
                if isinstance(data, (bytes, bytearray, memoryview)):
                    audio_bytes = data if isinstance(data, (bytes, bytearray)) else bytes(data)

                    if pcm_file is not None:
                        pcm_file.write(audio_bytes)

                    bytes_received += len(audio_bytes)
                    chunks += 1

                    now = time.monotonic()
                    if now - last_progress_ts >= PROGRESS_INTERVAL_SEC:
                        await send_json({'type': 'progress', 'bytes': bytes_received, 'chunks': chunks})
                        last_progress_ts = now

                    if recognizer:
                        if recognizer.AcceptWaveform(audio_bytes):
                            try:
                                result = json.loads(recognizer.Result())
                            except json.JSONDecodeError:
                                result = {}
                            text = (result.get('text') or '').strip()
                            if text:
                                LOG.info('Vosk final (%s): %s', conn_id, text)
                                await send_json({'type': 'final', 'text': text, 'final': True})
                                last_partial = ''
                        else:
                            try:
                                partial_obj = json.loads(recognizer.PartialResult())
                            except json.JSONDecodeError:
                                partial_obj = {}
                            partial = (partial_obj.get('partial') or '').strip()
                            if partial and partial != last_partial:
                                last_partial = partial
                                LOG.info('Vosk partial (%s): %s', conn_id, partial)
                                await send_json({'type': 'partial', 'partial': partial})
                else:
                    try:
                        obj = json.loads(data)
                        LOG.info('Got text message %s: %s', conn_id, obj)
                    except Exception:
                        LOG.info('Received non-binary message from %s', conn_id)

    except HandshakeError as exc:
        LOG.warning('Handshake failed %s: %s', conn_id, exc)
        try:
            await send_json({'type': 'error', 'error': 'handshake', 'message': str(exc)})
        except Exception:
            pass
    except websockets.exceptions.ConnectionClosedOK:
        LOG.info('Connection closed normally %s', conn_id)
    except websockets.exceptions.ConnectionClosedError:
        LOG.info('Connection closed with error %s', conn_id)
    except Exception:
        LOG.exception('Connection handler failed %s', conn_id)
        try:
            await send_json({'type': 'error', 'error': 'internal'})
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
                LOG.exception('Error while cancelling simulate loop for %s', conn_id)

        if recognizer:
            try:
                final_result = json.loads(recognizer.FinalResult())
            except json.JSONDecodeError:
                final_result = {}
            final_text = (final_result.get('text') or '').strip()
            if final_text:
                LOG.info('Vosk final (close) %s: %s', conn_id, final_text)

        saved_label = str(pcm_path) if pcm_path else 'disabled'
        LOG.info(
            'Connection %s finished bytes=%s chunks=%s saved=%s sampleRate=%s mode=%s',
            conn_id,
            bytes_received,
            chunks,
            saved_label,
            sample_rate,
            handshake_mode,
        )


async def _run_server():
    LOG.info('Starting streaming server on %s:%s', HOST, PORT)
    async with websockets.serve(handler, HOST, PORT):
        # run until cancelled
        while True:
            await asyncio.sleep(1)

def main():
    try:
        asyncio.run(_run_server())
    except KeyboardInterrupt:
        LOG.info('Keyboard interrupt, exiting')


if __name__ == '__main__':
    main()
