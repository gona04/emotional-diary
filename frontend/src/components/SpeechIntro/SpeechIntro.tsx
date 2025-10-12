import React, { useState, useEffect, useRef, useCallback } from 'react';
import './SpeechIntro.css';
import { useStreamingASR } from '../../hooks';
import useChatSocket from '../../hooks/useChatSocket';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { addMessage } from '../../store/chatSlice';
import { setMicrophoneUnlocked, setShowMicrophone as setShowMicrophoneAction } from '../../store/uiSlice';
import SpeechSynthesisComponent from '../SpeechSynthesisComponent';
import { ttsService } from '../../services/ttsService';

type Props = {
  currentSentence: number;
  showMicrophone: boolean;
  onOpenChat: () => void;
  setCurrentSentence: (i: number) => void;
  setShowMicrophone: (v: boolean) => void;
};

const SpeechIntro: React.FC<Props> = ({ currentSentence, showMicrophone, onOpenChat, setCurrentSentence, setShowMicrophone }) => {
  const dispatch = useAppDispatch();
  const microphoneUnlocked = useAppSelector((s: any) => s.ui.microphoneUnlocked);
  const { pitch, rate, volume, selectedVoice } = useAppSelector((state) => state.tts);
  // local icon state: toggles icon between mic and pause without affecting the pulsing animation
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const lastFinalRef = useRef<string>('');
  const didInitRef = useRef<boolean>(false);
  const [micVisible, setMicVisible] = useState<boolean>(false);

  const wsUrl = (process.env.REACT_APP_STREAMING_WS_URL || 'ws://localhost:8765').replace(/\/$/, '');
  const sentences = [
    "Hello...",
    `How high are you?`,
    "Sorry",
    "I meant to ask",
    "Hi..",
    "How are you?",
    "Feel free to share about your day with me :)"
  ];

  // Add state to track if we should speak responses
  const [shouldSpeakResponses, setShouldSpeakResponses] = useState(true);
  
  const handleAssistant = useCallback((text: string) => {
    const trimmed = (text || '').trim();
    if (!trimmed) return;
    console.log('[AI Response]', trimmed);
    
    // Try to parse JSON response and extract therapist_response for speech
    let therapistResponse = trimmed;
    try {
      const parsed = JSON.parse(trimmed);
      if (parsed.therapist_response) {
        therapistResponse = parsed.therapist_response;
      }
    } catch (e) {
      // If not JSON, use the raw text
      console.log('[AI Response] Not JSON, using raw text for speech');
    }

    // Add to chat store
    dispatch(addMessage({ from: 'bot', text: therapistResponse }));
    
    // Speak the therapist response using text-to-speech (only if enabled and microphone is not actively listening)
    if (therapistResponse && shouldSpeakResponses && !isPaused) {
      // Add a small delay to ensure any audio processing is complete
      setTimeout(async () => {
        // Add slight pauses for more natural speech
        const naturalText = therapistResponse
          .replace(/\. /g, '... ')  // Add pauses after sentences
          .replace(/\? /g, '?.. ')  // Add pauses after questions
          .replace(/! /g, '!.. ');  // Add pauses after exclamations
        
        await ttsService.speak(naturalText, { voice: selectedVoice, pitch, rate, volume });
        console.log('[TTS] Speaking therapist response with enhanced voice');
      }, 500); // 500ms delay to ensure smooth transition
    }
  }, [dispatch, shouldSpeakResponses, isPaused, selectedVoice, pitch, rate, volume]);

  useChatSocket(handleAssistant);

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

    // Don't stop the connection automatically - keep listening for AI response and more speech
    // User can manually click pause when done

    dispatch(addMessage({ from: 'user', text: trimmed }));
    // Backend automatically calls Mistral after final transcript, no need to send again
  }, handleAssistant, { simulate: false });

  useEffect(() => {
    if (showMicrophone) {
      const raf: (fn: FrameRequestCallback) => number = typeof window !== 'undefined' && typeof window.requestAnimationFrame === 'function'
        ? window.requestAnimationFrame.bind(window)
        : ((fn: FrameRequestCallback) => setTimeout(fn, 16)) as unknown as (fn: FrameRequestCallback) => number;

      const cancel: (id: number) => void = typeof window !== 'undefined' && typeof window.cancelAnimationFrame === 'function'
        ? window.cancelAnimationFrame.bind(window)
        : ((id: number) => clearTimeout(id));

      const id = raf(() => setMicVisible(true));
      return () => cancel(id);
    } else {
      setMicVisible(false);
    }
  }, [showMicrophone]);

  useEffect(() => {
    if (microphoneUnlocked || didInitRef.current) {
      return;
    }
    didInitRef.current = true;
    // Keep the microphone hidden and locked until the intro script finishes.
    try { dispatch(setMicrophoneUnlocked(false)); } catch (e) {}
    try { setShowMicrophone(false); } catch (e) {}
    try { dispatch(setShowMicrophoneAction(false)); } catch (e) {}
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [dispatch, setShowMicrophone, microphoneUnlocked]);

  useEffect(() => {
    return () => {
      try { stop(); } catch (e) {}
      lastFinalRef.current = '';
    };
  }, [stop]);

  return (
    <div className="background-pink">
      <div className="speech-content">
                <div className={`intro-view ${micVisible ? 'hidden' : 'visible'}`} aria-hidden={showMicrophone}>
          {currentSentence < sentences.length && sentences[currentSentence]}
          <SpeechSynthesisComponent
            sentences={sentences}
            currentSentence={currentSentence}
            setCurrentSentence={setCurrentSentence}
            setShowMicrophone={setShowMicrophone}
          />
          {/* Background sound options moved to global top-right picker */}
        </div>
  <div className={`mic-view ${micVisible ? 'visible' : 'hidden'}`} aria-hidden={!showMicrophone}>
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
