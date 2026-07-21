import { Alert, Card, CardContent, Chip, CircularProgress, Stack, Typography } from '@mui/material'
import { useEffect, useState } from 'react'

import { careerApi } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import type { TimelineItem } from '../types/career'

export function TimelinePage() {
  const [items, setItems] = useState<TimelineItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  useEffect(() => {
    void careerApi.timeline().then(setItems).catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Unable to load timeline'))
  }, [])
  return (
    <>
      <PageHeader title="Career timeline" description="A chronological projection generated from active career assets." />
      {error && <Alert severity="error">{error}</Alert>}
      {!items && !error && <CircularProgress aria-label="Loading timeline" />}
      <Stack spacing={2} sx={{ position: 'relative', pl: { md: 4 } }}>
        {items?.map((item) => (
          <Card key={item.id}>
            <CardContent>
              <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" gap={2}>
                <div>
                  <Typography variant="h6">{item.title}</Typography>
                  <Typography color="text.secondary">{[item.role, item.organisation].filter(Boolean).join(' · ') || 'Career event'}</Typography>
                </div>
                <Stack direction="row" gap={1} alignItems="center">
                  <Chip label={item.category} variant="outlined" />
                  <Typography fontWeight={700}>{item.start_date ?? 'Date not set'}</Typography>
                </Stack>
              </Stack>
            </CardContent>
          </Card>
        ))}
        {items?.length === 0 && <Typography color="text.secondary">Add dated career assets to build the timeline.</Typography>}
      </Stack>
    </>
  )
}

