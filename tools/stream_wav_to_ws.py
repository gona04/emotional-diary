#!/usr/bin/env python3
"""Headless test: stream a WAV file's audio as s16le PCM patches to the WebSocket server.
Usage: python tools/stream_wav_to_ws.py path/to/file.wav [--simulate]
"""
import argparse
import asyncio
import json
import sys

import soundfile as sf

try:
    import websockets
except Exception:
    print('Please install websockets in your venv: pip install websockets')
    raise


async def run(path, simulate: bool):
    data, sr = sf.read(path, dtype='float32')
    # convert to mono if needed
    if data.ndim > 1:
        data = data.mean(axis=1)
    # resample if needed (simple linear)
    target_sr = 16000
    if sr != target_sr:
        import numpy as np
        duration = data.shape[0] / sr
        new_len = int(duration * target_sr)
        data = np.interp(np.linspace(0, len(data), new_len, endpoint=False), np.arange(len(data)), data).astype('float32')

    uri = 'ws://localhost:8765'
    async with websockets.connect(uri) as ws:
        handshake = {
            'type': 'handshake',
            'sampleRate': target_sr,
            'channels': 1,
            'format': 's16le',
            'simulate': simulate,
        }
        await ws.send(json.dumps(handshake))
        print('handshake sent')

        # chunk size in samples (e.g., 0.1s)
        chunk_s = 0.12
        chunk_n = int(chunk_s * target_sr)
        i = 0
        while i < len(data):
            chunk = data[i:i+chunk_n]
            # float32 -> s16le
            ints = (chunk * 32767).astype('int16')
            await ws.send(ints.tobytes())
            i += chunk_n
            await asyncio.sleep(0.05)

        # wait for a short time to receive messages
        try:
            async for msg in ws:
                print('server msg:', msg)
        except websockets.ConnectionClosed as e:
            print('Connection closed', e)


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Stream WAV audio to ASR websocket server.')
    parser.add_argument('file', help='Path to WAV file to stream.')
    parser.add_argument('--simulate', action='store_true', help='Send simulated flag to server (skip Vosk).')
    args = parser.parse_args()

    asyncio.get_event_loop().run_until_complete(run(args.file, args.simulate))
