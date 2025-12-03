import ReactMarkdown from 'react-markdown'
import type { QueryResult } from '../types'

interface ResultsDisplayProps {
    results: QueryResult | null
}

export function ResultsDisplay({ results }: ResultsDisplayProps) {
    if (!results) return null

    return (
        <div className="bg-white rounded-lg shadow p-6">
            <h3 className="text-xl font-bold mb-4">Research Results</h3>

            {results.confidence !== undefined && (
                <div className="mb-4">
                    <span className="inline-block px-3 py-1 bg-blue-100 text-blue-800 rounded-full text-sm">
                        Confidence: {Math.round(results.confidence * 100)}%
                    </span>
                </div>
            )}

            <div className="prose max-w-none mb-6">
                <ReactMarkdown>{results.answer}</ReactMarkdown>
            </div>

            {results.references && results.references.length > 0 && (
                <div className="border-t pt-4">
                    <h4 className="font-bold mb-3">References</h4>
                    <div className="space-y-2">
                        {results.references.map((ref, idx) => (
                            <div key={idx} className="p-3 bg-gray-50 rounded text-sm">
                                <div className="font-medium mb-1">
                                    [{idx + 1}] {ref.title || `Document ${ref.doc_id}`}
                                </div>
                                {ref.score !== undefined && (
                                    <div className="text-xs text-gray-600 mb-1">
                                        Relevance: {Math.round(ref.score * 100)}%
                                    </div>
                                )}
                                <div className="text-gray-700 line-clamp-3">
                                    {ref.content}
                                </div>
                            </div>
                        ))}
                    </div>
                </div>
            )}
        </div>
    )
}
