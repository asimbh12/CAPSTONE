import { useEffect, useState } from 'react'

import { fetchHealth, type HealthResponse } from '../api/health'

type HealthState =
  | { status: 'checking' }
  | { status: 'online'; data: HealthResponse }
  | { status: 'offline'; message: string }

export function useApiHealth(): HealthState {
  const [state, setState] = useState<HealthState>({ status: 'checking' })

  useEffect(() => {
    const controller = new AbortController()
    fetchHealth(controller.signal)
      .then((data) => setState({ status: 'online', data }))
      .catch((error: unknown) => {
        if (!controller.signal.aborted) {
          const message = error instanceof Error ? error.message : 'Unknown API error'
          setState({ status: 'offline', message })
        }
      })
    return () => controller.abort()
  }, [])

  return state
}

