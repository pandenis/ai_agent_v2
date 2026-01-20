'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useChatStore } from '@/lib/stores/chat-store';
import { api } from '@/lib/api/client';
import { Tabs, TabList, Tab, TabPanel } from '@/components/ui/Tabs';
import { Brain, Zap, Activity, ChevronDown, Target, Database, DollarSign, HardDrive, Layers, Cpu } from 'lucide-react';

export function ContextPanel() {
  const [queryAnalysisOpen, setQueryAnalysisOpen] = useState(true);
  const { currentSessionId, messages, lastMetadata } = useChatStore();

  // Fetch facts
  const { data: facts, isLoading: factsLoading, error: factsError } = useQuery({
    queryKey: ['facts', currentSessionId],
    queryFn: () => api.getFacts(currentSessionId || undefined),
    refetchInterval: 60000,
  });

  // Fetch cache stats
  const { data: cacheStats } = useQuery({
    queryKey: ['cache-stats'],
    queryFn: () => api.getCacheStats(),
    refetchInterval: 30000, // Refresh every 30s
  });

  // Fetch session stats
  const { data: sessionStats } = useQuery({
    queryKey: ['session-stats', currentSessionId],
    queryFn: () => currentSessionId ? api.getSessionStats(currentSessionId) : null,
    enabled: !!currentSessionId,
    refetchInterval: 10000, // Refresh every 10s
  });

  // Calculate local stats (fallback)
  const messageCount = sessionStats?.message_count ?? messages.length;
  const userMessages = sessionStats?.user_messages ?? messages.filter(m => m.role === 'user').length;
  const assistantMessages = sessionStats?.assistant_messages ?? messages.filter(m => m.role === 'assistant').length;

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
            
            {factsLoading ? (
              <div className="space-y-2">
                {[1, 2, 3].map((i) => (
                  <div key={i} className="h-16 bg-muted rounded animate-pulse" />
                ))}
              </div>
            ) : factsError ? (
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
                  <span
                    className="text-sm text-muted-foreground flex items-center gap-1.5"
                    title="AI processing strategy: direct (memory only), enhanced (AI + memory), or deep_reasoning (multi-step)"
                  >
                    <Cpu className="w-3.5 h-3.5" /> Strategy
                  </span>
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
                    <span
                      className="text-sm text-muted-foreground flex items-center gap-1.5"
                      title="How confident the AI is in this response (0-100%)"
                    >
                      <Target className="w-3.5 h-3.5" /> Confidence
                    </span>
                    <span className="text-sm font-medium">{((lastMetadata.confidence || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-primary transition-all duration-500 ease-out"
                      style={{ width: `${(lastMetadata.confidence || 0) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Memory Coverage */}
                <div>
                  <div className="flex justify-between items-center mb-1">
                    <span
                      className="text-sm text-muted-foreground flex items-center gap-1.5"
                      title="How much of the query was answered from stored memory facts"
                    >
                      <Brain className="w-3.5 h-3.5" /> Memory Coverage
                    </span>
                    <span className="text-sm font-medium">{((lastMetadata.memory_coverage || 0) * 100).toFixed(0)}%</span>
                  </div>
                  <div className="h-2 bg-muted rounded-full overflow-hidden">
                    <div
                      className="h-full bg-green-500 transition-all duration-500 ease-out"
                      style={{ width: `${(lastMetadata.memory_coverage || 0) * 100}%` }}
                    />
                  </div>
                </div>

                {/* Sources */}
                {lastMetadata.sources && lastMetadata.sources.length > 0 && (
                  <div>
                    <span
                      className="text-sm text-muted-foreground flex items-center gap-1.5"
                      title="Data sources used to generate this response"
                    >
                      <Database className="w-3.5 h-3.5" /> Sources
                    </span>
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
                  <span
                    className="text-sm text-muted-foreground flex items-center gap-1.5"
                    title="Total processing time in milliseconds"
                  >
                    <Zap className="w-3.5 h-3.5" /> Response Time
                  </span>
                  <span className="text-sm font-medium">
                    {lastMetadata.elapsed_time_ms?.toFixed(2) || 0}ms
                  </span>
                </div>

                {/* Cost */}
                <div className="flex justify-between items-center">
                  <span
                    className="text-sm text-muted-foreground flex items-center gap-1.5"
                    title="Estimated API cost for this response in USD"
                  >
                    <DollarSign className="w-3.5 h-3.5" /> Cost
                  </span>
                  <span className="text-sm font-medium">
                    ${lastMetadata.cost_usd?.toFixed(6) || '0.000000'}
                  </span>
                </div>

                {/* Cached */}
                <div className="flex justify-between items-center">
                  <span
                    className="text-sm text-muted-foreground flex items-center gap-1.5"
                    title="Whether this response was served from cache (faster, free)"
                  >
                    <HardDrive className="w-3.5 h-3.5" /> Cached
                  </span>
                  <span className="text-sm font-medium">
                    {lastMetadata.cached ? '✅ Yes' : '❌ No'}
                  </span>
                </div>

                {/* Reasoning Depth */}
                <div className="flex justify-between items-center">
                  <span
                    className="text-sm text-muted-foreground flex items-center gap-1.5"
                    title="Number of reasoning steps used for complex queries"
                  >
                    <Layers className="w-3.5 h-3.5" /> Reasoning Depth
                  </span>
                  <span className="text-sm font-medium">
                    {lastMetadata.reasoning_depth || 1}
                  </span>
                </div>

                {/* Query Analysis - Collapsible */}
                {lastMetadata.query_analysis && (
                  <div className="border-t border-border pt-3 mt-3">
                    <button
                      onClick={() => setQueryAnalysisOpen(!queryAnalysisOpen)}
                      className="flex items-center justify-between w-full text-sm font-medium mb-2"
                    >
                      <span>🔍 Query Analysis</span>
                      <ChevronDown
                        className={`w-4 h-4 transition-transform ${queryAnalysisOpen ? 'rotate-180' : ''}`}
                      />
                    </button>

                    {queryAnalysisOpen && (
                      <div className="space-y-2 pl-2">
                        {/* Complexity */}
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">Complexity</span>
                          <span className={`px-2 py-0.5 rounded text-xs font-medium ${
                            lastMetadata.query_analysis.complexity === 'simple' ? 'bg-green-500/20 text-green-500' :
                            lastMetadata.query_analysis.complexity === 'medium' ? 'bg-yellow-500/20 text-yellow-500' :
                            'bg-red-500/20 text-red-500'
                          }`}>
                            {lastMetadata.query_analysis.complexity}
                          </span>
                        </div>

                        {/* Intent */}
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">Intent</span>
                          <span className="text-xs font-medium">
                            {lastMetadata.query_analysis.intent}
                          </span>
                        </div>

                        {/* Query Type */}
                        <div className="flex justify-between items-center">
                          <span className="text-xs text-muted-foreground">Type</span>
                          <span className="text-xs font-medium">
                            {lastMetadata.query_analysis.query_type}
                          </span>
                        </div>

                        {/* Topics */}
                        {lastMetadata.query_analysis.topics?.length > 0 && (
                          <div>
                            <span className="text-xs text-muted-foreground">Topics</span>
                            <div className="flex gap-1 mt-1 flex-wrap">
                              {lastMetadata.query_analysis.topics.map((topic, i) => (
                                <span
                                  key={i}
                                  className="px-1.5 py-0.5 bg-blue-500/20 text-blue-500 text-xs rounded"
                                >
                                  {topic}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}

                        {/* Entities */}
                        {lastMetadata.query_analysis.entities?.length > 0 && (
                          <div>
                            <span className="text-xs text-muted-foreground">Entities</span>
                            <div className="flex gap-1 mt-1 flex-wrap">
                              {lastMetadata.query_analysis.entities.map((entity, i) => (
                                <span
                                  key={i}
                                  className="px-1.5 py-0.5 bg-purple-500/20 text-purple-500 text-xs rounded"
                                >
                                  {entity}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    )}
                  </div>
                )}
              </div>
            )}
          </div>
        </TabPanel>

        {/* System Stats Tab */}
        <TabPanel id="system">
          <div className="p-4 space-y-6">
            {/* Session Stats */}
            <div>
              <h4 className="text-sm font-medium mb-3">📈 Session Stats</h4>
              <div className="space-y-3">
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

                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-muted-foreground text-xs mb-1">Session ID</div>
                  <div className="font-mono text-xs truncate">
                    {currentSessionId || 'No session'}
                  </div>
                </div>

                <div className="bg-muted p-3 rounded-lg">
                  <div className="text-muted-foreground text-xs">Memory Facts</div>
                  <div className="font-semibold text-lg">{facts?.length || 0}</div>
                </div>
              </div>
            </div>

            {/* Cache Stats */}
            <div>
              <h4 className="text-sm font-medium mb-3">💾 Cache Performance</h4>
              {cacheStats ? (
                <div className="space-y-3">
                  {/* Hit Rate */}
                  <div>
                    <div className="flex justify-between items-center mb-1">
                      <span className="text-sm text-muted-foreground">Hit Rate</span>
                      <span className="text-sm font-medium">{(cacheStats.hit_rate * 100).toFixed(1)}%</span>
                    </div>
                    <div className="h-2 bg-muted rounded-full overflow-hidden">
                      <div 
                        className="h-full bg-green-500 transition-all duration-300"
                        style={{ width: `${cacheStats.hit_rate * 100}%` }}
                      />
                    </div>
                  </div>

                  <div className="grid grid-cols-2 gap-2">
                    <div className="bg-muted p-3 rounded-lg">
                      <div className="text-muted-foreground text-xs">Hits</div>
                      <div className="font-semibold text-lg text-green-500">{cacheStats.hits}</div>
                    </div>
                    <div className="bg-muted p-3 rounded-lg">
                      <div className="text-muted-foreground text-xs">Misses</div>
                      <div className="font-semibold text-lg text-orange-500">{cacheStats.misses}</div>
                    </div>
                  </div>

                  <div className="bg-muted p-3 rounded-lg">
                    <div className="text-muted-foreground text-xs">Cache Size</div>
                    <div className="font-semibold">{cacheStats.size} / {cacheStats.max_size}</div>
                  </div>

                  {cacheStats.estimated_bytes && (
                    <div className="bg-muted p-3 rounded-lg">
                      <div className="text-muted-foreground text-xs">Memory Usage</div>
                      <div className="font-semibold">
                        {(cacheStats.estimated_bytes / 1024).toFixed(1)} KB
                      </div>
                    </div>
                  )}
                </div>
              ) : (
                <div className="text-sm text-muted-foreground">
                  Loading cache stats...
                </div>
              )}
            </div>
          </div>
        </TabPanel>
      </Tabs>
    </div>
  );
}
