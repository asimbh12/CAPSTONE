import AddOutlined from '@mui/icons-material/AddOutlined'
import ArchiveOutlined from '@mui/icons-material/ArchiveOutlined'
import EditOutlined from '@mui/icons-material/EditOutlined'
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, Divider, FormControl,
  Grid, InputLabel, LinearProgress, MenuItem, Select, Stack, TextField, Typography,
} from '@mui/material'
import { type FormEvent, useCallback, useEffect, useState } from 'react'

import { careerApi } from '../api/client'
import { Feedback } from '../components/Feedback'
import { PageHeader } from '../components/PageHeader'
import type { Fellowship, FellowshipInput, Target } from '../types/career'

const emptyForm = (): FellowshipInput => ({
  name: '',
  organisation: '',
  website: '',
  deadline: null,
  status: 'exploring',
  target_id: null,
  opportunity_id: null,
  sponsor_name: '',
  sponsor_status: 'not_identified',
  next_action: '',
  notes: '',
})

export function FellowshipsPage() {
  const [items, setItems] = useState<Fellowship[] | null>(null)
  const [summary, setSummary] = useState({ active: 0, closing_soon: 0, sponsor_attention: 0 })
  const [targets, setTargets] = useState<Target[]>([])
  const [form, setForm] = useState<FellowshipInput>(emptyForm())
  const [editingId, setEditingId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [fellowships, targetRows] = await Promise.all([
        careerApi.listFellowships(),
        careerApi.listTargets(),
      ])
      setItems(fellowships.items)
      setSummary({
        active: fellowships.active,
        closing_soon: fellowships.closing_soon,
        sponsor_attention: fellowships.sponsor_attention,
      })
      setTargets(targetRows)
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load fellowships')
    }
  }, [])

  useEffect(() => { void load() }, [load])

  async function save(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (editingId) await careerApi.updateFellowship(editingId, form)
      else await careerApi.createFellowship(form)
      setFeedback(editingId ? 'Fellowship workflow updated.' : 'Fellowship added.')
      setEditingId(null)
      setForm(emptyForm())
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to save fellowship')
    } finally {
      setBusy(false)
    }
  }

  function edit(item: Fellowship) {
    setEditingId(item.id)
    setForm({
      name: item.name,
      organisation: item.organisation,
      website: item.website,
      deadline: item.deadline,
      status: item.status,
      target_id: item.target_id,
      opportunity_id: item.opportunity_id,
      sponsor_name: item.sponsor_name,
      sponsor_status: item.sponsor_status,
      next_action: item.next_action,
      notes: item.notes,
    })
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function archive(id: string) {
    setBusy(true)
    try {
      await careerApi.archiveFellowship(id)
      setFeedback('Fellowship archived.')
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to archive fellowship')
    } finally {
      setBusy(false)
    }
  }

  return <>
    <PageHeader
      eyebrow="RECOGNITION PATHWAYS"
      title="Fellowship dashboard"
      description="Track fellowship deadlines, sponsor readiness, next actions and evidence-based readiness without duplicating career assets."
    />
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Grid container spacing={2} mb={3}>
      {[
        ['Active pathways', summary.active],
        ['Closing within 30 days', summary.closing_soon],
        ['Sponsor attention', summary.sponsor_attention],
      ].map(([label, value]) => <Grid key={label} size={{ xs: 12, sm: 4 }}>
        <Card><CardContent><Typography color="text.secondary">{label}</Typography>
          <Typography variant="h3" color="primary.main">{value}</Typography>
        </CardContent></Card>
      </Grid>)}
    </Grid>
    <Card sx={{ mb: 3 }}><CardContent>
      <Typography variant="h6" gutterBottom>{editingId ? 'Update fellowship' : 'Add fellowship'}</Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        Link a fellowship to an existing target to reuse its criteria, mapped career evidence and
        latest readiness assessment. Record only public professional sponsor information.
      </Alert>
      <Box component="form" onSubmit={event => void save(event)}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}><TextField required fullWidth label="Fellowship" value={form.name} onChange={event => setForm({ ...form, name: event.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Organisation" value={form.organisation} onChange={event => setForm({ ...form, organisation: event.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Public website" value={form.website} onChange={event => setForm({ ...form, website: event.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 3 }}><TextField fullWidth type="date" label="Deadline" slotProps={{ inputLabel: { shrink: true } }} value={form.deadline ?? ''} onChange={event => setForm({ ...form, deadline: event.target.value || null })} /></Grid>
          <Grid size={{ xs: 12, md: 3 }}><FormControl fullWidth><InputLabel>Workflow status</InputLabel>
            <Select label="Workflow status" value={form.status} onChange={event => setForm({ ...form, status: event.target.value })}>
              {['exploring', 'preparing', 'seeking_sponsor', 'ready', 'submitted', 'awarded', 'unsuccessful', 'paused'].map(value => <MenuItem key={value} value={value}>{value.replaceAll('_', ' ')}</MenuItem>)}
            </Select>
          </FormControl></Grid>
          <Grid size={{ xs: 12, md: 6 }}><FormControl fullWidth><InputLabel>Readiness target</InputLabel>
            <Select label="Readiness target" value={form.target_id ?? ''} onChange={event => setForm({ ...form, target_id: event.target.value || null })}>
              <MenuItem value="">Not linked yet</MenuItem>
              {targets.map(target => <MenuItem key={target.id} value={target.id}>{target.title}</MenuItem>)}
            </Select>
          </FormControl></Grid>
          <Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Sponsor or nominator" value={form.sponsor_name} onChange={event => setForm({ ...form, sponsor_name: event.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 4 }}><FormControl fullWidth><InputLabel>Sponsor status</InputLabel>
            <Select label="Sponsor status" value={form.sponsor_status} onChange={event => setForm({ ...form, sponsor_status: event.target.value })}>
              {['not_identified', 'candidate', 'approached', 'confirmed', 'not_required'].map(value => <MenuItem key={value} value={value}>{value.replaceAll('_', ' ')}</MenuItem>)}
            </Select>
          </FormControl></Grid>
          <Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Next action" value={form.next_action} onChange={event => setForm({ ...form, next_action: event.target.value })} /></Grid>
          <Grid size={12}><TextField fullWidth multiline minRows={2} label="Public professional notes" value={form.notes} onChange={event => setForm({ ...form, notes: event.target.value })} /></Grid>
          <Grid size={12}><Stack direction="row" gap={1}>
            <Button type="submit" variant="contained" disabled={busy || !form.name.trim()} startIcon={busy ? <CircularProgress size={18} /> : <AddOutlined />}>{editingId ? 'Save fellowship' : 'Add fellowship'}</Button>
            {editingId && <Button onClick={() => { setEditingId(null); setForm(emptyForm()) }}>Cancel</Button>}
          </Stack></Grid>
        </Grid>
      </Box>
    </CardContent></Card>
    {!items ? <CircularProgress aria-label="Loading fellowships" /> : <Grid container spacing={2}>
      {items.map(item => <Grid key={item.id} size={{ xs: 12, lg: 6 }}><Card sx={{ height: '100%' }}><CardContent>
        <Stack direction="row" justifyContent="space-between" gap={2}>
          <Box><Typography variant="h6">{item.name}</Typography><Typography color="text.secondary">{item.organisation}</Typography></Box>
          <Chip label={item.status.replaceAll('_', ' ')} color={item.status === 'awarded' ? 'success' : item.deadline_status === 'closing_soon' ? 'warning' : 'default'} />
        </Stack>
        <Stack direction="row" gap={1} flexWrap="wrap" mt={1}>
          <Chip size="small" variant="outlined" label={item.deadline ? `${item.days_remaining} days · ${item.deadline}` : 'No deadline'} />
          <Chip size="small" variant="outlined" label={`Sponsor: ${item.sponsor_status.replaceAll('_', ' ')}`} />
        </Stack>
        <Divider sx={{ my: 2 }} />
        {item.readiness_score === null ? <Alert severity="info">
          {item.target_id ? 'Linked target has not been assessed yet.' : 'Link a readiness target to reuse mapped career evidence.'}
        </Alert> : <>
          <Stack direction="row" justifyContent="space-between"><Typography fontWeight={800}>Readiness · {item.target_title}</Typography><Typography fontWeight={900} color="primary.main">{item.readiness_score}%</Typography></Stack>
          <LinearProgress variant="determinate" value={item.readiness_score} sx={{ mt: 1, height: 8, borderRadius: 2 }} />
          <Typography variant="caption">Version {item.readiness_version} · confidence {item.readiness_confidence}%</Typography>
          <Grid container spacing={1} mt={1}><Grid size={6}><Typography variant="caption" fontWeight={800}>Strengths</Typography><Typography variant="body2">{item.strengths.slice(0, 3).join(' · ') || 'None recorded'}</Typography></Grid><Grid size={6}><Typography variant="caption" fontWeight={800}>Gaps</Typography><Typography variant="body2">{item.gaps.slice(0, 3).join(' · ') || 'No major gaps'}</Typography></Grid></Grid>
        </>}
        <Typography mt={2} fontWeight={800}>Next action</Typography><Typography color="text.secondary">{item.next_action || 'Not set'}</Typography>
        <Stack direction="row" gap={1} mt={2}>
          <Button startIcon={<EditOutlined />} onClick={() => edit(item)}>Edit</Button>
          <Button color="inherit" startIcon={<ArchiveOutlined />} disabled={busy} onClick={() => void archive(item.id)}>Archive</Button>
        </Stack>
      </CardContent></Card></Grid>)}
    </Grid>}
    {items?.length === 0 && <Alert severity="info">No fellowship pathways yet. Add ATSE, AAHMS, IEEE, FIET, Engineers Australia or a custom fellowship above.</Alert>}
    <Feedback message={feedback} onClose={() => setFeedback(null)} />
  </>
}
