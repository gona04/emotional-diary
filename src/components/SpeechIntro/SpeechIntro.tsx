import React, { useState, useEffect, useRef } from 'react';
import SpeechSynthesisComponent from '../SpeechSynthesisComponent';
import './SpeechIntro.css';
import { useStreamingASR } from '../../hooks';
import { useAppDispatch } from '../../store/hooks';
import { addMessage, fetchBotReply } from '../../store/chatSlice';

type Props = {
  currentSentence: number;
  showMicrophone: boolean;
  onOpenChat: () => void;
  setCurrentSentence: (i: number) => void;
  setShowMicrophone: (v: boolean) => void;
};

const SpeechIntro: React.FC<Props> = ({ currentSentence, showMicrophone, onOpenChat, setCurrentSentence, setShowMicrophone }) => {
  const dispatch = useAppDispatch();
  const sentences = [
    "Hello...",
    `How high are you?`,
    "Sorry",
    "I meant to ask",
    "Hi..",
    "How are you?",
    "Feel free to share about your day with me :)"
  ];
  // local icon state: toggles icon between mic and pause without affecting the pulsing animation
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const lastFinalRef = useRef<string>('');

  const wsUrl = (process.env.REACT_APP_STREAMING_WS_URL || 'ws://localhost:8765').replace(/\/$/, '');

  // streaming hook (real streaming). Logs partial/final transcripts.
  const { start, stop } = useStreamingASR(wsUrl, (p: string) => {
    const partial = (p || '').trim();
    if (!partial) return;
    console.log('[ASR partial]', partial);
  }, (f: string) => {
    const trimmed = (f || '').trim();
    if (!trimmed || trimmed === lastFinalRef.current) return;
    lastFinalRef.current = trimmed;

    console.log('[ASR final]', trimmed);

    try {
      stop();
    } catch (e) {
      console.warn('Failed to stop streaming after final transcript', e);
    }

    setIsPaused(false);

    dispatch(addMessage({ from: 'user', text: trimmed }));
    dispatch(fetchBotReply(trimmed) as any);

    // Note: Chat will only open when user clicks the chat icon, not automatically
    // User input has been processed and bot reply is being prepared
    console.log('Voice input processed. Click the chat icon to view conversation.');
  }, { simulate: false });

  useEffect(() => {
    return () => {
      try { stop(); } catch (e) {}
      lastFinalRef.current = '';
    };
  }, [stop]);

  return (
    <div className="background-pink">
      <div className="speech-content">
        <div className={`intro-view ${showMicrophone ? 'hidden' : 'visible'}`} aria-hidden={showMicrophone}>
          {currentSentence < sentences.length && sentences[currentSentence]}
          <SpeechSynthesisComponent
            sentences={sentences}
            currentSentence={currentSentence}
            setCurrentSentence={setCurrentSentence}
            setShowMicrophone={setShowMicrophone}
          />
          {/* Background sound options moved to global top-right picker */}
        </div>

        <div className={`mic-view ${showMicrophone ? 'visible' : 'hidden'}`} aria-hidden={!showMicrophone}>
          <div className="mic-coverer">
            <div className='mic-cover'>
              <button
                className="microphone-icon"
                onClick={async () => {
                  try {
                    const next = !isPaused;
                    setIsPaused(next);
                    if (next) {
                      lastFinalRef.current = '';
                      // start streaming
                      await start();
                    } else {
                      // stop streaming
                      stop();
                    }
                  } catch (e) { console.warn('mic toggle error', e); }
                }}
                aria-pressed={isPaused}
                aria-label={isPaused ? 'Resume' : 'Pause'}
              >
                {isPaused ? (
                  // Pause icon (two vertical bars)
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" height="10rem" aria-hidden="false" role="img">
                    <title>Pause</title>
                    <rect x="6" y="4" width="4" height="16" rx="1" fill="rgb(239, 87, 113)" />
                    <rect x="14" y="4" width="4" height="16" rx="1" fill="rgb(239, 87, 113)" />
                  </svg>
                ) : (
                  // Microphone icon
                  <svg id="microphone" xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" height="10rem" aria-hidden="false" role="img">
                    <title>Start microphone</title>
                    <path d="M192 0C139 0 96 43 96 96V256c0 53 43 96 96 96s96-43 96-96V96c0-53-43-96-96-96zM64 216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 89.1 66.2 162.7 152 174.4V464H120c-13.3 0-24 10.7-24 24s10.7 24 24 24h72 72c13.3 0 24-10.7 24-24s-10.7-24-24-24H216V430.4c85.8-11.7 152-85.3 152-174.4V216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 70.7-57.3 128-128 128s-128-57.3-128-128V216z" fill="rgb(239, 87, 113)" />
                  </svg>
                )}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default SpeechIntro;
