import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import FolderCopyOutlined from '@mui/icons-material/FolderCopyOutlined'
import FlagOutlined from '@mui/icons-material/FlagOutlined'
import TimelineOutlined from '@mui/icons-material/TimelineOutlined'
import WorkOutlineOutlined from '@mui/icons-material/WorkOutlineOutlined'
import { Alert, Box, Card, CardContent, CircularProgress, Grid, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'

import { careerApi } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import type { CareerAsset, Goal, OpportunitySummary, Profile, TimelineItem } from '../types/career'

interface OverviewState {
  profile: Profile | null
  assets: CareerAsset[]
  goals: Goal[]
  timeline: TimelineItem[]
  opportunities: OpportunitySummary
}

export function OverviewPage() {
  const [state, setState] = useState<OverviewState | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    void Promise.all([
      careerApi.getProfile(),
      careerApi.listAssets(new URLSearchParams({ asset_status: 'active' })),
      careerApi.listGoals(),
      careerApi.timeline(),
      careerApi.opportunitySummary(),
    ])
      .then(([profile, assets, goals, timeline, opportunities]) => setState({ profile, assets: assets.items, goals, timeline, opportunities }))
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Unable to load overview'))
  }, [])

  if (error) return <Alert severity="error">{error}</Alert>
  if (!state) return <CircularProgress aria-label="Loading overview" />

  const categoryCount = new Set(state.assets.map((asset) => asset.category)).size
  const latest = state.assets.slice(0, 4)
  return (
    <>
      <PageHeader
        eyebrow="CAREER INTELLIGENCE FOUNDATION"
        title={state.profile?.name ? `Welcome, ${state.profile.name}` : 'Build your career intelligence foundation'}
        description="Capture public professional achievements once, connect them to evidence and strategy, and reuse them across every future opportunity."
      />
      {!state.profile?.name && (
        <Alert severity="info" sx={{ mb: 3 }}>
          Begin with Profile & goals, then add your first career asset.
        </Alert>
      )}
      <Grid container spacing={3} mb={5}>
        {[
          { label: 'Active assets', value: state.assets.length, icon: <FolderCopyOutlined /> },
          { label: 'Asset categories', value: categoryCount, icon: <AutoAwesomeOutlined /> },
          { label: 'Strategic goals', value: state.goals.length, icon: <FlagOutlined /> },
          { label: 'Timeline events', value: state.timeline.length, icon: <TimelineOutlined /> },
          { label: 'Open opportunities', value: state.opportunities.active, icon: <WorkOutlineOutlined /> },
          { label: 'Closing soon', value: state.opportunities.closing_soon, icon: <WorkOutlineOutlined /> },
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
      <Typography variant="h4" mb={2}>Recent career assets</Typography>
      {latest.length === 0 ? (
        <Card><CardContent><Typography color="text.secondary">No career assets yet.</Typography></CardContent></Card>
      ) : (
        <Grid container spacing={2}>
          {latest.map((asset) => (
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
