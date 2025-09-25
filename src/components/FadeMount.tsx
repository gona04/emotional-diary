import React, { useEffect, useState } from 'react';
import './FadeMount.css';

type Props = {
  show: boolean;
  duration?: number; // ms
  children?: React.ReactNode;
  className?: string;
};

const FadeMount: React.FC<Props> = ({ show, duration = 260, children, className = '' }) => {
  const [mounted, setMounted] = useState<boolean>(show);
  const [phase, setPhase] = useState<string>('');

  useEffect(() => {
    let timer: ReturnType<typeof setTimeout> | undefined;

    if (show) {
      // mount immediately, then start enter animation
      setMounted(true);
      // next frame to ensure transition runs
      requestAnimationFrame(() => {
        setPhase('enter');
        timer = setTimeout(() => setPhase('entered'), duration);
      });
    } else if (mounted) {
      // start exit animation then unmount
      setPhase('exit');
      timer = setTimeout(() => {
        setMounted(false);
        setPhase('');
      }, duration);
    }

    return () => {
      if (timer) clearTimeout(timer);
    };
  }, [show, duration, mounted]);

  if (!mounted) return null;

  const cls = ['fade-mount', phase ? `fade-${phase}` : '', className].filter(Boolean).join(' ');

  return <div className={cls}>{children}</div>;
};

export default FadeMount;
