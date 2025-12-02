'use client'

import React from 'react'

interface MemoryPanelProps {
  sessionId?: string
  isOpen?: boolean
  onClose?: () => void
}

export function MemoryPanel({ sessionId, isOpen, onClose }: MemoryPanelProps) {
  if (!isOpen || !sessionId) {
    return (
      <div className="h-full flex flex-col">
        <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
          <h2 className="text-sm font-semibold text-gray-900">Memory Panel</h2>
        </div>
        <div className="flex-1 flex items-center justify-center text-xs text-gray-400 px-4 text-center">
          Select a session to view memory.
        </div>
      </div>
    )
  }

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-3 border-b border-gray-200 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-gray-900">Memory for Session</h2>
        <button
          onClick={onClose}
          className="text-xs text-gray-500 hover:text-gray-700"
        >
          Close
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4 text-xs text-gray-600">
        <div className="text-gray-400 mb-2">
          TODO: load and display facts for session <span className="font-mono">{sessionId}</span>
        </div>
      </div>
    </div>
  )
}
