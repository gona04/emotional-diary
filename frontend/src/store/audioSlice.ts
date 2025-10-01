import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type AudioState = {
  previewId: string | null;
  topPreviewId: string | null;
  padPlaying: boolean;
  padStartTime: number | null;
  padBpm: number | null;
};

const initialState: AudioState = {
  previewId: null,
  topPreviewId: null,
  padPlaying: false,
  padStartTime: null,
  padBpm: null,
};

const audioSlice = createSlice({
  name: 'audio',
  initialState,
  reducers: {
    setPreviewId(state, action: PayloadAction<string | null>) {
      state.previewId = action.payload;
    },
    setTopPreviewId(state, action: PayloadAction<string | null>) {
      state.topPreviewId = action.payload;
    },
    setPadPlaying(state, action: PayloadAction<boolean>) {
      state.padPlaying = action.payload;
    },
    setPadStartTime(state, action: PayloadAction<number | null>) {
      state.padStartTime = action.payload;
    },
    setPadBpm(state, action: PayloadAction<number | null>) {
      state.padBpm = action.payload;
    }
  }
});

export const { setPreviewId, setTopPreviewId, setPadPlaying, setPadStartTime, setPadBpm } = audioSlice.actions;
export default audioSlice.reducer;
