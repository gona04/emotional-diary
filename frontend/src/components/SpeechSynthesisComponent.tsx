import { useEffect, useRef } from 'react';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { setShowMicrophone as setShowMicrophoneAction, setMicrophoneUnlocked } from '../store/uiSlice';
import { getBestVoice } from '../store/ttsSlice';

interface SpeechSynthesisComponentProps {
    sentences: string[];
    currentSentence: number;
    setCurrentSentence: (index: number) => void;
    setShowMicrophone: (value: boolean) => void;
  }

const SpeechSynthesisComponent: React.FC<SpeechSynthesisComponentProps> = ({ sentences, currentSentence, setCurrentSentence, setShowMicrophone }) => {
  const dispatch = useAppDispatch();
  const { preferredVoices, pitch, rate, volume } = useAppSelector((state) => state.tts);
  const timeoutsRef = useRef<number[]>([]);
  const unlockTimeoutRef = useRef<number | null>(null);

  useEffect(() => {

    const speakSentence = (index:any) => {
      if (index < sentences.length) {
        const utterance = new SpeechSynthesisUtterance(sentences[index]);
        
        // Function to get the best available voice
        const selectedVoice = getBestVoice(preferredVoices);
        utterance.voice = selectedVoice;
        utterance.pitch = pitch;
        utterance.rate = rate;
        utterance.volume = volume;
        
        utterance.onstart = () => setShowMicrophone(false);
        utterance.onend = () => {
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
        };
        window.speechSynthesis.speak(utterance);
      }
    };

    speakSentence(currentSentence);

    return () => {
      // clear any pending timeouts
      timeoutsRef.current.forEach((id) => window.clearTimeout(id));
      timeoutsRef.current = [];
      window.speechSynthesis.cancel();
    };
  }, [currentSentence, sentences, setCurrentSentence, setShowMicrophone, dispatch, preferredVoices, pitch, rate, volume]);

  return null;
};

export default SpeechSynthesisComponent;
