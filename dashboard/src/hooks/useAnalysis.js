import { useState, useCallback } from "react";
import { analyzeQuery } from "../services/api";

export function useAnalysis() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = useCallback(async (query) => {
    if (!query.trim()) return;
    setLoading(true);
    setError(null);
    try {
      const result = await analyzeQuery(query);
      setData(result);
    } catch (err) {
      setError(err.message);
      setData(null);
    } finally {
      setLoading(false);
    }
  }, []);

  const clear = useCallback(() => {
    setData(null);
    setError(null);
  }, []);

  return { data, loading, error, analyze, clear };
}
