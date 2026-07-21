import { render, screen, waitFor } from '@testing-library/react'
import userEvent from '@testing-library/user-event'
import { vi } from 'vitest'

import { App } from './App'

function jsonResponse(payload: unknown): Promise<Response> {
  return Promise.resolve({ ok: true, status: 200, json: () => Promise.resolve(payload) } as Response)
}

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders the Stage 3 overview and navigates to career assets', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn((input: RequestInfo | URL) => {
        const url = typeof input === 'string' ? input : input instanceof URL ? input.href : input.url
        if (url.endsWith('/health')) return jsonResponse({ status: 'ok', service: 'api', version: '0.1.0', environment: 'test' })
        if (url.includes('/assets?')) return jsonResponse({ items: [], total: 0 })
        if (url.endsWith('/profile')) return jsonResponse(null)
        if (url.endsWith('/goals') || url.endsWith('/themes') || url.endsWith('/organisations') || url.endsWith('/timeline')) return jsonResponse([])
        return Promise.reject(new Error(`Unexpected request: ${url}`))
      }),
    )

    render(<App />)
    expect(
      await screen.findByRole('heading', { name: /build your career intelligence foundation/i }),
    ).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('Local API online')).toBeInTheDocument())

    await userEvent.click(screen.getByRole('button', { name: 'Career assets' }))
    expect(await screen.findByRole('heading', { name: 'Career assets' })).toBeInTheDocument()
    expect(await screen.findByText(/No assets match these filters/i)).toBeInTheDocument()
  })

  it('shows a useful status when the API is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('connection refused')))
    render(<App />)
    expect(await screen.findByText('API unavailable')).toBeInTheDocument()
  })
})
