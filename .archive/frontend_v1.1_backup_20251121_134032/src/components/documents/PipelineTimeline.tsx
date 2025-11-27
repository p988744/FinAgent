import type { PipelineStatusResponse } from '../../types/pipeline';
import { STAGE_CONFIG, STATUS_CONFIG } from '../../types/pipeline';

interface PipelineTimelineProps {
  pipeline: PipelineStatusResponse;
}

export default function PipelineTimeline({ pipeline }: PipelineTimelineProps) {
  const formatDuration = (seconds?: number) => {
    if (seconds === undefined || seconds === null) return '-';
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  return (
    <div className="text-xs text-gray-600 space-y-1">
      {pipeline.total_duration_seconds !== undefined && (
        <div>總時長: {formatDuration(pipeline.total_duration_seconds)}</div>
      )}
      {pipeline.started_at && (
        <div>開始: {new Date(pipeline.started_at).toLocaleString('zh-TW', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}</div>
      )}
      {pipeline.completed_at && (
        <div>完成: {new Date(pipeline.completed_at).toLocaleString('zh-TW', { month: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit', second: '2-digit' })}</div>
      )}
    </div>
  );
}
