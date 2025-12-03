/**
 * QuerySubmitCard Component
 *
 * Hero query input with command-center aesthetic
 */

import React, { useState } from 'react';

interface QuerySubmitCardProps {
  onSubmit: (queryText: string) => void;
  isSubmitting: boolean;
}

const EXAMPLE_QUERIES = [
  '玉山銀行洗錢防制裁罰',
  '2020年金管會裁罰案件',
  '中信銀行內線交易案例',
  '國泰世華資訊揭露違規',
];

export function QuerySubmitCard({ onSubmit, isSubmitting }: QuerySubmitCardProps) {
  const [queryText, setQueryText] = useState('');
  const [isFocused, setIsFocused] = useState(false);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (queryText.trim()) {
      onSubmit(queryText.trim());
    }
  };

  const handleExampleClick = (example: string) => {
    setQueryText(example);
  };

  const charCount = queryText.length;

  return (
    <div className={`card p-6 transition-all duration-300 ${isFocused ? 'border-amber-500/30 shadow-glow-amber' : ''}`}>
      {/* Header */}
      <div className="flex items-center gap-3 mb-5">
        <div className="w-10 h-10 rounded-xl bg-amber-500/10 flex items-center justify-center">
          <svg className="w-5 h-5 text-amber-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M21 21l-6-6m2-5a7 7 0 11-14 0 7 7 0 0114 0z" />
          </svg>
        </div>
        <div>
          <h2 className="text-lg font-serif font-semibold text-slate-100">研究查詢</h2>
          <p className="text-xs text-slate-500">輸入您的金融法律研究問題</p>
        </div>
      </div>

      <form onSubmit={handleSubmit}>
        {/* Query Input */}
        <div className="relative mb-4">
          <textarea
            id="query"
            value={queryText}
            onChange={(e) => setQueryText(e.target.value)}
            onFocus={() => setIsFocused(true)}
            onBlur={() => setIsFocused(false)}
            placeholder="例如：玉山銀行洗錢防制裁罰案例分析"
            className="input input-textarea font-sans text-base leading-relaxed"
            rows={4}
            disabled={isSubmitting}
          />
          <div className="absolute bottom-3 right-3 flex items-center gap-2">
            <span className={`text-xs transition-colors ${charCount > 0 ? 'text-slate-400' : 'text-slate-600'}`}>
              {charCount} 字元
            </span>
          </div>
        </div>

        {/* Example Queries */}
        <div className="mb-5">
          <div className="flex items-center gap-2 mb-3">
            <svg className="w-4 h-4 text-slate-500" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M13 10V3L4 14h7v7l9-11h-7z" />
            </svg>
            <span className="text-xs text-slate-500 uppercase tracking-wider">快速範例</span>
          </div>
          <div className="flex flex-wrap gap-2">
            {EXAMPLE_QUERIES.map((example, index) => (
              <button
                key={index}
                type="button"
                onClick={() => handleExampleClick(example)}
                className="group px-3 py-1.5 text-sm bg-slate-800/50 hover:bg-slate-800 rounded-lg text-slate-400 hover:text-slate-200 border border-slate-700/50 hover:border-slate-600 transition-all duration-200"
                disabled={isSubmitting}
              >
                <span className="group-hover:text-amber-400 transition-colors">#</span> {example}
              </button>
            ))}
          </div>
        </div>

        {/* Submit Button */}
        <button
          type="submit"
          disabled={isSubmitting || !queryText.trim()}
          className="btn btn-primary w-full text-base font-semibold disabled:opacity-50 disabled:cursor-not-allowed disabled:shadow-none"
        >
          {isSubmitting ? (
            <>
              <svg className="w-5 h-5 animate-spin" fill="none" viewBox="0 0 24 24">
                <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z" />
              </svg>
              處理中...
            </>
          ) : (
            <>
              <svg className="w-5 h-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M14 5l7 7m0 0l-7 7m7-7H3" />
              </svg>
              開始研究
            </>
          )}
        </button>
      </form>

      {/* Bottom hint */}
      <p className="text-xs text-slate-600 text-center mt-4">
        按下 Enter 或點擊按鈕提交查詢
      </p>
    </div>
  );
}
