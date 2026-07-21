import { useState, useCallback } from "react";
import { analyzeQuery } from "../services/api";

export function useAnalysis() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const analyze = useCallback(async (payload) => {
    // If payload is a string, format it as query string, else it's an object
    const finalPayload = typeof payload === 'string' ? { query: payload } : payload;
    
    // If there's no NL query and all filters are empty, don't submit
    if (typeof payload === 'object' && !finalPayload.query && !finalPayload.plant && !finalPayload.line && !finalPayload.machine && !finalPayload.shift && !finalPayload.from_date && !finalPayload.to_date) {
      return;
    }
    if (typeof payload === 'string' && !finalPayload.query.trim()) {
      return;
    }

    setLoading(true);
    setError(null);
    try {
      const result = await analyzeQuery(finalPayload);
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
