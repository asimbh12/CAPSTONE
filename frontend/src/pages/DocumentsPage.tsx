import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import DownloadOutlined from '@mui/icons-material/DownloadOutlined'
import SaveOutlined from '@mui/icons-material/SaveOutlined'
import {
  Alert, Box, Button, Card, CardContent, Chip, CircularProgress, FormControl,
  Grid, InputLabel, MenuItem, Select, Stack, TextField, Typography,
} from '@mui/material'
import { type FormEvent, useCallback, useEffect, useMemo, useState } from 'react'

import { careerApi, downloadUrl } from '../api/client'
import { Feedback } from '../components/Feedback'
import { PageHeader } from '../components/PageHeader'
import type { CareerDocument } from '../types/career'

const labels: Record<CareerDocument['document_type'], string> = {
  professional_biography: 'Professional biography',
  executive_profile: 'Executive profile',
  linkedin_about: 'LinkedIn About',
}

export function DocumentsPage() {
  const [items, setItems] = useState<CareerDocument[] | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [documentType, setDocumentType] =
    useState<CareerDocument['document_type']>('professional_biography')
  const [title, setTitle] = useState('Professional biography')
  const [audience, setAudience] = useState('')
  const [purpose, setPurpose] = useState('')
  const [tone, setTone] = useState<CareerDocument['tone']>('executive')
  const [editTitle, setEditTitle] = useState('')
  const [content, setContent] = useState('')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [feedback, setFeedback] = useState<string | null>(null)
  const selected = useMemo(
    () => items?.find(item => item.id === selectedId) ?? items?.[0] ?? null,
    [items, selectedId],
  )

  const load = useCallback(async () => {
    try {
      const response = await careerApi.listCareerDocuments()
      setItems(response.items)
      setSelectedId(current => current ?? response.items[0]?.id ?? null)
      setError(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to load career documents')
    }
  }, [])

  useEffect(() => { void load() }, [load])
  useEffect(() => {
    if (selected) {
      setEditTitle(selected.title)
      setContent(selected.content)
    }
  }, [selected])

  async function generate(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      const created = await careerApi.generateCareerDocument({
        document_type: documentType, title, audience, purpose, tone, asset_ids: [],
      })
      await load()
      setSelectedId(created.id)
      setFeedback('Grounded career document generated. Review and edit it before use.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to generate document')
    } finally {
      setBusy(false)
    }
  }

  async function save() {
    if (!selected) return
    setBusy(true)
    setError(null)
    try {
      await careerApi.updateCareerDocument(selected.id, editTitle, content)
      await load()
      setFeedback('Document changes saved locally.')
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to save document')
    } finally {
      setBusy(false)
    }
  }

  return <>
    <PageHeader
      eyebrow="REUSABLE CAREER COMMUNICATION"
      title="Document studio"
      description="Generate evidence-grounded career narratives from your profile and active career assets, then review, edit and export them."
    />
    {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
    <Card sx={{ mb: 3 }}><CardContent>
      <Typography variant="h6" gutterBottom>Create a career document</Typography>
      <Alert severity="info" sx={{ mb: 2 }}>
        Generation reads verified assets and never modifies them. Unsupported claims are surfaced
        for review.
      </Alert>
      <Box component="form" onSubmit={event => void generate(event)}>
        <Grid container spacing={2}>
          <Grid size={{ xs: 12, md: 4 }}><FormControl fullWidth>
            <InputLabel>Document type</InputLabel>
            <Select label="Document type" value={documentType} onChange={event => {
              const value = event.target.value
              setDocumentType(value)
              setTitle(labels[value])
            }}>
              {Object.entries(labels).map(([value, label]) =>
                <MenuItem key={value} value={value}>{label}</MenuItem>)}
            </Select>
          </FormControl></Grid>
          <Grid size={{ xs: 12, md: 4 }}><TextField required fullWidth label="Document title" value={title} onChange={event => setTitle(event.target.value)} /></Grid>
          <Grid size={{ xs: 12, md: 4 }}><FormControl fullWidth>
            <InputLabel>Tone</InputLabel>
            <Select label="Tone" value={tone} onChange={event => setTone(event.target.value)}>
              <MenuItem value="executive">Executive</MenuItem>
              <MenuItem value="academic">Academic</MenuItem>
              <MenuItem value="accessible">Accessible</MenuItem>
            </Select>
          </FormControl></Grid>
          <Grid size={{ xs: 12, md: 5 }}><TextField fullWidth label="Audience" placeholder="Board, conference, university website…" value={audience} onChange={event => setAudience(event.target.value)} /></Grid>
          <Grid size={{ xs: 12, md: 7 }}><TextField fullWidth label="Purpose and emphasis" placeholder="What should this document help achieve?" value={purpose} onChange={event => setPurpose(event.target.value)} /></Grid>
          <Grid size={12}><Button type="submit" variant="contained" disabled={busy || !title.trim()} startIcon={busy ? <CircularProgress size={18} /> : <AutoAwesomeOutlined />}>Generate grounded draft</Button></Grid>
        </Grid>
      </Box>
    </CardContent></Card>
    {items && items.length > 0 && <Grid container spacing={3}>
      <Grid size={{ xs: 12, lg: 3 }}><Card><CardContent>
        <Typography fontWeight={800} mb={1}>Saved documents</Typography>
        <Stack spacing={1}>{items.map(item =>
          <Button key={item.id} variant={selected?.id === item.id ? 'contained' : 'text'} color={selected?.id === item.id ? 'primary' : 'inherit'} sx={{ justifyContent: 'flex-start', textAlign: 'left' }} onClick={() => setSelectedId(item.id)}>
            {item.title}
          </Button>)}</Stack>
      </CardContent></Card></Grid>
      <Grid size={{ xs: 12, lg: 9 }}>{selected && <Card><CardContent>
        <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={2} mb={2}>
          <Stack direction="row" gap={1} flexWrap="wrap">
            <Chip label={labels[selected.document_type]} />
            <Chip variant="outlined" label={selected.provider === 'gemini' ? 'Gemini grounded draft' : 'Local grounded draft'} />
            <Chip variant="outlined" label={`${selected.asset_ids.length} source assets`} />
          </Stack>
          <Stack direction="row" gap={1}>
            <Button startIcon={<DownloadOutlined />} href={downloadUrl(`/career-documents/${selected.id}/export/docx`)}>DOCX</Button>
            <Button startIcon={<DownloadOutlined />} href={downloadUrl(`/career-documents/${selected.id}/export/pdf`)}>PDF</Button>
          </Stack>
        </Stack>
        {selected.unsupported_claims.length > 0 && <Alert severity="warning" sx={{ mb: 2 }}>
          Evidence limitations: {selected.unsupported_claims.join(' · ')}
        </Alert>}
        <Stack spacing={2}>
          <TextField label="Title" value={editTitle} onChange={event => setEditTitle(event.target.value)} />
          <TextField multiline minRows={22} label="Draft content" value={content} onChange={event => setContent(event.target.value)} />
          <Button variant="contained" onClick={() => void save()} disabled={busy || content.trim().length < 20} startIcon={<SaveOutlined />}>Save reviewed document</Button>
        </Stack>
      </CardContent></Card>}</Grid>
    </Grid>}
    {items?.length === 0 && <Alert severity="info">No career documents yet. Generate the first grounded draft above.</Alert>}
    <Feedback message={feedback} onClose={() => setFeedback(null)} />
  </>
}
