'use client';

import { useState } from 'react';
import { SessionList } from '@/components/features/SessionList';
import { ChatInterface } from '@/components/chat/ChatInterface';
import { apiClient } from '@/lib/api/client';

export default function ChatPage() {
  const [activeSessionId, setActiveSessionId] = useState<string | null>(null);

  const handleSessionSelect = (sessionId: string) => {
    console.log('Switching to session:', sessionId);
    setActiveSessionId(sessionId);
  };

  const handleCreateSession = async () => {
    try {
      const newSession = await apiClient.createSession('groq');
      setActiveSessionId(newSession.session_id);
    } catch (err) {
      console.error('Failed to create session:', err);
      alert('Failed to create session');
    }
  };

  return (
    <div className="flex h-screen bg-slate-900">
      {/* LEFT SIDEBAR - SessionList */}
      <div className="w-80 border-r border-slate-700 bg-slate-950">
        <SessionList
          currentSessionId={activeSessionId || undefined}
          onSessionSelect={handleSessionSelect}
          onNewSession={handleCreateSession}
        />
      </div>

      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col">
        {activeSessionId ? (
          <ChatInterface sessionId={activeSessionId} />
        ) : (
          <div className="flex-1 flex items-center justify-center text-slate-400">
            <div className="text-center">
              <p className="text-xl mb-2">No session selected</p>
              <p className="text-sm">Select a session from the list or create a new one</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
