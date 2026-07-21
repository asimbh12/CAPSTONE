import { Alert } from '@mui/material'
import { useState } from 'react'

import { AppLayout, type PageKey } from './components/AppLayout'
import { AssetsPage } from './pages/AssetsPage'
import { DataPage } from './pages/DataPage'
import { OverviewPage } from './pages/OverviewPage'
import { ProfilePage } from './pages/ProfilePage'
import { TimelinePage } from './pages/TimelinePage'

export function App() {
  const [page, setPage] = useState<PageKey>('overview')
  const content = {
    overview: <OverviewPage />,
    assets: <AssetsPage />,
    timeline: <TimelinePage />,
    profile: <ProfilePage />,
    data: <DataPage />,
  }[page] ?? <Alert severity="error">Unknown page.</Alert>

  return <AppLayout page={page} onNavigate={setPage}>{content}</AppLayout>
}
