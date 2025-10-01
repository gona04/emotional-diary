// This hook used to manage webkitSpeechRecognition behavior. The app
// now manages SpeechRecognition directly in the recorder component. We
// keep a minimal stub here so any remaining imports won't break.
import { useCallback } from "react";

const useSpeechToText = (_props: { options: any; isRecording: boolean }) => {
  const noop = useCallback(() => {}, []);
  return [false, "", noop, noop] as const;
};

export default useSpeechToText;