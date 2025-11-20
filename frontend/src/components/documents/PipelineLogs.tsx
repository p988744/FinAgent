import { useState } from 'react';
import type { PipelineStageInfo } from '../../types/pipeline';

interface LogEntry {
  timestamp: string;
  level: string;
  message: string;
}

interface PipelineLogsProps {
  stages: PipelineStageInfo[];
}

const LOG_LEVEL_STYLES = {
  INFO: 'text-blue-600 bg-blue-50',
  WARNING: 'text-yellow-600 bg-yellow-50',
  ERROR: 'text-red-600 bg-red-50',
  DEBUG: 'text-gray-600 bg-gray-50',
} as const;

const LOG_LEVEL_ICONS = {
  INFO: 'ℹ️',
  WARNING: '⚠️',
  ERROR: '❌',
  DEBUG: '🔍',
} as const;

export default function PipelineLogs({ stages }: PipelineLogsProps) {
  const [isExpanded, setIsExpanded] = useState(false);

  // Collect all logs from all stages
  const allLogs: LogEntry[] = [];
  for (const stage of stages) {
    if (stage.details?.logs && Array.isArray(stage.details.logs)) {
      allLogs.push(...stage.details.logs);
    }
  }

  // Sort by timestamp
  allLogs.sort((a, b) => a.timestamp.localeCompare(b.timestamp));

  if (allLogs.length === 0) {
    return null; // Don't show logs section if no logs
  }

  return (
    <div className="border border-gray-200 rounded-lg overflow-hidden">
      {/* Header */}
      <button
        onClick={() => setIsExpanded(!isExpanded)}
        className="w-full px-3 py-2 bg-gray-50 hover:bg-gray-100 transition-colors flex items-center justify-between text-sm"
      >
        <div className="flex items-center gap-2">
          <span className="text-gray-600">📋</span>
          <span className="font-medium text-gray-700">處理日誌</span>
          <span className="text-xs text-gray-500">({allLogs.length} 條記錄)</span>
        </div>
        <svg
          className={`w-4 h-4 text-gray-500 transition-transform ${isExpanded ? 'rotate-180' : ''}`}
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
        >
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 9l-7 7-7-7" />
        </svg>
      </button>

      {/* Logs content */}
      {isExpanded && (
        <div className="max-h-64 overflow-y-auto bg-white">
          <div className="divide-y divide-gray-100">
            {allLogs.map((log, index) => {
              const level = (log.level as keyof typeof LOG_LEVEL_STYLES) || 'INFO';
              const levelStyle = LOG_LEVEL_STYLES[level] || LOG_LEVEL_STYLES.INFO;
              const levelIcon = LOG_LEVEL_ICONS[level] || LOG_LEVEL_ICONS.INFO;

              return (
                <div key={index} className="px-3 py-2 hover:bg-gray-50 transition-colors">
                  <div className="flex items-start gap-2">
                    {/* Icon and level badge */}
                    <div className="flex-shrink-0 flex items-center gap-1.5">
                      <span className="text-sm">{levelIcon}</span>
                      <span className={`px-1.5 py-0.5 text-xs font-medium rounded ${levelStyle}`}>
                        {level}
                      </span>
                    </div>

                    {/* Log message */}
                    <div className="flex-1 min-w-0">
                      <p className="text-sm text-gray-800 break-words">{log.message}</p>
                      <p className="text-xs text-gray-500 mt-0.5">
                        {new Date(log.timestamp).toLocaleString('zh-TW', {
                          month: 'short',
                          day: 'numeric',
                          hour: '2-digit',
                          minute: '2-digit',
                          second: '2-digit',
                        })}
                      </p>
                    </div>
                  </div>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
