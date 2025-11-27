/**
 * Custom hook for managing async research API calls with polling
 *
 * This hook handles:
 * - Query submission to async endpoint
 * - Status polling (every 3 seconds)
 * - Session history management
 * - Error handling
 */

import { useState, useEffect, useCallback, useRef } from 'react';
import type {
  AsyncQueryResponse,
  SessionStatus,
  SessionStatusType,
  QueryResult,
  Session,
  HistoryResponse,
} from '../types/async-api';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';
const POLLING_INTERVAL_MS = 3000; // 3 seconds

interface UseAsyncResearchReturn {
  // State
  isSubmitting: boolean;
  isPolling: boolean;
  sessionId: string | null;
  status: SessionStatusType | null;
  currentAgent: string | null;
  result: QueryResult | null;
  error: string | null;
  processingTime: number | null;
  sessionData: SessionStatus | null;

  // Actions
  submitQuery: (queryText: string) => Promise<void>;
  stopPolling: () => void;
  clearSession: () => void;

  // History
  history: Session[];
  loadSession: (sessionId: string) => Promise<void>;
  refreshHistory: () => Promise<void>;
}

export function useAsyncResearch(): UseAsyncResearchReturn {
  // State
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [isPolling, setIsPolling] = useState(false);
  const [sessionId, setSessionId] = useState<string | null>(null);
  const [status, setStatus] = useState<SessionStatusType | null>(null);
  const [currentAgent, setCurrentAgent] = useState<string | null>(null);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [processingTime, setProcessingTime] = useState<number | null>(null);
  const [sessionData, setSessionData] = useState<SessionStatus | null>(null);
  const [history, setHistory] = useState<Session[]>([]);

  // Refs
  const pollingIntervalRef = useRef<NodeJS.Timeout | null>(null);

  // Stop polling
  const stopPolling = useCallback(() => {
    if (pollingIntervalRef.current) {
      clearInterval(pollingIntervalRef.current);
      pollingIntervalRef.current = null;
    }
    setIsPolling(false);
  }, []);

  // Clear session
  const clearSession = useCallback(() => {
    stopPolling();
    setSessionId(null);
    setStatus(null);
    setCurrentAgent(null);
    setResult(null);
    setError(null);
    setProcessingTime(null);
    setSessionData(null);
  }, [stopPolling]);

  // Fetch session status
  const fetchStatus = useCallback(async (sid: string): Promise<SessionStatus> => {
    const response = await fetch(`${API_BASE_URL}/api/v1/research/status/${sid}`);

    if (!response.ok) {
      throw new Error(`Failed to fetch status: ${response.statusText}`);
    }

    return response.json();
  }, []);

  // Poll status endpoint
  const pollStatus = useCallback(async (sid: string) => {
    try {
      const statusData = await fetchStatus(sid);

      // Update state
      setSessionData(statusData);
      setStatus(statusData.status);
      setCurrentAgent(statusData.current_agent || null);
      setProcessingTime(statusData.processing_time_seconds || null);

      // Check if completed or failed
      if (statusData.status === 'completed') {
        stopPolling();

        if (statusData.result) {
          setResult({
            response: statusData.result.response,
            citations: statusData.result.citations,
            processing_time: statusData.processing_time_seconds || 0,
            metadata: statusData.result.metadata,
          });
        }

        // Refresh history after completion
        refreshHistory();
      } else if (statusData.status === 'failed') {
        stopPolling();
        setError(statusData.error_message || 'Query failed');
      }
    } catch (err) {
      console.error('Polling error:', err);
      setError(err instanceof Error ? err.message : 'Failed to poll status');
      stopPolling();
    }
  }, [fetchStatus, stopPolling]);

  // Start polling
  const startPolling = useCallback((sid: string) => {
    // Clear any existing interval
    stopPolling();

    // Start new polling interval
    setIsPolling(true);
    pollingIntervalRef.current = setInterval(() => {
      pollStatus(sid);
    }, POLLING_INTERVAL_MS);

    // Poll immediately
    pollStatus(sid);
  }, [stopPolling, pollStatus]);

  // Submit query
  const submitQuery = useCallback(async (queryText: string) => {
    if (!queryText.trim()) {
      setError('Query text cannot be empty');
      return;
    }

    // Clear previous session state before submitting new query
    stopPolling();
    setSessionId(null);
    setStatus(null);
    setCurrentAgent(null);
    setResult(null);
    setError(null);
    setProcessingTime(null);
    setSessionData(null);

    setIsSubmitting(true);

    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/query/async`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query_text: queryText }),
      });

      if (!response.ok) {
        throw new Error(`Failed to submit query: ${response.statusText}`);
      }

      const data: AsyncQueryResponse = await response.json();

      // Update state
      setSessionId(data.session_id);
      setStatus('pending');

      // Start polling
      startPolling(data.session_id);
    } catch (err) {
      console.error('Submit error:', err);
      setError(err instanceof Error ? err.message : 'Failed to submit query');
    } finally {
      setIsSubmitting(false);
    }
  }, [startPolling, stopPolling]);

  // Load session
  const loadSession = useCallback(async (sid: string) => {
    clearSession();
    setSessionId(sid);

    try {
      const statusData = await fetchStatus(sid);

      setSessionData(statusData);
      setStatus(statusData.status);
      setCurrentAgent(statusData.current_agent || null);
      setProcessingTime(statusData.processing_time_seconds || null);

      if (statusData.status === 'completed' && statusData.result) {
        setResult({
          response: statusData.result.response,
          citations: statusData.result.citations,
          processing_time: statusData.processing_time_seconds || 0,
          metadata: statusData.result.metadata,
        });
      } else if (statusData.status === 'failed') {
        setError(statusData.error_message || 'Query failed');
      } else if (statusData.status === 'in_progress') {
        // Resume polling if still in progress
        startPolling(sid);
      }
    } catch (err) {
      console.error('Load session error:', err);
      setError(err instanceof Error ? err.message : 'Failed to load session');
    }
  }, [clearSession, fetchStatus, startPolling]);

  // Refresh history
  const refreshHistory = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/v1/research/history?limit=10`);

      if (!response.ok) {
        throw new Error(`Failed to fetch history: ${response.statusText}`);
      }

      const data: HistoryResponse = await response.json();
      setHistory(data.sessions);
    } catch (err) {
      console.error('History error:', err);
    }
  }, []);

  // Load history on mount
  useEffect(() => {
    refreshHistory();
  }, [refreshHistory]);

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopPolling();
    };
  }, [stopPolling]);

  return {
    // State
    isSubmitting,
    isPolling,
    sessionId,
    status,
    currentAgent,
    result,
    error,
    processingTime,
    sessionData,

    // Actions
    submitQuery,
    stopPolling,
    clearSession,

    // History
    history,
    loadSession,
    refreshHistory,
  };
}
