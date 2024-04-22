import React, { useEffect, useState } from "react";
import useSpeechToText from "../hooks/AudioToTextHook";

interface AudioToTextProps {
  isRecording: boolean;
  deletePressed: boolean;
}

function AudioToTextComponent({ isRecording, deletePressed }: AudioToTextProps) {
  const [textInput, setTextInput] = useState("");

  const [, transcript, , stopListening] = useSpeechToText({
    options: { continuous: true },
    isRecording: isRecording,
  });

  const handleStopVoiceInput = () => {
    stopListening();
  };

  // Update textInput whenever there's a new transcript
  React.useEffect(() => {
    if (transcript) {
      setTextInput(transcript);
    }
  }, [transcript]);

  useEffect(() => {
    if(deletePressed) {
      setTextInput(" ");
    }
  }, [deletePressed])

  return (
    <div>
      <textarea
        name="generatedText"
        id="generatedText"
        cols={30}
        rows={10}
        placeholder="Press the record icon to have some text generated"
        disabled={true}
        value={textInput}
        onChange={() => {}}
      ></textarea>
    </div>
  );
}

export default AudioToTextComponent;
