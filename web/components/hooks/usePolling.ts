"use client";

import { useCallback, useEffect, useRef, useState } from "react";

interface UsePollingOptions<T> {
  interval?: number;
  enabled?: boolean;
  transform?: (data: any) => T;
}

export function usePolling<T = any>(url: string, initialData: T, { interval = 5000, enabled = true, transform }: UsePollingOptions<T> = {}) {
  const [data, setData] = useState<T>(initialData);
  const [error, setError] = useState<string | null>(null);
  const timer = useRef<NodeJS.Timeout | null>(null);

  const fetchData = useCallback(async () => {
    if (!enabled) return;
    try {
      const response = await fetch(url, { cache: "no-store" });
      if (!response.ok) {
        throw new Error(await response.text());
      }
      const payload = await response.json();
      setData(transform ? transform(payload) : payload);
      setError(null);
    } catch (err) {
      console.error(`Polling error for ${url}`, err);
      setError(err instanceof Error ? err.message : "Unknown error");
    }
  }, [enabled, transform, url]);

  useEffect(() => {
    fetchData();
    if (!enabled) return;
    timer.current = setInterval(fetchData, interval);
    return () => {
      if (timer.current) clearInterval(timer.current);
    };
  }, [enabled, fetchData, interval]);

  return { data, error };
}
