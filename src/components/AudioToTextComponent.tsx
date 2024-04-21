import { useState } from "react";
import useSpeechToText from "../hooks/AudioToTextHook";

function AudioToTextComponent(props: { isRecording: any }) {
  const [textInput, setTextInput] = useState("");
  const [isListening, transcript, startListening, stopListening] =
  useSpeechToText({ options: { continuous: true }, isRecording: props.isRecording });

  const startStopListening = () => {
    isListening ? stopVoiceInput() : startListening();
  };

  const stopVoiceInput = () => {
    setTextInput((prevVal: any) => prevVal + (transcript.length ? (prevVal.length ? " " : "") + transcript : ''))
    stopListening()
  }
  return (
    <div>
      <textarea
        name="generatedText"
        id="generatedText"
        cols={30}
        rows={10}
        placeholder="Press the record icon to have some text generated"
        disabled={isListening}
        value={isListening ? textInput + (transcript.length ? (textInput.length ? ' ' : '') + transcript : '') : textInput}
      ></textarea>
    </div>
  );
}

export default AudioToTextComponent;
