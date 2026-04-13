import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Show the Tauri window once the webview is ready.
// The window starts hidden (visible: false in tauri.conf.json) to prevent the
// split-second "double screen" flicker on Windows 11 / DWM.
//
// IMPORTANT: We use a retry loop rather than a one-shot check because on
// Linux/WebKit2GTK, Tauri injects __TAURI_INTERNALS__ asynchronously — it may
// not be present when this module first executes.  The loop retries every 100 ms
// for up to 3 seconds, then gives up (avoids infinite loop in plain-browser).
// On Windows (WebView2), __TAURI_INTERNALS__ is available synchronously so the
// very first attempt at t=50ms succeeds.
if (typeof window !== 'undefined') {
  const _tryShowWindow = (attempt: number) => {
    if ('__TAURI_INTERNALS__' in window) {
      import('@tauri-apps/api/window')
        .then(({ getCurrentWindow }) => getCurrentWindow().show())
        .catch(() => {/* ignore — window may already be visible */});
    } else if (attempt < 30) {
      // __TAURI_INTERNALS__ not ready yet (WebKit2GTK async init) — retry
      setTimeout(() => _tryShowWindow(attempt + 1), 100);
    }
    // After 30 attempts (~3 s) give up: probably running in a browser, not Tauri
  };
  // 50 ms initial delay: lets WebView2 paint its first frame on Windows before
  // showing, preventing the DWM double-surface flicker on Windows 11.
  setTimeout(() => _tryShowWindow(0), 50);
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
