'use client'

import { useState } from 'react'
import { SessionList } from '@/components/features/SessionList'
import { MemoryPanel } from '@/components/features/MemoryPanel'

export default function TestSessionsPage() {
  const [currentSessionId, setCurrentSessionId] = useState<string>()
  const [selectedInfo, setSelectedInfo] = useState<string>('')
  const [memoryOpen, setMemoryOpen] = useState(false)

  const handleSessionSelect = (sessionId: string) => {
    setCurrentSessionId(sessionId)
    setSelectedInfo(`Selected session: ${sessionId}`)
    setMemoryOpen(false) // Close memory when switching sessions
    console.log('Session selected:', sessionId)
  }

  const handleNewSession = () => {
    setSelectedInfo('New session button clicked!')
    console.log('New session requested')
  }

  const handleShowMemory = () => {
    if (currentSessionId) {
      setMemoryOpen(true)
      setSelectedInfo(`Showing memory for: ${currentSessionId}`)
    }
  }

  return (
    <div className="h-screen flex bg-gradient-to-br from-gray-50 to-gray-100">
      {/* SessionList Component */}
      <SessionList
        currentSessionId={currentSessionId}
        onSessionSelect={handleSessionSelect}
        onNewSession={handleNewSession}
      />

      {/* Test Info Panel */}
      <div className="flex-1 p-8 overflow-y-auto">
        <div className="max-w-2xl mx-auto">
          <h1 className="text-3xl font-bold text-gray-900 mb-6">
            SessionList + MemoryPanel Test
          </h1>

          {/* Current State */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Current State
            </h2>
            <div className="space-y-2 text-sm">
              <div>
                <span className="font-medium text-gray-700">Active Session ID:</span>
                <code className="ml-2 px-2 py-1 bg-gray-100 rounded text-blue-600 text-xs">
                  {currentSessionId || 'None'}
                </code>
              </div>
              <div>
                <span className="font-medium text-gray-700">Last Action:</span>
                <span className="ml-2 text-gray-600">
                  {selectedInfo || 'No action yet'}
                </span>
              </div>
              <div>
                <span className="font-medium text-gray-700">Memory Panel:</span>
                <span className="ml-2 text-gray-600">
                  {memoryOpen ? '✅ Open' : '❌ Closed'}
                </span>
              </div>
            </div>
          </div>

          {/* Show Memory Button */}
          <div className="bg-white rounded-lg shadow-md p-6 mb-6">
            <h2 className="text-lg font-semibold text-gray-900 mb-3">
              Memory Panel Control
            </h2>
            <button
              onClick={handleShowMemory}
              disabled={!currentSessionId}
              className={`px-6 py-3 rounded-lg font-medium transition-all ${
                currentSessionId
                  ? 'bg-gradient-to-r from-blue-500 to-purple-600 text-white hover:from-blue-600 hover:to-purple-700'
                  : 'bg-gray-200 text-gray-400 cursor-not-allowed'
              }`}
            >
              💭 Show Memory Panel
            </button>
            {!currentSessionId && (
              <p className="text-xs text-gray-500 mt-2">
                Select a session first
              </p>
            )}
          </div>

          {/* Test Instructions */}
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-6 mb-6">
            <h2 className="text-lg font-semibold text-blue-900 mb-3">
              Test Instructions
            </h2>
            <ul className="space-y-2 text-sm text-blue-800">
              <li>✅ Select a session from the list</li>
              <li>✅ Click "Show Memory Panel" button</li>
              <li>✅ Check if facts load</li>
              <li>✅ Check importance stars display</li>
              <li>✅ Check tags display</li>
              <li>✅ Check timestamps ("X ago")</li>
              <li>✅ Click ✕ to close panel</li>
              <li>✅ Check slide-in animation</li>
            </ul>
          </div>

          {/* API Info */}
          <div className="p-4 bg-gray-100 rounded-lg text-xs text-gray-600">
            <strong>Sessions API:</strong> http://localhost:8000/api/v1/sessions
            <br />
            <strong>Facts API:</strong> http://localhost:8000/api/v1/sessions/{'{id}'}/facts
          </div>
        </div>
      </div>

      {/* MemoryPanel (conditional) */}
      {memoryOpen && currentSessionId && (
        <MemoryPanel
          sessionId={currentSessionId}
          onClose={() => setMemoryOpen(false)}
        />
      )}
    </div>
  )
}