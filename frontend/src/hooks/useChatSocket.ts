import { useCallback, useEffect, useRef, useState } from 'react';

const HANDSHAKE_PAYLOAD = {
  type: 'handshake',
  chat: true,
  simulate: true,
  format: 'text',
};

type AssistantHandler = (text: string, payload?: Record<string, unknown>) => void;

type UseChatSocketResult = {
  ready: boolean;
  sendMessage: (text: string) => void;
};

export const useChatSocket = (onAssistant: AssistantHandler): UseChatSocketResult => {
  const wsRef = useRef<WebSocket | null>(null);
  const queueRef = useRef<string[]>([]);
  const [ready, setReady] = useState<boolean>(false);

  const wsUrl = (process.env.REACT_APP_STREAMING_WS_URL || 'ws://localhost:8765').replace(/\/$/, '');

  useEffect(() => {
    const ws = new WebSocket(wsUrl);
    wsRef.current = ws;

    ws.onopen = () => {
      try { ws.send(JSON.stringify(HANDSHAKE_PAYLOAD)); } catch (e) { console.warn('chat handshake failed', e); }
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data as string);
        if (data.type === 'handshake_ack') {
          setReady(true);
          const pending = queueRef.current.splice(0, queueRef.current.length);
          pending.forEach((pendingText) => {
            try { ws.send(pendingText); } catch (err) { console.warn('chat send failed', err); }
          });
          return;
        }
        if (data.type === 'assistant' && typeof data.text === 'string') {
          onAssistant(data.text, data);
        }
      } catch (err) {
        console.log('chat socket message', event.data);
      }
    };

    ws.onerror = (err) => {
      console.error('chat socket error', err);
    };

    ws.onclose = () => {
      setReady(false);
      wsRef.current = null;
    };

    return () => {
      try { ws.close(); } catch (e) {}
      wsRef.current = null;
      setReady(false);
      queueRef.current = [];
    };
  }, [wsUrl, onAssistant]);

  const sendMessage = useCallback((text: string) => {
    const trimmed = (text || '').trim();
    if (!trimmed) return;
    const payload = JSON.stringify({ type: 'user_text', text: trimmed });
    const ws = wsRef.current;
    if (ws && ws.readyState === WebSocket.OPEN && ready) {
      try { ws.send(payload); } catch (err) { console.warn('chat send failed', err); }
    } else {
      queueRef.current.push(payload);
    }
  }, [ready]);

  return { ready, sendMessage };
};

export default useChatSocket;
