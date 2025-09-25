import React from 'react';
import Chatbot from '../components/Chatbot';
import SpeechIntro from '../components/SpeechIntro';
import FadeMount from '../components/FadeMount';
import { useAppSelector, useAppDispatch } from '../store/hooks';
import { setShowInput, setShowMicrophone, setCurrentSentence } from '../store/uiSlice';

const HomePage: React.FC = () => {
  const dispatch = useAppDispatch();
  const currentSentence = useAppSelector((s: any) => s.ui.currentSentence);
  const showInput = useAppSelector((s: any) => s.ui.showInput);
  const showMicrophone = useAppSelector((s: any) => s.ui.showMicrophone);

  return (
    <div>
      <FadeMount show={!showInput}>
        <SpeechIntro
          currentSentence={currentSentence}
          showMicrophone={showMicrophone}
          setCurrentSentence={(i: number) => dispatch(setCurrentSentence(i))}
          setShowMicrophone={(v: boolean) => dispatch(setShowMicrophone(v))}
          onOpenChat={() => dispatch(setShowInput(true))}
        />
      </FadeMount>

      <FadeMount show={showInput}>
        <Chatbot onClose={() => dispatch(setShowInput(false))} />
      </FadeMount>
    </div>
  );
};

export default HomePage;
