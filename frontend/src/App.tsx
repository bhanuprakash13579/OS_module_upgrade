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

export default function App() {
  return (
    <AuthProvider>
      <DevModeBanner />
      <BrowserRouter>
        <AppRoutes />
      </BrowserRouter>
    </AuthProvider>
  );
}
