import { StrictMode } from 'react'
import { createRoot } from 'react-dom/client'
import App from './App.tsx'
import './index.css'

// Show the Tauri window only after the webview has painted its first frame.
// The window starts hidden (visible: false in tauri.conf.json) to prevent the
// split-second where Windows DWM sees the native host frame and the WebView2
// compositor surface as two separate surfaces — the "double screen" flicker
// visible in the taskbar thumbnail on Windows 11.
if (typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window) {
  import('@tauri-apps/api/window').then(({ getCurrentWindow }) => {
    requestAnimationFrame(() => getCurrentWindow().show());
  });
}

createRoot(document.getElementById('root')!).render(
  <StrictMode>
    <App />
  </StrictMode>,
)
