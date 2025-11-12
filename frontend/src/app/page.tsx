'use client'

import { useState } from 'react'
import { submitQuerySync, handleApiError } from '@/lib/api'
import type { Query, LegalAnswer } from '@/lib/types'

export default function Home() {
  const [query, setQuery] = useState<string>('')
  const [loading, setLoading] = useState<boolean>(false)
  const [error, setError] = useState<string>('')
  const [result, setResult] = useState<LegalAnswer | null>(null)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setResult(null)
    setLoading(true)

    const queryObj: Query = {
      text: query,
      max_results: 5,
      include_full_documents: false,
    }

    try {
      const answer = await submitQuerySync(queryObj)
      setResult(answer)
    } catch (err) {
      setError(handleApiError(err))
    } finally {
      setLoading(false)
    }
  }

  return (
    <main className="container mx-auto px-4 py-8 max-w-4xl">
      <div className="text-center mb-8">
        <h1 className="text-4xl font-bold text-gray-800 mb-2">
          法律研究代理系統
        </h1>
        <p className="text-gray-600">
          Legal Research Agent for Taiwan Regulatory Enforcement
        </p>
      </div>

      {/* Query Input Form */}
      <div className="bg-white rounded-lg shadow-md p-6 mb-6">
        <form onSubmit={handleSubmit}>
          <div className="mb-4">
            <label
              htmlFor="query"
              className="block text-sm font-medium text-gray-700 mb-2"
            >
              請輸入您的法律研究查詢 (繁體中文)
            </label>
            <textarea
              id="query"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              placeholder="例如：玉山銀行在2020年因洗錢防制違規受到什麼處分？"
              className="w-full px-4 py-3 border border-gray-300 rounded-md focus:ring-2 focus:ring-blue-500 focus:border-transparent resize-none"
              rows={4}
              required
              disabled={loading}
            />
          </div>

          <button
            type="submit"
            disabled={loading || !query.trim()}
            className="w-full bg-blue-600 text-white py-3 px-6 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors font-medium"
          >
            {loading ? '處理中...' : '提交查詢'}
          </button>
        </form>
      </div>

      {/* Error Message */}
      {error && (
        <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-md mb-6">
          <p className="font-medium">錯誤</p>
          <p>{error}</p>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="bg-white rounded-lg shadow-md p-6">
          {/* Executive Summary */}
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-800 mb-3">執行摘要</h2>
            <p className="text-gray-700 leading-relaxed">{result.executive_summary}</p>
          </div>

          {/* Key Findings */}
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-800 mb-3">關鍵發現</h2>
            <ul className="list-disc list-inside space-y-2">
              {result.key_findings.map((finding, index) => (
                <li key={index} className="text-gray-700">{finding}</li>
              ))}
            </ul>
          </div>

          {/* Detailed Analysis */}
          <div className="mb-6">
            <h2 className="text-xl font-bold text-gray-800 mb-3">詳細分析</h2>
            <p className="text-gray-700 leading-relaxed whitespace-pre-wrap">
              {result.detailed_analysis}
            </p>
          </div>

          {/* Citations */}
          {result.citations.length > 0 && (
            <div className="mb-6">
              <h2 className="text-xl font-bold text-gray-800 mb-3">引用來源</h2>
              <div className="space-y-3">
                {result.citations.map((citation) => (
                  <div
                    key={citation.id}
                    className="border-l-4 border-blue-500 pl-4 py-2 bg-gray-50"
                  >
                    <p className="text-sm font-medium text-gray-600">
                      [引用{citation.id}] {citation.authority === 'primary' ? '主要來源' : '次要來源'}
                    </p>
                    <p className="text-gray-800">{citation.formatted_citation}</p>
                    {citation.url && (
                      <a
                        href={citation.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="text-blue-600 hover:underline text-sm"
                      >
                        查看文件
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* Confidence Score */}
          <div className="border-t pt-4">
            <div className="flex items-center justify-between mb-2">
              <span className="font-medium text-gray-700">信心分數:</span>
              <span className={`px-3 py-1 rounded-full text-sm font-medium ${
                result.confidence_score === '高' ? 'bg-green-100 text-green-800' :
                result.confidence_score === '中' ? 'bg-yellow-100 text-yellow-800' :
                'bg-red-100 text-red-800'
              }`}>
                {result.confidence_score}
              </span>
            </div>
            <p className="text-sm text-gray-600">{result.confidence_explanation}</p>

            {result.processing_time_ms && (
              <p className="text-xs text-gray-500 mt-2">
                處理時間: {result.processing_time_ms}ms
              </p>
            )}
          </div>
        </div>
      )}
    </main>
  )
}
