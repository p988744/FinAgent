/**
 * ResearchPage - Main research interface (v2.0 Chat-based)
 */

import { ChatInterface } from '../components/chat';
import { useResearch } from '../hooks/useResearch';

export function ResearchPage() {
  const { messages, isLoading, sendMessage, clearMessages } = useResearch();

  return (
    <div className="h-[calc(100vh-3.5rem)] flex flex-col bg-noir-950">
      {/* Sub-header with actions */}
      <div className="flex-shrink-0 px-6 py-2 border-b border-noir-800/50 bg-noir-900/50">
        <div className="max-w-4xl mx-auto flex items-center justify-between">
          <span className="text-xs text-noir-500">金融法律研究助手</span>
          <div className="flex items-center gap-2">
            {messages.length > 0 && (
              <button
                onClick={clearMessages}
                className="flex items-center gap-1.5 px-3 py-1.5 text-xs text-noir-400 hover:text-noir-200 hover:bg-noir-800 rounded-lg transition-all"
              >
                <svg className="w-3.5 h-3.5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 6v6m0 0v6m0-6h6m-6 0H6" />
                </svg>
                新對話
              </button>
            )}
          </div>
        </div>
      </div>

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
