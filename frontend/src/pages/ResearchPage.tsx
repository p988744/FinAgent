/**
 * ResearchPage - Main research interface (v2.0 Chat-based)
 */

import { ChatInterface } from '../components/chat';
import { useResearch } from '../hooks/useResearch';

export function ResearchPage() {
  const { messages, isLoading, sendMessage, clearMessages } = useResearch();

  return (
    <div className="page-container bg-noir-950">
      {/* Header */}
      <header className="sticky top-0 z-50 glass-dark border-b border-noir-800/50">
        <div className="content-container py-3">
          <div className="flex items-center justify-between">
            {/* Logo */}
            <div className="flex items-center gap-3">
              <div className="w-8 h-8 rounded-lg bg-gradient-to-br from-brass-500 to-brass-700 flex items-center justify-center">
                <svg className="w-4 h-4 text-noir-950" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 15.5m14.8-.2l.2.2v1.561c0 1.115-.763 2.083-1.849 2.353l-.294.074A24.282 24.282 0 0112 20.25a24.282 24.282 0 01-5.857-.513l-.294-.074A2.25 2.25 0 014 17.561V15.5M19.8 15.3v-2.95" />
                </svg>
              </div>
              <div>
                <h1 className="text-sm font-display font-semibold text-noir-100">
                  FinAgent
                </h1>
                <p className="text-2xs text-noir-500">金融法律研究助手</p>
              </div>
            </div>

            {/* Actions */}
            <div className="flex items-center gap-2">
              {messages.length > 0 && (
                <button
                  onClick={clearMessages}
                  className="btn btn-ghost btn-sm"
                >
                  <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                  </svg>
                  新對話
                </button>
              )}
              <button className="btn btn-ghost btn-icon btn-sm">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6.253v13m0-13C10.832 5.477 9.246 5 7.5 5S4.168 5.477 3 6.253v13C4.168 18.477 5.754 18 7.5 18s3.332.477 4.5 1.253m0-13C13.168 5.477 14.754 5 16.5 5c1.747 0 3.332.477 4.5 1.253v13C19.832 18.477 18.247 18 16.5 18c-1.746 0-3.332.477-4.5 1.253" />
                </svg>
              </button>
              <button className="btn btn-ghost btn-icon btn-sm">
                <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M10.325 4.317c.426-1.756 2.924-1.756 3.35 0a1.724 1.724 0 002.573 1.066c1.543-.94 3.31.826 2.37 2.37a1.724 1.724 0 001.065 2.572c1.756.426 1.756 2.924 0 3.35a1.724 1.724 0 00-1.066 2.573c.94 1.543-.826 3.31-2.37 2.37a1.724 1.724 0 00-2.572 1.065c-.426 1.756-2.924 1.756-3.35 0a1.724 1.724 0 00-2.573-1.066c-1.543.94-3.31-.826-2.37-2.37a1.724 1.724 0 00-1.065-2.572c-1.756-.426-1.756-2.924 0-3.35a1.724 1.724 0 001.066-2.573c-.94-1.543.826-3.31 2.37-2.37.996.608 2.296.07 2.572-1.065z" />
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
                </svg>
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="flex-1 overflow-hidden">
        <ChatInterface
          messages={messages}
          onSendMessage={sendMessage}
          isLoading={isLoading}
        />
      </main>
    </div>
  );
}
