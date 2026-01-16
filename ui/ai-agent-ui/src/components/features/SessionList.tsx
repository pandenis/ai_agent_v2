'use client';

import { useEffect, useState, useMemo } from 'react';
import { useQuery, useQueryClient } from '@tanstack/react-query';
import { useSessionStore } from '@/lib/stores/session-store';
import { useChatStore, ChatMessage } from '@/lib/stores/chat-store';
import { api } from '@/lib/api/client';
import { cn } from '@/lib/utils';
import { generateUUID } from '@/lib/utils/uuid';

export function SessionList() {
  const queryClient = useQueryClient();
  const { activeSessionId, setActiveSession, setSessions } = useSessionStore();
  const { setSession, setMessages, setLoading, clearMessages } = useChatStore();
  const [isCreating, setIsCreating] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');

  // Fetch sessions
  const { data: sessions, isLoading, error } = useQuery({
    queryKey: ['sessions'],
    queryFn: api.getSessions,
    refetchInterval: 30000,
  });

  // Filter sessions by search query
  const filteredSessions = useMemo(() => {
    if (!sessions || !searchQuery.trim()) return sessions;
    const query = searchQuery.toLowerCase();
    return sessions.filter(session => 
      session.agent_name?.toLowerCase().includes(query) ||
      session.session_id.toLowerCase().includes(query)
    );
  }, [sessions, searchQuery]);

  // Sync to store
  useEffect(() => {
    if (sessions) {
      setSessions(sessions);
    }
  }, [sessions, setSessions]);

  const handleSelectSession = async (sessionId: string) => {
    setActiveSession(sessionId);
    setSession(sessionId);
    setLoading(true);

    try {
      const messages = await api.getMessages(sessionId);
      const chatMessages: ChatMessage[] = messages.map((msg) => ({
        id: msg.id || generateUUID(),
        role: msg.role,
        content: msg.content,
        timestamp: new Date(msg.timestamp),
        metadata: msg.metadata,
      }));
      setMessages(chatMessages);
    } catch (err) {
      console.error('Failed to load messages:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleNewSession = async () => {
    setIsCreating(true);
    try {
      const newSession = await api.createSession({ agent_name: 'mistral' });
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      setActiveSession(newSession.session_id);
      setSession(newSession.session_id);
      clearMessages();
    } catch (err) {
      console.error('Failed to create session:', err);
    } finally {
      setIsCreating(false);
    }
  };

  const handleDeleteSession = async (e: React.MouseEvent, sessionId: string) => {
    e.stopPropagation(); // Don't select the session
    if (!confirm('Delete this session?')) return;
    
    try {
      await api.deleteSession(sessionId);
      queryClient.invalidateQueries({ queryKey: ['sessions'] });
      
      // If deleted the active session, clear it
      if (activeSessionId === sessionId) {
        setActiveSession(null);
        clearMessages();
      }
    } catch (err) {
      console.error('Failed to delete session:', err);
    }
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
          value={searchQuery}
          onChange={(e) => setSearchQuery(e.target.value)}
          placeholder="🔍 Search dialogs..."
          className="w-full px-3 py-2 text-sm rounded-md border border-border bg-background focus:outline-none focus:ring-2 focus:ring-primary"
        />
      </div>

      {/* New Dialog Button */}
      <div className="p-3">
        <button 
          onClick={handleNewSession}
          disabled={isCreating}
          className="w-full px-3 py-2 bg-primary text-primary-foreground rounded-md text-sm font-medium disabled:opacity-50"
        >
          {isCreating ? 'Creating...' : '+ New Dialog'}
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
        ) : filteredSessions?.length === 0 ? (
          <div className="p-3 text-sm text-muted-foreground text-center">
            {searchQuery ? 'No matching sessions' : 'No sessions yet'}
          </div>
        ) : (
          <div className="p-2 space-y-1">
            {filteredSessions?.map((session) => (
              <div
                key={session.session_id}
                className={cn(
                  'group relative w-full p-3 rounded-lg text-left transition-colors cursor-pointer',
                  activeSessionId === session.session_id
                    ? 'bg-primary/10 border border-primary/20'
                    : 'hover:bg-accent'
                )}
                onClick={() => handleSelectSession(session.session_id)}
              >
                <div className="font-medium text-sm truncate pr-6">
                  {session.agent_name || 'Untitled'}
                </div>
                <div className="text-xs text-muted-foreground mt-1">
                  {formatDate(session.created_at)} • {session.message_count} msgs
                </div>
                
                {/* Delete button */}
                <button
                  onClick={(e) => handleDeleteSession(e, session.session_id)}
                  className="absolute top-2 right-2 p-1 rounded opacity-0 group-hover:opacity-100 hover:bg-destructive/20 text-destructive transition-opacity"
                  title="Delete session"
                >
                  🗑️
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
