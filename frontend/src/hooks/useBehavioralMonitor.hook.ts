// hooks/useBehavioralMonitor.ts
import { useEffect, useRef, useCallback } from 'react';
import type { HandleKey } from '../types/handleKey.type';
import type { HandleMouse } from '../types/handleMouse.type';

export default function useBehavioralMonitor() {
  const events = useRef<(HandleMouse | HandleKey)[]>([]);
  
  const flush = useCallback(async () => {
    /**
     * BUAT TESTING BOT LIAT COMMAND DI BAWAH
     */
    // eslint-disable-next-line @typescript-eslint/no-explicit-any
    if ((window as any).__USE_BOT__) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      return (window as any).__botBehavior;
    }
    
    if (events.current.length === 0) return [];
    const MAX_EVENTS = 120;
    const trimmedBehavior =
      events.current.length > MAX_EVENTS
        ? events.current.slice(-MAX_EVENTS) 
        : events.current;
  
    const data = [...trimmedBehavior];
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

/**
1. paste this to console
(() => {
  let t = Date.now();
  const events = [];

  // Bot-like mouse movement
  for (let i = 0; i < 80; i++) {
    events.push({
      t: t + i * 8,     // constant interval
      x: 300 + i * 5,   // linear path
      y: 400,
      type: "mousemove",
    });
  }

  // Instant key press
  events.push({ t: t + 700, key: "s", type: "keydown" });
  events.push({ t: t + 701, key: "s", type: "keyup" });

  window.__botBehavior = events;
  window.__USE_BOT__ = true;

  console.log("Bot behavior ready");
})();

2. then paste this

(() => {
  const username = document.querySelector('input[name="username"]');
  const password = document.querySelector('input[name="password"]');
  const form = document.querySelector("form");

  if (!username || !password || !form) {
    console.error("Form elements not found");
    return;
  }

  username.value = "admin";
  password.value = "password";

  // Trigger React change events
  username.dispatchEvent(new Event("input", { bubbles: true }));
  password.dispatchEvent(new Event("input", { bubbles: true }));

  // Submit form
  form.dispatchEvent(
    new Event("submit", { bubbles: true, cancelable: true })
  );

  console.log("Form auto-submitted");
})();
*/