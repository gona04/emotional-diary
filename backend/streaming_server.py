#!/usr/bin/env python3
"""Simple WebSocket streaming server for ASR patches (simulate mode supported).

Protocol:
- Client sends a JSON handshake text frame: { type: 'handshake', sampleRate: 16000, channels:1, format:'s16le', simulate: true }
- Then client sends binary frames containing raw s16le PCM. Server writes to /tmp/stream_<id>.pcm
- Server responds with JSON progress and (in simulate mode) partial/final transcripts.
"""
import asyncio
import json
import logging
import os
import pathlib
import signal
import sys
import uuid
from typing import Any

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
    pcm_path = f'/tmp/stream_{conn_id}.pcm'
    f = open(pcm_path, 'wb')
    sample_rate = 16000
    simulate = False
    recognizer = None
    chunks = 0
    bytes_received = 0

    async def send_json(obj):
        try:
            await ws.send(json.dumps(obj))
        except Exception:
            LOG.exception('Failed sending json')

    try:
        # Expect handshake first (text)
        msg = await ws.recv()
        try:
            obj = json.loads(msg)
            if obj.get('type') == 'handshake':
                sample_rate = int(obj.get('sampleRate', sample_rate))
                simulate = bool(obj.get('simulate', False))
                LOG.info('Handshake %s sampleRate=%s simulate=%s', conn_id, sample_rate, simulate)

                if not simulate:
                    if HAVE_VOSK:
                        try:
                            model = ensure_vosk_model()
                            recognizer = KaldiRecognizer(model, sample_rate)
                            try:  # some builds expose SetWords
                                recognizer.SetWords(True)
                            except AttributeError:
                                pass
                            await send_json({'type': 'handshake_ack', 'ok': True, 'mode': 'vosk'})
                            LOG.info('Vosk transcription enabled for %s', conn_id)
                        except Exception as exc:
                            LOG.exception('Failed to initialise Vosk recognizer; falling back to simulate mode')
                            await send_json({
                                'type': 'warning',
                                'warning': 'vosk_unavailable',
                                'message': str(exc),
                            })
                            simulate = True
                            recognizer = None
                    else:
                        await send_json({
                            'type': 'warning',
                            'warning': 'vosk_not_installed',
                            'message': 'Install vosk and download a model to enable real transcription.'
                        })
                        simulate = True

                if simulate:
                    await send_json({'type': 'handshake_ack', 'ok': True, 'mode': 'simulate'})
            else:
                LOG.warning('Expected handshake, got %s', obj)
        except json.JSONDecodeError:
            LOG.warning('First message not JSON handshake')

        if simulate and not recognizer:
            # periodically send fake partials while receiving audio
            async def simulate_loop():
                count = 0
                while True:
                    await asyncio.sleep(0.8)
                    count += 1
                    await send_json({'type':'partial', 'partial': f'simulated partial {count}'})
            sim_task = asyncio.create_task(simulate_loop())
        else:
            sim_task = None

        # read binary frames until close
        last_partial = ''
        while True:
            data = await ws.recv()
            if isinstance(data, (bytes, bytearray)):
                f.write(data)
                bytes_received += len(data)
                chunks += 1
                if chunks % 5 == 0:
                    await send_json({'type':'progress', 'bytes': bytes_received, 'chunks': chunks})

                if recognizer:
                    if recognizer.AcceptWaveform(data):
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
                # handle text messages maybe
                try:
                    obj = json.loads(data)
                    LOG.info('Got text message: %s', obj)
                except Exception:
                    LOG.info('Received non-binary message')

    except websockets.exceptions.ConnectionClosedOK:
        LOG.info('Connection closed normally %s', conn_id)
    except Exception:
        LOG.exception('Connection handler failed %s', conn_id)
        try:
            await send_json({'type':'error', 'error':'internal'})
        except Exception:
            pass
    finally:
        try:
            if sim_task:
                sim_task.cancel()
        except Exception:
            pass
        try:
            f.close()
        except Exception:
            pass

        if recognizer:
            try:
                final_result = json.loads(recognizer.FinalResult())
            except json.JSONDecodeError:
                final_result = {}
            final_text = (final_result.get('text') or '').strip()
            if final_text:
                LOG.info('Vosk final (close) %s: %s', conn_id, final_text)

        LOG.info('Connection %s finished bytes=%s chunks=%s saved=%s', conn_id, bytes_received, chunks, pcm_path)


async def _run_server():
    host = '0.0.0.0'
    port = 8765
    LOG.info('Starting streaming server on %s:%s', host, port)
    async with websockets.serve(handler, host, port):
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
