import { useState, useEffect } from 'react';


import './App.css';

function App() {
  const [text, setText] = useState<string>('');
  const [currentSentence, setCurrentSentence] = useState<number>(0);
  const [showInput, setShowInput] = useState<boolean>(false);
  const [showMicrophone, setShowMicrophone] = useState<boolean>(false);

  useEffect(() => {
    let sentences = [
      "Hello, how high are you?",
      "Sorry",
      "I meant to ask",
      "Hi..",
      "how are you?",
      "feel free to share about your day with me :)"
    ];

    const speakSentence = (index: number) => {
      if (index < sentences.length) {
        const utterance = new SpeechSynthesisUtterance(sentences[index]);
        utterance.pitch = 1.2; 
        utterance.rate = 0.8; 
        utterance.onstart = () => {
          setShowMicrophone(false);
        };
        utterance.onend = () => {
          setTimeout(() => {
            setCurrentSentence(index + 1);
          }, 1000);
          if(sentences[index] === "feel free to share about your day with me :)") {
            setShowMicrophone(true);
          }
        };
        window.speechSynthesis.speak(utterance);
        setText(sentences[index]);
      }
    };

    speakSentence(currentSentence); 
    return () => {
      window.speechSynthesis.cancel();
    };
  }, [currentSentence]);

  function newUI() {
    setShowInput(true);
  }

  return (
    <div className="App">
     {!showInput &&
      <div className="background-pink">
      {!showMicrophone &&(text)}
      { showMicrophone && (
        <div className="mic-coverer">
          <div className='mic-cover'>
            <div className="microphone-icon" onClick={newUI}>
              <svg id='microphone' xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" height="10rem">
              <path d="M192 0C139 0 96 43 96 96V256c0 53 43 96 96 96s96-43 96-96V96c0-53-43-96-96-96zM64 216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 89.1 66.2 162.7 152 174.4V464H120c-13.3 0-24 10.7-24 24s10.7 24 24 24h72 72c13.3 0 24-10.7 24-24s-10.7-24-24-24H216V430.4c85.8-11.7 152-85.3 152-174.4V216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 70.7-57.3 128-128 128s-128-57.3-128-128V216z" fill="rgb(239, 87, 113)"/>
            </svg>
          </div>
        </div>
        </div>
      )} 
      </div> }
      {showInput && (
      <div className="microphone-new-place">
        <svg id='microphone' xmlns="http://www.w3.org/2000/svg" viewBox="0 0 384 512" height="2rem">
          <path d="M192 0C139 0 96 43 96 96V256c0 53 43 96 96 96s96-43 96-96V96c0-53-43-96-96-96zM64 216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 89.1 66.2 162.7 152 174.4V464H120c-13.3 0-24 10.7-24 24s10.7 24 24 24h72 72c13.3 0 24-10.7 24-24s-10.7-24-24-24H216V430.4c85.8-11.7 152-85.3 152-174.4V216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 70.7-57.3 128-128 128s-128-57.3-128-128V216z" fill="rgb(239, 87, 113)"/>
        </svg>
        <form action="/">
          <input type="text" className="bgInput" />
          <button className='remove-btn-style' type="submit" title='submit'>
          <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 512 512" height="1.5rem"><path d="M498.1 5.6c10.1 7 15.4 19.1 13.5 31.2l-64 416c-1.5 9.7-7.4 18.2-16 23s-18.9 5.4-28 1.6L284 427.7l-68.5 74.1c-8.9 9.7-22.9 12.9-35.2 8.1S160 493.2 160 480V396.4c0-4 1.5-7.8 4.2-10.7L331.8 202.8c5.8-6.3 5.6-16-.4-22s-15.7-6.4-22-.7L106 360.8 17.7 316.6C7.1 311.3 .3 300.7 0 288.9s5.9-22.8 16.1-28.7l448-256c10.7-6.1 23.9-5.5 34 1.4z" fill="rgb(239, 87, 113)"/></svg>
          </button>
        </form>
      </div>
        )}
    </div>
    
  );
}

export default App;