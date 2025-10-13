import { act, render } from '@testing-library/react';
import React from 'react';
import { Provider } from 'react-redux';
import { configureStore } from '@reduxjs/toolkit';
import SpeechSynthesisComponent from './SpeechSynthesisComponent';
import uiReducer from '../store/uiSlice';
import chatReducer from '../store/chatSlice';
import promptReducer from '../store/promptSlice';
import audioReducer from '../store/audioSlice';

const FINAL_SENTENCE = 'Feel free to share about your day with me :)';

class MockSpeechSynthesisUtterance {
  text: string;
  onstart: (() => void) | null = null;
  onend: (() => void) | null = null;
  pitch = -5;
  rate = -2;

  constructor(text: string) {
    this.text = text;
  }
}

const speakMock = jest.fn();

beforeAll(() => {
  // @ts-expect-error test shim
  global.SpeechSynthesisUtterance = MockSpeechSynthesisUtterance;
});

beforeEach(() => {
  jest.useFakeTimers();
  speakMock.mockClear();
  (window as any).speechSynthesis = {
    speak: speakMock,
    cancel: jest.fn(),
  };
});

afterEach(() => {
  jest.clearAllTimers();
  jest.useRealTimers();
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

describe('SpeechSynthesisComponent', () => {
  test('enables the microphone when the final prompt finishes', () => {
    const setCurrentSentence = jest.fn();
    const setShowMicrophone = jest.fn();
    const store = makeStore();

    render(
      <Provider store={store}>
        <SpeechSynthesisComponent
          sentences={[FINAL_SENTENCE]}
          currentSentence={0}
          setCurrentSentence={setCurrentSentence}
          setShowMicrophone={setShowMicrophone}
        />
      </Provider>
    );

    expect(speakMock).toHaveBeenCalledTimes(1);
    const utterance = speakMock.mock.calls[0][0] as MockSpeechSynthesisUtterance;

    act(() => {
      utterance.onstart?.();
      utterance.onend?.();
      jest.advanceTimersByTime(1000);
      jest.advanceTimersByTime(1200);
    });

    expect(setCurrentSentence).toHaveBeenCalledWith(1);
    expect(setShowMicrophone).toHaveBeenCalledWith(true);
  });
});