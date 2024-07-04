import { useState, useRef, useEffect, useCallback } from "react";

const useSpeechToText = ({ options, isRecording }: { options: any; isRecording: boolean }) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState<string>("");
  const recognitionRef = useRef<any | null>(null);

  const initializeRecognition = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error("Web speech API is not supported");
      return;
    }

    const recognition = new SpeechRecognition();
    recognition.interimResults = options.interimResults ?? true;
    recognition.lang = options.lang ?? "en-US";
    recognition.continuous = options.continuous ?? false;

    if ("webkitSpeechGrammarList" in window) {
      const grammar = "#JSGF V1.0; grammar punctuation; public <punc> = . | , | ? | ! | ; | : ;";
      const speechRecognitionList = new (window as any).webkitSpeechGrammarList();
      speechRecognitionList.addFromString(grammar, 1);
      recognition.grammars = speechRecognitionList;
    }

    recognition.onresult = (event: any) => {
      const currentTranscript = Array.from(event.results)
        .map((result: any) => result[0].transcript)
        .join("");
      setTranscript(currentTranscript);
    };

    recognition.onerror = (event: any) => {
      console.error("Speech recognition error:", event.error);
    };

    recognition.onend = () => {
      setIsListening(false);
      if (options.resetTranscriptOnStop) {
        setTranscript("");
      }
    };

    recognitionRef.current = recognition;
  }, [options.continuous, options.interimResults, options.lang, options.resetTranscriptOnStop]);

  useEffect(() => {
    initializeRecognition();
    return () => {
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [initializeRecognition]);

  useEffect(() => {
    if (isRecording) {
      startListening();
    } else {
      stopListening();
    }
  }, [isRecording]);

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

  return { isListening, transcript, startListening, stopListening };
};

export default useSpeechToText;