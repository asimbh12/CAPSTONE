import DifferenceOutlined from '@mui/icons-material/DifferenceOutlined'
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Dialog, DialogActions,
  DialogContent, DialogTitle, FormControlLabel, Radio, RadioGroup, Stack, Typography,
} from '@mui/material'
import { useCallback, useEffect, useState } from 'react'

import { careerApi } from '../api/client'
import { Feedback } from '../components/Feedback'
import { PageHeader } from '../components/PageHeader'
import type { TimelineDuplicateGroup, TimelineItem } from '../types/career'

export function TimelinePage() {
  const [items, setItems] = useState<TimelineItem[] | null>(null)
  const [duplicateGroups, setDuplicateGroups] = useState<TimelineDuplicateGroup[]>([])
  const [reviewGroup, setReviewGroup] = useState<TimelineDuplicateGroup | null>(null)
  const [keepId, setKeepId] = useState('')
  const [confirming, setConfirming] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [timeline, duplicates] = await Promise.all([
        careerApi.timeline(), careerApi.timelineDuplicates(),
      ])
      setItems(timeline)
      setDuplicateGroups(duplicates)
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load timeline')
    }
  }, [])

  useEffect(() => { void load() }, [load])

  function review(group: TimelineDuplicateGroup) {
    const preferred = [...group.items].sort((left, right) => right.evidence_count - left.evidence_count)[0]
    setReviewGroup(group)
    setKeepId(preferred?.id ?? '')
  }

  async function resolveDuplicates() {
    if (!reviewGroup || !keepId) return
    const archiveIds = reviewGroup.items.filter((item) => item.id !== keepId).map((item) => item.id)
    setBusy(true)
    setError(null)
    try {
      await careerApi.resolveTimelineDuplicates(keepId, archiveIds)
      setFeedback(`Kept one record and archived ${archiveIds.length} duplicate${archiveIds.length === 1 ? '' : 's'}. No information was permanently deleted.`)
      setConfirming(false)
      setReviewGroup(null)
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to resolve duplicate records')
      setConfirming(false)
    } finally {
      setBusy(false)
    }
  }

  const archiveCount = reviewGroup ? reviewGroup.items.length - 1 : 0

  return (
    <>
      <PageHeader title="Career timeline" description="A chronological projection generated from active career assets." />
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {duplicateGroups.length > 0 && <Alert severity="warning" sx={{ mb: 3 }} action={<Button color="inherit" size="small" startIcon={<DifferenceOutlined />} onClick={() => review(duplicateGroups[0])}>Review matches</Button>}><Typography fontWeight={800}>{duplicateGroups.length} possible duplicate group{duplicateGroups.length === 1 ? '' : 's'} found</Typography><Typography variant="body2">Nothing will be removed without your confirmation.</Typography></Alert>}
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

      <Dialog open={Boolean(reviewGroup)} onClose={() => !busy && setReviewGroup(null)} fullWidth maxWidth="md">
        <DialogTitle>Review possible duplicate records</DialogTitle>
        <DialogContent>
          {reviewGroup && <>
            <Alert severity="info" sx={{ mb: 2 }}>{reviewGroup.confidence}% match confidence · {reviewGroup.reasons.join(' · ')}</Alert>
            <Typography mb={2}>Select the most complete record to keep. The other record{archiveCount === 1 ? '' : 's'} will be archived only after a second confirmation.</Typography>
            <RadioGroup value={keepId} onChange={(event) => setKeepId(event.target.value)}>
              <Stack gap={2}>
                {reviewGroup.items.map((item) => <Card variant="outlined" key={item.id}><CardContent><FormControlLabel value={item.id} control={<Radio />} label={<Box><Typography fontWeight={800}>{item.title}</Typography><Typography variant="body2" color="text.secondary">{[item.start_date, item.role, item.organisation, item.category].filter(Boolean).join(' · ')}</Typography><Typography variant="body2" mt={1}>{item.description || 'No description provided.'}</Typography><Stack direction="row" gap={1} mt={1}><Chip size="small" label={`${item.evidence_count} evidence`} /><Chip size="small" variant="outlined" label={item.source_kind} /></Stack></Box>} sx={{ alignItems: 'flex-start', m: 0 }} /></CardContent></Card>)}
              </Stack>
            </RadioGroup>
            {duplicateGroups.length > 1 && <Typography variant="body2" color="text.secondary" mt={2}>Resolve this group first; the next possible match will remain available for review.</Typography>}
          </>}
        </DialogContent>
        <DialogActions><Button onClick={() => setReviewGroup(null)} disabled={busy}>Cancel</Button><Button variant="contained" color="warning" disabled={!keepId || busy} onClick={() => setConfirming(true)}>Keep selected record</Button></DialogActions>
      </Dialog>

      <Dialog open={confirming} onClose={() => !busy && setConfirming(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Confirm duplicate resolution</DialogTitle>
        <DialogContent><Alert severity="warning"><Typography fontWeight={800}>Archive {archiveCount} duplicate record{archiveCount === 1 ? '' : 's'}?</Typography><Typography variant="body2">The selected record will remain active. Rejected records are retained in the local database and audit history; they are not permanently deleted.</Typography></Alert></DialogContent>
        <DialogActions><Button onClick={() => setConfirming(false)} disabled={busy}>Go back</Button><Button variant="contained" color="warning" disabled={busy} onClick={() => void resolveDuplicates()}>{busy ? 'Archiving…' : 'Confirm and archive'}</Button></DialogActions>
      </Dialog>
      <Feedback message={feedback} onClose={() => setFeedback(null)} />
    </>
  )
}
