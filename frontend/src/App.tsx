import { Alert } from '@mui/material'
import { useState } from 'react'

import { AppLayout, type PageKey } from './components/AppLayout'
import { AssetsPage } from './pages/AssetsPage'
import { DataPage } from './pages/DataPage'
import { OverviewPage } from './pages/OverviewPage'
import { OnboardingPage } from './pages/OnboardingPage'
import { OpportunitiesPage } from './pages/OpportunitiesPage'
import { ProfilePage } from './pages/ProfilePage'
import { TimelinePage } from './pages/TimelinePage'

export function App() {
  const [page, setPage] = useState<PageKey>('overview')
  const content = {
    overview: <OverviewPage />,
    onboarding: <OnboardingPage />,
    assets: <AssetsPage />,
    timeline: <TimelinePage />,
    opportunities: <OpportunitiesPage />,
    profile: <ProfilePage />,
    data: <DataPage />,
  }[page] ?? <Alert severity="error">Unknown page.</Alert>

  return <AppLayout page={page} onNavigate={setPage}>{content}</AppLayout>
}
