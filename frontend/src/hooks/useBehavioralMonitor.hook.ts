// hooks/useBehavioralMonitor.ts
import { useEffect, useRef, useCallback } from 'react';
import type { HandleKey } from '../types/handleKey.type';
import type { HandleMouse } from '../types/handleMouse.type';

export default function useBehavioralMonitor() {
  const events = useRef<(HandleMouse | HandleKey)[]>([]);

  const flush = useCallback(async () => {
    if (events.current.length === 0) return [];
    
    const data = [...events.current];
    events.current = [];
    return data;
  }, []);

  useEffect(() => {
    const handleMouse = (e: MouseEvent) => {
      events.current.push({
        t: Date.now(),
        x: e.clientX,
        y: e.clientY,
        type: e.type,
      });
    };

    const handleKey = (e: KeyboardEvent) => {
      events.current.push({
        t: Date.now(),
        key: e.key,
        type: e.type,
      });
    };

    window.addEventListener('mousemove', handleMouse);
    window.addEventListener('keydown', handleKey);
    window.addEventListener('keyup', handleKey);
    return () => {
      window.removeEventListener('mousemove', handleMouse);
      window.removeEventListener('keydown', handleKey);
      window.removeEventListener('keyup', handleKey);
    };
  }, []);

  return { flush };
}