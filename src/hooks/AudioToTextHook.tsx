import { useState, useRef, useEffect, useCallback } from "react";

interface Options {
  interimResults?: boolean;
  lang?: string;
  continuous?: boolean;
  resetTranscriptOnStop?: boolean;
}

interface UseSpeechToTextProps {
  options: Options;
  isRecording: boolean;
}

interface SpeechRecognition extends EventTarget {
  start: () => void;
  stop: () => void;
  onresult: ((this: SpeechRecognition, ev: Event) => any) | null;
  onerror: ((this: SpeechRecognition, ev: Event) => any) | null;
  onend: ((this: SpeechRecognition, ev: Event) => any) | null;
  interimResults: boolean;
  lang: string;
  continuous: boolean;
  grammars: SpeechGrammarList;
}

interface SpeechRecognitionEvent extends Event {
  results: SpeechRecognitionResultList;
}

interface SpeechRecognitionResultList {
  [index: number]: SpeechRecognitionResult;
  length: number;
}

interface SpeechRecognitionResult {
  [index: number]: SpeechRecognitionAlternative;
  isFinal: boolean;
}

interface SpeechRecognitionAlternative {
  transcript: string;
  confidence: number;
}

interface SpeechGrammarList {
  addFromString: (string: string, weight: number) => void;
}

const useSpeechToText = ({ options, isRecording }: UseSpeechToTextProps) => {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState("");
  const recognitionRef = useRef<SpeechRecognition | null>(null);

  const initializeRecognition = useCallback(() => {
    const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
    if (!SpeechRecognition) {
      console.error("Web Speech API is not supported");
      return;
    }

    const recognition: SpeechRecognition = new SpeechRecognition();
    recognition.interimResults = options.interimResults ?? true;
    recognition.lang = options.lang ?? "en-US";
    recognition.continuous = options.continuous ?? false;

    if ("webkitSpeechGrammarList" in window) {
      const grammar = "#JSGF V1.0; grammar punctuation; public <punc> = . | , | ? | ! | ; | : ;";
      const speechRecognitionList = new (window as any).webkitSpeechGrammarList();
      speechRecognitionList.addFromString(grammar, 1);
      recognition.grammars = speechRecognitionList;
    }

    recognition.onresult = (event: Event) => {
      const speechEvent = event as SpeechRecognitionEvent;
      const currentTranscript = Array.from(speechEvent.results)
        .map((result) => result[0].transcript)
        .join("");
      setTranscript(currentTranscript);
    };

    recognition.onerror = (event: Event) => {
      console.error("Speech recognition error:", event);
    };

    recognition.onend = () => {
      setIsListening(false);
      if (options.resetTranscriptOnStop) {
        setTranscript("");
      }
    };

    recognitionRef.current = recognition;
  }, [options.interimResults, options.lang, options.continuous, options.resetTranscriptOnStop]);

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
