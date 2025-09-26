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

      {/* Floating Chat Icon - only show when chat is not already open */}
      {!showInput && (
        <button
          className="chat-icon-button"
          onClick={() => dispatch(setShowInput(true))}
          title="Open chat"
          aria-label="Open chat"
        >
          <svg
            xmlns="http://www.w3.org/2000/svg"
            viewBox="0 0 24 24"
            width="24"
            height="24"
            fill="currentColor"
          >
            <path d="M20 2H4C2.9 2 2 2.9 2 4v12c0 1.1.9 2 2 2h4l4 4 4-4h4c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-2 12H6v-2h12v2zm0-3H6V9h12v2zm0-3H6V6h12v2z"/>
          </svg>
        </button>
      )}
    </div>
  );
};

export default HomePage;
