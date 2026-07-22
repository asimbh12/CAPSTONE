import AccountCircleOutlined from '@mui/icons-material/AccountCircleOutlined'
import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import BackupOutlined from '@mui/icons-material/BackupOutlined'
import FolderCopyOutlined from '@mui/icons-material/FolderCopyOutlined'
import InsightsOutlined from '@mui/icons-material/InsightsOutlined'
import MenuOutlined from '@mui/icons-material/MenuOutlined'
import TimelineOutlined from '@mui/icons-material/TimelineOutlined'
import TrackChangesOutlined from '@mui/icons-material/TrackChangesOutlined'
import WorkOutlineOutlined from '@mui/icons-material/WorkOutlineOutlined'
import {
  AppBar,
  Box,
  Chip,
  Container,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemIcon,
  ListItemText,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import { type ReactNode, useState } from 'react'

import { useApiHealth } from '../hooks/useApiHealth'

export type PageKey = 'overview' | 'onboarding' | 'assets' | 'timeline' | 'opportunities' | 'targets' | 'profile' | 'data'

interface AppLayoutProps {
  page: PageKey
  onNavigate: (page: PageKey) => void
  children: ReactNode
}

const drawerWidth = 256
const navigation: Array<{ key: PageKey; label: string; icon: ReactNode }> = [
  { key: 'overview', label: 'Overview', icon: <InsightsOutlined /> },
  { key: 'onboarding', label: 'Import career', icon: <AutoAwesomeOutlined /> },
  { key: 'assets', label: 'Career assets', icon: <FolderCopyOutlined /> },
  { key: 'timeline', label: 'Timeline', icon: <TimelineOutlined /> },
  { key: 'opportunities', label: 'Opportunities', icon: <WorkOutlineOutlined /> },
  { key: 'targets', label: 'Targets & readiness', icon: <TrackChangesOutlined /> },
  { key: 'profile', label: 'Profile & goals', icon: <AccountCircleOutlined /> },
  { key: 'data', label: 'Data safety', icon: <BackupOutlined /> },
]

export function AppLayout({ page, onNavigate, children }: AppLayoutProps) {
  const health = useApiHealth()
  const [mobileOpen, setMobileOpen] = useState(false)
  const status = health.status === 'online' ? 'Local API online' : 'API unavailable'

  const navigate = (key: PageKey) => {
    onNavigate(key)
    setMobileOpen(false)
  }
  const drawer = (
    <Stack height="100%">
      <Stack direction="row" alignItems="center" gap={1.5} px={2.5} py={2.5}>
        <Box sx={{ width: 38, height: 38, borderRadius: 2.5, bgcolor: 'primary.main', color: 'white', display: 'grid', placeItems: 'center' }}>
          <InsightsOutlined />
        </Box>
        <Box>
          <Typography fontWeight={900} letterSpacing=".04em">CAPSTONE</Typography>
          <Typography variant="caption" color="text.secondary">Career intelligence</Typography>
        </Box>
      </Stack>
      <Divider />
      <List component="nav" aria-label="Primary navigation" sx={{ px: 1.5, py: 2 }}>
        {navigation.map((item) => (
          <ListItemButton
            key={item.key}
            selected={page === item.key}
            onClick={() => navigate(item.key)}
            aria-current={page === item.key ? 'page' : undefined}
            sx={{ borderRadius: 2, mb: 0.5, minHeight: 46 }}
          >
            <ListItemIcon sx={{ minWidth: 40, color: page === item.key ? 'primary.main' : 'text.secondary' }}>{item.icon}</ListItemIcon>
            <ListItemText primary={item.label} primaryTypographyProps={{ fontWeight: page === item.key ? 800 : 600 }} />
          </ListItemButton>
        ))}
      </List>
      <Box flex={1} />
      <Divider />
      <Box p={2.5}>
        <Chip size="small" label={status} color={health.status === 'online' ? 'success' : health.status === 'offline' ? 'error' : 'default'} variant="outlined" aria-live="polite" />
        <Typography variant="caption" color="text.secondary" display="block" mt={1}>Single-user local workspace</Typography>
      </Box>
    </Stack>
  )

  return (
    <Box minHeight="100vh" sx={{ display: 'flex' }}>
      <AppBar position="fixed" color="inherit" elevation={0} sx={{ display: { md: 'none' }, borderBottom: '1px solid', borderColor: 'divider' }}>
        <Toolbar>
          <IconButton edge="start" onClick={() => setMobileOpen(true)} aria-label="Open navigation"><MenuOutlined /></IconButton>
          <Typography fontWeight={900} ml={1}>CAPSTONE</Typography>
          <Box flex={1} />
          <Chip size="small" label={health.status === 'online' ? 'Online' : 'Offline'} color={health.status === 'online' ? 'success' : 'error'} variant="outlined" />
        </Toolbar>
      </AppBar>
      <Box component="aside" sx={{ width: { md: drawerWidth }, flexShrink: { md: 0 } }}>
        <Drawer variant="temporary" open={mobileOpen} onClose={() => setMobileOpen(false)} sx={{ display: { xs: 'block', md: 'none' }, '& .MuiDrawer-paper': { width: drawerWidth } }}>{drawer}</Drawer>
        <Drawer variant="permanent" open sx={{ display: { xs: 'none', md: 'block' }, '& .MuiDrawer-paper': { width: drawerWidth, boxSizing: 'border-box' } }}>{drawer}</Drawer>
      </Box>
      <Box component="main" sx={{ flex: 1, minWidth: 0, pt: { xs: 8, md: 0 } }}>
        <Container maxWidth="xl" sx={{ py: { xs: 3, md: 5 }, px: { xs: 2, sm: 3, lg: 5 } }}>{children}</Container>
      </Box>
    </Box>
  )
}
