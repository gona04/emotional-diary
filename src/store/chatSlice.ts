import { createSlice, PayloadAction } from '@reduxjs/toolkit';

export type Message = { from: 'user' | 'bot'; text: string };

export type ChatState = {
  messages: Message[];
  loading: boolean;
};

const initialState: ChatState = { messages: [], loading: false };

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage(state: ChatState, action: PayloadAction<Message>) {
      state.messages.push(action.payload);
    },
    clearMessages(state: ChatState) {
      state.messages = [];
    },
    setLoading(state: ChatState, action: PayloadAction<boolean>) {
      state.loading = action.payload;
    }
  }
});

export const { addMessage, clearMessages, setLoading } = chatSlice.actions;
export default chatSlice.reducer;
