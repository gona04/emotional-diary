import { useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { setShowMicrophone as setShowMicrophoneAction, setMicrophoneUnlocked } from '../store/uiSlice';
import { ttsService } from '../services/ttsService';

interface SpeechSynthesisComponentProps {
    sentences: string[];
    currentSentence: number;
    setCurrentSentence: (index: number) => void;
    setShowMicrophone: (value: boolean) => void;
  }

const SpeechSynthesisComponent: React.FC<SpeechSynthesisComponentProps> = ({ sentences, currentSentence, setCurrentSentence, setShowMicrophone }) => {
  const dispatch = useAppDispatch();
  const { pitch, rate, volume, selectedVoice } = useAppSelector((state) => state.tts);
  const timeoutsRef = useRef<number[]>([]);
  const unlockTimeoutRef = useRef<number | null>(null);

  useEffect(() => {
    const speakSentence = async (index: number) => {
      if (index < sentences.length) {
        setShowMicrophone(false);
        await ttsService.speak(sentences[index], { voice: selectedVoice, pitch, rate, volume });
        // Wait 1s after the sentence finishes before advancing the sentence
        const timeoutId = window.setTimeout(() => {
          setCurrentSentence(index + 1);
          // When the friendly prompt finishes, unlock and show microphone
          if (sentences[index] === "Feel free to share about your day with me :)") {
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
  }, [currentSentence, sentences, setCurrentSentence, setShowMicrophone, dispatch, selectedVoice, pitch, rate, volume]);

  return null;
};

export default SpeechSynthesisComponent;
