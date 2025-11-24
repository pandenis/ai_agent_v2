'use client'

import { useEffect, useState } from 'react'
import { Session } from '@/types'
import { apiClient } from '@/lib/api/client'
import Button from '@/components/ui/Button'
import { formatDistanceToNow } from 'date-fns'

interface SessionListProps {
  currentSessionId?: string
  onSessionSelect: (sessionId: string) => void
  onNewSession: () => void
}

export function SessionList({
  currentSessionId,
  onSessionSelect,
  onNewSession
}: SessionListProps) {
  const [sessions, setSessions] = useState<Session[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  // Load sessions on mount
  useEffect(() => {
    loadSessions()
  }, [])

  const loadSessions = async () => {
    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getSessions(50, 0)
      setSessions(data)
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load sessions')
      console.error('Error loading sessions:', err)
    } finally {
      setLoading(false)
    }
  }

  const formatTimeAgo = (dateString: string) => {
    try {
      return formatDistanceToNow(new Date(dateString), { addSuffix: true })
    } catch {
      return 'Unknown'
    }
  }

  if (loading) {
    return (
      <div className="w-64 bg-white border-r border-gray-200 p-4">
        <div className="animate-pulse space-y-4">
          <div className="h-10 bg-gray-200 rounded"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
          <div className="h-20 bg-gray-200 rounded"></div>
        </div>
      </div>
    )
  }

  if (error) {
    return (
      <div className="w-64 bg-white border-r border-gray-200 p-4">
        <div className="text-red-600 text-sm mb-4">
          ⚠️ {error}
        </div>
        <Button onClick={loadSessions} variant="secondary" className="w-full">
          Retry
        </Button>
      </div>
    )
  }

  return (
    <div className="w-64 bg-white border-r border-gray-200 flex flex-col h-full">
      {/* Header */}
      <div className="p-4 border-b border-gray-200">
        <h2 className="text-lg font-semibold text-gray-900 mb-3">
          Sessions
        </h2>
        <Button
          onClick={onNewSession}
          className="w-full"
          size="sm"
        >
          + New Session
        </Button>
      </div>

      {/* Session List */}
      <div className="flex-1 overflow-y-auto">
        {sessions.length === 0 ? (
          <div className="p-4 text-center text-gray-500 text-sm">
            No sessions yet. Create your first one!
          </div>
        ) : (
          <div className="p-2 space-y-2">
            {sessions.map((session) => (
              <SessionItem
                key={session.session_id}
                session={session}
                isActive={session.session_id === currentSessionId}
                onClick={() => onSessionSelect(session.session_id)}
                formatTimeAgo={formatTimeAgo}
              />
            ))}
          </div>
        )}
      </div>

      {/* Footer Stats */}
      <div className="p-4 border-t border-gray-200 text-xs text-gray-500">
        {sessions.length} {sessions.length === 1 ? 'session' : 'sessions'}
      </div>
    </div>
  )
}

// Separate component for session item
interface SessionItemProps {
  session: Session
  isActive: boolean
  onClick: () => void
  formatTimeAgo: (date: string) => string
}

function SessionItem({ session, isActive, onClick, formatTimeAgo }: SessionItemProps) {
  return (
    <button
      onClick={onClick}
      className={`
        w-full text-left p-3 rounded-lg transition-all
        ${isActive
          ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white shadow-md'
          : 'bg-gray-50 hover:bg-gray-100 text-gray-900'
        }
      `}
    >
      {/* Active indicator */}
      <div className="flex items-center gap-2 mb-1">
        {isActive && (
          <span className="w-2 h-2 bg-green-400 rounded-full animate-pulse"></span>
        )}
        <span className={`text-xs font-medium ${isActive ? 'text-white' : 'text-gray-500'}`}>
          {session.agent_name || 'mistral'}
        </span>
      </div>

      {/* Session info */}
      <div className={`text-sm font-medium mb-1 truncate ${isActive ? 'text-white' : 'text-gray-900'}`}>
        Session {session.session_id.slice(0, 8)}...
      </div>

      {/* Metadata */}
      <div className="flex items-center justify-between text-xs">
        <span className={isActive ? 'text-blue-100' : 'text-gray-500'}>
          {session.message_count || 0} messages
        </span>
        <span className={isActive ? 'text-blue-100' : 'text-gray-400'}>
          {formatTimeAgo(session.created_at)}
        </span>
      </div>
    </button>
  )
}