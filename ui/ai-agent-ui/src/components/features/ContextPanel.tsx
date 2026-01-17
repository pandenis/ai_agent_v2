'use client';

import { useQuery } from '@tanstack/react-query';
import { Brain, Zap, Activity } from 'lucide-react';
import { useChatStore } from '@/lib/stores/chat-store';
import { api } from '@/lib/api/client';
import { Tabs, TabList, Tab, TabPanel } from '@/components/ui/Tabs';

export function ContextPanel() {
  const { currentSessionId, messages, lastMetadata } = useChatStore();

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
        <h3 className="font-semibold">⚙️ Technical Panel</h3>
      </div>

      {/* Tabs */}
      <Tabs defaultTab="facts">
        <TabList className="px-2">
          <Tab id="facts" label="Facts" icon={<Brain className="w-4 h-4" />} />
          <Tab id="response" label="Response" icon={<Zap className="w-4 h-4" />} />
          <Tab id="system" label="System" icon={<Activity className="w-4 h-4" />} />
        </TabList>

        {/* Facts Tab */}
        <TabPanel id="facts">
          <div className="p-4">
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
        </TabPanel>

        {/* Response Metadata Tab */}
        <TabPanel id="response">
          <div className="p-4">
            <h4 className="text-sm font-medium mb-3">📊 Last Response</h4>
            
            {!lastMetadata ? (
              <div className="text-sm text-muted-foreground">
                Send a message to see response metadata
              </div>
            ) : (
              <div className="space-y-3">
                {/* Strategy */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Strategy</span>
                  <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                    lastMetadata.strategy === 'direct' ? 'bg-green-500/20 text-green-500' :
                    lastMetadata.strategy === 'enhanced' ? 'bg-blue-500/20 text-blue-500' :
                    'bg-purple-500/20 text-purple-500'
                  }`}>
                    {lastMetadata.strategy}
                  </span>
                </div>

                {/* Confidence */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-muted-foreground">Confidence</span>
                    <span className="text-sm font-medium">{((lastMetadata.confidence || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-primary transition-all duration-300"
                      style={{ width: `${(lastMetadata.confidence || 0) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Memory Coverage */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span className="text-sm text-muted-foreground">Memory Coverage</span>
                    <span className="text-sm font-medium">{((lastMetadata.memory_coverage || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div 
                      className="h-full bg-green-500 transition-all duration-300"
                      style={{ width: `${(lastMetadata.memory_coverage || 0) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Sources */}
                {lastMetadata.sources && lastMetadata.sources.length > 0 && (
                  <div>
                    <span className="text-sm text-muted-foreground">Sources</span>
                    <div className="flex gap-1 mt-1 flex-wrap">
                      {lastMetadata.sources.map((source, i) => (
                        <span
                          key={i}
                          className="px-2 py-0.5 bg-muted text-xs rounded"
                        >
                          {source === 'memory' ? '🧠' : '🤖'} {source}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                {/* Time */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Response Time</span>
                  <span className="text-sm font-medium">
                    ⚡ {lastMetadata.elapsed_time_ms?.toFixed(2) || 0}ms
                  </span>
                </div>

                {/* Cost */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Cost</span>
                  <span className="text-sm font-medium">
                    💰 ${lastMetadata.cost_usd?.toFixed(6) || '0.000000'}
                  </span>
                </div>

                {/* Cached */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Cached</span>
                  <span className="text-sm font-medium">
                    {lastMetadata.cached ? '✅ Yes' : '❌ No'}
                  </span>
                </div>

                {/* Reasoning Depth */}
                <div className="flex justify-between items-center">
                  <span className="text-sm text-muted-foreground">Reasoning Depth</span>
                  <span className="text-sm font-medium">
                    {lastMetadata.reasoning_depth || 1}
                  </span>
                </div>
              </div>
            )}
          </div>
        </TabPanel>

        {/* System Stats Tab */}
        <TabPanel id="system">
          <div className="p-4">
            <h4 className="text-sm font-medium mb-3">📈 Session Stats</h4>
            
            <div className="space-y-3">
              {/* Message counts */}
              <div className="grid grid-cols-2 gap-2">
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-muted-foreground text-xs">Total Messages</div>
                  <div className="font-semibold text-lg">{messageCount}</div>
                </div>
                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-muted-foreground text-xs">You / AI</div>
                  <div className="font-semibold text-lg">{userMessages} / {assistantMessages}</div>
                </div>
              </div>

              {/* Session ID */}
              <div className="bg-muted p-3 rounded-lg">
                <div className="text-muted-foreground text-xs mb-1">Session ID</div>
                <div className="font-mono text-xs truncate">
                  {currentSessionId || 'No session'}
                </div>
              </div>

              {/* Facts count */}
              <div className="bg-muted p-3 rounded-lg">
                <div className="text-muted-foreground text-xs">Memory Facts</div>
                <div className="font-semibold text-lg">{facts?.length || 0}</div>
              </div>
            </div>

            {/* Future: Cache stats will go here */}
            <div className="mt-6">
              <h4 className="text-sm font-medium mb-3 text-muted-foreground">
                💾 Cache Stats (coming soon)
              </h4>
              <div className="text-xs text-muted-foreground">
                Cache statistics will be available after T4 implementation
              </div>
            </div>
          </div>
        </TabPanel>
      </Tabs>
    </div>
  );
}
