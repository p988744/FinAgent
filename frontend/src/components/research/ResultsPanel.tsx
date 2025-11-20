import { Download, FileText, Shield } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'
import type { QueryResult } from '../../types/query'

interface ResultsPanelProps {
  result: QueryResult | null
  onExport: () => void
}

// Custom markdown components for citation links
const createMarkdownComponents = (onCitationClick?: (id: number) => void): Components => ({
  a: ({ node, href, children, ...props }) => {
    // Check if this is a citation link (e.g., #cite-1)
    if (href?.startsWith('#cite-')) {
      const citationId = parseInt(href.replace('#cite-', ''), 10)
      return (
        <a
          href={href}
          onClick={(e) => {
            e.preventDefault()
            onCitationClick?.(citationId)
          }}
          className="inline-flex items-center px-1.5 py-0.5 rounded text-xs font-semibold bg-navy-100 text-navy-900 border border-navy-200 hover:bg-navy-200 transition-colors cursor-pointer no-underline"
          {...props}
        >
          引用{citationId}
        </a>
      )
    }
    // Regular links
    return (
      <a href={href} className="text-blue-600 hover:text-blue-800 underline" target="_blank" rel="noopener noreferrer" {...props}>
        {children}
      </a>
    )
  },
})

function getConfidenceColor(confidence: string) {
  if (confidence.includes('高') || confidence === 'high') {
    return 'bg-success-600'
  } else if (confidence.includes('中') || confidence === 'medium') {
    return 'bg-warning-500'
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
    <span className="inline-flex items-center px-2 py-0.5 rounded text-xs font-semibold bg-navy-100 text-navy-900 border border-navy-200">
      引用{id}
    </span>
  )
}

export function ResultsPanel({ result, onExport }: ResultsPanelProps) {
  if (!result) {
    return (
      <div className="bg-white rounded-lg shadow-md border border-gray-200 p-6">
        <div className="text-center py-12 text-gray-500">
          <FileText className="h-12 w-12 mx-auto mb-4 text-gray-400" />
          <p className="font-medium">查詢結果將顯示在這裡</p>
        </div>
      </div>
    )
  }

  // Handler for citation link clicks
  const handleCitationClick = (citationId: number) => {
    const citationElement = document.getElementById(`citation-${citationId}`)
    if (citationElement) {
      citationElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // Highlight the citation briefly
      citationElement.classList.add('ring-2', 'ring-navy-500')
      setTimeout(() => {
        citationElement.classList.remove('ring-2', 'ring-navy-500')
      }, 2000)
    }
  }

  const markdownComponents = createMarkdownComponents(handleCitationClick)

  return (
    <div className="bg-white rounded-lg shadow border border-gray-200">
      {/* Professional Report Header */}
      <div className="bg-gradient-to-r from-navy-700 to-navy-800 px-6 py-4 rounded-t-lg">
        <div className="flex items-center justify-between">
          <div>
            <h3 className="text-lg font-bold text-white">研究報告</h3>
            <p className="text-navy-100 text-xs mt-0.5">Legal Research Report</p>
          </div>
          <div className="flex items-center space-x-3">
            {/* Confidence Badge */}
            <div className="flex items-center space-x-2 bg-white/10 backdrop-blur-sm px-3 py-1.5 rounded-lg border border-white/20">
              <Shield className="h-4 w-4 text-white" />
              <span className="text-white text-sm font-semibold">{getConfidenceText(result.confidence)}</span>
            </div>
            {/* Export Button */}
            <button
              onClick={onExport}
              className="inline-flex items-center px-3 py-1.5 bg-white/10 backdrop-blur-sm border border-white/20 rounded-lg text-xs font-semibold text-white hover:bg-white/20 transition-colors"
            >
              <Download className="h-3.5 w-3.5 mr-1.5" />
              匯出
            </button>
          </div>
        </div>
      </div>

      {/* Report Metadata Bar */}
      <div className="bg-gray-50 px-6 py-2 border-b border-gray-200 flex items-center justify-between text-xs">
        <div className="flex items-center space-x-4 text-gray-600">
          <span>處理時間: <span className="font-semibold text-gray-900">{formatTime(result.processing_time_ms)}</span></span>
          <span className="text-gray-300">|</span>
          <span>引用來源: <span className="font-semibold text-gray-900">{result.citations.length} 筆</span></span>
        </div>
        <div className="flex items-center space-x-2">
          <div className="w-20 bg-gray-200 rounded-full h-1.5">
            <div
              className={`h-1.5 rounded-full ${getConfidenceColor(result.confidence)}`}
              style={{ width: result.confidence.includes('高') ? '90%' : result.confidence.includes('中') ? '60%' : '30%' }}
            />
          </div>
        </div>
      </div>

      {/* Report Body */}
      <div className="px-6 py-5 space-y-6">
        {/* Final Answer Section */}
        <section>
          <div className="flex items-center space-x-2 mb-3">
            <div className="w-1 h-5 bg-navy-700 rounded-full"></div>
            <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">最終答案</h4>
          </div>
          <div className="text-sm text-gray-900 bg-gray-50 p-4 rounded-lg border border-gray-200 leading-relaxed prose prose-sm max-w-none">
            <ReactMarkdown components={markdownComponents}>{result.detailed_analysis}</ReactMarkdown>
          </div>
        </section>

        {/* Executive Summary Section */}
        <section>
          <div className="flex items-center space-x-2 mb-3">
            <div className="w-1 h-5 bg-navy-700 rounded-full"></div>
            <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">執行摘要</h4>
          </div>
          <div className="text-sm text-gray-900 bg-blue-50 p-4 rounded-lg border border-blue-200 leading-relaxed prose prose-sm max-w-none">
            <ReactMarkdown components={markdownComponents}>{result.summary}</ReactMarkdown>
          </div>
        </section>

        {/* Key Findings Section */}
        <section>
          <div className="flex items-center space-x-2 mb-3">
            <div className="w-1 h-5 bg-navy-700 rounded-full"></div>
            <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">關鍵發現</h4>
          </div>
          <div className="space-y-3">
            {result.key_findings.map((finding, index) => (
              <div key={index} className="flex items-start bg-white border border-gray-200 rounded-lg p-3 hover:border-navy-300 transition-colors">
                <span className="flex-shrink-0 w-6 h-6 bg-navy-700 text-white rounded-full flex items-center justify-center text-xs font-bold mr-3 mt-0.5">
                  {index + 1}
                </span>
                <div className="text-sm text-gray-900 leading-relaxed prose prose-sm max-w-none flex-1">
                  <ReactMarkdown components={markdownComponents}>{finding}</ReactMarkdown>
                </div>
              </div>
            ))}
          </div>
        </section>

        {/* Citations Section */}
        <section>
          <div className="flex items-center space-x-2 mb-3">
            <div className="w-1 h-5 bg-navy-700 rounded-full"></div>
            <h4 className="text-sm font-bold text-gray-900 uppercase tracking-wide">引用來源</h4>
            <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded">
              {result.citations.length} 筆
            </span>
          </div>
          <div className="space-y-2">
            {result.citations.map((citation) => (
              <div
                key={citation.id}
                id={`citation-${citation.id}`}
                className="border border-gray-200 rounded-lg p-3 hover:bg-gray-50 hover:border-navy-300 transition-all bg-white scroll-mt-4"
              >
                <div className="flex items-start justify-between mb-2">
                  <div className="flex items-center space-x-2">
                    <CitationBadge id={citation.id} />
                    <span className="text-sm font-semibold text-gray-900">
                      {citation.source}
                    </span>
                  </div>
                  <span className="text-xs text-gray-600 bg-gray-100 px-2 py-0.5 rounded font-medium">
                    {citation.authority}
                  </span>
                </div>
                <div className="flex items-center space-x-3 text-xs">
                  <span className="text-gray-600">
                    <span className="font-medium text-gray-700">類型:</span> {citation.citation_type}
                  </span>
                  {citation.date && (
                    <>
                      <span className="text-gray-300">•</span>
                      <span className="text-gray-600">
                        <span className="font-medium text-gray-700">日期:</span> {citation.date}
                      </span>
                    </>
                  )}
                  {citation.relevance !== undefined && (
                    <>
                      <span className="text-gray-300">•</span>
                      <span className="bg-green-100 text-green-800 px-2 py-0.5 rounded border border-green-200 font-medium">
                        相關度 {Math.round(citation.relevance * 100)}%
                      </span>
                    </>
                  )}
                </div>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  )
}
