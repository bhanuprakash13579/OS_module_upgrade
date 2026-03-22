import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useState, useEffect } from 'react';
import api from './lib/api';
import DevModeBanner from './components/DevModeBanner';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import Login from './pages/auth/Login';
import ModuleSelection from './pages/ModuleSelection';
// Static imports — Tauri is a local desktop app; lazy-loading only adds startup latency
import SDOModule from './pages/sdo';
import AdjudicationModule from './pages/adjudication';
import QueryModule from './pages/query';
import ApisModule from './pages/apis';
import RestoreBackup from './pages/backup/RestoreBackup';

// ── Auto-updater banner (Tauri desktop only) ──────────────────────────────────
// Checks for a new release silently in the background 5 seconds after startup.
// If an update is found, shows a thin banner at the very top of the screen.
// Any user (SDO / DC / AC) can click "Update Now" — no admin login needed.
function AutoUpdater() {
  const isTauri = typeof window !== 'undefined' && '__TAURI_INTERNALS__' in window;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  const [updateObj, setUpdateObj] = useState<any>(null);
  const [installing, setInstalling] = useState(false);
  const [dismissed, setDismissed] = useState(false);

  useEffect(() => {
    if (!isTauri) return;
    // Wait 5 s so the app finishes loading before hitting the network
    const timer = setTimeout(async () => {
      try {
        const { check } = await import('@tauri-apps/plugin-updater');
        const update = await check();
        if (update) setUpdateObj(update);
      } catch {
        // Silently ignore — network may be offline or keys not configured yet
      }
    }, 5000);
    return () => clearTimeout(timer);
  }, [isTauri]);

  if (!isTauri || !updateObj || dismissed) return null;

  const install = async () => {
    setInstalling(true);
    try {
      await updateObj.downloadAndInstall();
      const { relaunch } = await import('@tauri-apps/plugin-process');
      await relaunch();
    } catch {
      setInstalling(false);
    }
  };

  return (
    <div className="fixed top-0 left-0 right-0 z-50 flex items-center justify-between gap-3 bg-blue-600 text-white text-xs px-4 py-2 shadow-md">
      <span>
        ✦ A new version of COPS ({updateObj.version}) is available.
        Your data is safe — only the app is updated.
      </span>
      <div className="flex items-center gap-2 shrink-0">
        <button
          onClick={install}
          disabled={installing}
          className="bg-white text-blue-700 font-semibold px-3 py-1 rounded hover:bg-blue-50 disabled:opacity-60"
        >
          {installing ? 'Installing…' : 'Update Now'}
        </button>
        <button
          onClick={() => setDismissed(true)}
          disabled={installing}
          className="opacity-70 hover:opacity-100 px-1"
          aria-label="Dismiss"
        >
          ✕
        </button>
      </div>
    </div>
  );
}

// SDO-only guard
function SDORoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, canAccessSDO } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login/sdo" replace />;
  if (!canAccessSDO()) return <Navigate to="/login/sdo" replace />;
  return <>{children}</>;
}

// Adjudication-only guard
function AdjudicationRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, canAccessAdjudication } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login/adjudication" replace />;
  if (!canAccessAdjudication()) return <Navigate to="/login/adjudication" replace />;
  return <>{children}</>;
}

// Query guard (allows SDO and Adjn roles)
function QueryRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, canAccessQuery } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login/query" replace />;
  if (!canAccessQuery()) return <Navigate to="/login/query" replace />;
  return <>{children}</>;
}

// APIS guard (SDO and Adjn roles + feature flag must be enabled)
function ApisRoute({ children }: { children: React.ReactNode }) {
  const { isAuthenticated, canAccessApis } = useAuth();
  const [enabled, setEnabled] = useState<boolean | null>(null);

  useEffect(() => {
    api.get('/features')
      .then(r => setEnabled(!!r.data.apis_enabled))
      .catch(() => setEnabled(false));
  }, []);

  if (enabled === null) return <div className="min-h-screen bg-slate-900" />; // still loading
  if (!enabled) return <Navigate to="/modules" replace />;
  if (!isAuthenticated) return <Navigate to="/login/apis" replace />;
  if (!canAccessApis()) return <Navigate to="/login/apis" replace />;
  return <>{children}</>;
}

function AppRoutes() {
  return (
    <Routes>
      {/* Public Landing Page */}
      <Route path="/modules" element={<ModuleSelection />} />

      {/* Dynamic Login Page for specific modules */}
      <Route path="/login/:moduleType" element={<Login />} />

      {/* SDO Module — SDO role only */}
      <Route
        path="/sdo/*"
        element={
          <SDORoute>
            <SDOModule />
          </SDORoute>
        }
      />

      {/* Adjudication Module — DC and AC only */}
      <Route
        path="/adjudication/*"
        element={
          <AdjudicationRoute>
            <AdjudicationModule />
          </AdjudicationRoute>
        }
      />

      {/* Query Module — Cross Role Access */}
      <Route
        path="/query/*"
        element={
          <QueryRoute>
            <QueryModule />
          </QueryRoute>
        }
      />

      {/* COPS ↔ APIS Module — SDO and Adjn roles */}
      <Route
        path="/apis/*"
        element={
          <ApisRoute>
            <ApisModule />
          </ApisRoute>
        }
      />

      {/* Hidden Admin Panel — no pre-auth needed; the page itself requires sysadmin credentials */}
      <Route path="/restore-backup" element={<RestoreBackup />} />

      {/* Root → always redirect to public module selection */}
      <Route path="/" element={<Navigate to="/modules" replace />} />
      <Route path="/login" element={<Navigate to="/modules" replace />} />
      <Route path="*" element={<Navigate to="/modules" replace />} />
    </Routes>
  );
}

// Polls /api/mode until the Python backend is ready, then renders the app.
// Without this, the window opens immediately while the sidecar is still
// running startup migrations and seed queries — resulting in blank pages
// and API errors for the first few seconds.
const SPLASH_BG = { background: 'linear-gradient(135deg, #0f172a 0%, #1e3a5f 50%, #0f172a 100%)' };

function BackendGate({ children }: { children: React.ReactNode }) {
  const [ready, setReady] = useState(false);
  const [dots, setDots] = useState('');

  useEffect(() => {
    let cancelled = false;
    let dotTimer: ReturnType<typeof setInterval>;

    const poll = async () => {
      while (!cancelled) {
        try {
          await api.get('/mode', { timeout: 2000 });
          if (!cancelled) setReady(true);
          return;
        } catch {
          await new Promise(r => setTimeout(r, 800));
        }
      }
    };

    dotTimer = setInterval(() => setDots(d => d.length >= 3 ? '' : d + '.'), 500);
    poll();
    return () => {
      cancelled = true;
      clearInterval(dotTimer);
    };
  }, []);

  if (!ready) {
    return (
      <div className="min-h-screen flex flex-col items-center justify-center" style={SPLASH_BG}>
        <img src="/cops_logo.png" alt="COPS" className="w-24 h-24 object-contain mb-6 opacity-90" />
        <p className="text-white text-lg font-semibold tracking-widest">COPS</p>
        <p className="text-blue-300 text-sm mt-2 w-32 text-center">Starting{dots}</p>
      </div>
    );
  }

  return <>{children}</>;
}

export default function App() {
  return (
    <AuthProvider>
      <BackendGate>
        <AutoUpdater />
        <DevModeBanner />
        <BrowserRouter>
          <AppRoutes />
        </BrowserRouter>
      </BackendGate>
    </AuthProvider>
  );
}
