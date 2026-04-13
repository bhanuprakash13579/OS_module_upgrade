import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Show the Tauri window once the webview is ready.
// The window starts hidden (visible: false in tauri.conf.json) to prevent the
// split-second "double screen" flicker on Windows 11 / DWM.
//
// IMPORTANT: Do NOT use requestAnimationFrame here. On Linux/WebKit (and some
// Tauri versions on Windows), rAF is throttled in hidden windows — the callback
// never fires, so show() never gets called and the window stays permanently
// invisible. A microtask (Promise.resolve) fires too early on some Linux setups,
// resulting in a permanently hidden window. A 50ms timeout is reliable on all OS.
if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
  import('@tauri-apps/api/window').then(({ getCurrentWindow }) => {
    setTimeout(() => getCurrentWindow().show(), 50);
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
