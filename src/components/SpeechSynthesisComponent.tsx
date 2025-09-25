import { useEffect, useRef } from 'react';
import { useAppDispatch } from '../store/hooks';
import { setShowMicrophone as setShowMicrophoneAction, setMicrophoneUnlocked } from '../store/uiSlice';

interface SpeechSynthesisComponentProps {
    sentences: string[];
    currentSentence: number;
    setCurrentSentence: (index: number) => void;
    setShowMicrophone: (value: boolean) => void;
  }

const SpeechSynthesisComponent: React.FC<SpeechSynthesisComponentProps> = ({ sentences, currentSentence, setCurrentSentence, setShowMicrophone }) => {
  const dispatch = useAppDispatch();
  const timeoutsRef = useRef<number[]>([]);
  const unlockTimeoutRef = useRef<number | null>(null);

  useEffect(() => {

    const speakSentence = (index:any) => {
      if (index < sentences.length) {
        const utterance = new SpeechSynthesisUtterance(sentences[index]);
        utterance.pitch = 1.2;
        utterance.rate = 0.8;
        utterance.onstart = () => setShowMicrophone(false);
        utterance.onend = () => {
          // Wait 1s after the sentence finishes before advancing the sentence
          // and (if this is the friendly final prompt) enable the Speak UI so the
          // icon has a moment to load.
          const timeoutId = window.setTimeout(() => {
            setCurrentSentence(index + 1);
            // When the friendly prompt finishes, make sure the Speak UI is shown.
            // Call the prop setter for backward-compatibility and also dispatch to the store
            // directly so this works even when other wrappers changed the prop wiring.
            if (sentences[index] === "Feel free to share about your day with me :)") {
              // mark microphone as unlocked so UI can't be auto-enabled earlier
              try { dispatch(setMicrophoneUnlocked(true)); } catch (e) {}
              // wait one extra second then request the UI to show the mic (and call prop)
              try {
                unlockTimeoutRef.current = window.setTimeout(() => {
                  try { setShowMicrophone(true); } catch (e) {}
                  try { dispatch(setShowMicrophoneAction(true)); } catch (e) {}
                }, 1000) as unknown as number;
              } catch (e) {}
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
  }, [currentSentence, sentences, setCurrentSentence, setShowMicrophone, dispatch]);

  return null;
};

export default SpeechSynthesisComponent;
