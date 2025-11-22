'use client'

import { useState, useEffect } from 'react'
import { apiClient } from '@/lib/api/client'

export function useHealth() {
  const [status, setStatus] = useState<'healthy' | 'unhealthy' | 'checking'>('checking')
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    async function checkHealth() {
      try {
        const data = await apiClient.health()
        setStatus(data.status === 'healthy' ? 'healthy' : 'unhealthy')
        setError(null)
      } catch (err: any) {
        setStatus('unhealthy')
        setError(err.message || 'API is not responding')
      }
    }

    checkHealth()
    // Check every 30 seconds
    const interval = setInterval(checkHealth, 30000)
    
    return () => clearInterval(interval)
  }, [])

  return { status, error }
}
