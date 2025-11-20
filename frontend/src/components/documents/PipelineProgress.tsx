import type { PipelineStatusResponse } from '../../types/pipeline';
import { STAGE_CONFIG, STATUS_CONFIG } from '../../types/pipeline';

interface PipelineProgressProps {
  pipeline: PipelineStatusResponse;
  compact?: boolean;
}

export default function PipelineProgress({ pipeline, compact = false }: PipelineProgressProps) {
  const { current_stage, overall_status, progress_percentage, stages } = pipeline;

  const formatDuration = (seconds?: number) => {
    if (seconds === undefined || seconds === null) return '-';
    if (seconds < 1) return `${Math.round(seconds * 1000)}ms`;
    if (seconds < 60) return `${seconds.toFixed(1)}s`;
    const mins = Math.floor(seconds / 60);
    const secs = Math.floor(seconds % 60);
    return `${mins}m ${secs}s`;
  };

  // Status icon mapping
  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'success':
        return '✅';
      case 'in_progress':
        return '⏳';
      case 'failed':
        return '❌';
      case 'skipped':
        return '⏭️';
      default:
        return '⏸️';
    }
  };

  if (compact) {
    return (
      <div className="flex items-center gap-2">
        <div className="flex-1 bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              overall_status === 'failed'
                ? 'bg-red-500'
                : overall_status === 'success'
                  ? 'bg-green-500'
                  : 'bg-blue-500'
            }`}
            style={{ width: `${progress_percentage}%` }}
          />
        </div>
        <span className="text-xs text-gray-600 min-w-[3rem]">{Math.round(progress_percentage)}%</span>
      </div>
    );
  }

  // Full view: show detailed stage list with timing
  return (
    <div className="space-y-2">
      {/* Progress bar */}
      <div className="relative">
        <div className="w-full bg-gray-200 rounded-full h-2">
          <div
            className={`h-2 rounded-full transition-all duration-300 ${
              overall_status === 'failed'
                ? 'bg-red-500'
                : overall_status === 'success'
                  ? 'bg-green-500'
                  : 'bg-blue-500'
            }`}
            style={{ width: `${progress_percentage}%` }}
          />
        </div>
        <div className="flex justify-between mt-1 text-xs text-gray-600">
          <span className="font-medium">{Math.round(progress_percentage)}%</span>
          <span
            className={`px-2 py-0.5 rounded-full text-xs font-medium ${
              STATUS_CONFIG[overall_status]?.color || 'text-gray-600'
            } ${STATUS_CONFIG[overall_status]?.bgColor || 'bg-gray-100'}`}
          >
            {STATUS_CONFIG[overall_status]?.label || overall_status}
          </span>
        </div>
      </div>

      {/* Stage list with timing */}
      {stages.length > 0 && (
        <div className="space-y-1 mt-3">
          {stages.map((stage, index) => {
            const config = STAGE_CONFIG[stage.stage];
            const isActive = stage.stage === current_stage;

            return (
              <div
                key={index}
                className={`flex items-center justify-between text-xs py-1 px-2 rounded ${
                  isActive ? 'bg-blue-50' : ''
                }`}
              >
                <div className="flex items-center gap-2">
                  <span>{getStatusIcon(stage.status)}</span>
                  <span className={`${isActive ? 'font-medium text-blue-700' : 'text-gray-700'}`}>
                    {config?.label || stage.stage}
                  </span>
                </div>
                <span className="text-gray-500">{formatDuration(stage.duration)}</span>
              </div>
            );
          })}
        </div>
      )}

      {/* Fallback if no stages */}
      {stages.length === 0 && (
        <div className="text-xs text-gray-500 text-center py-2">
          {STAGE_CONFIG[current_stage]?.description || current_stage}
        </div>
      )}
    </div>
  );
}
