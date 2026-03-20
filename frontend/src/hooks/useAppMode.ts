import { useState, useEffect } from 'react';
import api from '@/lib/api';

interface AppMode {
  isProd: boolean;
  isLoading: boolean;
}

export function useAppMode(): AppMode {
  const [isProd, setIsProd] = useState<boolean>(true); // default to prod until known
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    api.get('/mode')
      .then(r => setIsProd(!!r.data.prod_mode))
      .catch(() => setIsProd(true)) // safe fallback: assume prod on error
      .finally(() => setIsLoading(false));
  }, []);

  return { isProd, isLoading };
}
