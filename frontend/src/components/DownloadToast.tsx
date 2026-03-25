import { useEffect, useState, useCallback, useRef } from 'react';
import { CheckCircle, X } from 'lucide-react';

// ── Shared toast state (module-level singleton) ──────────────────────────────
// Any component can push a toast; the single <DownloadToast /> rendered in the
// root layout picks it up and renders it in a fixed corner — zero layout shift,
// zero interaction blocking.

type ToastEntry = { id: number; message: string };
let _nextId = 0;
let _listeners: Array<(toasts: ToastEntry[]) => void> = [];
let _toasts: ToastEntry[] = [];

function _notify() {
  _listeners.forEach(fn => fn([..._toasts]));
}

/** Call from anywhere to show a non-blocking success toast (auto-dismisses in 3s). */
export function showDownloadToast(message: string) {
  const id = ++_nextId;
  _toasts.push({ id, message });
  // Keep max 3 visible at once
  if (_toasts.length > 3) _toasts = _toasts.slice(-3);
  _notify();
  setTimeout(() => {
    _toasts = _toasts.filter(t => t.id !== id);
    _notify();
  }, 3000);
}

/** Render this ONCE near the app root (e.g. in AppLayout). */
export default function DownloadToast() {
  const [toasts, setToasts] = useState<ToastEntry[]>([]);
  const ref = useRef(setToasts);
  ref.current = setToasts;

  useEffect(() => {
    const listener = (t: ToastEntry[]) => ref.current(t);
    _listeners.push(listener);
    return () => { _listeners = _listeners.filter(l => l !== listener); };
  }, []);

  const dismiss = useCallback((id: number) => {
    _toasts = _toasts.filter(t => t.id !== id);
    _notify();
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div className="fixed bottom-4 right-4 z-[9999] flex flex-col gap-2 pointer-events-none print:hidden">
      {toasts.map(t => (
        <div
          key={t.id}
          className="pointer-events-auto flex items-center gap-2 bg-emerald-600 text-white text-sm font-medium pl-3 pr-2 py-2.5 rounded-lg shadow-lg animate-[slideInRight_0.25s_ease-out] max-w-sm"
        >
          <CheckCircle className="w-4 h-4 shrink-0" />
          <span className="flex-1 truncate">{t.message}</span>
          <button
            onClick={() => dismiss(t.id)}
            className="ml-1 p-0.5 rounded hover:bg-white/20 transition-colors shrink-0"
          >
            <X className="w-3.5 h-3.5" />
          </button>
        </div>
      ))}
    </div>
  );
}
