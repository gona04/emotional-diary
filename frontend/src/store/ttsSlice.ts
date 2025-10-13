import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type TTSState = {
  voices: string[];
  pitch: number;
  rate: number;
  volume: number;
  selectedVoice: string;
};

const initialState: TTSState = {
  voices: ['en-US-EmmaNeural'],
  pitch: -10,   // Even lower pitch for therapy
  rate: 0.85,   // Comfortable pace
  volume: 0.9,  // Comfortable volume
  selectedVoice: 'en-US-EmmaNeural',
};

const ttsSlice = createSlice({
  name: 'tts',
  initialState,
  reducers: {
    setPitch(state: TTSState, action: PayloadAction<number>) {
      state.pitch = action.payload;
    },
    setRate(state: TTSState, action: PayloadAction<number>) {
      state.rate = action.payload;
    },
    setVolume(state: TTSState, action: PayloadAction<number>) {
      state.volume = action.payload;
    },
    setSelectedVoice(state: TTSState, action: PayloadAction<string>) {
      state.selectedVoice = action.payload;
    },
  }
});

export const { setPitch, setRate, setVolume, setSelectedVoice } = ttsSlice.actions;
export default ttsSlice.reducer;