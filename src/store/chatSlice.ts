import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';

export type Message = { from: 'user' | 'bot'; text: string };

export type ChatState = {
  messages: Message[];
  loading: boolean;
};

const initialState: ChatState = { messages: [], loading: false };

// Async thunk to simulate fetching a bot reply (placeholder for real API)
export const fetchBotReply = createAsyncThunk('chat/fetchBotReply', async (userText: string) => {
  // Simple heuristic-based reply (could be replaced with API call)
  const lowered = userText.toLowerCase();
  let reply = "I'm here to listen. Tell me more.";
  if (lowered.includes('sad') || lowered.includes('unhappy') || lowered.includes('depressed')) {
    reply = "I'm sorry you're feeling down. Would you like a grounding exercise?";
  } else if (lowered.includes('happy') || lowered.includes('good') || lowered.includes('great')) {
    reply = "That's wonderful to hear — tell me more about what's going well.";
  } else if (lowered.includes('help')) {
    reply = "I can listen or offer small suggestions — what would you prefer?";
  }

  // simulate network latency
  await new Promise((r) => setTimeout(r, 600 + Math.random() * 600));
  return reply;
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
