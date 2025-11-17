import { Download, FileText, Shield } from 'lucide-react'
import type { QueryResult } from '../../types/query'

interface ResultsPanelProps {
  result: QueryResult | null
  onExport: () => void
}

function getConfidenceColor(confidence: string) {
  if (confidence.includes('高') || confidence === 'high') {
    return 'bg-green-500'
  } else if (confidence.includes('中') || confidence === 'medium') {
    return 'bg-yellow-500'
  } else {
    return 'bg-red-500'
  }
}

function getConfidenceText(confidence: string) {
  if (confidence.includes('高') || confidence === 'high') {
    return '高信心'
  } else if (confidence.includes('中') || confidence === 'medium') {
    return '中信心'
  } else {
    return '低信心'
  }
}

function formatTime(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(2)}s`
}

function CitationBadge({ id }: { id: number }) {
  return (
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-medium bg-blue-100 text-blue-800">
      引用{id}
    </span>
  )
}

export function ResultsPanel({ result, onExport }: ResultsPanelProps) {
  if (!result) {
    return (
      <div className="bg-white rounded-lg shadow p-6">
        <div className="text-center py-12 text-gray-500">
          <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p>查詢結果將顯示在這裡</p>
        </div>
      </div>
    )
  }

  return (
    <div className="bg-white rounded-lg shadow p-6 space-y-6">
      {/* Header with export button */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold text-gray-900">查詢結果</h3>
        <button
          onClick={onExport}
          className="inline-flex items-center px-3 py-1.5 border border-gray-300 rounded-md text-sm font-medium text-gray-700 bg-white hover:bg-gray-50"
        >
          <Download className="h-4 w-4 mr-2" />
          匯出 JSON
        </button>
      </div>

      {/* Confidence score */}
      <div className="flex items-center space-x-4">
        <div className="flex items-center">
          <Shield className="h-5 w-5 text-gray-500 mr-2" />
          <span className="text-sm font-medium text-gray-700">信心評分:</span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-32 bg-gray-200 rounded-full h-2.5">
            <div
              className={`h-2.5 rounded-full ${getConfidenceColor(result.confidence)}`}
              style={{ width: result.confidence.includes('高') ? '90%' : result.confidence.includes('中') ? '60%' : '30%' }}
            />
          </div>
          <span className="text-sm font-semibold">
            {getConfidenceText(result.confidence)}
          </span>
        </div>
        <span className="text-xs text-gray-500">
          處理時間: {formatTime(result.processing_time_ms)}
        </span>
      </div>

      {/* Executive Summary */}
      <div>
        <h4 className="text-md font-semibold text-gray-800 mb-2">執行摘要</h4>
        <p className="text-gray-700 bg-blue-50 p-4 rounded-md">
          {result.summary}
        </p>
      </div>

      {/* Key Findings */}
      <div>
        <h4 className="text-md font-semibold text-gray-800 mb-2">關鍵發現</h4>
        <ul className="space-y-2">
          {result.key_findings.map((finding, index) => (
            <li key={index} className="flex items-start">
              <span className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-800 rounded-full flex items-center justify-center text-sm font-medium mr-3">
                {index + 1}
              </span>
              <span className="text-gray-700">{finding}</span>
            </li>
          ))}
        </ul>
      </div>

      {/* Detailed Analysis */}
      <div>
        <h4 className="text-md font-semibold text-gray-800 mb-2">詳細分析</h4>
        <div className="prose prose-sm max-w-none text-gray-700 bg-gray-50 p-4 rounded-md whitespace-pre-wrap">
          {result.detailed_analysis}
        </div>
      </div>

      {/* Citations */}
      <div>
        <h4 className="text-md font-semibold text-gray-800 mb-2">
          引用來源 ({result.citations.length})
        </h4>
        <div className="space-y-3">
          {result.citations.map((citation) => (
            <div
              key={citation.id}
              className="border border-gray-200 rounded-md p-3 hover:bg-gray-50"
            >
              <div className="flex items-start justify-between">
                <div className="flex items-center space-x-2">
                  <CitationBadge id={citation.id} />
                  <span className="text-sm font-medium text-gray-900">
                    {citation.source}
                  </span>
                </div>
                <span className="text-xs text-gray-500">
                  {citation.authority}
                </span>
              </div>
              <div className="mt-1 flex items-center space-x-4 text-xs text-gray-500">
                <span>類型: {citation.citation_type}</span>
                {citation.date && <span>日期: {citation.date}</span>}
                {citation.relevance !== undefined && (
                  <span>相關度: {Math.round(citation.relevance * 100)}%</span>
                )}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
