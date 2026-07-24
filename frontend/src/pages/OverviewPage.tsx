import ArrowForwardOutlined from '@mui/icons-material/ArrowForwardOutlined'
import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import FolderCopyOutlined from '@mui/icons-material/FolderCopyOutlined'
import FlagOutlined from '@mui/icons-material/FlagOutlined'
import TaskAltOutlined from '@mui/icons-material/TaskAltOutlined'
import TimelineOutlined from '@mui/icons-material/TimelineOutlined'
import WorkOutlineOutlined from '@mui/icons-material/WorkOutlineOutlined'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  Stack,
  Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'

import { careerApi } from '../api/client'
import type { PageKey } from '../components/AppLayout'
import { PageHeader } from '../components/PageHeader'
import type { Dashboard, DashboardAction } from '../types/career'

interface OverviewPageProps {
  onNavigate: (page: PageKey) => void
}

const urgencyColor: Record<DashboardAction['urgency'], 'error' | 'warning' | 'info' | 'default'> = {
  critical: 'error',
  high: 'warning',
  medium: 'info',
  low: 'default',
}

export function OverviewPage({ onNavigate }: OverviewPageProps) {
  const [dashboard, setDashboard] = useState<Dashboard | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void careerApi.dashboard()
      .then(setDashboard)
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Unable to load overview'))
  }, [])

  if (error) return <Alert severity="error">{error}</Alert>
  if (!dashboard) return <CircularProgress aria-label="Loading overview" />

  const metrics = dashboard.metrics
  return (
    <>
      <PageHeader
        eyebrow="CAREER INTELLIGENCE COMMAND CENTRE"
        title={dashboard.profile_name ? `Welcome, ${dashboard.profile_name}` : 'Build your career intelligence foundation'}
        description="See what is established, what needs attention, and the most valuable next actions across your career strategy."
      />
      <Grid container spacing={3} mb={5}>
        {[
          { label: 'Active assets', value: metrics.active_assets, icon: <FolderCopyOutlined /> },
          { label: 'Asset categories', value: metrics.asset_categories, icon: <AutoAwesomeOutlined /> },
          { label: 'Strategic goals', value: metrics.strategic_goals, icon: <FlagOutlined /> },
          { label: 'Timeline events', value: metrics.timeline_events, icon: <TimelineOutlined /> },
          { label: 'Open opportunities', value: metrics.open_opportunities, icon: <WorkOutlineOutlined /> },
          { label: 'Closing soon', value: metrics.closing_soon, icon: <WorkOutlineOutlined /> },
        ].map((metric) => (
          <Grid key={metric.label} size={{ xs: 12, sm: 6, md: 4, lg: 2 }}>
            <Card>
              <CardContent>
                <Stack direction="row" justifyContent="space-between" color="primary.main">
                  <Typography color="text.secondary" fontWeight={700}>{metric.label}</Typography>
                  {metric.icon}
                </Stack>
                <Typography variant="h3" mt={2}>{metric.value}</Typography>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      <Stack direction="row" alignItems="center" justifyContent="space-between" gap={2} mb={2}>
        <Box>
          <Typography variant="h4">Next best actions</Typography>
          <Typography color="text.secondary">Deterministic recommendations based on incomplete or time-sensitive workflows.</Typography>
        </Box>
        {dashboard.actions.length === 0 && <Chip color="success" icon={<TaskAltOutlined />} label="Core workflows up to date" />}
      </Stack>
      {dashboard.actions.length === 0 ? (
        <Alert severity="success" sx={{ mb: 5 }}>No urgent workflow gaps were detected. Continue maintaining evidence, targets, opportunities and regular backups.</Alert>
      ) : (
        <Grid container spacing={2} mb={5}>
          {dashboard.actions.map((action, index) => (
            <Grid key={action.key} size={{ xs: 12, md: 6 }}>
              <Card variant={index === 0 ? 'elevation' : 'outlined'} sx={index === 0 ? { border: '1px solid', borderColor: 'primary.main' } : undefined}>
                <CardContent>
                  <Stack direction="row" justifyContent="space-between" gap={2} alignItems="flex-start">
                    <Box>
                      <Stack direction="row" gap={1} alignItems="center" mb={1}>
                        <Chip size="small" color={urgencyColor[action.urgency]} label={action.urgency} />
                        {action.count > 1 && <Chip size="small" variant="outlined" label={`${action.count} records`} />}
                      </Stack>
                      <Typography variant="h6">{action.title}</Typography>
                      <Typography color="text.secondary" mt={0.5}>{action.description}</Typography>
                    </Box>
                    <Typography variant="h5" color="primary.main">#{index + 1}</Typography>
                  </Stack>
                  <Button sx={{ mt: 2 }} endIcon={<ArrowForwardOutlined />} onClick={() => onNavigate(action.page)}>Open workspace</Button>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}

      <Typography variant="h4" mb={2}>Recent career assets</Typography>
      {dashboard.recent_assets.length === 0 ? (
        <Card><CardContent><Typography color="text.secondary">No career assets yet.</Typography></CardContent></Card>
      ) : (
        <Grid container spacing={2}>
          {dashboard.recent_assets.map((asset) => (
            <Grid key={asset.id} size={{ xs: 12, md: 6 }}>
              <Card>
                <CardContent>
                  <Typography color="secondary.main" fontWeight={800}>{asset.category}</Typography>
                  <Typography variant="h6">{asset.title}</Typography>
                  <Typography color="text.secondary" mt={1}>{asset.impact_summary || asset.description || 'No summary yet.'}</Typography>
                  <Box mt={2}><Typography variant="caption">{asset.evidence.length} evidence item{asset.evidence.length === 1 ? '' : 's'}</Typography></Box>
                </CardContent>
              </Card>
            </Grid>
          ))}
        </Grid>
      )}
    </>
  )
}
