/**
 * ChatInput - Input field for chat messages with send button
 */

import { useState, useRef, useEffect, KeyboardEvent } from 'react';

interface ChatInputProps {
  onSend: (message: string) => void;
  isLoading?: boolean;
  placeholder?: string;
  disabled?: boolean;
}

export function ChatInput({
  onSend,
  isLoading = false,
  placeholder = '輸入您的金融法律問題...',
  disabled = false,
}: ChatInputProps) {
  const [message, setMessage] = useState('');
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  // Auto-resize textarea
  useEffect(() => {
    const textarea = textareaRef.current;
    if (textarea) {
      textarea.style.height = 'auto';
      textarea.style.height = `${Math.min(textarea.scrollHeight, 200)}px`;
    }
  }, [message]);

  const handleSubmit = () => {
    const trimmedMessage = message.trim();
    if (trimmedMessage && !isLoading && !disabled) {
      onSend(trimmedMessage);
      setMessage('');
      // Reset textarea height
      if (textareaRef.current) {
        textareaRef.current.style.height = 'auto';
      }
    }
  };

  const handleKeyDown = (e: KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit();
    }
  };

  const canSend = message.trim().length > 0 && !isLoading && !disabled;

  return (
    <div className="chat-input-container">
      <div className="chat-input-wrapper">
        {/* Text Input */}
        <textarea
          ref={textareaRef}
          value={message}
          onChange={(e) => setMessage(e.target.value)}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled || isLoading}
          rows={1}
          className="flex-1 bg-transparent border-0 text-noir-100 placeholder:text-noir-500 resize-none focus:outline-none focus:ring-0 px-4 py-3 max-h-[200px]"
        />

        {/* Actions */}
        <div className="flex items-center gap-2 pr-2">
          {/* Character count */}
          {message.length > 0 && (
            <span className="text-2xs text-noir-500 tabular-nums">
              {message.length}
            </span>
          )}

          {/* Send Button */}
          <button
            onClick={handleSubmit}
            disabled={!canSend}
            className={`btn btn-primary btn-icon transition-all duration-200 ${
              canSend
                ? 'opacity-100 translate-y-0'
                : 'opacity-50 cursor-not-allowed'
            }`}
          >
            {isLoading ? (
              <div className="spinner w-4 h-4" />
            ) : (
              <svg className="w-4 h-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 19l9 2-9-18-9 18 9-2zm0 0v-8" />
              </svg>
            )}
          </button>
        </div>
      </div>

      {/* Hints */}
      <div className="flex items-center justify-between mt-2 px-2">
        <p className="text-2xs text-noir-600">
          按 <kbd className="px-1.5 py-0.5 bg-noir-800 rounded text-noir-400">Enter</kbd> 發送，
          <kbd className="px-1.5 py-0.5 bg-noir-800 rounded text-noir-400">Shift + Enter</kbd> 換行
        </p>
        {isLoading && (
          <span className="text-2xs text-brass-400 flex items-center gap-1">
            <span className="status-dot status-dot-processing" />
            正在處理...
          </span>
        )}
      </div>
    </div>
  );
}
