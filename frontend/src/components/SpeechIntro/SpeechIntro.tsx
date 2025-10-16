import React, { useState, useEffect, useRef, useCallback } from "react";
import "./SpeechIntro.css";
import { useStreamingASR } from "../../hooks";
import useChatSocket from "../../hooks/useChatSocket";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { addMessage } from "../../store/chatSlice";
import {
  setMicrophoneUnlocked,
  setShowMicrophone as setShowMicrophoneAction,
} from "../../store/uiSlice";
import SpeechSynthesisComponent from "../SpeechSynthesisComponent";
import { ttsService } from "../../services/ttsService";

type Props = {
  currentSentence: number;
  showMicrophone: boolean;
  onOpenChat: () => void;
  setCurrentSentence: (i: number) => void;
  setShowMicrophone: (v: boolean) => void;
};

const SpeechIntro: React.FC<Props> = ({
  currentSentence,
  showMicrophone,
  onOpenChat,
  setCurrentSentence,
  setShowMicrophone,
}) => {
  const dispatch = useAppDispatch();
  const microphoneUnlocked = useAppSelector(
    (s: any) => s.ui.microphoneUnlocked
  );
  const { pitch, rate, volume, selectedVoice } = useAppSelector(
    (state) => state.tts
  );
  // local icon state: toggles icon between mic and pause without affecting the pulsing animation
  const [isPaused, setIsPaused] = useState<boolean>(false);
  const lastFinalRef = useRef<string>("");
  const didInitRef = useRef<boolean>(false);
  const [micVisible, setMicVisible] = useState<boolean>(false);
  const [displayedText, setDisplayedText] = useState<string>("");

  const wsUrl = (
    process.env.REACT_APP_STREAMING_WS_URL || "ws://localhost:8765"
  ).replace(/\/$/, "");

  // State for jokes - start with EMPTY array, not defaults
  const [sentences, setSentences] = useState<string[]>([]);
  const [jokesLoaded, setJokesLoaded] = useState(false);
  const fetchingJokesRef = useRef(false); // Prevent duplicate fetches

  // Fetch intro jokes from backend on mount - ONLY ONCE
  useEffect(() => {
    // Prevent duplicate fetches
    if (fetchingJokesRef.current) {
      console.log("[IntroJokes] ⚠️ Already fetching, skipping duplicate request");
      return;
    }
    
    fetchingJokesRef.current = true;
    
    let ws: WebSocket | null = null;
    let timeoutId: NodeJS.Timeout | null = null;
    
    const fetchIntroJokes = async () => {
      try {
        ws = new WebSocket(wsUrl);
        
        ws.onopen = () => {
          console.log("[IntroJokes] WebSocket connected, requesting jokes");
          // Send handshake first
          ws!.send(JSON.stringify({
            type: "handshake",
            sampleRate: 16000,
            channels: 1,
            format: "s16le",
            simulate: true,
            chat: true
          }));
          
          // Request jokes after a short delay to allow handshake to complete
          setTimeout(() => {
            if (ws && ws.readyState === WebSocket.OPEN) {
              console.log("[IntroJokes] Sending get_intro_jokes request");
              ws.send(JSON.stringify({ type: "get_intro_jokes" }));
            }
          }, 100);
        };
        
        ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data);
            console.log("[IntroJokes] Received message type:", data.type);
            if (data.type === "intro_jokes" && Array.isArray(data.jokes)) {
              console.log("[IntroJokes] ✅ Received jokes from backend:", data.jokes);
              setSentences(data.jokes); // Set jokes ONCE
              setJokesLoaded(true);
              fetchingJokesRef.current = false; // Reset flag
              if (ws) ws.close(); // Close connection after receiving jokes
            }
          } catch (e) {
            console.error("[IntroJokes] Error parsing message:", e);
          }
        };
        
        ws.onerror = (error) => {
          console.error("[IntroJokes] WebSocket error:", error);
          // Fallback to default jokes on error
          setSentences([
            "Hey there..",
            "I'd ask..",
            "How you are..",
            "But..",
            "I'm afraid..",
            "You'll tell me..",
            "Just kidding..",
            "I don't have..",
            "A heart..",
            "I'm a machine..",
            "But I can..",
            "Surprisingly..",
            "Take that chaos..",
            "Without judgment..",
            "So..",
            "Tell me..",
            "Feel free to share about your day with me"
          ]);
          setJokesLoaded(true);
          fetchingJokesRef.current = false; // Reset flag
        };
        
        ws.onclose = () => {
          console.log("[IntroJokes] WebSocket closed");
        };
        
        // Timeout fallback - use default jokes if no response in 5 seconds
        timeoutId = setTimeout(() => {
          console.log("[IntroJokes] ⏱️ Timeout - using default jokes");
          setSentences([
            "Hey there..",
            "I'd ask..",
            "How you are..",
            "But..",
            "I'm afraid..",
            "You'll tell me..",
            "Just kidding..",
            "I don't have..",
            "A heart..",
            "I'm a machine..",
            "But I can..",
            "Surprisingly..",
            "Take that chaos..",
            "Without judgment..",
            "So..",
            "Tell me..",
            "Feel free to share about your day with me"
          ]);
          setJokesLoaded(true);
          fetchingJokesRef.current = false; // Reset flag
          if (ws) ws.close();
        }, 5000);
      } catch (error) {
        console.error("[IntroJokes] Error fetching jokes:", error);
        // Fallback to default jokes on exception
        setSentences([
          "Hey there..",
          "I'd ask..",
          "How you are..",
          "But..",
          "I'm afraid..",
          "You'll tell me..",
          "Just kidding..",
          "I don't have..",
          "A heart..",
          "I'm a machine..",
          "But I can..",
          "Surprisingly..",
          "Take that chaos..",
          "Without judgment..",
          "So..",
          "Tell me..",
          "Feel free to share about your day with me"
        ]);
        setJokesLoaded(true); // Use default jokes on error
      }
    };
    
    fetchIntroJokes();
    
    // Cleanup function
    return () => {
      if (timeoutId) clearTimeout(timeoutId);
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.close();
      }
    };
  }, [wsUrl]); // Only depend on wsUrl, fetch fresh jokes on every mount


  const handleAssistant = useCallback(
    (text: string) => {
      const trimmed = (text || "").trim();
      if (!trimmed) return;
      console.log("[AI Response]", trimmed);

      // Try to parse JSON response and extract therapist_response for speech
      let therapistResponse = trimmed;
      try {
        const parsed = JSON.parse(trimmed);
        if (parsed.therapist_response) {
          therapistResponse = parsed.therapist_response;
        }
      } catch (e) {
        // If not JSON, use the raw text
        console.log("[AI Response] Not JSON, using raw text for speech");
      }

      // Add to chat store
      dispatch(addMessage({ from: "bot", text: therapistResponse }));

      // Speak the therapist response using text-to-speech (only if microphone is not actively listening)
      if (therapistResponse && !isPaused) {
        // Add a small delay to ensure any audio processing is complete
        setTimeout(async () => {
          // Add slight pauses for more natural speech
          const naturalText = therapistResponse
            .replace(/\. /g, "... ") // Add pauses after sentences
            .replace(/\? /g, "?.. ") // Add pauses after questions
            .replace(/! /g, "!.. "); // Add pauses after exclamations

          await ttsService.speak(naturalText, {
            voice: selectedVoice,
            pitch,
            rate,
            volume,
          });
          console.log("[TTS] Speaking therapist response with enhanced voice");
        }, 50); // 500ms delay to ensure smooth transition
      }
    },
    [
      dispatch,
      isPaused,
      selectedVoice,
      pitch,
      rate,
      volume,
    ]
  );

  useChatSocket(handleAssistant);

  // Callback when speech actually starts - show text at this moment
  const handleSpeechStart = useCallback((index: number) => {
    console.log('[SpeechStart] Showing text for sentence:', index);
    setDisplayedText(sentences[index]);
  }, [sentences]);

  // streaming hook (real streaming). Logs partial/final transcripts.
  const { start, stop } = useStreamingASR(
    wsUrl,
    (p: string) => {
      const partial = (p || "").trim();
      if (!partial) return;
      console.log("[ASR partial]", partial);
    },
    (f: string) => {
      const trimmed = (f || "").trim();
      if (!trimmed || trimmed === lastFinalRef.current) return;
      lastFinalRef.current = trimmed;

      console.log("[ASR final]", trimmed);

      // Don't stop the connection automatically - keep listening for AI response and more speech
      // User can manually click pause when done

      dispatch(addMessage({ from: "user", text: trimmed }));
      // Backend automatically calls Mistral after final transcript, no need to send again
    },
    handleAssistant,
    { simulate: false }
  );

  useEffect(() => {
    if (showMicrophone) {
      const raf: (fn: FrameRequestCallback) => number =
        typeof window !== "undefined" &&
        typeof window.requestAnimationFrame === "function"
          ? window.requestAnimationFrame.bind(window)
          : (((fn: FrameRequestCallback) => setTimeout(fn, 16)) as unknown as (
              fn: FrameRequestCallback
            ) => number);

      const cancel: (id: number) => void =
        typeof window !== "undefined" &&
        typeof window.cancelAnimationFrame === "function"
          ? window.cancelAnimationFrame.bind(window)
          : (id: number) => clearTimeout(id);

      const id = raf(() => setMicVisible(true));
      return () => cancel(id);
    } else {
      setMicVisible(false);
    }
  }, [showMicrophone]);

  // Text display is now handled by handleSpeechStart callback
  // No need for separate useEffect that shows text based on currentSentence

  useEffect(() => {
    return () => {
      try {
        stop();
      } catch (e) {}
      lastFinalRef.current = "";
    };
  }, [stop]);

  return (
    <div className="background-pink">
      <div className="speech-content">
        <div
          className={`intro-view ${micVisible ? "hidden" : "visible"}`}
          aria-hidden={showMicrophone}
        >
          {displayedText}
          {jokesLoaded && ( // Only render SpeechSynthesis when jokes are ready
            <SpeechSynthesisComponent
              sentences={sentences}
              currentSentence={currentSentence}
              setCurrentSentence={setCurrentSentence}
              setShowMicrophone={setShowMicrophone}
              onSpeechStart={handleSpeechStart}
            />
          )}
          {/* Background sound options moved to global top-right picker */}
        </div>
        <div
          className={`mic-view ${micVisible ? "visible" : "hidden"}`}
          aria-hidden={!showMicrophone}
        >
          <div className="mic-coverer">
            <div className="mic-cover">
              <button
                className="microphone-icon"
                onClick={async () => {
                  try {
                    const next = !isPaused;
                    setIsPaused(next);
                    if (next) {
                      lastFinalRef.current = "";
                      // start streaming
                      await start();
                    } else {
                      // stop streaming
                      stop();
                    }
                  } catch (e) {
                    console.warn("mic toggle error", e);
                  }
                }}
                aria-pressed={isPaused}
                aria-label={isPaused ? "Resume" : "Pause"}
              >
                {isPaused ? (
                  // Pause icon (two vertical bars)
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 24 24"
                    height="10rem"
                    aria-hidden="false"
                    role="img"
                  >
                    <title>Pause</title>
                    <rect
                      x="6"
                      y="4"
                      width="4"
                      height="16"
                      rx="1"
                      fill="rgb(239, 87, 113)"
                    />
                    <rect
                      x="14"
                      y="4"
                      width="4"
                      height="16"
                      rx="1"
                      fill="rgb(239, 87, 113)"
                    />
                  </svg>
                ) : (
                  // Microphone icon
                  <svg
                    id="microphone"
                    xmlns="http://www.w3.org/2000/svg"
                    viewBox="0 0 384 512"
                    height="10rem"
                    aria-hidden="false"
                    role="img"
                  >
                    <title>Start microphone</title>
                    <path
                      d="M192 0C139 0 96 43 96 96V256c0 53 43 96 96 96s96-43 96-96V96c0-53-43-96-96-96zM64 216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 89.1 66.2 162.7 152 174.4V464H120c-13.3 0-24 10.7-24 24s10.7 24 24 24h72 72c13.3 0 24-10.7 24-24s-10.7-24-24-24H216V430.4c85.8-11.7 152-85.3 152-174.4V216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 70.7-57.3 128-128 128s-128-57.3-128-128V216z"
                      fill="rgb(239, 87, 113)"
                    />
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
