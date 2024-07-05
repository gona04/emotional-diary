import { useState } from 'react';
import RecorderComponent from './components/RecorderComponent';
import './App.css';
import SpeechSynthesisComponent from './components/SpeechSynthesisComponent';


function App() {
  const [currentSentence, setCurrentSentence] = useState(0);
  const [showInput, setShowInput] = useState(false);
  const [showMicrophone, setShowMicrophone] = useState(false);
  //The sentences that the bot will say
  const sentences = [
    "Hello...",
    `How high are you?`,
    "Sorry",
    "I meant to ask",
    "Hi..",
    "How are you?",
    "Feel free to share about your day with me :)"
  ];

  //When this is clicked, the input UI will be shown for the user to record their voice
  const handleNewUI = () => {
    setShowInput(true);
  };

  return (
    <div className="App">
      {!showInput && (
        <div className="background-pink">
          {!showMicrophone && (
            <div>
              {currentSentence < sentences.length && sentences[currentSentence]}
            <SpeechSynthesisComponent
          sentences={sentences}
          currentSentence={currentSentence}
          setCurrentSentence={setCurrentSentence}
          setShowMicrophone={setShowMicrophone}
          />
            </div>
            
          )}
          {showMicrophone && (
            <div className="mic-coverer">
              <div className='mic-cover'>
                <button className="microphone-icon" onClick={handleNewUI}>
                  <svg id='microphone' xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" height="10rem">
                    <path d="M192 0C139 0 96 43 96 96V256c0 53 43 96 96 96s96-43 96-96V96c0-53-43-96-96-96zM64 216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 89.1 66.2 162.7 152 174.4V464H120c-13.3 0-24 10.7-24 24s10.7 24 24 24h72 72c13.3 0 24-10.7 24-24s-10.7-24-24-24H216V430.4c85.8-11.7 152-85.3 152-174.4V216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 70.7-57.3 128-128 128s-128-57.3-128-128V216z" fill="rgb(239, 87, 113)" />
                  </svg>
                </button>
              </div>
            </div>
          )}
        </div>
      )}
      {
        showInput &&
        <>
          <RecorderComponent />
        </>
        
      }
    </div>
  );
}

export default App;
