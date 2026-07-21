import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import LinkOutlined from '@mui/icons-material/LinkOutlined'
import UploadFileOutlined from '@mui/icons-material/UploadFileOutlined'
import RefreshOutlined from '@mui/icons-material/RefreshOutlined'
import SaveOutlined from '@mui/icons-material/SaveOutlined'
import {
  Alert, Box, Button, Card, CardContent, Checkbox, FormControlLabel, Grid, MenuItem,
  Stack, TextField, Typography,
} from '@mui/material'
import { useEffect, useState } from 'react'

import { careerApi } from '../api/client'
import { Feedback } from '../components/Feedback'
import { PageHeader } from '../components/PageHeader'
import type { AiProviderStatus, IngestionRun, PublicProfileSource } from '../types/career'

type Policy = 'ai_allowed' | 'local_only' | 'redacted'

export function OnboardingPage() {
  const [file, setFile] = useState<File | null>(null)
  const [sources, setSources] = useState<PublicProfileSource[]>([
    { url: '', source_type: 'institutional_profile' },
    { url: '', source_type: 'google_scholar' },
  ])
  const [policy, setPolicy] = useState<Policy>('ai_allowed')
  const [confirmed, setConfirmed] = useState(false)
  const [run, setRun] = useState<IngestionRun | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [provider, setProvider] = useState<AiProviderStatus | null>(null)
  const [history, setHistory] = useState<IngestionRun[]>([])

  useEffect(() => {
    void Promise.all([careerApi.providerStatus(), careerApi.listIngestions()])
      .then(([status, runs]) => { setProvider(status); setHistory(runs) })
      .catch(() => undefined)
  }, [])

  async function analyseDocument() {
    if (!file) return
    const form = new FormData(); form.append('file', file); form.append('ai_handling_policy', policy); form.append('confirmed_public_information', String(confirmed))
    await execute(() => careerApi.ingestDocument(form))
  }
  async function analyseUrls() {
    const populated = sources.filter((item) => item.url.trim())
    if (populated.length === 1) await execute(() => careerApi.ingestUrl(populated[0].url, policy))
    else await execute(() => careerApi.ingestUrlCollection(populated, policy))
  }
  function updateSource(index: number, changes: Partial<PublicProfileSource>) {
    setSources((items) => items.map((item, itemIndex) => itemIndex === index ? { ...item, ...changes } : item))
  }
  async function execute(action: () => Promise<IngestionRun>) {
    setBusy(true); setError(null)
    try { const next = await action(); setRun(next); setHistory((items) => [next, ...items]) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to analyse source') } finally { setBusy(false) }
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
  async function saveCorrections() {
    if (!run) return
    setBusy(true)
    try { setRun(await careerApi.saveIngestionProposal(run.id, run.proposal)); setFeedback('Corrections saved.') } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to save corrections') } finally { setBusy(false) }
  }
  async function reprocess() {
    if (!run) return
    setBusy(true)
    try { const next = await careerApi.reprocessIngestion(run.id); setRun(next); setFeedback(`Reprocessed with ${next.provider}.`) } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to reprocess source') } finally { setBusy(false) }
  }
  async function suppress() {
    if (!run) return
    setBusy(true)
    try { setRun(await careerApi.suppressIngestion(run.id)); setFeedback('Proposal suppressed.') } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to suppress proposal') } finally { setBusy(false) }
  }
  function updateAsset(index: number, changes: Partial<IngestionRun['proposal']['assets'][number]>) {
    if (!run) return
    const assets = [...run.proposal.assets]; assets[index] = { ...assets[index], ...changes }
    setRun({ ...run, proposal: { ...run.proposal, assets } })
  }

  return <>
    <PageHeader eyebrow="DOCUMENT-LED ONBOARDING" title="Build from your career materials" description="Upload a CV or add a public professional page. CAPSTONE extracts a reviewable profile and career timeline proposal before anything is applied." />
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    {provider && <Alert severity={provider.active_provider === 'gemini' ? 'success' : 'warning'} sx={{ mb: 2 }}>Active analysis provider: <strong>{provider.active_provider}</strong>{provider.model ? ` · ${provider.model}` : ''}. Choosing “AI allowed” grants permission; it does not override this active provider.</Alert>}
    <Alert severity="info" sx={{ mb: 3 }}>JSON is not required. PDF, DOCX and TXT are supported. Deakin Experts profile links automatically include profile, outputs, grants, professional activities, teaching and supervision. For LinkedIn, upload your profile PDF or data export rather than relying on automated scraping.</Alert>
    <Card sx={{ mb: 3 }}><CardContent><Grid container spacing={2} alignItems="center">
      <Grid size={{ xs: 12, md: 5 }}><Button component="label" fullWidth variant="outlined" startIcon={<UploadFileOutlined />}>{file?.name || 'Choose CV or career document'}<input hidden type="file" accept=".pdf,.docx,.txt" onChange={(event) => setFile(event.target.files?.[0] ?? null)} /></Button></Grid>
      <Grid size={{ xs: 12, md: 5 }}><Stack gap={1.5}>{sources.map((source, index) => <Stack direction={{ xs: 'column', sm: 'row' }} gap={1} key={index}><TextField select label="Source type" value={source.source_type} onChange={(event) => updateSource(index, { source_type: event.target.value })} sx={{ minWidth: 190 }}><MenuItem value="institutional_profile">Institutional profile</MenuItem><MenuItem value="orcid">ORCID</MenuItem><MenuItem value="google_scholar">Google Scholar</MenuItem><MenuItem value="personal_website">Personal website</MenuItem><MenuItem value="media">Media/public link</MenuItem><MenuItem value="other">Other</MenuItem></TextField><TextField fullWidth label={`Public URL ${index + 1}`} value={source.url} onChange={(event) => updateSource(index, { url: event.target.value })} slotProps={{ input: { startAdornment: <LinkOutlined sx={{ mr: 1 }} /> } }} />{sources.length > 2 && <Button color="warning" onClick={() => setSources((items) => items.filter((_, itemIndex) => itemIndex !== index))}>Remove</Button>}</Stack>)}<Button onClick={() => setSources((items) => [...items, { url: '', source_type: 'other' }])}>Add another URL</Button></Stack></Grid>
      <Grid size={{ xs: 12, md: 2 }}><TextField select fullWidth label="Processing" value={policy} onChange={(event) => setPolicy(event.target.value as Policy)}><MenuItem value="local_only">Local only</MenuItem><MenuItem value="ai_allowed">AI allowed</MenuItem><MenuItem value="redacted">Redacted</MenuItem></TextField></Grid>
      <Grid size={12}><FormControlLabel control={<Checkbox checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />} label="I confirm these sources contain only publicly available professional information." /></Grid>
      <Grid size={12}><Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5}><Button variant="contained" disabled={!file || !confirmed || busy} onClick={() => void analyseDocument()} startIcon={<AutoAwesomeOutlined />}>Analyse document</Button><Button variant="outlined" disabled={!sources.some((item) => item.url.trim()) || !confirmed || busy} onClick={() => void analyseUrls()}>Analyse public sources</Button></Stack></Grid>
    </Grid></CardContent></Card>
    {!run && history.length > 0 && <Card sx={{ mb: 3 }}><CardContent><Typography variant="h5" mb={2}>Recent analyses</Typography><Stack gap={1}>{history.slice(0, 8).map((item) => <Button key={item.id} variant="outlined" onClick={() => setRun(item)} sx={{ justifyContent: 'space-between' }}><span>{item.source_label}</span><span>{item.provider} · {item.status}</span></Button>)}</Stack></CardContent></Card>}
    {run && <Card><CardContent><Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}><Box><Typography variant="h5">Review extraction</Typography><Typography color="text.secondary">{run.source_label} · {run.provider} · {run.status}</Typography></Box><Stack direction={{ xs: 'column', sm: 'row' }} gap={1}><Button startIcon={<SaveOutlined />} disabled={busy || run.status !== 'ready_for_review'} onClick={() => void saveCorrections()}>Save corrections</Button><Button startIcon={<RefreshOutlined />} disabled={busy || run.status === 'applied'} onClick={() => void reprocess()}>Reprocess</Button><Button color="warning" disabled={busy || run.status !== 'ready_for_review'} onClick={() => void suppress()}>Suppress</Button><Button variant="contained" disabled={busy || run.status !== 'ready_for_review'} onClick={() => void apply()}>Apply selected information</Button></Stack></Stack>
      {run.proposal.warnings.map((warning) => <Alert severity="warning" sx={{ mt: 2 }} key={warning}>{warning}</Alert>)}
      {run.proposal.conflicts?.map((conflict) => <Alert severity="error" sx={{ mt: 2 }} key={conflict}>{conflict}</Alert>)}
      {run.proposal.coverage && Object.keys(run.proposal.coverage).length > 0 && <Stack direction="row" flexWrap="wrap" gap={1} mt={2}>{Object.entries(run.proposal.coverage).map(([sourceType, count]) => <Alert severity="info" key={sourceType}>{sourceType.replaceAll('_', ' ')}: {count} proposed assets</Alert>)}</Stack>}
      {run.proposal.source_diagnostics && Object.keys(run.proposal.source_diagnostics).length > 0 && <Alert severity="info" sx={{ mt: 2 }}>Source coverage: {Object.entries(run.proposal.source_diagnostics).map(([key, value]) => `${key.replaceAll('_', ' ')}: ${String(value)}`).join(' · ')}</Alert>}
      <Typography variant="h6" mt={3} mb={2}>Proposed profile fields</Typography><Grid container spacing={2}>
        {([['name','Name'],['current_title','Current title'],['current_organisation','Current organisation'],['career_narrative','Career narrative']] as const).map(([field,label]) => <Grid key={field} size={{ xs: 12, md: field === 'career_narrative' ? 12 : 4 }}><TextField fullWidth multiline={field === 'career_narrative'} label={label} value={run.proposal.profile[field]} onChange={(event) => updateProfile(field, event.target.value)} /></Grid>)}
      </Grid><Typography variant="h6" mt={4} mb={2}>Proposed career assets ({run.proposal.assets.filter((item) => item.include).length} selected)</Typography>
      <Stack gap={2}>{run.proposal.assets.map((asset, index) => <Card variant="outlined" key={`${asset.title}-${index}`}><CardContent><FormControlLabel control={<Checkbox checked={asset.include} onChange={(event) => updateAsset(index, { include: event.target.checked })} />} label="Include this career asset" />{asset.source_labels?.length > 0 && <Typography variant="caption" display="block" mb={1}>Sources: {asset.source_labels.join(' · ')}</Typography>}<Grid container spacing={2}><Grid size={{ xs: 12, md: 6 }}><TextField fullWidth label="Title" value={asset.title} onChange={(event) => updateAsset(index, { title: event.target.value })} /></Grid><Grid size={{ xs: 12, md: 3 }}><TextField fullWidth label="Organisation" value={asset.organisation} onChange={(event) => updateAsset(index, { organisation: event.target.value })} /></Grid><Grid size={{ xs: 12, md: 3 }}><TextField fullWidth label="Category" value={asset.category} onChange={(event) => updateAsset(index, { category: event.target.value })} /></Grid><Grid size={12}><TextField fullWidth multiline label="Description / evidence" value={asset.description} onChange={(event) => updateAsset(index, { description: event.target.value })} /></Grid></Grid></CardContent></Card>)}</Stack>
      {run.proposal.assets.length === 0 && <Alert severity="info">No dated assets were confidently detected. Enable Gemini processing or add entries manually before applying.</Alert>}
    </CardContent></Card>}
    <Feedback message={feedback} onClose={() => setFeedback(null)} />
  </>
}
