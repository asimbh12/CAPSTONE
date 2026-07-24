import { Alert } from '@mui/material'
import { useState } from 'react'

import { AppLayout, type PageKey } from './components/AppLayout'
import { AssetsPage } from './pages/AssetsPage'
import { DataPage } from './pages/DataPage'
import { OverviewPage } from './pages/OverviewPage'
import { OnboardingPage } from './pages/OnboardingPage'
import { OpportunitiesPage } from './pages/OpportunitiesPage'
import { ApplicationsPage } from './pages/ApplicationsPage'
import { ProfilePage } from './pages/ProfilePage'
import { TimelinePage } from './pages/TimelinePage'
import { TargetsPage } from './pages/TargetsPage'

export function App() {
  const [page, setPage] = useState<PageKey>('overview')
  const content = {
    overview: <OverviewPage onNavigate={setPage} />,
    onboarding: <OnboardingPage />,
    assets: <AssetsPage />,
    timeline: <TimelinePage />,
    opportunities: <OpportunitiesPage />,
    applications: <ApplicationsPage />,
    targets: <TargetsPage />,
    profile: <ProfilePage />,
    data: <DataPage />,
  }[page] ?? <Alert severity="error">Unknown page.</Alert>

  return <AppLayout page={page} onNavigate={setPage}>{content}</AppLayout>
}
