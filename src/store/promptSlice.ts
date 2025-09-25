import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type PromptState = {
  promptMode: string;
  showPromptInfo: boolean;
  promptInfoText: string;
};

const initialState: PromptState = {
  promptMode: 'Walk With Me',
  showPromptInfo: false,
  promptInfoText: '',
};

const promptSlice = createSlice({
  name: 'prompt',
  initialState,
  reducers: {
    setPromptMode(state, action: PayloadAction<string>) {
      state.promptMode = action.payload;
    },
    setShowPromptInfo(state, action: PayloadAction<boolean>) {
      state.showPromptInfo = action.payload;
    },
    setPromptInfoText(state, action: PayloadAction<string>) {
      state.promptInfoText = action.payload;
    }
  }
});

export const { setPromptMode, setShowPromptInfo, setPromptInfoText } = promptSlice.actions;
export default promptSlice.reducer;
