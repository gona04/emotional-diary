import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type TTSState = {
  preferredVoices: string[];
  pitch: number;
  rate: number;
  volume: number;
};

const initialState: TTSState = {
  preferredVoices: [
    'Samantha', 'Alex', 'Victoria', 'Karen', 'Moira', 'Tessa', // macOS voices
    'Google US English', 'Microsoft Zira Desktop', 'Microsoft David Desktop', // Other systems
  ],
  pitch: 1.0,   // Natural pitch
  rate: 0.85,   // Comfortable pace
  volume: 0.9,  // Comfortable volume
};

const ttsSlice = createSlice({
  name: 'tts',
  initialState,
  reducers: {
    setPreferredVoices(state: TTSState, action: PayloadAction<string[]>) {
      state.preferredVoices = action.payload;
    },
    setPitch(state: TTSState, action: PayloadAction<number>) {
      state.pitch = action.payload;
    },
    setRate(state: TTSState, action: PayloadAction<number>) {
      state.rate = action.payload;
    },
    setVolume(state: TTSState, action: PayloadAction<number>) {
      state.volume = action.payload;
    },
  }
});

export const { setPreferredVoices, setPitch, setRate, setVolume } = ttsSlice.actions;
export default ttsSlice.reducer;

// Utility function to get the best voice
export const getBestVoice = (preferredVoices: string[]) => {
  const voices = window.speechSynthesis.getVoices();

  for (const voiceName of preferredVoices) {
    const voice = voices.find(v => v.name.includes(voiceName));
    if (voice) return voice;
  }

  // Fallback to any English voice
  return voices.find(v => v.lang.startsWith('en')) || voices[0] || null;
};