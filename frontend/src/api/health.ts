export interface HealthResponse {
  status: 'ok'
  service: 'api'
  version: string
  environment: string
}

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? 'http://127.0.0.1:8000/api'

export async function fetchHealth(signal?: AbortSignal): Promise<HealthResponse> {
  const response = await fetch(`${apiBaseUrl}/health`, { signal })
  if (!response.ok) {
    throw new Error(`API health check failed with status ${response.status}`)
  }
  const payload = (await response.json()) as unknown
  return payload as HealthResponse
}
