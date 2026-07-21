import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import LinkOutlined from '@mui/icons-material/LinkOutlined'
import UploadFileOutlined from '@mui/icons-material/UploadFileOutlined'
import {
  Alert, Box, Button, Card, CardContent, Checkbox, FormControlLabel, Grid, MenuItem,
  Stack, TextField, Typography,
} from '@mui/material'
import { useState } from 'react'

import { careerApi } from '../api/client'
import { Feedback } from '../components/Feedback'
import { PageHeader } from '../components/PageHeader'
import type { IngestionRun } from '../types/career'

type Policy = 'ai_allowed' | 'local_only' | 'redacted'

export function OnboardingPage() {
  const [file, setFile] = useState<File | null>(null)
  const [url, setUrl] = useState('')
  const [policy, setPolicy] = useState<Policy>('local_only')
  const [confirmed, setConfirmed] = useState(false)
  const [run, setRun] = useState<IngestionRun | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)

  async function analyseDocument() {
    if (!file) return
    const form = new FormData(); form.append('file', file); form.append('ai_handling_policy', policy); form.append('confirmed_public_information', String(confirmed))
    await execute(() => careerApi.ingestDocument(form))
  }
  async function analyseUrl() { await execute(() => careerApi.ingestUrl(url, policy)) }
  async function execute(action: () => Promise<IngestionRun>) {
    setBusy(true); setError(null)
    try { setRun(await action()) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to analyse source') } finally { setBusy(false) }
  }
  async function apply() {
    if (!run) return
    setBusy(true); setError(null)
    try {
      const result = await careerApi.applyIngestion(run.id, run.proposal)
      setFeedback(`Imported ${result.assets_created} assets; filled ${result.profile_fields_filled.length} profile fields.`)
      setRun({ ...run, status: 'applied' })
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to apply proposal') } finally { setBusy(false) }
  }
  function updateProfile(field: keyof IngestionRun['proposal']['profile'], value: string) {
    if (run) setRun({ ...run, proposal: { ...run.proposal, profile: { ...run.proposal.profile, [field]: value } } })
  }
  function updateAsset(index: number, changes: Partial<IngestionRun['proposal']['assets'][number]>) {
    if (!run) return
    const assets = [...run.proposal.assets]; assets[index] = { ...assets[index], ...changes }
    setRun({ ...run, proposal: { ...run.proposal, assets } })
  }

  return <>
    <PageHeader eyebrow="DOCUMENT-LED ONBOARDING" title="Build from your career materials" description="Upload a CV or add a public professional page. CAPSTONE extracts a reviewable profile and career timeline proposal before anything is applied." />
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Alert severity="info" sx={{ mb: 3 }}>JSON is not required. PDF, DOCX and TXT are supported. For LinkedIn, upload your profile PDF or data export rather than relying on automated scraping.</Alert>
    <Card sx={{ mb: 3 }}><CardContent><Grid container spacing={2} alignItems="center">
      <Grid size={{ xs: 12, md: 5 }}><Button component="label" fullWidth variant="outlined" startIcon={<UploadFileOutlined />}>{file?.name || 'Choose CV or career document'}<input hidden type="file" accept=".pdf,.docx,.txt" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></Button></Grid>
      <Grid size={{ xs: 12, md: 5 }}><TextField fullWidth label="Public profile or media URL" value={url} onChange={(event) => setUrl(event.target.value)} slotProps={{ input: { startAdornment: <LinkOutlined sx={{ mr: 1 }} /> } }} /></Grid>
      <Grid size={{ xs: 12, md: 2 }}><TextField select fullWidth label="Processing" value={policy} onChange={(event) => setPolicy(event.target.value as Policy)}><MenuItem value="local_only">Local only</MenuItem><MenuItem value="ai_allowed">AI allowed</MenuItem><MenuItem value="redacted">Redacted</MenuItem></TextField></Grid>
      <Grid size={12}><FormControlLabel control={<Checkbox checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />} label="I confirm these sources contain only publicly available professional information." /></Grid>
      <Grid size={12}><Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5}><Button variant="contained" disabled={!file || !confirmed || busy} onClick={() => void analyseDocument()} startIcon={<AutoAwesomeOutlined />}>Analyse document</Button><Button variant="outlined" disabled={!url || !confirmed || busy} onClick={() => void analyseUrl()}>Analyse public URL</Button></Stack></Grid>
    </Grid></CardContent></Card>
    {run && <Card><CardContent><Stack direction="row" justifyContent="space-between"><Box><Typography variant="h5">Review extraction</Typography><Typography color="text.secondary">{run.source_label} · {run.provider}</Typography></Box><Button variant="contained" disabled={busy || run.status === 'applied'} onClick={() => void apply()}>Apply selected information</Button></Stack>
      {run.proposal.warnings.map((warning) => <Alert severity="warning" sx={{ mt: 2 }} key={warning}>{warning}</Alert>)}
      <Typography variant="h6" mt={3} mb={2}>Proposed profile fields</Typography><Grid container spacing={2}>
        {([['name','Name'],['current_title','Current title'],['current_organisation','Current organisation'],['career_narrative','Career narrative']] as const).map(([field,label]) => <Grid key={field} size={{ xs: 12, md: field === 'career_narrative' ? 12 : 4 }}><TextField fullWidth multiline={field === 'career_narrative'} label={label} value={run.proposal.profile[field]} onChange={(event) => updateProfile(field, event.target.value)} /></Grid>)}
      </Grid><Typography variant="h6" mt={4} mb={2}>Proposed career assets ({run.proposal.assets.filter((item) => item.include).length} selected)</Typography>
      <Stack gap={2}>{run.proposal.assets.map((asset, index) => <Card variant="outlined" key={`${asset.title}-${index}`}><CardContent><FormControlLabel control={<Checkbox checked={asset.include} onChange={(event) => updateAsset(index, { include: event.target.checked })} />} label="Include this career asset" /><Grid container spacing={2}><Grid size={{ xs: 12, md: 6 }}><TextField fullWidth label="Title" value={asset.title} onChange={(event) => updateAsset(index, { title: event.target.value })} /></Grid><Grid size={{ xs: 12, md: 3 }}><TextField fullWidth label="Organisation" value={asset.organisation} onChange={(event) => updateAsset(index, { organisation: event.target.value })} /></Grid><Grid size={{ xs: 12, md: 3 }}><TextField fullWidth label="Category" value={asset.category} onChange={(event) => updateAsset(index, { category: event.target.value })} /></Grid><Grid size={12}><TextField fullWidth multiline label="Description / evidence" value={asset.description} onChange={(event) => updateAsset(index, { description: event.target.value })} /></Grid></Grid></CardContent></Card>)}</Stack>
      {run.proposal.assets.length === 0 && <Alert severity="info">No dated assets were confidently detected. Enable Gemini processing or add entries manually before applying.</Alert>}
    </CardContent></Card>}
    <Feedback message={feedback} onClose={() => setFeedback(null)} />
  </>
}
