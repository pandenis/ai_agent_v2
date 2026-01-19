'use client';

import { useState, useRef, useEffect } from 'react';
import { useChatStore } from '@/lib/stores/chat-store';
import { api } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { MessageContent } from './MessageContent';

export function ChatArea() {
  const [input, setInput] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const { messages, isLoading, currentSessionId, addMessage, setLoading, setError } = useChatStore();

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || isLoading) return;

    const userMessage = input.trim();
    setInput('');

    addMessage({ role: 'user', content: userMessage });
    setLoading(true);

    try {
      const response = await api.orchestrate({
        query: userMessage,
        session_id: currentSessionId || 'default-session',
      });

      addMessage({
        role: 'assistant',
        content: response.text,
        metadata: {
          strategy: response.metadata.strategy,
          cached: response.metadata.cached,
          elapsed_time_ms: response.metadata.elapsed_time_ms,
          memory_coverage: response.metadata.memory_coverage,
          confidence: response.metadata.confidence,
          query_analysis: response.query_analysis,
        },
      });
    } catch (error) {
      setError(error instanceof Error ? error.message : 'An error occurred');
      addMessage({
        role: 'assistant',
        content: 'Sorry, an error occurred. Please try again.',
      });
    } finally {
      setLoading(false);
    }
  };

  const handleCopy = async (id: string, content: string) => {
    await navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="flex flex-col h-full">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto p-4 space-y-4">
        {messages.length === 0 ? (
          <div className="text-center text-muted-foreground py-8">
            Start a conversation...
          </div>
        ) : (
          messages.map((message) => (
            <div
              key={message.id}
              className={cn(
                'group relative max-w-[80%] p-4 rounded-lg',
                message.role === 'user'
                  ? 'ml-auto bg-primary text-primary-foreground'
                  : 'mr-auto bg-muted'
              )}
            >
              {/* Copy button */}
              <button
                onClick={() => handleCopy(message.id, message.content)}
                className={cn(
                  'absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 transition-opacity',
                  message.role === 'user' 
                    ? 'hover:bg-white/20' 
                    : 'hover:bg-black/10'
                )}
                title="Copy message"
              >
                {copiedId === message.id ? '✓' : '📋'}
              </button>

              <MessageContent content={message.content} />
              
              {message.metadata && (
                <div className="mt-2 text-xs opacity-70 flex gap-2 flex-wrap">
                  {message.metadata.strategy && (
                    <span className="px-1.5 py-0.5 bg-background/20 rounded">
                      {message.metadata.strategy}
                    </span>
                  )}
                  {message.metadata.elapsed_time_ms && (
                    <span>{message.metadata.elapsed_time_ms.toFixed(0)}ms</span>
                  )}
                  {message.metadata.cached && <span>cached</span>}
                  {message.metadata.confidence && (
                    <span>{(message.metadata.confidence * 100).toFixed(0)}% conf</span>
                  )}
                </div>
              )}
            </div>
          ))
        )}

        {isLoading && (
          <div className="mr-auto bg-muted p-4 rounded-lg">
            <div className="flex items-center gap-2 text-sm">
              <span className="w-2 h-2 bg-current rounded-full animate-bounce" />
              <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:0.1s]" />
              <span className="w-2 h-2 bg-current rounded-full animate-bounce [animation-delay:0.2s]" />
              <span className="ml-2">AI is thinking...</span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <form onSubmit={handleSubmit} className="p-4 border-t border-border">
        <div className="flex gap-2">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Type a message..."
            disabled={isLoading}
            className="flex-1 px-4 py-2 rounded-lg border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary disabled:opacity-50"
          />
          <button
            type="submit"
            disabled={isLoading || !input.trim()}
            className="px-4 py-2 bg-primary text-primary-foreground rounded-lg disabled:opacity-50 transition-opacity"
          >
            Send
          </button>
        </div>
      </form>
    </div>
  );
}
