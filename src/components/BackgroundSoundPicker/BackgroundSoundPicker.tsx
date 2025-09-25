import React, { useCallback, useEffect, useRef, useState } from 'react';
import './BackgroundSoundPicker.css';
import CustomSelect from './CustomSelect';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { setShowInput, setShowMicrophone, setShowAnimation } from '../../store/uiSlice';
import { setPromptMode, setShowPromptInfo, setPromptInfoText } from '../../store/promptSlice';
import { setPreviewId, setTopPreviewId, setPadPlaying, setPadStartTime, setPadBpm } from '../../store/audioSlice';

// (type removed - explicit nav items rendered inline)

const BackgroundSoundPicker: React.FC = () => {
  // no redux dispatch needed here; selection is handled locally via toggles

  const audioCtxRef = useRef<AudioContext | null>(null);
  const padNodesRef = useRef<OscillatorNode[] | null>(null);
  const padGainRef = useRef<GainNode | null>(null);
  const padStartTimeRef = useRef<number | null>(null);
  const padBpmRef = useRef<number | null>(60);
  const [clickedId, setClickedId] = useState<string | null>(null);
  const promptMode = useAppSelector((s) => s.prompt.promptMode);
  const showPromptInfo = useAppSelector((s) => s.prompt.showPromptInfo);
  const promptInfoText = useAppSelector((s) => s.prompt.promptInfoText);
  const promptCloseRef = useRef<HTMLButtonElement | null>(null);
  useEffect(() => {
    if (showPromptInfo) {
      // small timeout to ensure the element is rendered before focusing
      setTimeout(() => {
        try { promptCloseRef.current?.focus(); } catch (e) {}
      }, 10);
    }
  }, [showPromptInfo]);
  const dispatch = useAppDispatch();
  const showMicrophone = useAppSelector(s => s.ui.showMicrophone);
  const showInput = useAppSelector(s => s.ui.showInput);
  const showAnimation = useAppSelector(s => s.ui.showAnimation);
  const previewId = useAppSelector((s) => s.audio.previewId);
  const topPreviewId = useAppSelector((s) => s.audio.topPreviewId);
  // padPlaying flag currently unused in render; keep in store for future use
  useAppSelector((s) => s.audio.padPlaying);

  const onActivate = useCallback((id: string, fn: () => void) => {
    setClickedId(id);
    window.setTimeout(() => setClickedId(null), 220);
    fn();
  }, []);

  const toggleMicrophone = useCallback(() => {
    dispatch(setShowMicrophone(!showMicrophone));
  }, [dispatch, showMicrophone]);

  const toggleChat = useCallback(() => {
    dispatch(setShowInput(!showInput));
  }, [dispatch, showInput]);

  const toggleAnimation = useCallback(() => {
    dispatch(setShowAnimation(!showAnimation));
  }, [dispatch, showAnimation]);

  

  function ensureCtx() {
    if (!audioCtxRef.current) {
      const Ctx = (window.AudioContext || (window as any).webkitAudioContext) as typeof AudioContext;
      audioCtxRef.current = new Ctx();
    }
    return audioCtxRef.current!;
  }

  const stopAll = useCallback(() => {
    try {
      padNodesRef.current?.forEach((n) => { try { n.stop(); n.disconnect(); } catch (e) {} });
    } catch (e) {}
    padNodesRef.current = null;
    if (padGainRef.current) {
      try { padGainRef.current.disconnect(); } catch (e) {}
      padGainRef.current = null;
    }
    if (metronomeIntervalRef.current) {
      clearInterval(metronomeIntervalRef.current);
      metronomeIntervalRef.current = null;
    }
    padStartTimeRef.current = null;
    padBpmRef.current = null;
    dispatch(setPreviewId(null));
    dispatch(setTopPreviewId(null));
    dispatch(setPadPlaying(false));
    dispatch(setPadStartTime(null));
    dispatch(setPadBpm(null));
  }, [dispatch]);

  // --- Top-bar generators: snaps/metronome and counting ---
  const metronomeIntervalRef = useRef<number | null>(null);
  const snapBufferRef = useRef<AudioBuffer | null>(null);
  // upload disabled — default snap from public/samples is used
  const loadedDefaultRef = useRef<boolean>(false);

  async function ensureSnapBuffer(ctx: AudioContext) {
    if (snapBufferRef.current) return snapBufferRef.current;
    // create a short click/snapping noise buffer
    const sr = ctx.sampleRate;
    const len = Math.floor(0.06 * sr);
    const buf = ctx.createBuffer(1, len, sr);
    const data = buf.getChannelData(0);
    for (let i = 0; i < len; i++) {
      // white noise with fast envelope
      data[i] = (Math.random() * 2 - 1) * Math.exp(-10 * i / sr) * 0.8;
    }
    snapBufferRef.current = buf;
    return buf;
  }

  // file upload removed; user-supplied uploads are disabled

  // load two default samples from public/samples if present
  useEffect(() => {
    if (loadedDefaultRef.current) return;
  loadedDefaultRef.current = true;
  const filename = 'wet-snap-quiet_A#_minor.wav';
  const encoded = `/samples/${encodeURIComponent(filename)}`;
  const raw = `/samples/${filename}`;
  const pct = `/samples/${filename.replace('#', '%23')}`;
  // metronome URLs removed
  const ctx = ensureCtx();

  // load snap and metronome in parallel so one doesn't block the other
  (async () => {
    // Snap loader
    try {
      // eslint-disable-next-line @typescript-eslint/ban-ts-comment
      // @ts-ignore
      const mod = await import('../assests/sample/wet-snap-quiet_A#_minor.wav');
      let url: string | null = null;
      if (mod) url = typeof mod === 'string' ? mod : (mod as any).default || null;
      if (url) {
        try {
          const res = await fetch(url);
          if (!res.ok) { console.warn('[BackgroundSoundPicker] bundled snap fetch not ok', url, res.status); }
          const ab = await res.arrayBuffer();
          try { await ctx.resume(); } catch (e) {}
          try { const buf = await ctx.decodeAudioData(ab.slice(0)); snapBufferRef.current = buf; console.log('[BackgroundSoundPicker] loaded snap from bundled asset'); } catch (err) { console.warn('[BackgroundSoundPicker] decodeAudioData failed for bundled snap', err); }
        } catch (err) { console.warn('[BackgroundSoundPicker] fetch failed for bundled snap', err); }
      }
    } catch (err) { console.warn('[BackgroundSoundPicker] dynamic import failed for snap', err); }
    for (const u of [encoded, pct, raw]) {
      if (snapBufferRef.current) break;
        try {
          console.log('[BackgroundSoundPicker] trying snap url', u);
          const res = await fetch(u);
          if (!res.ok) { console.warn('snap fetch not ok', u, res.status); continue; }
          const ab = await res.arrayBuffer();
          try { await ctx.resume(); } catch (e) {}
          try { const buf = await ctx.decodeAudioData(ab.slice(0)); snapBufferRef.current = buf; console.log('[BackgroundSoundPicker] loaded snap from url', u); break; } catch (err) { console.warn('decodeAudioData failed for', u, err); continue; }
      } catch (err) { console.warn('fetch failed for', u, err); continue; }
    }
  // ensure snap exists at least generated
  try { await ensureSnapBuffer(ctx); } catch (e) {}
  })();

  // metronome removed
  }, []);

  // generic buffer play helper removed (not used after metronome removal)

  // metronome functions removed

  function playSnap(ctx: AudioContext, when: number) {
    const src = ctx.createBufferSource();
    src.buffer = snapBufferRef.current!;
    const g = ctx.createGain();
    // create a short percussive envelope
    g.gain.setValueAtTime(0.0001, when);
    g.gain.exponentialRampToValueAtTime(0.6, when + 0.005);
    g.gain.exponentialRampToValueAtTime(0.0001, when + 0.18);
    src.connect(g); g.connect(ctx.destination);
    try { src.start(when); } catch (e) { src.start(); }
    // cleanup after playback
    src.onended = () => {
      try { src.disconnect(); g.disconnect(); } catch (e) {}
    };
  }

  async function startMetronomeAndSnap(bpm = 60) {
    // metronome removed; keep single snap preview only
    const ctx = ensureCtx();
    try { await ctx.resume(); } catch (e) {}
    await ensureSnapBuffer(ctx);
    if (!snapBufferRef.current) {
      console.warn('[BackgroundSoundPicker] no snap buffer available, aborting preview');
      return;
    }
    // one-shot snap at next immediate moment
    const t = ctx.currentTime + 0.02;
    try { playSnap(ctx, t); } catch (e) { console.warn('[BackgroundSoundPicker] playSnap failed', e); }
    dispatch(setTopPreviewId('snap'));
    // auto clear preview state shortly after
    setTimeout(() => stopTopBar(), 300);
  }

  // Start a repeating snap loop aligned to the pad BPM/start time.
  async function startSnapLoop(bpm = 60) {
    const ctx = ensureCtx();
    try { await ctx.resume(); } catch (e) {}
    await ensureSnapBuffer(ctx);
    if (!snapBufferRef.current) {
      console.warn('[BackgroundSoundPicker] no snap buffer available, aborting loop');
      return;
    }
    // clear any existing loop
    if (metronomeIntervalRef.current) {
      clearInterval(metronomeIntervalRef.current);
      metronomeIntervalRef.current = null;
    }
    // compute interval and alignment
    const useBpm = padStartTimeRef.current ? (padBpmRef.current || bpm) : bpm;
    const interval = 60 / useBpm;
    let first: number;
    if (padStartTimeRef.current) {
      const padStart = padStartTimeRef.current;
      const elapsed = (ctx.currentTime - padStart) % interval;
      const untilNext = (elapsed <= 0.0001) ? 0 : (interval - elapsed);
      first = ctx.currentTime + Math.max(0.02, untilNext + 0.01);
    } else {
      first = ctx.currentTime + 0.02;
    }
    // schedule first snap
    playSnap(ctx, first);
    // schedule repeating snaps
    metronomeIntervalRef.current = window.setInterval(() => {
      const t = ctx.currentTime + 0.02;
      playSnap(ctx, t);
    }, interval * 1000);
    dispatch(setTopPreviewId('snap'));
  }

  const stopTopBar = useCallback(() => {
    if (metronomeIntervalRef.current) {
      clearInterval(metronomeIntervalRef.current);
      metronomeIntervalRef.current = null;
    }
    dispatch(setTopPreviewId(null));
  }, [dispatch]);

  useEffect(() => {
    return () => {
      stopAll();
    };
  }, [stopAll]);


  // stop audio and reset previews when switching to Casual talk
  useEffect(() => {
    if (promptMode === 'Casual talk') {
      // stop any playing pad/snap
      stopAll();
      stopTopBar();
    }
  }, [promptMode, stopAll, stopTopBar]);

  // counting removed

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
    // record pad start time to allow alignment
    padStartTimeRef.current = ctx.currentTime;
    // default bpm for pad; could be exposed in UI later
    padBpmRef.current = 60;
    dispatch(setPreviewId('healing-pad'));
    dispatch(setPadPlaying(true));
    dispatch(setPadStartTime(ctx.currentTime));
    dispatch(setPadBpm(60));
  }

  // healing-bell removed; persistent healing loop replaced by healing-pad only

  function handlePreview(id: string) {
    if (previewId === id) { stopAll(); return; }
    if (id === 'healing-pad') startPad();
  }

  function handleTopPreview(id: string) {
    if (topPreviewId === id) { stopTopBar(); return; }
    if (id === 'snap') {
      // if pad is playing, start a repeating snap loop aligned to the pad
      if (padStartTimeRef.current) startSnapLoop(60);
      else startMetronomeAndSnap(60);
    }
    // metronome removed; snap remains
  }

  // selection is handled via direct toggle clicks on the nav items

  // stop control removed; individual controls manage playback

  return (
    <div className="bg-sound-picker small">
      <nav className="bg-sound-topbar nav-bar" role="navigation" aria-label="Background sounds">
          <div className="nav-inner">
            <div className="nav-left">
              <div role="menu" aria-label="background-sounds" className="nav-sounds">
                {promptMode !== 'Casual talk' && (
                  <>
                    <div
                      className={`nav-item ${previewId === 'healing-pad' ? 'playing' : ''} ${clickedId === 'healing-pad' ? 'clicked' : ''}`}
                      onClick={() => onActivate('healing-pad', () => handlePreview('healing-pad'))}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { onActivate('healing-pad', () => handlePreview('healing-pad')); } }}
                      tabIndex={0}
                      role="menuitem"
                    >
                      Healing Pad
                    </div>
                    <div
                      className={`nav-item ${topPreviewId === 'snap' ? 'playing' : ''} ${clickedId === 'snap' ? 'clicked' : ''}`}
                      onClick={() => onActivate('snap', () => handleTopPreview('snap'))}
                      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { onActivate('snap', () => handleTopPreview('snap')); } }}
                      tabIndex={0}
                      role="menuitem"
                    >
                      Snap
                    </div>
                  </>
                )}
              </div>
            </div>

              <div className="nav-center" aria-hidden={false}>
              <label className="sr-only" htmlFor="nav-prompt">Start prompt</label>
              <CustomSelect
                id="nav-prompt"
                className="nav-prompt-custom"
                options={["Casual Talk", "Quick Tools", "Let's Talk", "Walk With Me"]}
                value={promptMode}
                onChange={(v) => {
                  // update prompt mode and show an explanatory popup (user-friendly, no therapy names)
                  dispatch(setPromptMode(v));
                  // set the description based on the chosen label
                  let txt = '';
                  switch (v) {
                    case 'Casual Talk':
                      txt = 'A low-pressure, friendly conversation  great when you just want to talk about your day, how youre feeling, or get something off your chest.';
                      break;
                    case 'Quick Solutions':
                      txt = 'Short, practical strategies you can try right now if things feel overwhelming. Use this when you need immediate, simple steps to steady yourself.';
                      break;
                    case "Let's Talk":
                      txt = 'A deeper, guided conversation to help you explore patterns that keep showing up  especially if you find yourself repeating the same chaotic moments. Good when you want structured support to make sense of things and try a different approach.';
                      break;
                    case 'Walk With Me':
                      txt = `A calming, guided session with soothing cues and gentle steps to help shift perspective. Best when youre feeling somewhat steady  if you are in the middle of a chaos try 'Quick Solutions'.`;
                      break;
                    default:
                      txt = '';
                  }
                  dispatch(setPromptInfoText(txt));
                  dispatch(setShowPromptInfo(true));
                }}
              />
            </div>

            <div className="nav-actions" role="toolbar" aria-label="actions">
              <div
                className={`nav-action ${showMicrophone ? 'active' : ''} ${clickedId === 'speak' ? 'clicked' : ''}`}
                onClick={() => onActivate('speak', toggleMicrophone)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { onActivate('speak', toggleMicrophone); } }}
                tabIndex={0}
                role="button"
                aria-pressed={showMicrophone}
              >
                Speak
              </div>

              <div
                className={`nav-action ${showInput ? 'active' : ''} ${clickedId === 'chat' ? 'clicked' : ''}`}
                onClick={() => onActivate('chat', toggleChat)}
                onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { onActivate('chat', toggleChat); } }}
                tabIndex={0}
                role="button"
                aria-pressed={showInput}
              >
                Chat
              </div>

              {promptMode !== 'Casual talk' && (
                <div
                  className={`nav-action ${showAnimation ? 'active' : ''} ${clickedId === 'animation' ? 'clicked' : ''}`}
                  onClick={() => onActivate('animation', toggleAnimation)}
                  onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { onActivate('animation', toggleAnimation); } }}
                  tabIndex={0}
                  role="button"
                  aria-pressed={showAnimation}
                >
                  Animation
                </div>
              )}
            </div>
          </div>
        </nav>

          {/* Prompt info modal */}
          {showPromptInfo && (
            <div
              className="prompt-modal-overlay"
              role="dialog"
              aria-modal="true"
              aria-labelledby="prompt-modal-title"
              onClick={() => dispatch(setShowPromptInfo(false))}
                onKeyDown={(e) => { if (e.key === 'Escape') dispatch(setShowPromptInfo(false)); }}
              tabIndex={-1}
            >
              <div className="prompt-modal" onClick={(e) => e.stopPropagation()}>
                <h3 id="prompt-modal-title">{promptMode}</h3>
                <p className="prompt-modal-desc">{promptInfoText}</p>
                <button
                  ref={promptCloseRef}
                  type="button"
                  className="prompt-modal-close"
                  aria-label={`Close ${promptMode} info`}
                  onClick={() => dispatch(setShowPromptInfo(false))}
                >
                  ×
                </button>
              </div>
            </div>
          )}

      {/* footer removed - stop control moved to individual controls */}
    </div>
  );
};

export default BackgroundSoundPicker;
