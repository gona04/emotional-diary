import { useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { setShowMicrophone as setShowMicrophoneAction, setMicrophoneUnlocked } from '../store/uiSlice';
import { ttsService } from '../services/ttsService';

interface SpeechSynthesisComponentProps {
    sentences: string[];
    currentSentence: number;
    setCurrentSentence: (index: number) => void;
    setShowMicrophone: (value: boolean) => void;
    onSpeechStart?: (index: number) => void; // Callback when speech starts
  }

const SpeechSynthesisComponent: React.FC<SpeechSynthesisComponentProps> = ({ sentences, currentSentence, setCurrentSentence, setShowMicrophone, onSpeechStart }) => {
  const dispatch = useAppDispatch();
  const { pitch, rate, volume, selectedVoice } = useAppSelector((state) => state.tts);
  const timeoutsRef = useRef<number[]>([]);
  const unlockTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    const speakSentence = async (index: number) => {
      if (index < sentences.length) {
        setShowMicrophone(false);
        // Remove emojis and special characters from text before speaking
        const cleanText = sentences[index].replace(/[^\w\s.,!?-]/g, '').trim();
        console.log('🎤 About to call ttsService.speak for:', `"${cleanText}"`);
        
        // Notify parent that speech is starting (after a tiny delay to let audio load)
        const startTimeoutId = window.setTimeout(() => {
          if (onSpeechStart) {
            onSpeechStart(index);
          }
        }, 200); // 200ms to let audio start loading
        timeoutsRef.current!.push(startTimeoutId);
        
        await ttsService.speak(cleanText, { voice: selectedVoice, pitch, rate, volume });
        // Wait 1s after the sentence finishes before advancing the sentence
        const timeoutId = window.setTimeout(() => {
          setCurrentSentence(index + 1);
          // When the friendly prompt finishes, unlock and show microphone
          if (sentences[index] === "Feel free to share about your day with me") {
            dispatch(setMicrophoneUnlocked(true));
            // wait one extra second then show the mic
            unlockTimeoutRef.current = window.setTimeout(() => {
              setShowMicrophone(true);
              dispatch(setShowMicrophoneAction(true));
            }, 1000) as unknown as number;
          }
        }, 1000);
        timeoutsRef.current!.push(timeoutId as unknown as number);
      }
    };

    speakSentence(currentSentence);

    return () => {
      // clear any pending timeouts
      timeoutsRef.current.forEach((id) => window.clearTimeout(id));
      timeoutsRef.current = [];
    };
  }, [currentSentence, sentences, setCurrentSentence, setShowMicrophone, dispatch, selectedVoice, pitch, rate, volume, onSpeechStart]);

  return null;
};

export default SpeechSynthesisComponent;
