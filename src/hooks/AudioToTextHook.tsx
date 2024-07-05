import { useState, useRef, useEffect, useCallback } from "react";

const useSpeechToText = (props: { options: any; isRecording: boolean }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState<any>("");
  const recognitionRef: any = useRef(null);

  // Destructure options for clarity and to easily add them to the dependency array
  const { continuous, interimResults, lang } = props.options;

  useEffect(() => {
    if (!("webkitSpeechRecognition" in window)) {
      console.error("Web speech API is not supported");
      return;
    }
    recognitionRef.current = new (window as any).webkitSpeechRecognition();
    const recognition: any = recognitionRef.current;
    recognition.interimResults = interimResults || true;
    recognition.lang = lang || "en-US";
    recognition.continuous = continuous || false;

    if ("webkitSpeechGrammarList" in window) {
      const grammar =
        "#JSGF V1.0; grammar punctuation; public <punc> = . | , | ? | ! | ; | : ;";
      const speechRecognitionList = new (window as any).webkitSpeechGrammarList();
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
  }, [props.isRecording, continuous, interimResults, lang]);

  const startListening = useCallback(() => {
    if (recognitionRef.current && !isListening) {
      recognitionRef.current.start();
      setIsListening(true);
    }
  }, [isListening]); 

  const stopListening = useCallback(() => {
    if (recognitionRef.current && isListening) {
      recognitionRef.current.stop();
      setIsListening(false);
    }
  }, [isListening]); 

  useEffect(() => {
    // Start or stop listening based on the props.isRecording prop
    if (props.isRecording) {
      startListening();
    } else {
      stopListening();
    }
  }, [props.isRecording, startListening, stopListening]); // Updated dependency array

  return [isListening, transcript, startListening, stopListening];
};

export default useSpeechToText;