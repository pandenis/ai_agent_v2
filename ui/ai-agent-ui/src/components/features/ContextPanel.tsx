'use client';

import { useQuery } from '@tanstack/react-query';
import { useChatStore } from '@/lib/stores/chat-store';
import { api } from '@/lib/api/client';

export function ContextPanel() {
  const { currentSessionId, messages } = useChatStore();

  // Fetch facts
  const { data: facts, isLoading, error } = useQuery({
    queryKey: ['facts', currentSessionId],
    queryFn: () => api.getFacts(currentSessionId || undefined),
    refetchInterval: 60000,
  });

  // Calculate stats
  const messageCount = messages.length;
  const userMessages = messages.filter(m => m.role === 'user').length;
  const assistantMessages = messages.filter(m => m.role === 'assistant').length;

  return (
    <div className="flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-border">
        <h3 className="font-semibold">Context</h3>
      </div>

      {/* Stats */}
      <div className="p-4 border-b border-border">
        <h4 className="text-sm font-medium mb-3">Session Stats</h4>
        <div className="grid grid-cols-2 gap-2 text-sm">
          <div className="bg-muted p-2 rounded">
            <div className="text-muted-foreground text-xs">Messages</div>
            <div className="font-semibold">{messageCount}</div>
          </div>
          <div className="bg-muted p-2 rounded">
            <div className="text-muted-foreground text-xs">You / AI</div>
            <div className="font-semibold">{userMessages} / {assistantMessages}</div>
          </div>
        </div>
      </div>

      {/* Memory/Facts */}
      <div className="flex-1 overflow-y-auto p-4">
        <h4 className="text-sm font-medium mb-3">
          Memory ({facts?.length || 0} facts)
        </h4>
        
        {isLoading ? (
          <div className="space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-muted rounded animate-pulse" />
            ))}
          </div>
        ) : error ? (
          <div className="text-sm text-red-500">
            Error loading facts
          </div>
        ) : !facts || facts.length === 0 ? (
          <div className="text-sm text-muted-foreground">
            No facts stored yet
          </div>
        ) : (
          <div className="space-y-2">
            {facts.slice(0, 10).map((fact) => (
              <div
                key={fact.fact_id}
                className="p-3 bg-muted rounded-lg text-sm"
              >
                <div className="mb-2">{fact.text}</div>
                <div className="flex items-center gap-2 text-xs text-muted-foreground">
                  <span title="Importance">
                    {'⭐'.repeat(Math.min(Math.round(fact.importance * 5), 5))}
                  </span>
                  <span>•</span>
                  <span>{(fact.confidence * 100).toFixed(0)}% conf</span>
                </div>
                {fact.tags?.length > 0 && (
                  <div className="flex gap-1 mt-2 flex-wrap">
                    {fact.tags.map((tag, i) => (
                      <span
                        key={i}
                        className="px-1.5 py-0.5 bg-primary/10 text-primary text-xs rounded"
                      >
                        {tag}
                      </span>
                    ))}
                  </div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
