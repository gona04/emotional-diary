import React, { useState, useRef, useEffect } from 'react';
import './Chatbot.css';

const sampleBotReplies = [
  "I'm here to listen. Tell me what's on your mind.",
  "That sounds important — would you like to explore it more?",
  "I'm sorry you're feeling that way. Do you know when that started?",
  "Take a breath. Would you like a suggestion to feel a bit better right now?",
  "Thanks for sharing — small steps often help. What's one thing you can do today?",
];

type Props = {
  onClose?: () => void;
};

const Chatbot: React.FC<Props> = ({ onClose }) => {
  const [messages, setMessages] = useState<Array<{ from: 'user' | 'bot'; text: string }>>([]);
  const [input, setInput] = useState('');
  const inputRef = useRef<HTMLInputElement | null>(null);

  useEffect(() => {
    // Greet when the chatbot mounts
    setMessages([{ from: 'bot', text: 'Hi — I\'m your friendly diary assistant. How can I help today?' }]);
    inputRef.current?.focus();
  }, []);

  const send = (text: string) => {
    if (!text.trim()) return;
    const trimmed = text.trim();
    setMessages((m) => [...m, { from: 'user', text: trimmed }]);
    setInput('');

    // Simulate a bot reply with a small delay
    window.setTimeout(() => {
      // Simple reply selection based on keywords — keeps everything client-side.
      const lowered = trimmed.toLowerCase();
      let reply = sampleBotReplies[Math.floor(Math.random() * sampleBotReplies.length)];
      if (lowered.includes('sad') || lowered.includes('unhappy') || lowered.includes('depressed')) {
        reply = "I'm sorry you're feeling down. Would you like a grounding exercise?";
      } else if (lowered.includes('happy') || lowered.includes('good') || lowered.includes('great')) {
        reply = "That's wonderful to hear — tell me more about what's going well.";
      } else if (lowered.includes('help')) {
        reply = "I can listen or offer small suggestions — what would you prefer?";
      }
      setMessages((m) => [...m, { from: 'bot', text: reply }]);
    }, 600 + Math.random() * 700);
  };

  return (
    <div className="chat-overlay">
      <div className="chat-container">
        <div className="chat-header">
          <div>Diary Assistant</div>
          <button className="chat-close" onClick={() => onClose && onClose()}>Close</button>
        </div>
      <div className="chat-body" role="log">
        {messages.map((msg, i) => (
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
