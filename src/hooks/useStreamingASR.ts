import { useEffect, useRef } from 'react';

const TARGET_SAMPLE_RATE = 16000;

function floatTo16BitPCM(float32Array: Float32Array) {
  const l = float32Array.length;
  const buf = new ArrayBuffer(l * 2);
  const view = new DataView(buf);
  for (let i = 0; i < l; i++) {
    let s = Math.max(-1, Math.min(1, float32Array[i]));
    view.setInt16(i * 2, s < 0 ? s * 0x8000 : s * 0x7fff, true);
  }
  return buf;
}

// simple linear resampler
function resampleLinear(input: Float32Array, inRate: number, outRate: number): Float32Array {
  if (inRate === outRate) return input;
  const inLength = input.length;
  const outLength = Math.max(1, Math.round(inLength * outRate / inRate));
  const out = new Float32Array(outLength);
  const ratio = (inLength - 1) / (outLength - 1);
  for (let i = 0; i < outLength; i++) {
    const idx = i * ratio;
    const idxLow = Math.floor(idx);
    const idxHigh = Math.min(inLength - 1, idxLow + 1);
    const frac = idx - idxLow;
    out[i] = input[idxLow] * (1 - frac) + input[idxHigh] * frac;
  }
  return out;
}

type StreamingOptions = {
  simulate?: boolean;
};

export function useStreamingASR(wsUrl: string, onPartial: (t: string) => void, onFinal: (t: string) => void, options?: StreamingOptions) {
  const wsRef = useRef<WebSocket | null>(null);
  const ctxRef = useRef<AudioContext | null>(null);
  const nodeRef = useRef<AudioWorkletNode | null>(null);

  useEffect(() => {
    return () => {
      if (wsRef.current) { try { wsRef.current.close(); } catch(e) {} }
      if (nodeRef.current) { try { nodeRef.current.port.close(); } catch(e) {} }
      if (ctxRef.current) { try { ctxRef.current.close(); } catch(e) {} }
    };
  }, []);

  async function start() {
    // If already started, do nothing
    if (nodeRef.current) {
      console.warn('Streaming already started');
      return;
    }

    const ensureAudioContext = (): AudioContext => {
      const Ctx = (window.AudioContext || (window as any).webkitAudioContext) as typeof AudioContext;
      if (!ctxRef.current || ctxRef.current.state === 'closed') {
        try {
          ctxRef.current = new Ctx({ sampleRate: TARGET_SAMPLE_RATE });
        } catch (e) {
          ctxRef.current = new Ctx();
        }
      }
      return ctxRef.current as AudioContext;
    };

    const sendHandshake = (wsInst?: WebSocket) => {
      try {
        const wsToUse = wsInst || wsRef.current;
        if (!wsToUse) return;
        const handshakeObj: any = { type: 'handshake', sampleRate: TARGET_SAMPLE_RATE, channels: 1, format: 's16le' };
        if (options && options.simulate) handshakeObj.simulate = true;
        const handshake = JSON.stringify(handshakeObj);
        if (wsToUse.readyState === WebSocket.OPEN) wsToUse.send(handshake);
      } catch (e) { console.warn('handshake send failed', e); }
    };

  // create audio context and worklet
  let audioCtx = ensureAudioContext();
  console.log('AudioContext state before addModule:', audioCtx.state);
    try {
      await audioCtx.audioWorklet.addModule('/worklets/capture-processor.js');
    } catch (e) {
      console.error('Failed to load audio worklet module /worklets/capture-processor.js', e);
      try { await stop(); } catch(_) {}
      throw new Error('AudioWorklet load failed');
    }

    let stream: MediaStream;
    try {
      stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    } catch (e) {
      console.error('getUserMedia failed', e);
      try { await stop(); } catch(_) {}
      throw e;
    }

    // ensure context is open
    if (audioCtx.state === 'closed') {
      console.warn('AudioContext closed unexpectedly, recreating');
      try { await audioCtx.close(); } catch (e) {}
      audioCtx = ensureAudioContext();
      try { await audioCtx.audioWorklet.addModule('/worklets/capture-processor.js'); } catch (e) { console.error('re-add module failed', e); try { await stop(); } catch(_) {} throw e; }
    }

  const src = audioCtx.createMediaStreamSource(stream);
    let node: AudioWorkletNode;
    try {
      node = new AudioWorkletNode(audioCtx, 'capture-processor');
    } catch (e) {
      console.error('AudioWorkletNode creation failed, attempting to recreate context and retry', e);
      try { await audioCtx.close(); } catch (er) {}
  const retryCtx = ensureAudioContext();
  // update our local reference to the new context
  audioCtx = retryCtx;
      try {
        await retryCtx.audioWorklet.addModule('/worklets/capture-processor.js');
        node = new AudioWorkletNode(retryCtx, 'capture-processor');
      } catch (er) {
        console.error('Retry failed for AudioWorkletNode', er);
        try { await stop(); } catch(_) {}
        throw er;
      }
    }

    // Simple energy-based VAD + patching: buffer voiced frames and send as one binary patch when silence detected
    const vadBuffer: Float32Array[] = [];
    let voiced = false;
    let silenceFrames = 0;
    const SILENCE_FRAME_THRESHOLD = 6; // number of frames of silence to consider end of utterance
    const VAD_RMS_THRESHOLD = 0.01; // adjust as needed

    function rms(fr: Float32Array) {
      let sum = 0;
      for (let i = 0; i < fr.length; i++) sum += fr[i] * fr[i];
      return Math.sqrt(sum / fr.length);
    }

    node.port.onmessage = (ev) => {
      let float32 = ev.data as Float32Array;
      const inputRate = audioCtx.sampleRate || TARGET_SAMPLE_RATE;
      if (inputRate !== TARGET_SAMPLE_RATE) {
        float32 = resampleLinear(float32, inputRate, TARGET_SAMPLE_RATE);
      }

      const level = rms(float32);
      if (level > VAD_RMS_THRESHOLD) {
        voiced = true;
        silenceFrames = 0;
        vadBuffer.push(float32);
      } else if (voiced) {
        // we were in voiced state, count silence frames
        silenceFrames += 1;
        vadBuffer.push(float32);
        if (silenceFrames >= SILENCE_FRAME_THRESHOLD) {
          // end of utterance, concatenate and send
          const totalLen = vadBuffer.reduce((s, a) => s + a.length, 0);
          const concat = new Float32Array(totalLen);
          let offset = 0;
          for (const arr of vadBuffer) { concat.set(arr, offset); offset += arr.length; }
          const pcm = floatTo16BitPCM(concat as Float32Array);
          if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            try { if ((wsRef.current as any)._handshakeSent !== true) { sendHandshake(); (wsRef.current as any)._handshakeSent = true; } } catch(e){}
            wsRef.current.send(pcm);
          }
          // reset
          vadBuffer.length = 0;
          voiced = false;
          silenceFrames = 0;
        }
      } else {
        // not voiced and not buffering; ignore
      }
    };
  src.connect(node);
  // Do not route to output to avoid feedback; connect to destination if you want
  try { node.connect(audioCtx.destination); } catch (e) { /* some contexts disallow direct connect, ignore */ }
    nodeRef.current = node;

    // Now that audio is ready, open WebSocket and hook handlers
    try {
      const ws = new WebSocket(wsUrl);
      ws.binaryType = 'arraybuffer';
      ws.onopen = () => { console.log('ws open'); sendHandshake(ws); };
      ws.onmessage = (ev) => {
        try {
          const msg = JSON.parse(ev.data as string);
          if (msg.partial) onPartial(msg.partial);
          if (msg.text && msg.final) onFinal(msg.text);
        } catch (e) { console.log('ws msg', ev.data); }
      };
      wsRef.current = ws;
    } catch (e) {
      console.error('Failed to create WebSocket', e);
      // cleanup audio if socket fails
      try { node.disconnect(); } catch(e){}
      try { audioCtx.close(); } catch(e){}
      nodeRef.current = null;
      ctxRef.current = null;
      if (wsRef.current) { try { wsRef.current.close(); } catch(e){} wsRef.current = null; }
      throw e;
    }
  }

  function stop() {
    if (wsRef.current) { try { wsRef.current.close(); } catch (e) {} wsRef.current = null; }
    if (nodeRef.current) { try { nodeRef.current.disconnect(); } catch (e) {} nodeRef.current = null; }
    if (ctxRef.current) { try { ctxRef.current.close(); } catch (e) {} ctxRef.current = null; }
  }

  return { start, stop };
}

export default useStreamingASR;
