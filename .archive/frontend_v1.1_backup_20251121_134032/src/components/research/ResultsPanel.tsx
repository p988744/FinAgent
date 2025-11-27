import { Download, FileText, Shield, Quote, Clock, BookOpen } from 'lucide-react'
import ReactMarkdown from 'react-markdown'
import type { Components } from 'react-markdown'
import type { QueryResult } from '../../types/research'
import clsx from 'clsx'

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
        <button
          onClick={(e) => {
            e.preventDefault()
            onCitationClick?.(citationId)
          }}
          className="inline-flex items-center px-1.5 py-0.5 mx-1 rounded text-[10px] font-bold bg-primary-500/10 text-primary-400 border border-primary-500/20 hover:bg-primary-500/20 transition-colors align-super"
        >
          [{citationId}]
        </button>
      )
    }
    // Regular links
    return (
      <a
        href={href}
        className="text-primary-400 hover:text-primary-300 underline underline-offset-2 decoration-primary-400/30"
        target="_blank"
        rel="noopener noreferrer"
        {...props}
      >
        {children}
      </a>
    )
  },
  p: ({ children }) => <p className="mb-4 last:mb-0 leading-relaxed text-slate-300">{children}</p>,
  h1: ({ children }) => <h1 className="text-2xl font-bold text-white mb-4 mt-6 first:mt-0">{children}</h1>,
  h2: ({ children }) => <h2 className="text-xl font-bold text-white mb-3 mt-5">{children}</h2>,
  h3: ({ children }) => <h3 className="text-lg font-bold text-white mb-2 mt-4">{children}</h3>,
  ul: ({ children }) => <ul className="list-disc list-outside ml-4 mb-4 space-y-1 text-slate-300">{children}</ul>,
  ol: ({ children }) => <ol className="list-decimal list-outside ml-4 mb-4 space-y-1 text-slate-300">{children}</ol>,
  li: ({ children }) => <li className="pl-1">{children}</li>,
  blockquote: ({ children }) => (
    <blockquote className="border-l-4 border-primary-500/50 pl-4 py-1 my-4 bg-slate-800/30 rounded-r italic text-slate-400">
      {children}
    </blockquote>
  ),
  code: ({ className, children, ...props }) => {
    const match = /language-(\w+)/.exec(className || '')
    const isInline = !match
    return isInline ? (
      <code className="px-1.5 py-0.5 rounded bg-slate-800 text-slate-200 text-sm font-mono" {...props}>
        {children}
      </code>
    ) : (
      <div className="rounded-lg overflow-hidden my-4 border border-slate-700 bg-slate-900">
        <div className="px-4 py-2 bg-slate-800/50 border-b border-slate-700 text-xs text-slate-400 font-mono">
          {match?.[1] || 'code'}
        </div>
        <pre className="p-4 overflow-x-auto text-sm text-slate-300 font-mono">
          <code className={className} {...props}>
            {children}
          </code>
        </pre>
      </div>
    )
  }
})

function getConfidenceColor(confidence: string) {
  if (confidence.includes('高') || confidence === 'high') {
    return 'text-success-400 bg-success-500/10 border-success-500/20'
  } else if (confidence.includes('中') || confidence === 'medium') {
    return 'text-warning-400 bg-warning-500/10 border-warning-500/20'
  } else {
    return 'text-red-400 bg-red-500/10 border-red-500/20'
  }
}

function formatTime(ms: number): string {
  if (ms < 1000) {
    return `${ms}ms`
  }
  return `${(ms / 1000).toFixed(2)}s`
}

export function ResultsPanel({ result, onExport }: ResultsPanelProps) {
  if (!result) return null

  // Handler for citation link clicks
  const handleCitationClick = (citationId: number) => {
    const citationElement = document.getElementById(`citation-${citationId}`)
    if (citationElement) {
      citationElement.scrollIntoView({ behavior: 'smooth', block: 'center' })
      // Highlight the citation briefly
      citationElement.classList.add('ring-2', 'ring-primary-500', 'bg-slate-800')
      setTimeout(() => {
        citationElement.classList.remove('ring-2', 'ring-primary-500', 'bg-slate-800')
      }, 2000)
    }
  }

  const markdownComponents = createMarkdownComponents(handleCitationClick)

  return (
    <div className="space-y-6">
      {/* Main Report Card */}
      <div className="glass-card rounded-xl overflow-hidden">
        {/* Header */}
        <div className="relative px-6 py-8 border-b border-slate-700/50 bg-gradient-to-b from-slate-800/50 to-slate-900/50">
          <div className="absolute top-0 left-0 w-full h-1 bg-gradient-to-r from-primary-500 via-accent-500 to-primary-500" />

          <div className="flex items-start justify-between">
            <div>
              <h2 className="text-2xl font-bold text-white tracking-tight">Research Report</h2>
              <div className="flex items-center space-x-4 mt-2 text-sm text-slate-400">
                <div className="flex items-center">
                  <Clock className="w-4 h-4 mr-1.5" />
                  {formatTime(result.processing_time_ms)}
                </div>
                <div className="flex items-center">
                  <BookOpen className="w-4 h-4 mr-1.5" />
                  {result.citations.length} Sources
                </div>
              </div>
            </div>

            <div className="flex items-center space-x-3">
              <div className={clsx(
                "flex items-center space-x-2 px-3 py-1.5 rounded-lg border text-sm font-medium",
                getConfidenceColor(result.confidence)
              )}>
                <Shield className="w-4 h-4" />
                <span>{result.confidence} Confidence</span>
              </div>

              <button
                onClick={onExport}
                className="flex items-center space-x-2 px-4 py-1.5 bg-primary-600 hover:bg-primary-500 text-white rounded-lg transition-colors font-medium shadow-lg shadow-primary-500/20"
              >
                <Download className="w-4 h-4" />
                <span>Export</span>
              </button>
            </div>
          </div>
        </div>

        {/* Content Body */}
        <div className="p-8 space-y-10">
          {/* Executive Summary */}
          <section>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 rounded-lg bg-primary-500/10 text-primary-400">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Executive Summary</h3>
            </div>
            <div className="bg-slate-800/30 rounded-xl p-6 border border-slate-700/50">
              <ReactMarkdown components={markdownComponents}>
                {result.summary}
              </ReactMarkdown>
            </div>
          </section>

          {/* Key Findings */}
          <section>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 rounded-lg bg-accent-500/10 text-accent-400">
                <Shield className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Key Findings</h3>
            </div>
            <div className="grid gap-4">
              {result.key_findings.map((finding, index) => (
                <div key={index} className="flex items-start p-4 rounded-xl bg-slate-800/20 border border-slate-700/50 hover:bg-slate-800/40 transition-colors">
                  <span className="flex-shrink-0 w-6 h-6 rounded-full bg-slate-700 text-slate-300 flex items-center justify-center text-xs font-bold mr-4 mt-0.5">
                    {index + 1}
                  </span>
                  <div className="flex-1">
                    <ReactMarkdown components={markdownComponents}>
                      {finding}
                    </ReactMarkdown>
                  </div>
                </div>
              ))}
            </div>
          </section>

          {/* Detailed Analysis */}
          <section>
            <div className="flex items-center space-x-3 mb-4">
              <div className="p-2 rounded-lg bg-slate-700/50 text-slate-300">
                <FileText className="w-5 h-5" />
              </div>
              <h3 className="text-lg font-bold text-white">Detailed Analysis</h3>
            </div>
            <div className="prose prose-invert prose-slate max-w-none">
              <ReactMarkdown components={markdownComponents}>
                {result.detailed_analysis}
              </ReactMarkdown>
            </div>
          </section>
        </div>
      </div>

      {/* Citations Panel */}
      <div className="glass-card rounded-xl overflow-hidden">
        <div className="px-6 py-4 border-b border-slate-700/50 bg-slate-800/30 flex items-center justify-between">
          <div className="flex items-center space-x-2">
            <Quote className="w-5 h-5 text-slate-400" />
            <h3 className="font-bold text-white">References</h3>
          </div>
          <span className="text-xs font-medium px-2 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
            {result.citations.length} Sources
          </span>
        </div>

        <div className="divide-y divide-slate-800">
          {result.citations.map((citation) => (
            <div
              key={citation.id}
              id={`citation-${citation.id}`}
              className="p-4 hover:bg-slate-800/30 transition-colors scroll-mt-24 group"
            >
              <div className="flex items-start justify-between mb-2">
                <div className="flex items-center space-x-3">
                  <span className="flex-shrink-0 w-6 h-6 rounded bg-slate-800 text-slate-400 border border-slate-700 flex items-center justify-center text-xs font-mono">
                    {citation.id}
                  </span>
                  <h4 className="text-sm font-medium text-primary-400 group-hover:text-primary-300 transition-colors">
                    {citation.source}
                  </h4>
                </div>
                <span className="text-xs font-medium px-2 py-1 rounded bg-slate-800 text-slate-400 border border-slate-700">
                  {citation.authority}
                </span>
              </div>

              <div className="ml-9 space-y-2">
                <div className="flex items-center space-x-4 text-xs text-slate-500">
                  <span>Type: <span className="text-slate-400">{citation.citation_type}</span></span>
                  {citation.date && (
                    <span>Date: <span className="text-slate-400">{citation.date}</span></span>
                  )}
                  {citation.relevance !== undefined && (
                    <span className={clsx(
                      "font-medium",
                      citation.relevance > 0.8 ? "text-success-400" : "text-warning-400"
                    )}>
                      {Math.round(citation.relevance * 100)}% Relevant
                    </span>
                  )}
                </div>

                {/* Snippet (optional, if available in data) */}
                {/* <p className="text-sm text-slate-400 line-clamp-2 pl-3 border-l-2 border-slate-700">
                  Snippet text here...
                </p> */}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
