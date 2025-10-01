class CaptureProcessor extends AudioWorkletProcessor {
  process(inputs) {
    try {
      const input = inputs[0];
      if (!input || input.length === 0) return true;
      const channelCount = input.length;
      const frames = input[0];
      if (!frames) return true;

      if (channelCount === 1) {
        const copy = new Float32Array(frames.length);
        copy.set(frames);
        this.port.postMessage(copy);
      } else {
        const len = frames.length;
        const out = new Float32Array(len);
        for (let c = 0; c < channelCount; c++) {
          const ch = input[c];
          for (let i = 0; i < len; i++) {
            out[i] += ch[i] / channelCount;
          }
        }
        this.port.postMessage(out);
      }
    } catch (e) {
      // avoid throwing inside audio thread
    }
    return true;
  }
}

registerProcessor('capture-processor', CaptureProcessor);
