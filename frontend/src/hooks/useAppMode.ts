import { useState, useEffect } from 'react';
import api from '@/lib/api';

interface AppMode {
  isProd: boolean;
  isLoading: boolean;
}

// Module-level cache — the mode never changes during a session, so we fetch
// it once and reuse the result for every component that calls useAppMode().
let _cachedMode: boolean | null = null;

export function useAppMode(): AppMode {
  const [isProd, setIsProd] = useState<boolean>(_cachedMode ?? true);
  const [isLoading, setIsLoading] = useState(_cachedMode === null);

  useEffect(() => {
    if (_cachedMode !== null) return; // already resolved
    api.get('/mode')
      .then(r => {
        _cachedMode = !!r.data.prod_mode;
        setIsProd(_cachedMode);
      })
      .catch(() => {
        _cachedMode = true; // safe fallback: assume prod on error
        setIsProd(true);
      })
      .finally(() => setIsLoading(false));
  }, []);

  return { isProd, isLoading };
}
