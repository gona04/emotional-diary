import { useState, useRef, useEffect } from "react";

const useSpeechToText = (props:{options: any, isRecording: boolean}) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState<any>("");
  const recognitionRef: any = useRef(null);

  useEffect(() => {
    if (!(`webkitSpeechRecognition` in window)) {
      console.error("Web speech API is not supported");
      return;
    }
    recognitionRef.current = new (window as any).webkitSpeechRecognition();
    const recognition: any = recognitionRef.current;
    recognition.interimResults = props.options.interimResults || true;
    recognition.lang = props.options.lang || "en-US";
    recognition.continuous = props.options.continuous || false;

    if ("webkitSpeechGrammarList" in window) {
      const grammar =
        "#JSGF V1.0; grammar punctuation; public <punc> = . | , | ? | ! | ; | : ;";
      const speechRecognitionList = new (
        window as any
      ).webkitSpeechGrammarList();
      speechRecognitionList.addFromString(grammar, 1);
      recognition.grammars = speechRecognitionList;
    }

    recognition.onresult = (event: any) => {
      let text = "";
      for (let i = 0; i < event.results.length; i++) {
        text += event.results[i][0].transcript;
      }
      setTranscript(text);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
    };

    recognition.onend = () => {
      setTranscript("");
      setIsListening(false);
    };

    return () => {
      recognition.stop();
    };
  }, [props.isRecording]); // Add props.isRecording to the dependency array

  useEffect(() => {
    // Start or stop listening based on the props.isRecording prop
    if (props.isRecording) {
      startListening();
    } else {
      stopListening();
    }
  }, [props.isRecording]); // Add props.isRecording to the dependency array

  const startListening = () => {
    if (recognitionRef.current && !isListening) {
      recognitionRef.current.start();
      setIsListening(true);
    }
  };

  const stopListening = () => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  };

  return [isListening, transcript, startListening, stopListening];
};

export default useSpeechToText;
