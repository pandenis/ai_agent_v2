'use client'

import { SessionList } from '@/components/features/SessionList'
import { MemoryPanel } from '@/components/features/MemoryPanel'
import { useEffect, useState } from 'react'

export default function TestSessionsPage() {
  const [sessions, setSessions] = useState<any[]>([])
  const [currentSessionId, setCurrentSessionId] = useState<string>()
  const [selectedInfo, setSelectedInfo] = useState<string>('')

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId)
    setSelectedInfo(`Selected session: ${sessionId}`)
    console.log('Session selected:', sessionId)
  }

  const fetchSessions = async () => {
    try {
      const res = await fetch('http://localhost:8000/api/v1/sessions')
      if (!res.ok) throw new Error('Failed to fetch sessions')
      const data = await res.json()
      setSessions(Array.isArray(data) ? data : [])
    } catch (err) {
      console.error('Error fetching sessions:', err)
      setSessions([])
    }
  }

  useEffect(() => {
    fetchSessions()
  }, [])

  const handleNewSession = async () => {
    setSelectedInfo('Creating new session...')
    try {
      const res = await fetch('http://localhost:8000/api/v1/sessions', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ agent_name: 'mistral' }),
      })
      if (!res.ok) throw new Error('Failed to create session')
      const session = await res.json()
      await fetchSessions()
      setCurrentSessionId(session.session_id)
      setSelectedInfo(`New session created: ${session.session_id}`)
    } catch (err) {
      setSelectedInfo('Error: Could not create session')
      console.error('Create session error:', err)
    }
  }

  return (
    <div className="h-screen flex bg-gradient-to-br from-gray-50 to-gray-100">
      {/* SessionList Component */}
      <SessionList
        sessions={sessions}
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
      />

      {/* Right side: MemoryPanel + Test Info */}
      <div className="flex-1 flex">
        {/* MemoryPanel */}
        <div className="w-[420px] border-l border-gray-200 bg-white/80 backdrop-blur-sm">
          <MemoryPanel
            sessionId={currentSessionId}
            isOpen={!!currentSessionId}
            onClose={() => setCurrentSessionId(undefined)}
          />
        </div>

        {/* Test Info Panel */}
        <div className="flex-1 p-8 overflow-y-auto">
          <div className="max-w-2xl mx-auto">
            <h1 className="text-3xl font-bold text-gray-900 mb-6">
              SessionList Component Test
            </h1>

            {/* Current State */}
            <div className="bg-white rounded-lg shadow-md p-6 mb-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                Current State
              </h2>
              <div className="space-y-2 text-sm">
                <div>
  <span className="font-medium text-gray-700">
    Active Session ID:
  </span>
  <code className="ml-2 px-2 py-1 bg-gray-100 rounded text-blue-600">
    {currentSessionId || 'None'}
  </code>
                </div>
                <div>
                  <span className="font-medium text-gray-700">
                    Last Action:
                  </span>
                  <span className="ml-2 text-gray-600">
                    {selectedInfo || 'No action yet'}
                  </span>
                </div>
              </div>
            </div>

            {/* Instructions */}
            <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
              <h2 className="text-lg font-semibold text-blue-900 mb-3">
                Test Instructions
              </h2>
              <ul className="space-y-2 text-sm text-blue-800">
                <li>✅ Check if sessions load from API</li>
                <li>✅ Click on a session - should highlight</li>
                <li>✅ Hover over sessions - should show hover effect</li>
                <li>✅ Click "New Session" button</li>
                <li>✅ Check time formatting ("X hours ago")</li>
                <li>✅ Check message count display</li>
                <li>✅ Check scrolling if many sessions</li>
                <li>✅ Check loading state on refresh</li>
                <li>✅ Check error handling (if backend down)</li>
              </ul>
            </div>

            {/* Actions */}
            <div className="bg-white rounded-lg shadow-md p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-3">
                Test Actions
              </h2>
              <div className="flex gap-3">
                <button
                  onClick={() => setCurrentSessionId(undefined)}
                  className="px-4 py-2 bg-gray-200 hover:bg-gray-300 rounded-lg text-sm font-medium"
                >
                  Clear Selection
                </button>
                <button
                  onClick={() => window.location.reload()}
                  className="px-4 py-2 bg-blue-500 hover:bg-blue-600 text-white rounded-lg text-sm font-medium"
                >
                  Reload Page
                </button>
              </div>
            </div>

                        {/* API Info */}
            <div className="mt-6 p-4 bg-gray-100 rounded-lg text-xs text-gray-600">
              <strong>API Endpoint:</strong> http://192.168.1.237:8000/api/v1/sessions
              <br />
              <strong>Expected:</strong> List of sessions with session_id, agent_name, created_at
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}