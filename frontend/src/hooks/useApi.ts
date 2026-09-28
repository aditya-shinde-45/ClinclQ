import { useState, useEffect } from 'react';

export function useApi<T>(apiCall: () => Promise<T>, deps: any[] = []) {
  const [data, setData] = useState<T | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let mounted = true;
    setLoading(true);
    
    apiCall()
      .then(result => {
        if (mounted) {
          setData(result);
          setError(null);
        }
      })
      .catch(err => {
        if (mounted) {
          setError(err.message || 'An error occurred');
        }
      })
      .finally(() => {
        if (mounted) {
          setLoading(false);
        }
      });

    return () => { mounted = false; };
  }, deps);

  return { data, loading, error, setData, refetch: () => setLoading(true) };
}

export function useApiMutation<T, P>(apiCall: (params: P) => Promise<T>) {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const mutate = async (params: P): Promise<T | null> => {
    setLoading(true);
    setError(null);
    
    try {
      const result = await apiCall(params);
      setLoading(false);
      return result;
    } catch (err: any) {
      setError(err.message || 'An error occurred');
      setLoading(false);
      return null;
    }
  };

  return { mutate, loading, error };
}
