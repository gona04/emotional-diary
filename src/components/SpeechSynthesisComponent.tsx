import { useEffect } from 'react';
import { useAppDispatch } from '../store/hooks';
import { setShowMicrophone as setShowMicrophoneAction } from '../store/uiSlice';

interface SpeechSynthesisComponentProps {
    sentences: string[];
    currentSentence: number;
    setCurrentSentence: (index: number) => void;
    setShowMicrophone: (value: boolean) => void;
  }

const SpeechSynthesisComponent: React.FC<SpeechSynthesisComponentProps> = ({ sentences, currentSentence, setCurrentSentence, setShowMicrophone }) => {
  const dispatch = useAppDispatch();

  useEffect(() => {
    const speakSentence = (index:any) => {
      if (index < sentences.length) {
        const utterance = new SpeechSynthesisUtterance(sentences[index]);
        utterance.pitch = 1.2;
        utterance.rate = 0.8;
        utterance.onstart = () => setShowMicrophone(false);
        utterance.onend = () => {
          setTimeout(() => {
            setCurrentSentence(index + 1);
          }, 1000);
          // When the friendly prompt finishes, make sure the Speak UI is shown.
          // Call the prop setter for backward-compatibility and also dispatch to the store
          // directly so this works even when other wrappers changed the prop wiring.
          if (sentences[index] === "Feel free to share about your day with me :)") {
            try { setShowMicrophone(true); } catch (e) {}
            try { dispatch(setShowMicrophoneAction(true)); } catch (e) {}
          }
        };
        window.speechSynthesis.speak(utterance);
      }
    };

    speakSentence(currentSentence);

    return () => {
      window.speechSynthesis.cancel();
    };
  }, [currentSentence, sentences, setCurrentSentence, setShowMicrophone, dispatch]);

  return null;
};

export default SpeechSynthesisComponent;
