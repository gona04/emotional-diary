import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type UIState = {
  currentSentence: number;
  showInput: boolean;
  showMicrophone: boolean;
  // whether programmatic enabling of the microphone is allowed
  microphoneUnlocked: boolean;
  showAnimation: boolean;
};

const initialState: UIState = {
  currentSentence: 0,
  showInput: false,
  showMicrophone: false,
  microphoneUnlocked: false,
  showAnimation: false,
};

const uiSlice = createSlice({
  name: 'ui',
  initialState,
  reducers: {
    setCurrentSentence(state: UIState, action: PayloadAction<number>) {
      state.currentSentence = action.payload;
    },
    setShowInput(state: UIState, action: PayloadAction<boolean>) {
      // when enabling input, disable other right-side UI panels
      if (action.payload) {
        state.showMicrophone = false;
        state.showAnimation = false;
      }
      state.showInput = action.payload;
    },
    setShowMicrophone(state: UIState, action: PayloadAction<boolean>) {
      // prevent programmatic enabling of the microphone unless explicitly unlocked
      if (action.payload === true && !state.microphoneUnlocked) {
        // ignore attempts to enable if not unlocked
        return;
      }
      // when enabling microphone, disable other right-side UI panels
      if (action.payload) {
        state.showInput = false;
        state.showAnimation = false;
      }
      state.showMicrophone = action.payload;
    }
    ,
    setMicrophoneUnlocked(state: UIState, action: PayloadAction<boolean>) {
      state.microphoneUnlocked = action.payload;
    }
    ,
    setShowAnimation(state: UIState, action: PayloadAction<boolean>) {
      // when enabling animation, disable other right-side UI panels
      if (action.payload) {
        state.showInput = false;
        state.showMicrophone = false;
      }
      state.showAnimation = action.payload;
    }
  }
});

export const { setCurrentSentence, setShowInput, setShowMicrophone, setShowAnimation, setMicrophoneUnlocked } = uiSlice.actions;
export default uiSlice.reducer;
