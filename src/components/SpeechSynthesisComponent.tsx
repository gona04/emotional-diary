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
        
        // Function to get the best available voice
        const getBestVoice = () => {
          const voices = window.speechSynthesis.getVoices();
          
          // Try to find a natural-sounding English voice
          const preferredVoices = [
            'Samantha', 'Alex', 'Victoria', 'Karen', 'Moira', 'Tessa', // macOS voices
            'Google US English', 'Microsoft Zira Desktop', 'Microsoft David Desktop', // Other systems
          ];
          
          for (const voiceName of preferredVoices) {
            const voice = voices.find(v => v.name.includes(voiceName));
            if (voice) return voice;
          }
          
          // Fallback to any English voice
          return voices.find(v => v.lang.startsWith('en')) || voices[0] || null;
        };
        
        // Set voice properties
        const selectedVoice = getBestVoice();
        utterance.voice = selectedVoice;
        utterance.pitch = 1.0;   // Natural pitch
        utterance.rate = 0.85;   // Comfortable pace
        utterance.volume = 0.9;  // Comfortable volume
        
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
  }, [currentSentence, sentences, setCurrentSentence, setShowMicrophone, dispatch]);

  return null;
};

export default SpeechSynthesisComponent;
