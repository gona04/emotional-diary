import { useEffect } from 'react';

interface SpeechSynthesisComponentProps {
    sentences: string[];
    currentSentence: number;
    setCurrentSentence: (index: number) => void;
    setShowMicrophone: (value: boolean) => void;
  }

const SpeechSynthesisComponent: React.FC<SpeechSynthesisComponentProps> = ({ sentences, currentSentence, setCurrentSentence, setShowMicrophone }) => {
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
          if (sentences[index] === "Feel free to share about your day with me :)") {
            setShowMicrophone(true);
          }
        };
        window.speechSynthesis.speak(utterance);
      }
    };

    speakSentence(currentSentence);

    return () => {
      window.speechSynthesis.cancel();
    };
  }, [currentSentence, sentences, setCurrentSentence, setShowMicrophone]);

  return null;
};

export default SpeechSynthesisComponent;
