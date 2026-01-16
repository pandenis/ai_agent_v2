'use client'

import { useEffect, useState } from 'react'
import { Session } from '@/types'
import { SkeletonLoader } from '@/components/ui/SkeletonLoader'
import { apiClient } from '@/lib/api/client'
import Button from '@/components/ui/Button'
import { formatDistanceToNow } from 'date-fns'

interface SessionListProps {
  sessions: Session[]
  currentSessionId?: string
  onSessionSelect: (sessionId: string) => void
  onNewSession: () => void
  isAiTyping?: boolean;
}

export function SessionList({
  sessions,
  currentSessionId,
  onSessionSelect,
  onNewSession,
  isAiTyping = false, 
}: SessionListProps) {
  const [isLoading, setIsLoading] = useState(true)

  useEffect(() => {
    // Simulate initial load
    if (sessions.length > 0) {
      setIsLoading(false)
    }
  }, [sessions])

  const formatTimeAgo = (dateString: string) => {
  try {
    const date = new Date(dateString)
    console.log('Raw created_at:', dateString, 'Parsed date:', date.toISOString())
    return formatDistanceToNow(date, { addSuffix: true })
  } catch {
    return 'Unknown'
  }
  }

  // Все JSX возвращается единственным return:
  return (
    <div className="w-64 bg-slate-800 border-r border-slate-700 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-slate-700">
  	<h2 className="text-lg font-semibold text-slate-100 mb-3">Sessions</h2>
        <Button onClick={onNewSession} className="w-full" size="sm">
          + New Session
        </Button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto">
        {isLoading ? (
            <SkeletonLoader count={5} />
        ) : sessions?.length === 0 ? (
          <div className="p-4 text-center text-slate-400 text-sm">
  		No sessions yet. Create your first one!
	  </div>
        ) : (
          <div className="p-2 space-y-2">
            {sessions?.map((session) => (
              <SessionItem
                key={session.session_id}
                session={session}
                isActive={session.session_id === currentSessionId}
                onClick={() => onSessionSelect(session.session_id)}
                formatTimeAgo={formatTimeAgo}
                isAiTyping={session.session_id === currentSessionId && isAiTyping}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
        {sessions?.length || 0} {(sessions?.length || 0) === 1 ? 'session' : 'sessions'}
      </div>
    </div>
  )
}

// Отдельный компонент SessionItem вынеси отдельно, НО ВНЕ SessionList
interface SessionItemProps {
  session: Session
  isActive: boolean
  onClick: () => void
  formatTimeAgo: (date: string) => string
  isAiTyping?: boolean;
}

function SessionItem({ session, isActive, onClick, formatTimeAgo, isAiTyping = false }: SessionItemProps) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left p-3 rounded-lg transition-all
        ${isActive
          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md'
          : 'bg-slate-700 hover:bg-slate-600 text-slate-200 border border-slate-600'
        }
      `}
    >
      <div className="flex flex-col gap-1">
        {/* Agent name */}
        <p className={`text-xs ${isActive ? 'text-slate-100' : 'text-slate-400'}`}>
          {session.agent_name || 'groq'}
        </p>
        
        {/* Session title */}
        <p className={`font-medium truncate ${isActive ? 'text-white' : 'text-slate-200'}`}>
          Session {session.session_id.slice(0, 8)}...
        </p>
        
        {/* Message count */}
        <p className={`text-xs ${isActive ? 'text-slate-200' : 'text-slate-300'}`}>
          {session.message_count || 0} messages
        </p>
        
        {/* Time ago or AI typing indicator */}
	<p className={`text-xs ${isActive ? 'text-slate-300' : 'text-slate-400'}`}>
	  {isActive && isAiTyping ? (
	    <span className="flex items-center gap-1">
	      <span className="inline-block w-2 h-2 bg-blue-400 rounded-full animate-pulse"></span>
	      AI is typing...
	    </span>
	  ) : (
	    formatTimeAgo(session.created_at)
	  )}
	</p>
      </div>
    </button>
  )
}
