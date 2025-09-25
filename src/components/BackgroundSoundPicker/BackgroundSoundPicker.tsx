import React, { useCallback, useEffect, useRef, useState } from 'react';
import './BackgroundSoundPicker.css';
import { useAppDispatch, useAppSelector } from '../../store/hooks';
import { setShowInput, setShowMicrophone, setShowAnimation } from '../../store/uiSlice';

// (type removed - explicit nav items rendered inline)

const BackgroundSoundPicker: React.FC = () => {
  // no redux dispatch needed here; selection is handled locally via toggles

  const audioCtxRef = useRef<AudioContext | null>(null);
  const padNodesRef = useRef<OscillatorNode[] | null>(null);
  const padGainRef = useRef<GainNode | null>(null);
  const padStartTimeRef = useRef<number | null>(null);
  const padBpmRef = useRef<number | null>(60);
  const [previewId, setPreviewId] = useState<string | null>(null);
  const [topPreviewId, setTopPreviewId] = useState<string | null>(null);
  const [clickedId, setClickedId] = useState<string | null>(null);
  const dispatch = useAppDispatch();
  const showMicrophone = useAppSelector(s => s.ui.showMicrophone);
  const showInput = useAppSelector(s => s.ui.showInput);
  const showAnimation = useAppSelector(s => s.ui.showAnimation);

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
    if (metronomeIntervalRef.current) {
      clearInterval(metronomeIntervalRef.current);
      metronomeIntervalRef.current = null;
    }
    padStartTimeRef.current = null;
    padBpmRef.current = null;
    setPreviewId(null);
    setTopPreviewId(null);
  }

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
    setTopPreviewId('snap');
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
    setTopPreviewId('snap');
  }

  function stopTopBar() {
    if (metronomeIntervalRef.current) {
      clearInterval(metronomeIntervalRef.current);
      metronomeIntervalRef.current = null;
    }
    setTopPreviewId(null);
  }

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
    setPreviewId('healing-pad');
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
              </div>
            </div>

            <div className="nav-center" aria-hidden={false}>
              <label className="sr-only" htmlFor="nav-prompt">Start prompt</label>
              <select id="nav-prompt" className="nav-prompt-select" aria-label="Quick prompt">
                <option>Tell me what bothers you</option>
              </select>
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
            </div>
          </div>
        </nav>

      {/* footer removed - stop control moved to individual controls */}
    </div>
  );
};

export default BackgroundSoundPicker;
