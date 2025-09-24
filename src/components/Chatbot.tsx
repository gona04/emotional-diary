import React, { useState, useRef, useEffect } from 'react';
import './Chatbot.css';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { addMessage, fetchBotReply } from '../store/chatSlice';

// bot replies are produced by the async thunk in the chat slice

type Props = {
  onClose?: () => void;
};

const Chatbot: React.FC<Props> = ({ onClose }) => {
  const messages = useAppSelector((s: any) => s.chat.messages || []);
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement | null>(null);

  const dispatch = useAppDispatch();

  useEffect(() => {
    // Greet when the chatbot mounts
    dispatch(addMessage({ from: 'bot', text: 'Hi — I\'m your friendly diary assistant. How can I help today?' }));
    inputRef.current?.focus();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const send = (text: string) => {
    const trimmed = text.trim();
    if (!trimmed) return;
    dispatch(addMessage({ from: 'user', text: trimmed }));
    setInput('');
    // dispatch async thunk to generate bot reply (simulated)
  // dispatch async thunk to generate bot reply (simulated)
  // cast to any to satisfy the TS inference for thunk action here
  dispatch(fetchBotReply(trimmed) as any);
  };

  return (
    <div className="chat-overlay">
      <div className="chat-container">
        <div className="chat-header">
          <div>Diary Assistant</div>
          <button className="chat-close" onClick={() => onClose && onClose()}>Close</button>
        </div>
      <div className="chat-body" role="log">
        {messages.map((msg: any, i: number) => (
          <div key={i} className={`chat-message ${msg.from === 'bot' ? 'bot' : 'user'}`}>
            <div className="chat-text">{msg.text}</div>
          </div>
        ))}
      </div>

      <div className="chat-input-area">
        <input
          ref={inputRef}
          placeholder="Write how you feel..."
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter') send(input);
          }}
        />
        <button onClick={() => send(input)}>Send</button>
      </div>
      </div>
    </div>
  );
};

export default Chatbot;
