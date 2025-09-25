import React, { useEffect, useRef, useState } from 'react';

type Props = {
  options: string[];
  value: string;
  onChange: (v: string) => void;
  id?: string;
  className?: string;
};

const CustomSelect: React.FC<Props> = ({ options, value, onChange, id, className }) => {
  const [open, setOpen] = useState(false);
  const [highlight, setHighlight] = useState<number>(Math.max(0, options.indexOf(value)));
  const rootRef = useRef<HTMLDivElement | null>(null);

  useEffect(() => {
    const onDoc = (e: MouseEvent) => {
      if (!rootRef.current) return;
      if (!rootRef.current.contains(e.target as Node)) setOpen(false);
    };
    document.addEventListener('mousedown', onDoc);
    return () => document.removeEventListener('mousedown', onDoc);
  }, []);

  useEffect(() => {
    setHighlight(Math.max(0, options.indexOf(value)));
  }, [value, options]);

  function toggle() {
    setOpen((s) => !s);
  }

  function onKeyDown(e: React.KeyboardEvent) {
    if (e.key === 'Enter') { e.preventDefault(); if (open) { onChange(options[highlight]); setOpen(false); } else setOpen(true); }
    else if (e.key === 'Escape') { setOpen(false); }
    else if (e.key === 'ArrowDown') { e.preventDefault(); setOpen(true); setHighlight((h) => Math.min(h + 1, options.length - 1)); }
    else if (e.key === 'ArrowUp') { e.preventDefault(); setOpen(true); setHighlight((h) => Math.max(h - 1, 0)); }
  }

  return (
    <div ref={rootRef} id={id} className={`custom-select ${className || ''}`} tabIndex={0} onKeyDown={onKeyDown} aria-haspopup="listbox" aria-expanded={open}>
      <button type="button" className="custom-select-toggle" onClick={toggle} aria-label="Open prompt menu">
        <span className="custom-select-value">{value}</span>
        <svg width="12" height="8" viewBox="0 0 10 6" aria-hidden focusable="false"><path d="M1 1l4 4 4-4" stroke="#fff" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round" fill="none"/></svg>
      </button>

      {open && (
        <ul role="listbox" className="custom-select-menu" tabIndex={-1}>
          {options.map((opt, i) => (
            <li
              key={opt}
              role="option"
              aria-selected={value === opt}
              className={`custom-select-item ${i === highlight ? 'highlight' : ''} ${value === opt ? 'selected' : ''}`}
              onMouseEnter={() => setHighlight(i)}
              onClick={() => { onChange(opt); setOpen(false); }}
            >
              {opt}
            </li>
          ))}
        </ul>
      )}
    </div>
  );
};

export default CustomSelect;
