import { EdgeTTS } from 'edge-tts-universal';

const ttsClient = new EdgeTTS('en-US-EmmaNeural');

export interface TTSOptions {
  voice?: string;
  pitch?: number;
  rate?: number;
  volume?: number;
}

export class TTSService {
  private audioContext: AudioContext | null = null;

  private getAudioContext(): AudioContext {
    if (!this.audioContext) {
      this.audioContext = new (window.AudioContext || (window as any).webkitAudioContext)();
    }
    return this.audioContext;
  }

  async speak(text: string, options: TTSOptions = {}): Promise<void> {
    try {
      // Use provided options or defaults
      const voice = options.voice || 'en-US-EmmaNeural';
      const pitch = options.pitch !== undefined ? options.pitch : -5;
      const rate = options.rate !== undefined ? options.rate : 1;
      const volume = options.volume !== undefined ? options.volume : 1;

      // Set options on the client
      ttsClient.voice = voice;
      if (pitch !== -5) ttsClient.pitch = `${pitch >= 0 ? '+' : ''}${pitch}Hz`;
      if (rate !== 1) ttsClient.rate = `${rate >= 1 ? '+' : ''}${Math.round((rate - 1) * 100)}%`;
      if (volume !== 1) ttsClient.volume = `${volume >= 1 ? '+' : ''}${Math.round((volume - 1) * 100)}%`;

      // Set text on the client
      ttsClient.text = text;

      // 1) ask the Edge TTS client for a raw audio buffer
      const audioData = await ttsClient.synthesize();

      // Handle different audio data formats to get ArrayBuffer
      let arrayBuffer: ArrayBuffer;
      if (audioData instanceof ArrayBuffer) {
        arrayBuffer = audioData;
      } else if (audioData instanceof Blob) {
        arrayBuffer = await audioData.arrayBuffer();
      } else if (audioData && audioData.audio && audioData.audio instanceof Blob) {
        arrayBuffer = await audioData.audio.arrayBuffer();
      } else if (audioData && (audioData as any).buffer) {
        arrayBuffer = (audioData as any).buffer.slice((audioData as any).byteOffset || 0, ((audioData as any).byteOffset || 0) + ((audioData as any).byteLength || (audioData as any).buffer.length));
      } else {
        console.error('Unknown audioData type:', typeof audioData, audioData);
        throw new Error('Unsupported audio data format from TTS');
      }

      // 2) turn it into a Blob and URL
      const blob = new Blob([arrayBuffer], { type: 'audio/mpeg' });
      const url = URL.createObjectURL(blob);

      // 3) play it through the browser Audio API
      const player = new Audio(url);

      // Add error handling for audio playback
      player.onerror = (error) => {
        console.error('Audio playback failed:', error);
        URL.revokeObjectURL(url);
        throw new Error('Audio playback failed');
      };

      await player.play();

      // Clean up the URL after playback
      player.onended = () => URL.revokeObjectURL(url);

    } catch (error) {
      console.error('TTS failed:', error);
      // Silently fail - don't crash the app, just log the error
      // Optionally could show a UI message, but for now just log
    }
  }
}

export const ttsService = new TTSService();