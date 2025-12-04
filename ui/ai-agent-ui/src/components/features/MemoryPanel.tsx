'use client'
import React, { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api/client'
import { SessionFact } from '@/types'

interface MemoryPanelProps {
  sessionId?: string
  isOpen?: boolean
  onClose?: () => void
}

export function MemoryPanel({ sessionId, isOpen, onClose }: MemoryPanelProps) {
  const [facts, setFacts] = useState<SessionFact[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Load facts when sessionId changes
  useEffect(() => {
    if (sessionId && isOpen) {
      loadFacts()
    }
  }, [sessionId, isOpen])

  const loadFacts = async () => {
    if (!sessionId) return

    try {
      setLoading(true)
      setError(null)
      const data = await apiClient.getSessionFacts(sessionId)
      setFacts(data.facts)
    } catch (err: any) {
      console.error('Failed to load facts:', err)
      setError(err.message || 'Failed to load facts')
    } finally {
      setLoading(false)
    }
  }

  // Render importance stars
  const renderStars = (importance: number) => {
    const stars = Math.round(importance * 5) // Convert 0-1 to 0-5 stars
    return '⭐'.repeat(stars)
  }

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
    <div className="h-full flex flex-col bg-slate-950">
      <div className="px-4 py-3 border-b border-slate-700 flex items-center justify-between">
        <h2 className="text-sm font-semibold text-slate-200">Memory</h2>
        <button
          onClick={onClose}
          className="text-xs text-slate-400 hover:text-slate-200"
        >
          ✕ Close
        </button>
      </div>

      <div className="flex-1 overflow-y-auto p-4">
        {loading && (
          <div className="text-center text-slate-400 text-sm py-8">
            Loading facts...
          </div>
        )}

        {error && (
          <div className="text-center text-red-400 text-sm py-4">
            {error}
          </div>
        )}

        {!loading && !error && facts.length === 0 && (
          <div className="text-center text-slate-500 text-sm py-8">
            No facts extracted yet for this session.
          </div>
        )}

        {!loading && !error && facts.length > 0 && (
          <div className="space-y-3">
            {facts.map((fact) => (
              <div
                key={fact.fact_id}
                className="p-3 bg-slate-900 rounded border border-slate-800 hover:border-slate-700"
              >
                <div className="flex items-start justify-between gap-2 mb-2">
                  <span className="text-yellow-400 text-sm">
                    {renderStars(fact.importance)}
                  </span>
                  <span className="text-xs text-slate-500">
                    {fact.fact_type}
                  </span>
                </div>
                <p className="text-sm text-slate-300 leading-relaxed">
                  {fact.text}
                </p>
                {fact.tags && fact.tags.length > 0 && (
                  <div className="flex flex-wrap gap-1 mt-2">
                    {fact.tags.map((tag, idx) => (
                      <span
                        key={idx}
                        className="px-2 py-0.5 text-xs bg-slate-800 text-slate-400 rounded"
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

      {!loading && !error && facts.length > 0 && (
        <div className="px-4 py-2 border-t border-slate-700 text-xs text-slate-500">
          {facts.length} fact{facts.length !== 1 ? 's' : ''} found
        </div>
      )}
    </div>
  )
}