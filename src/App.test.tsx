import React from 'react';
import { render, screen } from '@testing-library/react';
import { Provider } from 'react-redux';
import App from './App';
import { store } from './store/store';

jest.mock('./pages/HomePage', () => () => <div data-testid="home-page">HomePage Stub</div>);
jest.mock('./components/BackgroundSoundPicker/BackgroundSoundPicker', () => () => (
  <div data-testid="bg-picker">Background Picker Stub</div>
));

beforeAll(() => {
  // minimal mocks for browser-only APIs touched by components
  Object.defineProperty(window, 'speechSynthesis', {
    value: {
      speak: jest.fn(),
      cancel: jest.fn(),
    },
    configurable: true,
  });

  (window as any).AudioContext =
    (window as any).AudioContext ||
    function AudioContextMock(this: any) {
      return {
        state: 'suspended',
        resume: jest.fn(() => Promise.resolve()),
        close: jest.fn(() => Promise.resolve()),
        createMediaStreamSource: jest.fn(() => ({ connect: jest.fn() })),
        audioWorklet: { addModule: jest.fn(() => Promise.resolve()) },
        destination: {},
      };
    };

  Object.defineProperty(navigator, 'mediaDevices', {
    value: { getUserMedia: jest.fn(() => Promise.resolve({})) },
    configurable: true,
  });
});

test('renders app shell with stubs', () => {
  render(
    <Provider store={store}>
      <App />
    </Provider>
  );

  expect(screen.getByTestId('bg-picker')).toBeInTheDocument();
  expect(screen.getByTestId('home-page')).toBeInTheDocument();
});
