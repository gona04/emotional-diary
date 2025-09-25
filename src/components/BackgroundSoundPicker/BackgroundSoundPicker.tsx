import React, { useEffect, useRef, useState } from 'react';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { setBackgroundSound, setBackgroundSoundPlaying } from '../../store/uiSlice';
import './BackgroundSoundPicker.css';

type Sample = { id: string; label: string };

const SAMPLES: Sample[] = [
  { id: 'healing-pad', label: 'Healing Pad' },
];

const BackgroundSoundPicker: React.FC = () => {
  const dispatch = useAppDispatch();
  const selected = useAppSelector((s: any) => s.ui.backgroundSound) as string | null;

  const audioCtxRef = useRef<AudioContext | null>(null);
  const padNodesRef = useRef<OscillatorNode[] | null>(null);
  const padGainRef = useRef<GainNode | null>(null);
  const [previewId, setPreviewId] = useState<string | null>(null);

  useEffect(() => {
    return () => {
      stopAll();
    };
  }, []);

  function ensureCtx() {
    if (!audioCtxRef.current) {
      const Ctx = (window.AudioContext || (window as any).webkitAudioContext) as typeof AudioContext;
      audioCtxRef.current = new Ctx();
    }
    return audioCtxRef.current!;
  }

  function stopAll() {
    try {
      padNodesRef.current?.forEach((n) => { try { n.stop(); n.disconnect(); } catch (e) {} });
    } catch (e) {}
    padNodesRef.current = null;
    if (padGainRef.current) {
      try { padGainRef.current.disconnect(); } catch (e) {}
      padGainRef.current = null;
    }
    setPreviewId(null);
  }

  function startPad() {
    const ctx = ensureCtx();
    stopAll();
    const gain = ctx.createGain(); gain.gain.value = 0.00005; padGainRef.current = gain;
    const o1 = ctx.createOscillator(); o1.type = 'triangle'; o1.frequency.value = 110;
    const o2 = ctx.createOscillator(); o2.type = 'triangle'; o2.frequency.value = 165;
    const lfo = ctx.createOscillator(); lfo.type = 'sine'; lfo.frequency.value = 0.035;
    const lfoGain = ctx.createGain(); lfoGain.gain.value = 0.01;
    lfo.connect(lfoGain); lfoGain.connect(gain.gain);
    o1.connect(gain); o2.connect(gain); gain.connect(ctx.destination);
    o1.start(); o2.start(); lfo.start();
    gain.gain.exponentialRampToValueAtTime(0.03, ctx.currentTime + 4);
    padNodesRef.current = [o1, o2, lfo];
    setPreviewId('healing-pad');
  }

  // healing-bell removed; persistent healing loop replaced by healing-pad only

  function handlePreview(id: string) {
    if (previewId === id) { stopAll(); return; }
    if (id === 'healing-pad') startPad();
  }

  function handleUse(id: string) {
    // mark selected in redux and ensure audio plays
    dispatch(setBackgroundSound(`generated:${id}`));
    dispatch(setBackgroundSoundPlaying(true));
    // start persistent pad for selection if pad chosen
    if (id === 'healing-pad') startPad();
  }

  function handleStop() {
    dispatch(setBackgroundSoundPlaying(false));
    dispatch(setBackgroundSound(null));
    stopAll();
  }

  return (
    <div className="bg-sound-picker small">
      <div className="bg-sound-list">
        {SAMPLES.map((s) => (
          <div key={s.id} className={`bg-sound-item ${selected === `generated:${s.id}` ? 'selected' : ''}`}>
            <div className="label">{s.label}</div>
            <div className="controls">
              <button onClick={() => handlePreview(s.id)}>{previewId === s.id ? 'Stop' : 'Preview'}</button>
              <button onClick={() => handleUse(s.id)}>{selected === `generated:${s.id}` ? 'Selected' : 'Use'}</button>
            </div>
          </div>
        ))}
      </div>
      <div className="bg-sound-footer">
        <button onClick={handleStop}>Stop background</button>
      </div>
    </div>
  );
};

export default BackgroundSoundPicker;
