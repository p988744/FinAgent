import { useState, useEffect } from 'react';
import type { PipelineStatusResponse } from '../../types/pipeline';
import PipelineProgress from './PipelineProgress';
import PipelineTimeline from './PipelineTimeline';
import PipelineLogs from './PipelineLogs';

interface PipelineModalProps {
  docId: string | null;
  filename: string;
  isOpen: boolean;
  onClose: () => void;
}

const API_BASE = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export default function PipelineModal({ docId, filename, isOpen, onClose }: PipelineModalProps) {
  const [pipeline, setPipeline] = useState<PipelineStatusResponse | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [autoRefresh, setAutoRefresh] = useState(true);

  useEffect(() => {
    if (!isOpen || !docId) return;

    const fetchPipeline = async () => {
      try {
        setLoading(true);
        setError(null);
        const response = await fetch(`${API_BASE}/api/v1/documents/${docId}/pipeline`);

        if (!response.ok) {
          throw new Error(`Failed to fetch pipeline: ${response.statusText}`);
        }

        const data = await response.json();
        setPipeline(data);

        // Stop auto-refresh if pipeline is complete or failed
        if (data.overall_status === 'success' || data.overall_status === 'failed') {
          setAutoRefresh(false);
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Failed to load pipeline status');
      } finally {
        setLoading(false);
      }
    };

    fetchPipeline();

    // Auto-refresh every 2 seconds if still in progress
    const interval = autoRefresh
      ? setInterval(fetchPipeline, 2000)
      : undefined;

    return () => {
      if (interval) clearInterval(interval);
    };
  }, [docId, isOpen, autoRefresh]);

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 backdrop-blur-sm bg-black/30 flex items-center justify-center z-50 p-4">
      <div className="bg-white rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-hidden flex flex-col">
        {/* Header */}
        <div className="px-4 py-3 border-b flex items-center justify-between">
          <div className="flex-1 min-w-0 mr-3">
            <h2 className="text-lg font-semibold text-gray-900">處理進度</h2>
            <p className="text-xs text-gray-600 truncate">{filename}</p>
          </div>
          <button
            onClick={onClose}
            className="text-gray-400 hover:text-gray-600 transition-colors flex-shrink-0"
          >
            <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
            </svg>
          </button>
        </div>

        {/* Content */}
        <div className="flex-1 overflow-y-auto p-4">
          {loading && !pipeline && (
            <div className="flex items-center justify-center py-8">
              <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600" />
            </div>
          )}

          {error && (
            <div className="bg-red-50 border border-red-200 rounded-lg p-3 text-red-700">
              <p className="font-medium text-sm">載入失敗</p>
              <p className="text-xs mt-1">{error}</p>
            </div>
          )}

          {pipeline && (
            <div className="space-y-3">
              {/* Progress with stage details */}
              <div className="bg-gray-50 rounded-lg p-3">
                <PipelineProgress pipeline={pipeline} />
              </div>

              {/* Simple timeline info */}
              <div className="px-2">
                <PipelineTimeline pipeline={pipeline} />
              </div>

              {/* Processing logs */}
              <PipelineLogs stages={pipeline.stages} />

              {/* Auto-refresh indicator */}
              {autoRefresh && pipeline.overall_status === 'in_progress' && (
                <div className="flex items-center justify-center gap-2 text-xs text-gray-500">
                  <div className="animate-pulse w-1.5 h-1.5 bg-blue-500 rounded-full" />
                  <span>自動更新中...</span>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Footer */}
        <div className="px-4 py-2 border-t bg-gray-50 flex items-center justify-between">
          <div className="text-xs text-gray-600">
            {pipeline?.started_at && (
              <span>開始: {new Date(pipeline.started_at).toLocaleString('zh-TW', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })}</span>
            )}
          </div>
          <button
            onClick={onClose}
            className="px-3 py-1.5 text-sm bg-blue-600 text-white rounded hover:bg-blue-700 transition-colors"
          >
            關閉
          </button>
        </div>
      </div>
    </div>
  );
}
