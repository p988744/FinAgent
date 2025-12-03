/**
 * useResearch - Hook for managing research sessions and API calls
 */

import { useState, useCallback, useRef, useEffect } from 'react';
import type {
  Message,
  ThinkingState,
  ThinkingStep,
  Citation,
  SessionStatus,
  AsyncQueryResponse,
  SessionStatusResponse,
  GraphState,
  StepHistoryEntry,
} from '../types';

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';
const POLL_INTERVAL = 1500; // 1.5 seconds

interface UseResearchReturn {
  messages: Message[];
  isLoading: boolean;
  sessionStatus: SessionStatus;
  error: string | null;
  sendMessage: (content: string) => Promise<void>;
  clearMessages: () => void;
}

export function useResearch(): UseResearchReturn {
  const [messages, setMessages] = useState<Message[]>([]);
  const [isLoading, setIsLoading] = useState(false);
  const [sessionStatus, setSessionStatus] = useState<SessionStatus>('idle');
  const [error, setError] = useState<string | null>(null);

  const pollIntervalRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const currentSessionRef = useRef<string | null>(null);

  // Cleanup polling on unmount
  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  // Submit query to backend
  const submitQuery = async (queryText: string): Promise<AsyncQueryResponse> => {
    const response = await fetch(`${API_BASE}/api/v1/research/query/async`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ query_text: queryText }),
    });

    if (!response.ok) {
      throw new Error(`API error: ${response.status}`);
    }

    return response.json();
  };

  // Poll for session status
  const pollStatus = async (sessionId: string): Promise<SessionStatusResponse> => {
    const response = await fetch(`${API_BASE}/api/v1/research/status/${sessionId}`);

    if (!response.ok) {
      throw new Error(`Status API error: ${response.status}`);
    }

    return response.json();
  };

  // Convert API status to thinking state
  const mapToThinkingState = (status: SessionStatusResponse): ThinkingState => {
    const steps: ThinkingStep[] = [];

    // Add research plan tasks as steps
    if (status.research_plan?.tasks) {
      status.research_plan.tasks.forEach((task, index) => {
        steps.push({
          id: `task-${index}`,
          description: task.description,
          status: task.status === 'complete' ? 'complete' :
                  task.status === 'in_progress' ? 'active' :
                  task.status === 'error' ? 'error' : 'pending',
          result: task.result,
        });
      });
    }

    // Add agent steps if no plan tasks
    if (steps.length === 0 && status.agent_steps) {
      // Map node names to friendly descriptions
      const nodeDescriptions: Record<string, string> = {
        'query_analyzer': '分析查詢意圖',
        'planner': '制定研究計畫',
        'execute_task': '執行研究任務',
        'replanner': '檢視並調整計畫',
        'reporter': '生成研究報告',
      };

      status.agent_steps.forEach((step, index) => {
        // Use data.description if available, otherwise map from step name
        const stepName = step.step || step.agent || 'unknown';
        const description = step.data?.description ||
                           nodeDescriptions[stepName] ||
                           `${stepName} 代理執行中`;

        steps.push({
          id: `agent-${index}`,
          description,
          status: step.status === 'completed' ? 'complete' :
                  step.status === 'running' ? 'active' : 'pending',
        });
      });
    }

    // Build graph state from API response
    const graphState: GraphState = {
      input: status.query_text,
      current_node: status.current_agent,
    };

    // Add plan information
    if (status.research_plan) {
      graphState.plan = {
        goal: status.research_plan.goal,
        tasks: status.research_plan.tasks?.map((task, index) => ({
          id: task.task_number || index + 1,
          description: task.description,
          status: task.status,
          result: task.result,
        })),
      };
    }

    // Add dynamic plan progress
    if (status.dynamic_plan) {
      if (!graphState.plan) {
        graphState.plan = {};
      }
      // Merge dynamic plan info
    }

    // Add tool executions as past_steps
    if (status.tool_executions) {
      graphState.past_steps = Object.entries(status.tool_executions).map(([tool, result]) => [
        { tool },
        typeof result === 'string' ? result : JSON.stringify(result),
      ]);
    }

    // Map step_history from API response
    const stepHistory: StepHistoryEntry[] = (status.step_history || []).map((entry) => ({
      step: entry.step,
      status: entry.status,
      timestamp: entry.timestamp,
      sequence: entry.sequence,
      data: entry.data,
    }));

    return {
      isThinking: status.status === 'in_progress',
      currentStep: status.current_agent,
      steps,
      logs: (status.activity_log || []).map((log) => ({
        timestamp: new Date(log.timestamp),
        level: log.level as 'info' | 'debug' | 'warn' | 'error',
        message: log.message,
      })),
      graphState,
      stepHistory,
    };
  };

  // Convert API result to citations
  const mapToCitations = (result: SessionStatusResponse['result']): Citation[] => {
    if (!result?.citations) return [];

    return result.citations.map((c, index) => ({
      id: `citation-${index}`,
      number: index + 1,
      source: c.source || 'Unknown',
      content: c.excerpt || c.content || '',
      relevance: c.relevance,
    }));
  };

  // Build response content from backend result
  const buildResponseContent = (result: SessionStatusResponse['result']): string => {
    if (!result) return '';

    const parts: string[] = [];

    // Executive summary
    if (result.executive_summary) {
      parts.push(`## 執行摘要\n\n${result.executive_summary}`);
    }

    // Key findings
    if (result.key_findings && result.key_findings.length > 0) {
      parts.push(`## 關鍵發現\n\n${result.key_findings.map((f: string) => `• ${f}`).join('\n')}`);
    }

    // Detailed analysis
    if (result.detailed_analysis) {
      parts.push(`## 詳細分析\n\n${result.detailed_analysis}`);
    }

    // Confidence level
    if (result.confidence) {
      const level = result.confidence.level === 'HIGH' ? '高信心' :
                    result.confidence.level === 'MEDIUM' ? '中信心' : '低信心';
      parts.push(`## 信心評分：${level}\n\n${result.confidence.justification || ''}`);
    }

    // If there's a direct response field, use it
    if (result.response) {
      return result.response;
    }

    return parts.join('\n\n') || '查詢完成，但沒有找到相關資料。';
  };

  // Start polling for a session
  const startPolling = (sessionId: string, assistantMessageId: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    const poll = async () => {
      try {
        const status = await pollStatus(sessionId);

        // Update thinking state
        const thinkingState = mapToThinkingState(status);

        setMessages(prev => prev.map(msg => {
          if (msg.id === assistantMessageId) {
            return {
              ...msg,
              thinking: thinkingState,
              status: status.status === 'completed' ? 'complete' :
                     status.status === 'failed' ? 'error' : 'thinking',
            };
          }
          return msg;
        }));

        // Check if done
        if (status.status === 'completed' || status.status === 'failed') {
          setIsLoading(false);
          setSessionStatus(status.status);

          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
          }

          // Update message with result
          if (status.status === 'completed' && status.result) {
            const citations = mapToCitations(status.result);
            const responseContent = buildResponseContent(status.result);

            setMessages(prev => prev.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  content: responseContent,
                  citations,
                  status: 'complete',
                  thinking: { ...thinkingState, isThinking: false },
                  metadata: {
                    processingTime: status.processing_time_seconds,
                    totalTokens: status.result?.tokens_used,
                    llmCostUsd: status.result?.cost_usd,
                    workflow: 'plan-execute',
                  },
                };
              }
              return msg;
            }));
          } else if (status.status === 'failed') {
            setError(status.error_message || 'Research query failed');

            setMessages(prev => prev.map(msg => {
              if (msg.id === assistantMessageId) {
                return {
                  ...msg,
                  content: `抱歉，處理您的查詢時發生錯誤：${status.error_message || '未知錯誤'}`,
                  status: 'error',
                  thinking: { ...thinkingState, isThinking: false },
                };
              }
              return msg;
            }));
          }
        }
      } catch (err) {
        console.error('Polling error:', err);
      }
    };

    // Initial poll
    poll();

    // Start interval polling
    pollIntervalRef.current = setInterval(poll, POLL_INTERVAL);
  };

  // Send a message
  const sendMessage = useCallback(async (content: string) => {
    setError(null);
    setIsLoading(true);
    setSessionStatus('pending');

    // Add user message
    const userMessage: Message = {
      id: `user-${Date.now()}`,
      role: 'user',
      content,
      status: 'complete',
      timestamp: new Date(),
    };

    // Add placeholder assistant message
    const assistantMessageId = `assistant-${Date.now()}`;
    const assistantMessage: Message = {
      id: assistantMessageId,
      role: 'assistant',
      content: '',
      status: 'thinking',
      timestamp: new Date(),
      thinking: {
        isThinking: true,
        steps: [
          { id: 'init', description: '初始化研究流程...', status: 'active' },
        ],
        logs: [],
      },
    };

    setMessages(prev => [...prev, userMessage, assistantMessage]);

    try {
      // Submit query
      const response = await submitQuery(content);
      currentSessionRef.current = response.session_id;

      setSessionStatus('in_progress');

      // Start polling for updates
      startPolling(response.session_id, assistantMessageId);
    } catch (err) {
      setIsLoading(false);
      setSessionStatus('failed');
      setError(err instanceof Error ? err.message : 'Unknown error');

      // Update assistant message with error
      setMessages(prev => prev.map(msg => {
        if (msg.id === assistantMessageId) {
          return {
            ...msg,
            content: '抱歉，無法連接到伺服器。請稍後再試。',
            status: 'error',
            thinking: undefined,
          };
        }
        return msg;
      }));
    }
  }, []);

  // Clear all messages
  const clearMessages = useCallback(() => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }
    setMessages([]);
    setError(null);
    setSessionStatus('idle');
    currentSessionRef.current = null;
  }, []);

  return {
    messages,
    isLoading,
    sessionStatus,
    error,
    sendMessage,
    clearMessages,
  };
}
