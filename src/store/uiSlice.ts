import { createSlice, PayloadAction } from '@reduxjs/toolkit';

type UIState = {
  currentSentence: number;
  showInput: boolean;
  showMicrophone: boolean;
  showAnimation: boolean;
};

const initialState: UIState = {
  currentSentence: 0,
  showInput: false,
  showMicrophone: true,
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
      state.showInput = action.payload;
    },
    setShowMicrophone(state: UIState, action: PayloadAction<boolean>) {
      state.showMicrophone = action.payload;
    }
    ,
    setShowAnimation(state: UIState, action: PayloadAction<boolean>) {
      state.showAnimation = action.payload;
    }
  }
});

export const { setCurrentSentence, setShowInput, setShowMicrophone, setShowAnimation } = uiSlice.actions;
export default uiSlice.reducer;
