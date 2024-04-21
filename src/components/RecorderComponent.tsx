import React, { useState, useEffect } from "react";
import { AudioRecorder, useAudioRecorder } from "react-audio-voice-recorder";
import { uploadAudio } from "../services/audioservices";
import AudioToTextComponent from "./AudioToTextComponent";

function RecorderComponent() {
  const [audioData, setAudioData] = useState(null);
  const [displayRecorder, setDisplayrecorder] = useState(false);

  const recorderControls = useAudioRecorder();
  useEffect(() => {
    if (recorderControls.isRecording) {
      setDisplayrecorder(true);
    }
    if (recorderControls.recordingBlob !== undefined) {
      setDisplayrecorder(false);
    }
  }, [recorderControls.isRecording, recorderControls.recordingBlob]);

  const addAudioElement = (blob: any) => {
    setAudioData(blob);
  };

  const sendAudio = () => {
    uploadAudio(audioData);
  };

  const deleteAudio = () => {
    setAudioData(null);
  };

  return (
    <div className="microphone-new-place">
      {displayRecorder && (
        <AudioRecorder
          onRecordingComplete={addAudioElement}
          recorderControls={recorderControls}
          audioTrackConstraints={{
            noiseSuppression: true,
            echoCancellation: true,
          }}
          showVisualizer={true}
          onNotAllowedOrFound={(err) => console.table(err)}
          downloadFileExtension="mp3"
          mediaRecorderOptions={{
            audioBitsPerSecond: 128000,
          }}
        />
      )}
      {!displayRecorder && (
        <svg
          onClick={recorderControls.startRecording}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 384 512"
          height="1.5rem"
        >
          <path
            d="M192 0C139 0 96 43 96 96V256c0 53 43 96 96 96s96-43 96-96V96c0-53-43-96-96-96zM64 216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 89.1 66.2 162.7 152 174.4V464H120c-13.3 0-24 10.7-24 24s10.7 24 24 24h72 72c13.3 0 24-10.7 24-24s-10.7-24-24-24H216V430.4c85.8-11.7 152-85.3 152-174.4V216c0-13.3-10.7-24-24-24s-24 10.7-24 24v40c0 70.7-57.3 128-128 128s-128-57.3-128-128V216z"
            fill="rgb(239, 87, 113)"
          />
        </svg>
      )}
      {displayRecorder && (
        <svg
          onClick={recorderControls.stopRecording}
          xmlns="http://www.w3.org/2000/svg"
          viewBox="0 0 384 512"
          height="1.5rem"
        >
          <path d="M0 128C0 92.7 28.7 64 64 64H320c35.3 0 64 28.7 64 64V384c0 35.3-28.7 64-64 64H64c-35.3 0-64-28.7-64-64V128z" />
        </svg>
      )}
      <AudioToTextComponent isRecording={recorderControls.isRecording} />
      {audioData && (
        <div className="setting-text-area">
          <div>
            <button
              onClick={deleteAudio}
              className="remove-btn-style"
              title="Delete audio"
            >
              Delete
            </button>
          </div>
          <audio
            className="audio-player"
            src={URL.createObjectURL(audioData)}
            controls
          />
        </div>
      )}
      <svg
        onClick={sendAudio}
        xmlns="http://www.w3.org/2000/svg"
        viewBox="0 0 512 512"
        height="1.5rem"
      >
        <path
          d="M498.1 5.6c10.1 7 15.4 19.1 13.5 31.2l-64 416c-1.5 9.7-7.4 18.2-16 23s-18.9 5.4-28 1.6L284 427.7l-68.5 74.1c-8.9 9.7-22.9 12.9-35.2 8.1S160 493.2 160 480V396.4c0-4 1.5-7.8 4.2-10.7L331.8 202.8c5.8-6.3 5.6-16-.4-22s-15.7-6.4-22-.7L106 360.8 17.7 316.6C7.1 311.3 .3 300.7 0 288.9s5.9-22.8 16.1-28.7l448-256c10.7-6.1 23.9-5.5 34 1.4z"
          fill="rgb(239, 87, 113)"
        />
      </svg>
    </div>
  );
}

export default RecorderComponent;
