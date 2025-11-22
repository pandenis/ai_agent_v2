'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api/client'

export function useMemoryStats() {
  const [stats, setStats] = useState<{
    total_facts: number
    facts_by_type: Record<string, number>
    avg_importance: number
  } | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchStats() {
      try {
        setLoading(true)
        const data = await apiClient.getMemoryStats()
        setStats(data)
        setError(null)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch memory stats')
      } finally {
        setLoading(false)
      }
    }

    fetchStats()
  }, [])

  return { stats, loading, error }
}

export function useMemoryFacts(limit: number = 10) {
  const [facts, setFacts] = useState<any[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function fetchFacts() {
      try {
        setLoading(true)
        const data = await apiClient.getMemoryFacts(limit)
        setFacts(data.facts)
        setError(null)
      } catch (err: any) {
        setError(err.message || 'Failed to fetch facts')
      } finally {
        setLoading(false)
      }
    }

    fetchFacts()
  }, [limit])

  return { facts, loading, error }
}
