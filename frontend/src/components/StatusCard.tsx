/**
 * StatusCard Component
 *
 * Real-time processing status with terminal-style display
 */

import { useEffect, useState } from 'react';
import type { SessionStatusType } from '../types/async-api';

interface StatusCardProps {
  sessionId: string;
  status: SessionStatusType;
  currentAgent?: string;
  processingTime?: number;
  error?: string;
}

const AGENT_LABELS: Record<string, string> = {
  query_analyzer: '查詢分析器',
  planner: '任務規劃器',
  executor: '任務執行器',
  replanner: '重新規劃器',
  reporter: '報告產生器',
};

export function StatusCard({
  sessionId,
  status,
  currentAgent,
  processingTime,
  error,
}: StatusCardProps) {
  const [elapsedTime, setElapsedTime] = useState(0);

  // Update elapsed time every second
  useEffect(() => {
    if (status === 'pending' || status === 'in_progress') {
      const startTime = Date.now();
      const interval = setInterval(() => {
        setElapsedTime(Math.floor((Date.now() - startTime) / 1000));
      }, 1000);

      return () => clearInterval(interval);
    }
  }, [status]);

  const getStatusConfig = () => {
    switch (status) {
      case 'pending':
        return {
          badge: 'badge-slate',
          label: '排隊中',
          icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          dotClass: 'status-dot-pending',
        };
      case 'in_progress':
        return {
          badge: 'badge-amber',
          label: '處理中',
          icon: (
            <svg className="w-4 h-4 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ),
          dotClass: 'status-dot-processing',
        };
      case 'completed':
        return {
          badge: 'badge-emerald',
          label: '已完成',
          icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ),
          dotClass: 'status-dot-success',
        };
      case 'failed':
        return {
          badge: 'badge-rose',
          label: '失敗',
          icon: (
            <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ),
          dotClass: 'status-dot-error',
        };
      default:
        return {
          badge: 'badge-slate',
          label: '未知',
          icon: null,
          dotClass: '',
        };
    }
  };

  const statusConfig = getStatusConfig();
  const displayTime = processingTime !== undefined && processingTime !== null
    ? processingTime.toFixed(1)
    : elapsedTime.toFixed(1);

  const agentLabel = currentAgent ? (AGENT_LABELS[currentAgent] || currentAgent) : null;

  return (
    <div className="card p-6 animate-in">
      {/* Header */}
      <div className="flex items-center justify-between mb-5">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-slate-800 flex items-center justify-center">
            <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
            </svg>
          </div>
          <div>
            <h2 className="text-lg font-serif font-semibold text-slate-100">處理狀態</h2>
            <p className="text-xs text-slate-500 font-mono">{sessionId.slice(0, 8)}...</p>
          </div>
        </div>
        <span className={`badge ${statusConfig.badge}`}>
          <span className={`status-dot ${statusConfig.dotClass}`}></span>
          {statusConfig.label}
        </span>
      </div>

      {/* Progress Section */}
      <div className="space-y-4">
        {/* Current Agent */}
        {agentLabel && (
          <div className="flex items-center gap-3 p-4 rounded-lg bg-slate-800/50 border border-slate-700/30">
            <div className="relative">
              {statusConfig.icon}
              {status === 'in_progress' && (
                <span className="absolute -top-1 -right-1 w-2 h-2 bg-amber-400 rounded-full animate-ping"></span>
              )}
            </div>
            <div className="flex-1">
              <p className="text-xs text-slate-500 uppercase tracking-wider mb-1">當前階段</p>
              <p className="text-sm font-medium text-slate-200">{agentLabel}</p>
            </div>
            <div className="text-right">
              <p className="text-xs text-slate-500 mb-1">處理時間</p>
              <p className="text-lg font-mono font-semibold text-amber-400">{displayTime}s</p>
            </div>
          </div>
        )}

        {/* Progress Bar */}
        {status === 'in_progress' && (
          <div className="progress-bar">
            <div className="progress-bar-indeterminate w-full"></div>
          </div>
        )}

        {/* Pending Message */}
        {status === 'pending' && (
          <div className="flex items-center justify-center gap-3 p-6 rounded-lg bg-slate-800/30 border border-slate-700/30">
            <div className="flex gap-1">
              <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></span>
              <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '150ms' }}></span>
              <span className="w-2 h-2 bg-slate-500 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></span>
            </div>
            <p className="text-sm text-slate-400">正在等待處理佇列...</p>
          </div>
        )}

        {/* Error Message */}
        {error && (
          <div className="flex items-start gap-3 p-4 rounded-lg bg-rose-500/10 border border-rose-500/20">
            <svg className="w-5 h-5 text-rose-400 flex-shrink-0 mt-0.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4m0 4h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-sm font-medium text-rose-300 mb-1">處理錯誤</p>
              <p className="text-sm text-rose-200/80">{error}</p>
            </div>
          </div>
        )}

        {/* Completed Message */}
        {status === 'completed' && (
          <div className="flex items-center gap-3 p-4 rounded-lg bg-emerald-500/10 border border-emerald-500/20">
            <svg className="w-5 h-5 text-emerald-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
            <div>
              <p className="text-sm text-emerald-300">
                研究完成，耗時 <span className="font-mono font-semibold">{displayTime}</span> 秒
              </p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
