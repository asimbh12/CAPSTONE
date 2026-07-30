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
import type { AwardInput, AwardPathway, Target } from '../types/career'

const emptyForm = (): AwardInput => ({
  name: '', organisation: '', award_type: 'custom', website: '', deadline: null,
  status: 'exploring', target_id: null, opportunity_id: null, nominator_name: '',
  nominator_status: 'not_identified', dossier_status: 'not_started',
  next_action: '', notes: '',
})

export function AwardsPage() {
  const [items, setItems] = useState<AwardPathway[] | null>(null)
  const [summary, setSummary] = useState({ active: 0, closing_soon: 0, nomination_attention: 0 })
  const [targets, setTargets] = useState<Target[]>([])
  const [form, setForm] = useState<AwardInput>(emptyForm())
  const [editingId, setEditingId] = useState<string | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  const load = useCallback(async () => {
    try {
      const [awards, targetRows] = await Promise.all([careerApi.listAwards(), careerApi.listTargets()])
      setItems(awards.items)
      setSummary({
        active: awards.active, closing_soon: awards.closing_soon,
        nomination_attention: awards.nomination_attention,
      })
      setTargets(targetRows)
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load awards')
    }
  }, [])

  useEffect(() => { void load() }, [load])

  async function save(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      if (editingId) await careerApi.updateAward(editingId, form)
      else await careerApi.createAward(form)
      setFeedback(editingId ? 'Award pathway updated.' : 'Award pathway added.')
      setEditingId(null)
      setForm(emptyForm())
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to save award')
    } finally { setBusy(false) }
  }

  function edit(item: AwardPathway) {
    const {
      name, organisation, award_type, website, deadline, status, target_id, opportunity_id,
      nominator_name, nominator_status, dossier_status, next_action, notes,
    } = item
    setForm({
      name, organisation, award_type, website, deadline, status, target_id, opportunity_id,
      nominator_name, nominator_status, dossier_status, next_action, notes,
    })
    setEditingId(item.id)
    window.scrollTo({ top: 0, behavior: 'smooth' })
  }

  async function archive(id: string) {
    setBusy(true)
    try {
      await careerApi.archiveAward(id)
      setFeedback('Award pathway archived.')
      await load()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to archive award')
    } finally { setBusy(false) }
  }

  return <>
    <PageHeader
      eyebrow="RECOGNITION STRATEGY"
      title="Awards and recognition"
      description="Plan national and industry awards, nomination relationships, evidence dossiers and target-linked readiness."
    />
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Grid container spacing={2} mb={3}>
      {[
        ['Active pathways', summary.active],
        ['Closing within 30 days', summary.closing_soon],
        ['Nominator attention', summary.nomination_attention],
      ].map(([label, value]) => <Grid key={label} size={{ xs: 12, sm: 4 }}>
        <Card><CardContent><Typography color="text.secondary">{label}</Typography>
          <Typography variant="h3" color="primary.main">{value}</Typography>
        </CardContent></Card>
      </Grid>)}
    </Grid>
    <Card sx={{ mb: 3 }}><CardContent>
      <Typography variant="h6" gutterBottom>{editingId ? 'Update award pathway' : 'Add award pathway'}</Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        Link an award to a readiness target so existing mapped achievements are reused. Keep
        nominator details to public professional information only.
      </Alert>
      <Box component="form" onSubmit={event => void save(event)}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}><TextField required fullWidth label="Award" value={form.name} onChange={e => setForm({ ...form, name: e.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Organisation" value={form.organisation} onChange={e => setForm({ ...form, organisation: e.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Public website" value={form.website} onChange={e => setForm({ ...form, website: e.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 3 }}><FormControl fullWidth><InputLabel>Award family</InputLabel><Select label="Award family" value={form.award_type} onChange={e => setForm({ ...form, award_type: e.target.value })}>
            {['eureka', 'clunies_ross', 'research_australia', 'prime_ministers', 'industry', 'custom'].map(value => <MenuItem key={value} value={value}>{value.replaceAll('_', ' ')}</MenuItem>)}
          </Select></FormControl></Grid>
          <Grid size={{ xs: 12, md: 3 }}><TextField fullWidth type="date" label="Deadline" slotProps={{ inputLabel: { shrink: true } }} value={form.deadline ?? ''} onChange={e => setForm({ ...form, deadline: e.target.value || null })} /></Grid>
          <Grid size={{ xs: 12, md: 3 }}><FormControl fullWidth><InputLabel>Workflow status</InputLabel><Select label="Workflow status" value={form.status} onChange={e => setForm({ ...form, status: e.target.value })}>
            {['exploring', 'preparing', 'seeking_nominator', 'ready', 'submitted', 'awarded', 'unsuccessful', 'paused'].map(value => <MenuItem key={value} value={value}>{value.replaceAll('_', ' ')}</MenuItem>)}
          </Select></FormControl></Grid>
          <Grid size={{ xs: 12, md: 3 }}><FormControl fullWidth><InputLabel>Dossier</InputLabel><Select label="Dossier" value={form.dossier_status} onChange={e => setForm({ ...form, dossier_status: e.target.value })}>
            {['not_started', 'evidence_review', 'drafting', 'review', 'complete'].map(value => <MenuItem key={value} value={value}>{value.replaceAll('_', ' ')}</MenuItem>)}
          </Select></FormControl></Grid>
          <Grid size={{ xs: 12, md: 6 }}><FormControl fullWidth><InputLabel>Readiness target</InputLabel><Select label="Readiness target" value={form.target_id ?? ''} onChange={e => setForm({ ...form, target_id: e.target.value || null })}>
            <MenuItem value="">Not linked yet</MenuItem>{targets.map(target => <MenuItem key={target.id} value={target.id}>{target.title}</MenuItem>)}
          </Select></FormControl></Grid>
          <Grid size={{ xs: 12, md: 3 }}><TextField fullWidth label="Nominator" value={form.nominator_name} onChange={e => setForm({ ...form, nominator_name: e.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 3 }}><FormControl fullWidth><InputLabel>Nominator status</InputLabel><Select label="Nominator status" value={form.nominator_status} onChange={e => setForm({ ...form, nominator_status: e.target.value })}>
            {['not_identified', 'candidate', 'approached', 'confirmed', 'not_required'].map(value => <MenuItem key={value} value={value}>{value.replaceAll('_', ' ')}</MenuItem>)}
          </Select></FormControl></Grid>
          <Grid size={{ xs: 12, md: 6 }}><TextField fullWidth label="Next action" value={form.next_action} onChange={e => setForm({ ...form, next_action: e.target.value })} /></Grid>
          <Grid size={{ xs: 12, md: 6 }}><TextField fullWidth multiline minRows={2} label="Public professional notes" value={form.notes} onChange={e => setForm({ ...form, notes: e.target.value })} /></Grid>
          <Grid size={12}><Stack direction="row" gap={1}><Button type="submit" variant="contained" disabled={busy || !form.name.trim()} startIcon={busy ? <CircularProgress size={18} /> : <AddOutlined />}>{editingId ? 'Save award' : 'Add award'}</Button>
            {editingId && <Button onClick={() => { setEditingId(null); setForm(emptyForm()) }}>Cancel</Button>}</Stack></Grid>
        </Grid>
      </Box>
    </CardContent></Card>
    {!items ? <CircularProgress aria-label="Loading awards" /> : <Grid container spacing={2}>
      {items.map(item => <Grid key={item.id} size={{ xs: 12, lg: 6 }}><Card sx={{ height: '100%' }}><CardContent>
        <Stack direction="row" justifyContent="space-between" gap={2}>
          <Box><Typography variant="h6">{item.name}</Typography><Typography color="text.secondary">{item.organisation}</Typography></Box>
          <Chip label={item.status.replaceAll('_', ' ')} color={item.status === 'awarded' ? 'success' : item.deadline_status === 'closing_soon' ? 'warning' : 'default'} />
        </Stack>
        <Stack direction="row" gap={1} flexWrap="wrap" mt={1}>
          <Chip size="small" variant="outlined" label={item.deadline ? `${item.days_remaining} days · ${item.deadline}` : 'No deadline'} />
          <Chip size="small" variant="outlined" label={`Nominator: ${item.nominator_status.replaceAll('_', ' ')}`} />
          <Chip size="small" variant="outlined" label={`Dossier: ${item.dossier_status.replaceAll('_', ' ')}`} />
        </Stack>
        <Divider sx={{ my: 2 }} />
        {item.readiness_score === null ? <Alert severity="info">{item.target_id ? 'Linked target has not been assessed yet.' : 'Link a readiness target to reuse mapped career evidence.'}</Alert> : <>
          <Stack direction="row" justifyContent="space-between"><Typography fontWeight={800}>Readiness · {item.target_title}</Typography><Typography fontWeight={900} color="primary.main">{item.readiness_score}%</Typography></Stack>
          <LinearProgress variant="determinate" value={item.readiness_score} sx={{ mt: 1, height: 8, borderRadius: 2 }} />
          <Typography variant="caption">Version {item.readiness_version} · confidence {item.readiness_confidence}%</Typography>
          <Grid container spacing={1} mt={1}><Grid size={6}><Typography variant="caption" fontWeight={800}>Strengths</Typography><Typography variant="body2">{item.strengths.slice(0, 3).join(' · ') || 'None recorded'}</Typography></Grid><Grid size={6}><Typography variant="caption" fontWeight={800}>Gaps</Typography><Typography variant="body2">{item.gaps.slice(0, 3).join(' · ') || 'No major gaps'}</Typography></Grid></Grid>
        </>}
        <Typography mt={2} fontWeight={800}>Next action</Typography><Typography color="text.secondary">{item.next_action || 'Not set'}</Typography>
        <Stack direction="row" gap={1} mt={2}><Button startIcon={<EditOutlined />} onClick={() => edit(item)}>Edit</Button><Button color="inherit" startIcon={<ArchiveOutlined />} disabled={busy} onClick={() => void archive(item.id)}>Archive</Button></Stack>
      </CardContent></Card></Grid>)}
    </Grid>}
    {items?.length === 0 && <Alert severity="info">No award pathways yet. Add Eureka, Clunies Ross, Research Australia, Prime Minister's Prizes or a custom award above.</Alert>}
    <Feedback message={feedback} onClose={() => setFeedback(null)} />
  </>
}
