'use client';

import { useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useSessionStore } from '@/lib/stores/session-store';
import { useChatStore } from '@/lib/stores/chat-store';
import { api } from '@/lib/api/client';
import { cn } from '@/lib/utils';

export function SessionList() {
  const { activeSessionId, setActiveSession, setSessions } = useSessionStore();
  const { setSession } = useChatStore();

  // Fetch sessions
  const { data: sessions, isLoading, error } = useQuery({
    queryKey: ['sessions'],
    queryFn: api.getSessions,
    refetchInterval: 30000,
  });

  // Debug logging
  useEffect(() => {
    console.log('Sessions query:', { sessions, isLoading, error });
  }, [sessions, isLoading, error]);

  // Sync to store
  useEffect(() => {
    if (sessions) {
      setSessions(sessions);
    }
  }, [sessions, setSessions]);

  const handleSelectSession = (sessionId: string) => {
    setActiveSession(sessionId);
    setSession(sessionId);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMins / 60);
    const diffDays = Math.floor(diffHours / 24);

    if (diffMins < 1) return 'just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  // Show error if any
  if (error) {
    return (
      <div className="p-3 text-sm text-red-500">
        Error: {error.message}
      </div>
    );
  }

  return (
    <div className="flex flex-col h-full">
      {/* Search */}
      <div className="p-3 border-b border-border">
        <input
          type="search"
          placeholder="🔍 Search dialogs..."
          className="w-full px-3 py-2 text-sm rounded-md border border-border bg-background"
        />
      </div>

      {/* New Dialog Button */}
      <div className="p-3">
        <button className="w-full px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium">
          + New Dialog
        </button>
      </div>


      {/* Session List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
          <div className="p-3 space-y-2">
            {[1, 2, 3].map((i) => (
              <div key={i} className="h-16 bg-muted rounded-md animate-pulse" />
            ))}
          </div>
        ) : sessions?.length === 0 ? (
          <div className="p-3 text-sm text-muted-foreground text-center">
            No sessions yet
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {sessions?.map((session) => (
              <button
                key={session.session_id}
                onClick={() => handleSelectSession(session.session_id)}
                className={cn(
                  'w-full p-3 rounded-lg text-left transition-colors',
                  activeSessionId === session.session_id
                    ? 'bg-primary/10 border border-primary/20'
                    : 'hover:bg-accent'
                )}
              >
                <div className="font-medium text-sm truncate">
                  {session.agent_name || 'Untitled'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {formatDate(session.created_at)} • {session.message_count} msgs
                </div>
              </button>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
