import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined'
import DownloadOutlined from '@mui/icons-material/DownloadOutlined'
import UploadFileOutlined from '@mui/icons-material/UploadFileOutlined'
import {
  Accordion, AccordionDetails, AccordionSummary, Alert, Box, Button, Card,
  CardContent, Checkbox, Chip, CircularProgress, Divider, FormControlLabel,
  Grid, LinearProgress, Stack, Tab, Tabs, TextField, Typography,
} from '@mui/material'
import ExpandMoreOutlined from '@mui/icons-material/ExpandMoreOutlined'
import { type FormEvent, useCallback, useEffect, useMemo, useState } from 'react'

import { careerApi, downloadUrl } from '../api/client'
import { Feedback } from '../components/Feedback'
import { PageHeader } from '../components/PageHeader'
import type { JobApplication } from '../types/career'

const draftLabels = {
  cover_letter: 'Cover letter', selection_criteria: 'Selection criteria',
  tailored_cv: 'Tailored CV', interview_notes: 'Interview notes',
}

export function ApplicationsPage() {
  const [items, setItems] = useState<JobApplication[] | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [role, setRole] = useState('')
  const [organisation, setOrganisation] = useState('')
  const [description, setDescription] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [sourceMode, setSourceMode] = useState<'paste' | 'upload'>('paste')
  const [confirmed, setConfirmed] = useState(false)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [tab, setTab] = useState(0)
  const selected = useMemo(() => items?.find(item => item.id === selectedId) ?? items?.[0] ?? null, [items, selectedId])

  const load = useCallback(async () => {
    try {
      const response = await careerApi.listApplications()
      setItems(response.items)
      setSelectedId(current => current ?? response.items[0]?.id ?? null)
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load applications')
    }
  }, [])
  useEffect(() => { void load() }, [load])

  async function create(event: FormEvent) {
    event.preventDefault(); setBusy(true); setError(null)
    try {
      let application: JobApplication
      if (file) {
        const data = new FormData(); data.set('file', file); data.set('role_title', role)
        data.set('organisation', organisation); data.set('confirmed_public_information', String(confirmed))
        application = await careerApi.uploadApplication(data)
      } else {
        application = await careerApi.createApplication({ role_title: role, organisation, position_description: description, source_url: '', confirmed_public_information: confirmed })
      }
      await load(); setSelectedId(application.id); setRole(''); setOrganisation('')
      setDescription(''); setFile(null); setConfirmed(false)
      setFeedback('Position description imported. Review the proposed requirements before confirming them.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to import position description') }
    finally { setBusy(false) }
  }

  async function action(operation: (id: string) => Promise<JobApplication>, message: string) {
    if (!selected) return; setBusy(true); setError(null)
    try { await operation(selected.id); await load(); setFeedback(message) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Action failed') }
    finally { setBusy(false) }
  }

  function updateRequirement(requirementId: string, field: 'title' | 'description', value: string) {
    if (!selected) return
    setItems(current => current?.map(application => application.id === selected.id ? {
      ...application,
      requirements: application.requirements.map(requirement => requirement.id === requirementId
        ? { ...requirement, [field]: value }
        : requirement),
    } : application) ?? null)
  }

  return <>
    <PageHeader eyebrow="APPLICATION INTELLIGENCE" title="Job applications" description="Import a public position description, confirm its requirements, map verified career evidence, and prepare grounded application materials." />
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Card sx={{ mb: 3 }}><CardContent><Typography variant="h6" gutterBottom>Start an application</Typography>
      <Box component="form" onSubmit={event => void create(event)}><Grid container spacing={2}>
        <Grid size={{ xs: 12, md: 6 }}><TextField required fullWidth label="Role title" value={role} onChange={event => setRole(event.target.value)} /></Grid>
        <Grid size={{ xs: 12, md: 6 }}><TextField fullWidth label="Organisation" value={organisation} onChange={event => setOrganisation(event.target.value)} /></Grid>
        <Grid size={12}><Tabs value={sourceMode} onChange={(_, value: 'paste' | 'upload') => { setSourceMode(value); if (value === 'paste') setFile(null) }}><Tab value="paste" label="Paste position description" /><Tab value="upload" label="Upload position document" /></Tabs></Grid>
        {sourceMode === 'paste' ? <Grid size={12}><TextField fullWidth multiline minRows={6} label="Position description text" helperText="Paste the complete advertised position description, including selection criteria and role accountabilities." value={description} onChange={event => setDescription(event.target.value)} /></Grid> : <Grid size={12}><Alert severity="info" icon={<UploadFileOutlined />}><Typography fontWeight={800}>Upload the complete position description</Typography><Typography variant="body2" mb={1.5}>Supported formats: PDF, DOCX and TXT, up to 20 MB. The original remains in local storage.</Typography><Button component="label" variant="contained" startIcon={<UploadFileOutlined />}>Choose PDF, DOCX or TXT<input hidden type="file" accept=".pdf,.docx,.txt" onChange={event => setFile(event.target.files?.[0] ?? null)} /></Button>{file && <Chip sx={{ ml: 1 }} label={file.name} onDelete={() => setFile(null)} />}</Alert></Grid>}
        <Grid size={12}><FormControlLabel control={<Checkbox checked={confirmed} onChange={event => setConfirmed(event.target.checked)} />} label="I confirm this contains only publicly available professional information." /></Grid>
        <Grid size={12}><Button type="submit" variant="contained" disabled={busy || !confirmed || !role || (sourceMode === 'upload' ? !file : description.trim().length < 20)} startIcon={busy ? <CircularProgress size={18} /> : <DescriptionOutlined />}>{sourceMode === 'upload' ? 'Upload and extract requirements' : 'Import and extract requirements'}</Button></Grid>
      </Grid></Box>
    </CardContent></Card>
    {items && items.length > 0 && <Grid container spacing={3}>
      <Grid size={{ xs: 12, lg: 3 }}><Card><CardContent><Typography fontWeight={800} mb={1}>Applications</Typography><Stack spacing={1}>{items.map(item => <Button key={item.id} color={selected?.id === item.id ? 'primary' : 'inherit'} variant={selected?.id === item.id ? 'contained' : 'text'} sx={{ justifyContent: 'flex-start', textAlign: 'left' }} onClick={() => setSelectedId(item.id)}>{item.role_title}<br />{item.organisation}</Button>)}</Stack></CardContent></Card></Grid>
      <Grid size={{ xs: 12, lg: 9 }}>{selected && <Stack spacing={2}>
        <Card><CardContent><Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}><Box><Stack direction="row" gap={1}><Chip label={selected.status} /><Chip label={`${selected.requirements.length} requirements`} variant="outlined" /></Stack><Typography variant="h5" mt={1}>{selected.role_title}</Typography><Typography color="text.secondary">{selected.organisation}</Typography></Box><Stack direction="row" gap={1} flexWrap="wrap"><Button variant="contained" disabled={busy || selected.requirements_confirmed} onClick={() => void action(id => careerApi.confirmApplicationRequirements(id, selected), 'Requirements confirmed.')}>Confirm requirements</Button><Button variant="outlined" disabled={busy || !selected.requirements_confirmed} onClick={() => void action(careerApi.assessApplication, 'Career evidence mapped and fit assessed.')}>Map evidence & assess</Button><Button variant="outlined" disabled={busy || !selected.assessment} onClick={() => void action(careerApi.generateApplicationDrafts, 'Grounded application drafts generated.')}>Generate drafts</Button></Stack></Stack></CardContent></Card>
        <Card><CardContent><Typography variant="h6">Requirements and evidence</Typography><Alert severity="info" sx={{ my: 2 }}>Review and correct each extracted requirement before confirmation. Mapping uses existing active career assets and never changes those source records.</Alert>{selected.requirements.map(row => <Accordion key={row.id}><AccordionSummary expandIcon={<ExpandMoreOutlined />}><Box width="100%"><Stack direction="row" justifyContent="space-between" gap={2}><Typography fontWeight={700}>{row.title}</Typography><Chip size="small" label={row.asset_ids.length ? `${row.asset_ids.length} assets · ${row.coverage}%` : row.requirement_type} color={row.coverage >= 65 ? 'success' : row.coverage > 0 ? 'warning' : 'default'} /></Stack>{row.coverage > 0 && <LinearProgress variant="determinate" value={row.coverage} sx={{ mt: 1 }} />}</Box></AccordionSummary><AccordionDetails><Stack spacing={2}>{selected.requirements_confirmed ? <Typography color="text.secondary">{row.description}</Typography> : <><TextField label="Requirement" value={row.title} onChange={event => updateRequirement(row.id, 'title', event.target.value)} /><TextField multiline minRows={2} label="Description" value={row.description} onChange={event => updateRequirement(row.id, 'description', event.target.value)} /></>}{row.explanation && <Typography>{row.explanation}</Typography>}</Stack></AccordionDetails></Accordion>)}</CardContent></Card>
        {selected.assessment && <Card><CardContent><Typography variant="h6">Application fit</Typography><Typography variant="h3" color="primary.main">{selected.assessment.fit_score}/100</Typography><Typography color="text.secondary">Evidence confidence {selected.assessment.overall_confidence}%</Typography><Divider sx={{ my: 2 }} /><Grid container spacing={2}><Grid size={{ xs: 12, md: 6 }}><Typography fontWeight={800}>Strengths</Typography>{selected.assessment.strengths.map(value => <Typography key={value}>• {value}</Typography>)}</Grid><Grid size={{ xs: 12, md: 6 }}><Typography fontWeight={800}>Evidence gaps</Typography>{selected.assessment.gaps.map(value => <Typography key={value}>• {value}</Typography>)}</Grid></Grid></CardContent></Card>}
        {selected.drafts.length > 0 && <Card><CardContent><Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2}><Box><Typography variant="h6">Application materials</Typography><Chip size="small" color={selected.drafts[0].provider === 'gemini' ? 'secondary' : 'default'} label={selected.drafts[0].provider === 'gemini' ? 'Comprehensive Gemini draft' : 'Local fallback draft'} /></Box><Stack direction="row" gap={1}><Button startIcon={<DownloadOutlined />} href={downloadUrl(`/applications/${selected.id}/export/docx`)}>DOCX</Button><Button startIcon={<DownloadOutlined />} href={downloadUrl(`/applications/${selected.id}/export/pdf`)}>PDF</Button></Stack></Stack>{selected.drafts[0].unsupported_claims.length > 0 && <Alert severity="warning" sx={{ mt: 2 }}>Evidence limitations requiring review: {selected.drafts[0].unsupported_claims.join(' · ')}</Alert>}<Tabs value={Math.min(tab, selected.drafts.length - 1)} onChange={(_, value: number) => setTab(value)} variant="scrollable">{selected.drafts.map(draft => <Tab key={draft.id} label={draftLabels[draft.draft_type]} />)}</Tabs>{selected.drafts[Math.min(tab, selected.drafts.length - 1)] && <TextField fullWidth multiline minRows={18} value={selected.drafts[Math.min(tab, selected.drafts.length - 1)].content} slotProps={{ input: { readOnly: true } }} sx={{ mt: 2 }} />}</CardContent></Card>}
      </Stack>}</Grid>
    </Grid>}
    {items?.length === 0 && <Alert severity="info">No job applications yet. Import a position description above to begin.</Alert>}
    <Feedback message={feedback} onClose={() => setFeedback(null)} />
  </>
}
