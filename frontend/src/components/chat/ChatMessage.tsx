/**
 * ChatMessage - Individual message bubble in the chat interface
 */

import ReactMarkdown from 'react-markdown';
import type { Message, Citation } from '../../types';
import { ThinkingProcess } from './ThinkingProcess';
import { CitationInline } from './CitationInline';

interface ChatMessageProps {
  message: Message;
  onCitationClick?: (citation: Citation) => void;
}

export function ChatMessage({ message, onCitationClick }: ChatMessageProps) {
  const isUser = message.role === 'user';
  const isThinking = message.status === 'thinking';

  // Parse content for inline citations [引用1] or [1]
  const renderContent = (content: string, citations?: Citation[]) => {
    // If no citations, render with markdown
    if (!citations || citations.length === 0) {
      return (
        <div className="prose prose-invert prose-sm max-w-none">
          <ReactMarkdown
            components={{
              h1: ({ children }) => <h1 className="text-lg font-bold text-noir-100 mt-4 mb-2">{children}</h1>,
              h2: ({ children }) => <h2 className="text-base font-semibold text-noir-200 mt-3 mb-2">{children}</h2>,
              h3: ({ children }) => <h3 className="text-sm font-semibold text-noir-300 mt-2 mb-1">{children}</h3>,
              p: ({ children }) => <p className="text-noir-300 mb-2 leading-relaxed">{children}</p>,
              ul: ({ children }) => <ul className="list-disc list-inside text-noir-300 mb-2 space-y-1">{children}</ul>,
              ol: ({ children }) => <ol className="list-decimal list-inside text-noir-300 mb-2 space-y-1">{children}</ol>,
              li: ({ children }) => <li className="text-noir-300">{children}</li>,
              strong: ({ children }) => <strong className="font-semibold text-noir-100">{children}</strong>,
              em: ({ children }) => <em className="italic text-noir-200">{children}</em>,
              code: ({ children }) => <code className="bg-noir-800 px-1 py-0.5 rounded text-brass-400 text-xs">{children}</code>,
              blockquote: ({ children }) => <blockquote className="border-l-2 border-brass-500 pl-3 italic text-noir-400">{children}</blockquote>,
            }}
          >
            {content}
          </ReactMarkdown>
        </div>
      );
    }

    // With citations, render markdown and then process citation patterns
    // Match citation patterns: [引用1], [1], [引用1、2], [1,2]
    const parts = content.split(/(\[引用?[\d、,\s]+\]|\[\d+(?:[、,]\d+)*\])/g);

    return (
      <div className="prose prose-invert prose-sm max-w-none">
        {parts.map((part, index) => {
          const match = part.match(/\[引用?([\d、,\s]+)\]/);
          if (match) {
            const numbers = match[1].split(/[、,\s]+/).map(n => parseInt(n.trim()));
            return (
              <span key={index} className="inline-flex gap-0.5">
                {numbers.map(num => {
                  const citation = citations.find(c => c.number === num);
                  return citation ? (
                    <CitationInline
                      key={num}
                      citation={citation}
                      onClick={() => onCitationClick?.(citation)}
                    />
                  ) : (
                    <span key={num} className="citation-inline">{num}</span>
                  );
                })}
              </span>
            );
          }
          // Render this part as markdown
          return (
            <ReactMarkdown
              key={index}
              components={{
                h1: ({ children }) => <h1 className="text-lg font-bold text-noir-100 mt-4 mb-2">{children}</h1>,
                h2: ({ children }) => <h2 className="text-base font-semibold text-noir-200 mt-3 mb-2">{children}</h2>,
                h3: ({ children }) => <h3 className="text-sm font-semibold text-noir-300 mt-2 mb-1">{children}</h3>,
                p: ({ children }) => <span className="text-noir-300">{children}</span>,
                ul: ({ children }) => <ul className="list-disc list-inside text-noir-300 mb-2 space-y-1">{children}</ul>,
                ol: ({ children }) => <ol className="list-decimal list-inside text-noir-300 mb-2 space-y-1">{children}</ol>,
                li: ({ children }) => <li className="text-noir-300">{children}</li>,
                strong: ({ children }) => <strong className="font-semibold text-noir-100">{children}</strong>,
                em: ({ children }) => <em className="italic text-noir-200">{children}</em>,
                code: ({ children }) => <code className="bg-noir-800 px-1 py-0.5 rounded text-brass-400 text-xs">{children}</code>,
                blockquote: ({ children }) => <blockquote className="border-l-2 border-brass-500 pl-3 italic text-noir-400">{children}</blockquote>,
              }}
            >
              {part}
            </ReactMarkdown>
          );
        })}
      </div>
    );
  };

  return (
    <div className={`chat-message ${isUser ? 'chat-message-user' : 'chat-message-assistant'}`}>
      <div className={`chat-bubble ${isUser ? 'chat-bubble-user' : 'chat-bubble-assistant'}`}>
        {/* User Avatar / Assistant Icon */}
        {!isUser && (
          <div className="flex items-center gap-2 mb-3 pb-2 border-b border-noir-700/30">
            <div className="w-6 h-6 rounded-lg bg-brass-500/20 flex items-center justify-center">
              <svg className="w-4 h-4 text-brass-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M9.75 3.104v5.714a2.25 2.25 0 01-.659 1.591L5 14.5M9.75 3.104c-.251.023-.501.05-.75.082m.75-.082a24.301 24.301 0 014.5 0m0 0v5.714c0 .597.237 1.17.659 1.591L19.8 15.3M14.25 3.104c.251.023.501.05.75.082M19.8 15.3l-1.57.393A9.065 9.065 0 0112 15a9.065 9.065 0 00-6.23.693L5 15.5m14.8-.2l.2.2v1.561c0 1.115-.763 2.083-1.849 2.353l-.294.074A24.282 24.282 0 0112 20.25a24.282 24.282 0 01-5.857-.513l-.294-.074A2.25 2.25 0 014 17.561V15.5M19.8 15.3v-2.95" />
              </svg>
            </div>
            <span className="text-xs font-medium text-noir-400">FinAgent</span>
            {isThinking && (
              <span className="badge badge-brass ml-auto">
                <span className="status-dot status-dot-processing mr-1" />
                思考中
              </span>
            )}
          </div>
        )}

        {/* Thinking Process (for assistant messages) */}
        {/* Show during thinking (expanded) and after completion (collapsed) */}
        {!isUser && message.thinking && message.thinking.steps.length > 0 && (
          <ThinkingProcess
            thinking={message.thinking}
            defaultExpanded={message.thinking.isThinking}
          />
        )}

        {/* Message Content */}
        {message.content && (
          <div className="text-sm leading-relaxed">
            {renderContent(message.content, message.citations)}
          </div>
        )}

        {/* Metadata Footer */}
        {!isUser && message.status === 'complete' && message.metadata && (
          <div className="mt-4 pt-3 border-t border-noir-700/30 flex items-center gap-4 text-2xs text-noir-500">
            {message.metadata.processingTime && (
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 8v4l3 3m6-3a9 9 0 11-18 0 9 9 0 0118 0z" />
                </svg>
                {message.metadata.processingTime.toFixed(1)}s
              </span>
            )}
            {message.metadata.totalTokens && (
              <span className="flex items-center gap-1">
                <svg className="w-3 h-3" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M7 7h.01M7 3h5c.512 0 1.024.195 1.414.586l7 7a2 2 0 010 2.828l-7 7a2 2 0 01-2.828 0l-7-7A1.994 1.994 0 013 12V7a4 4 0 014-4z" />
                </svg>
                {message.metadata.totalTokens.toLocaleString()} tokens
              </span>
            )}
            {message.metadata.workflow && (
              <span className="badge badge-neutral text-2xs">
                {message.metadata.workflow === 'deep-agent' ? 'Deep Agent' : 'Plan & Execute'}
              </span>
            )}
          </div>
        )}
      </div>
    </div>
  );
}
