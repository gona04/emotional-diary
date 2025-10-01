import React, { useState } from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import { render } from '@testing-library/react';
import SpeechIntro from './SpeechIntro';
import uiReducer from '../../store/uiSlice';
import chatReducer from '../../store/chatSlice';
import promptReducer from '../../store/promptSlice';
import audioReducer from '../../store/audioSlice';

jest.mock('../../hooks', () => ({
  useStreamingASR: () => ({ start: jest.fn(), stop: jest.fn() }),
}));

beforeAll(() => {
  // Minimal speech synthesis shim so the component can render.
  // @ts-expect-error attaching on test env
  global.SpeechSynthesisUtterance = function MockUtterance(this: any, text: string) {
    this.text = text;
  };
  (window as any).speechSynthesis = {
    speak: jest.fn(),
    cancel: jest.fn(),
  };
});

function makeStore() {
  return configureStore({
    reducer: {
      ui: uiReducer,
      chat: chatReducer,
      prompt: promptReducer,
      audio: audioReducer,
    },
  });
}

describe('SpeechIntro', () => {
  test('hides the microphone when it mounts', () => {
    const store = makeStore();
    const setShowMicrophoneMock = jest.fn();

    const Harness: React.FC = () => {
      const [currentSentence, setCurrentSentence] = useState(0);
      const [showMicrophone, setShowMicrophone] = useState(false);

      return (
        <SpeechIntro
          currentSentence={currentSentence}
          showMicrophone={showMicrophone}
          onOpenChat={jest.fn()}
          setCurrentSentence={setCurrentSentence}
          setShowMicrophone={(value) => {
            setShowMicrophone(value);
            setShowMicrophoneMock(value);
          }}
        />
      );
    };

    render(
      <Provider store={store}>
        <Harness />
      </Provider>
    );

    expect(setShowMicrophoneMock).toHaveBeenCalledWith(false);
  });
});