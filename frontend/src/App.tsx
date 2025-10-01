import React from 'react';
import './App.css';
import HomePage from './pages/HomePage';
import BackgroundSoundPicker from './components/BackgroundSoundPicker/BackgroundSoundPicker';

const App: React.FC = () => {
  return (
    <>
      <div className="global-bg-picker">
        <BackgroundSoundPicker />
      </div>
      <HomePage />
    </>
  );
};

export default App;
