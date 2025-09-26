import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';

const BACKEND_BASE_URL = (process.env.REACT_APP_BACKEND_URL || 'http://localhost:8000').replace(/\/$/, '');

async function callMistralProxy(userText: string): Promise<string> {
  const fetchFn: typeof fetch | undefined = typeof fetch === 'function' ? fetch : undefined;
  if (!fetchFn) {
    console.error('Global fetch API is not available in this environment.');
    return "I'm having trouble connecting right now, but I'm still here to listen.";
  }
  try {
    const response = await fetchFn(`${BACKEND_BASE_URL}/api/mistral/chat/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ prompt: userText }),
    });

    if (!response.ok) {
      const detail = await response.text();
      throw new Error(`Backend error ${response.status}: ${detail}`);
    }

    const data = await response.json();
    const text = (data?.text || '').trim();
    if (!text) {
      throw new Error('Empty response from assistant');
    }
    return text;
  } catch (err: any) {
    console.error('Failed calling Mistral backend', err);
    return "I ran into a hiccup reaching the journal companion. Could you try again in a moment?";
  }
}

export type Message = { from: 'user' | 'bot'; text: string };

export type ChatState = {
  messages: Message[];
  loading: boolean;
};

const initialState: ChatState = { messages: [], loading: false };

export const fetchBotReply = createAsyncThunk('chat/fetchBotReply', async (userText: string) => {
  return callMistralProxy(userText);
});

const chatSlice = createSlice({
  name: 'chat',
  initialState,
  reducers: {
    addMessage(state: ChatState, action: PayloadAction<Message>) {
      state.messages.push(action.payload);
    },
    clearMessages(state: ChatState) {
      state.messages = [];
    }
  },
  extraReducers: (builder: any) => {
    builder
      .addCase(fetchBotReply.pending, (state: ChatState) => {
        state.loading = true;
      })
      .addCase(fetchBotReply.fulfilled, (state: ChatState, action: PayloadAction<string>) => {
        state.loading = false;
        state.messages.push({ from: 'bot', text: action.payload });
      })
      .addCase(fetchBotReply.rejected, (state: ChatState) => {
        state.loading = false;
      });
  }
});

export const { addMessage, clearMessages } = chatSlice.actions;
export default chatSlice.reducer;
