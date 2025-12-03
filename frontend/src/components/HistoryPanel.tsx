 * HistoryPanel Component
 *
 * Sidebar with query history timeline
 */

import React from 'react';
import type { Session } from '../types/async-api';

interface HistoryPanelProps {
  sessions: Session[];
  onSelectSession: (sessionId: string) => void;
  selectedSessionId?: string;
}

export function HistoryPanel({
  sessions,
  onSelectSession,
  selectedSessionId,
}: HistoryPanelProps) {
  const getStatusConfig = (status: string) => {
    switch (status) {
      case 'completed':
        return {
          icon: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M5 13l4 4L19 7" />
            </svg>
          ),
          color: 'text-emerald-400',
          bg: 'bg-emerald-500/10',
          border: 'border-emerald-500/20',
        };
      case 'failed':
        return {
          icon: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          ),
          color: 'text-rose-400',
          bg: 'bg-rose-500/10',
          border: 'border-rose-500/20',
        };
      case 'in_progress':
        return {
          icon: (
            <svg className="w-3.5 h-3.5 animate-spin" fill="none" viewBox="0 0 24 24">
              <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
              <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
            </svg>
          ),
          color: 'text-amber-400',
          bg: 'bg-amber-500/10',
          border: 'border-amber-500/20',
        };
      case 'pending':
        return {
          icon: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          color: 'text-slate-400',
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/20',
        };
      default:
        return {
          icon: (
            <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          ),
          color: 'text-slate-500',
          bg: 'bg-slate-500/10',
          border: 'border-slate-500/20',
        };
    }
  };

  const formatTimeAgo = (timestamp: string): string => {
    const date = new Date(timestamp);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return '剛剛';
    if (diffMins < 60) return `${diffMins} 分鐘前`;
    if (diffHours < 24) return `${diffHours} 小時前`;
    if (diffDays < 7) return `${diffDays} 天前`;
    return date.toLocaleDateString('zh-TW');
  };

  const truncateText = (text: string, maxLength: number): string => {
    if (text.length <= maxLength) return text;
    return text.substring(0, maxLength) + '...';
  };

  if (sessions.length === 0) {
    return (
      <div className="card p-5">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
            <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <h3 className="text-base font-serif font-semibold text-slate-200">查詢歷史</h3>
        </div>
        <div className="flex flex-col items-center justify-center py-10 text-center">
          <div className="w-12 h-12 rounded-full bg-slate-800/50 flex items-center justify-center mb-3">
            <svg className="w-6 h-6 text-slate-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M19 11H5m14 0a2 2 0 012 2v6a2 2 0 01-2 2H5a2 2 0 01-2-2v-6a2 2 0 012-2m14 0V9a2 2 0 00-2-2M5 11V9a2 2 0 012-2m0 0V5a2 2 0 012-2h6a2 2 0 012 2v2M7 7h10" />
            </svg>
          </div>
          <p className="text-sm text-slate-500">尚無查詢記錄</p>
          <p className="text-xs text-slate-600 mt-1">提交查詢後將在此顯示</p>
        </div>
      </div>
    );
  }

  return (
    <div className="card">
      {/* Header */}
      <div className="p-5 border-b border-slate-800/50">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-slate-800 flex items-center justify-center">
              <svg className="w-4 h-4 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
              </svg>
            </div>
            <h3 className="text-base font-serif font-semibold text-slate-200">查詢歷史</h3>
          </div>
          <span className="badge badge-slate">{sessions.length}</span>
        </div>
      </div>

      {/* Session List */}
      <div className="p-3 max-h-[600px] overflow-y-auto scrollbar-hide">
        <div className="space-y-2">
          {sessions.map((session, index) => {
            const statusConfig = getStatusConfig(session.status);
            const isSelected = selectedSessionId === session.session_id;

            return (
              <button
                key={session.session_id}
                onClick={() => onSelectSession(session.session_id)}
                className={`w-full text-left p-3 rounded-lg transition-all duration-200 group ${
                  isSelected
                    ? 'bg-amber-500/10 border border-amber-500/30'
                    : 'bg-slate-800/30 border border-transparent hover:bg-slate-800/50 hover:border-slate-700/50'
                }`}
                style={{
                  animationDelay: `${index * 50}ms`,
                }}
              >
                <div className="flex items-start gap-3">
                  {/* Status Icon */}
                  <div className={`w-7 h-7 rounded-lg ${statusConfig.bg} border ${statusConfig.border} flex items-center justify-center flex-shrink-0 ${statusConfig.color}`}>
                    {statusConfig.icon}
                  </div>

                  {/* Content */}
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium mb-1 line-clamp-2 ${isSelected ? 'text-amber-200' : 'text-slate-200 group-hover:text-slate-100'}`}>
                      {truncateText(session.query_text, 50)}
                    </p>
                    <div className="flex items-center gap-3 text-xs">
                      <span className="text-slate-500">
                        {formatTimeAgo(session.started_at)}
                      </span>
                      {session.processing_time_seconds !== undefined && session.processing_time_seconds !== null && (
                        <>
                          <span className="text-slate-700">·</span>
                          <span className="font-mono text-slate-500">
                            {session.processing_time_seconds.toFixed(1)}s
                          </span>
                        </>
                      )}
                    </div>
                  </div>

                  {/* Arrow indicator for selected */}
                  {isSelected && (
                    <svg className="w-4 h-4 text-amber-400 flex-shrink-0" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5l7 7-7 7" />
                    </svg>
                  )}
                </div>
              </button>
            );
          })}
        </div>
      </div>

      {/* Footer hint */}
      <div className="p-3 border-t border-slate-800/50">
        <p className="text-xs text-slate-600 text-center">
          點擊查看歷史查詢結果
        </p>
      </div>
    </div>
  );
}
