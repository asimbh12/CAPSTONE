import AccountCircleOutlined from '@mui/icons-material/AccountCircleOutlined'
import BackupOutlined from '@mui/icons-material/BackupOutlined'
import FolderCopyOutlined from '@mui/icons-material/FolderCopyOutlined'
import InsightsOutlined from '@mui/icons-material/InsightsOutlined'
import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import TimelineOutlined from '@mui/icons-material/TimelineOutlined'
import WorkOutlineOutlined from '@mui/icons-material/WorkOutlineOutlined'
import TrackChangesOutlined from '@mui/icons-material/TrackChangesOutlined'
import {
  AppBar,
  Box,
  Button,
  Chip,
  Container,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import type { ReactNode } from 'react'

import { useApiHealth } from '../hooks/useApiHealth'

export type PageKey = 'overview' | 'onboarding' | 'assets' | 'timeline' | 'opportunities' | 'targets' | 'profile' | 'data'

interface AppLayoutProps {
  page: PageKey
  onNavigate: (page: PageKey) => void
  children: ReactNode
}

const navigation: Array<{ key: PageKey; label: string; icon: ReactNode }> = [
  { key: 'overview', label: 'Overview', icon: <InsightsOutlined fontSize="small" /> },
  { key: 'onboarding', label: 'Import career', icon: <AutoAwesomeOutlined fontSize="small" /> },
  { key: 'assets', label: 'Career assets', icon: <FolderCopyOutlined fontSize="small" /> },
  { key: 'timeline', label: 'Timeline', icon: <TimelineOutlined fontSize="small" /> },
  { key: 'opportunities', label: 'Opportunities', icon: <WorkOutlineOutlined fontSize="small" /> },
  { key: 'targets', label: 'Targets', icon: <TrackChangesOutlined fontSize="small" /> },
  { key: 'profile', label: 'Profile & goals', icon: <AccountCircleOutlined fontSize="small" /> },
  { key: 'data', label: 'Data safety', icon: <BackupOutlined fontSize="small" /> },
]

export function AppLayout({ page, onNavigate, children }: AppLayoutProps) {
  const health = useApiHealth()
  return (
    <Box minHeight="100vh">
      <AppBar position="sticky" color="inherit" elevation={0}>
        <Toolbar sx={{ borderBottom: '1px solid', borderColor: 'divider', gap: 2 }}>
          <InsightsOutlined sx={{ color: 'primary.main' }} />
          <Typography variant="h6" fontWeight={900} sx={{ mr: 1 }}>
            CAPSTONE
          </Typography>
          <Stack
            direction="row"
            spacing={0.5}
            sx={{ flex: 1, overflowX: 'auto', py: 1 }}
            component="nav"
            aria-label="Primary navigation"
          >
            {navigation.map((item) => (
              <Button
                key={item.key}
                color={page === item.key ? 'primary' : 'inherit'}
                variant={page === item.key ? 'contained' : 'text'}
                startIcon={item.icon}
                onClick={() => onNavigate(item.key)}
                aria-current={page === item.key ? 'page' : undefined}
                sx={{ whiteSpace: 'nowrap' }}
              >
                {item.label}
              </Button>
            ))}
          </Stack>
          <Chip
            size="small"
            label={health.status === 'online' ? 'Local API online' : 'API unavailable'}
            color={health.status === 'online' ? 'success' : health.status === 'offline' ? 'error' : 'default'}
            variant="outlined"
            aria-live="polite"
          />
        </Toolbar>
      </AppBar>
      <Container maxWidth="xl" sx={{ py: { xs: 3, md: 5 } }}>
        {children}
      </Container>
    </Box>
  )
}
