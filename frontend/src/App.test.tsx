import { render, screen, waitFor } from '@testing-library/react'
import { vi } from 'vitest'

import { App } from './App'

describe('App', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('renders the Stage 2 application shell and reports API health', async () => {
    vi.stubGlobal(
      'fetch',
      vi.fn().mockResolvedValue({
        ok: true,
        json: () => Promise.resolve({
          status: 'ok',
          service: 'api',
          version: '0.1.0',
          environment: 'test',
        }),
      }),
    )

    render(<App />)

    expect(screen.getByRole('heading', { name: /turn career experience/i })).toBeInTheDocument()
    expect(screen.getByRole('heading', { name: 'Career assets' })).toBeInTheDocument()
    await waitFor(() => expect(screen.getByText('API online · v0.1.0')).toBeInTheDocument())
  })

  it('shows a useful warning when the API is unavailable', async () => {
    vi.stubGlobal('fetch', vi.fn().mockRejectedValue(new Error('connection refused')))

    render(<App />)

    expect(await screen.findByText(/local API could not be reached/i)).toBeInTheDocument()
  })
})
