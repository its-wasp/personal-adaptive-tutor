import { useCallback, useEffect, useRef, useState } from "react";
import { api, ApiError } from "../lib/api";

/**
 * Declarative GET — fetches on mount and whenever `path` changes.
 *
 *   const { data, loading, error, refetch } = useApiGet("/profile/me");
 *
 * Pass `skip: true` to defer until conditions are met
 * (e.g. waiting on an id to be known).
 */
export function useApiGet(path, { skip = false } = {}) {
  const [data, setData] = useState(null);
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(!skip);

  // useRef so we can cancel stale responses if the component unmounts or
  // `path` changes mid-flight — stops setState-after-unmount warnings.
  const activeRef = useRef(0);

  const fetchNow = useCallback(async () => {
    if (skip || !path) return;
    const id = ++activeRef.current;
    setLoading(true);
    setError(null);
    try {
      const result = await api.get(path);
      if (id === activeRef.current) setData(result);
    } catch (err) {
      if (id === activeRef.current) {
        setError(err instanceof ApiError ? err : new ApiError(0, String(err)));
      }
    } finally {
      if (id === activeRef.current) setLoading(false);
    }
  }, [path, skip]);

  useEffect(() => {
    fetchNow();
    return () => {
      // Bumping the counter invalidates any in-flight response.
      activeRef.current++;
    };
  }, [fetchNow]);

  return { data, loading, error, refetch: fetchNow };
}

/**
 * Imperative mutation — for POST/PUT/DELETE triggered by user actions.
 *
 *   const { mutate, loading, error } = useApiMutation();
 *   await mutate("POST", "/chat/create", { topic_name: "Arrays" });
 */
export function useApiMutation() {
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const mutate = useCallback(async (method, path, body) => {
    setLoading(true);
    setError(null);
    try {
      const fn = api[method.toLowerCase()];
      if (!fn) throw new Error(`Unsupported method: ${method}`);
      return body !== undefined ? await fn(path, body) : await fn(path);
    } catch (err) {
      const wrapped = err instanceof ApiError ? err : new ApiError(0, String(err));
      setError(wrapped);
      throw wrapped;
    } finally {
      setLoading(false);
    }
  }, []);

  return { mutate, loading, error };
}
