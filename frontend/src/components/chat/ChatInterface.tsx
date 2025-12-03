/**
 * ChatInterface - Main chat interface component
 * Combines messages list, input, and citation panel
 */

import { useRef, useEffect, useState } from 'react';
import type { Message, Citation } from '../../types';
import { ChatMessage } from './ChatMessage';
import { ChatInput } from './ChatInput';
import { CitationPanel } from './CitationPanel';

interface ChatInterfaceProps {
  messages: Message[];
  onSendMessage: (content: string) => void;
  isLoading?: boolean;
  showCitationPanel?: boolean;
}

export function ChatInterface({
  messages,
  onSendMessage,
  isLoading = false,
  showCitationPanel = false,
}: ChatInterfaceProps) {
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const [activeCitation, setActiveCitation] = useState<string | undefined>();
  const [isPanelOpen, setIsPanelOpen] = useState(showCitationPanel);

  // Get all citations from messages
  const allCitations = messages
    .filter(m => m.role === 'assistant' && m.citations)
    .flatMap(m => m.citations || []);

  // Auto-scroll to bottom on new messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleCitationClick = (citation: Citation) => {
    setActiveCitation(citation.id);
    setIsPanelOpen(true);
  };

  return (
    <div className="flex h-full">
      {/* Main Chat Area */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Messages */}
        <div className="flex-1 overflow-y-auto scrollbar-thin">
          <div className="chat-container py-6">
            {messages.length === 0 ? (
              <WelcomeScreen onExampleClick={onSendMessage} />
            ) : (
              <div className="chat-messages">
                {messages.map((message) => (
                  <ChatMessage
                    key={message.id}
                    message={message}
                    onCitationClick={handleCitationClick}
                  />
                ))}
                <div ref={messagesEndRef} />
              </div>
            )}
          </div>
        </div>

        {/* Input */}
        <ChatInput
          onSend={onSendMessage}
          isLoading={isLoading}
          disabled={isLoading}
        />
      </div>

      {/* Citation Panel */}
      {isPanelOpen && allCitations.length > 0 && (
        <CitationPanel
          citations={allCitations}
          activeCitation={activeCitation}
          onCitationClick={(c) => setActiveCitation(c.id)}
          onClose={() => setIsPanelOpen(false)}
        />
      )}

      {/* Toggle Citation Panel Button */}
      {allCitations.length > 0 && !isPanelOpen && (
        <button
          onClick={() => setIsPanelOpen(true)}
          className="fixed right-4 bottom-24 btn btn-secondary shadow-float"
        >
          <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <span>引用 ({allCitations.length})</span>
        </button>
      )}
    </div>
  );
}

/**
 * Welcome screen shown when there are no messages
 */
interface WelcomeScreenProps {
  onExampleClick: (content: string) => void;
}

function WelcomeScreen({ onExampleClick }: WelcomeScreenProps) {
  const examples = [
    '玉山銀行 2020 年洗錢防制裁罰案例分析',
    '金管會近年對銀行資安缺失的裁罰趨勢',
    '保險業違反個資法的裁罰案例有哪些？',
    '比較各銀行內控缺失的裁罰金額',
  ];

  return (
    <div className="flex flex-col items-center justify-center min-h-[60vh] px-6">
      {/* Logo/Title */}
      <div className="text-center mb-12">
        <div className="w-16 h-16 mx-auto mb-6 rounded-2xl bg-gradient-to-br from-brass-500 to-brass-700 flex items-center justify-center shadow-glow-brass">
          <svg className="w-8 h-8 text-noir-950" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 15.5m14.8-.2l.2.2v1.561c0 1.115-.763 2.083-1.849 2.353l-.294.074A24.282 24.282 0 0112 20.25a24.282 24.282 0 01-5.857-.513l-.294-.074A2.25 2.25 0 014 17.561V15.5M19.8 15.3v-2.95" />
          </svg>
        </div>
        <h1 className="text-3xl font-display font-semibold text-noir-100 mb-3">
          FinAgent
        </h1>
        <p className="text-noir-400 max-w-md mx-auto">
          專精台灣金融法律研究的 AI 助手，協助您分析金管會裁罰案例、法規解讀與判決書研究
        </p>
      </div>

      {/* Example Queries */}
      <div className="w-full max-w-2xl">
        <p className="text-xs text-noir-500 uppercase tracking-wider mb-4 text-center">
          試試這些問題
        </p>
        <div className="grid grid-cols-1 sm:grid-cols-2 gap-3">
          {examples.map((example, index) => (
            <button
              key={index}
              onClick={() => onExampleClick(example)}
              className="card card-interactive p-4 text-left group"
            >
              <div className="flex items-start gap-3">
                <div className="w-6 h-6 rounded-lg bg-brass-500/10 flex items-center justify-center flex-shrink-0 mt-0.5 group-hover:bg-brass-500/20 transition-colors">
                  <svg className="w-3.5 h-3.5 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8.228 9c.549-1.165 2.03-2 3.772-2 2.21 0 4 1.343 4 3 0 1.4-1.278 2.575-3.006 2.907-.542.104-.994.54-.994 1.093m0 3h.01M21 12a9 9 0 11-18 0 9 9 0 0118 0z" />
                  </svg>
                </div>
                <span className="text-sm text-noir-300 group-hover:text-noir-100 transition-colors">
                  {example}
                </span>
              </div>
            </button>
          ))}
        </div>
      </div>

      {/* Features */}
      <div className="mt-12 flex items-center gap-6 text-2xs text-noir-500">
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-jade-500" />
          即時思考流程
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-brass-500" />
          引用來源追蹤
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-1.5 h-1.5 rounded-full bg-azure-500" />
          多代理協作
        </span>
      </div>
    </div>
  );
}
