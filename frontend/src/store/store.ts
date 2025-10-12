import { configureStore } from '@reduxjs/toolkit';
import uiReducer from './uiSlice';
import chatReducer from './chatSlice';
import promptReducer from './promptSlice';
import audioReducer from './audioSlice';
import ttsReducer from './ttsSlice';

// Simple logger middleware
const logger = (storeAPI: any) => (next: any) => (action: any) => {
  // eslint-disable-next-line no-console
  console.log('dispatching', action.type);
  const result = next(action);
  // eslint-disable-next-line no-console
  console.log('next state', storeAPI.getState());
  return result;
};

export const store = configureStore({
  reducer: {
    ui: uiReducer,
    chat: chatReducer,
    prompt: promptReducer,
    audio: audioReducer,
    tts: ttsReducer,
  },
  middleware: (getDefaultMiddleware: any) => getDefaultMiddleware().concat(logger),
  devTools: true,
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch;

