import AddOutlined from '@mui/icons-material/AddOutlined'
import ArchiveOutlined from '@mui/icons-material/ArchiveOutlined'
import AttachFileOutlined from '@mui/icons-material/AttachFileOutlined'
import EditOutlined from '@mui/icons-material/EditOutlined'
import SearchOutlined from '@mui/icons-material/SearchOutlined'
import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import {
  Alert,
  Box,
  Button,
  Card,
  CardActionArea,
  CardContent,
  Checkbox,
  Chip,
  CircularProgress,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
  Divider,
  FormControlLabel,
  Grid,
  InputAdornment,
  MenuItem,
  Stack,
  TextField,
  Typography,
} from '@mui/material'
import { type ChangeEvent, type FormEvent, useCallback, useEffect, useState } from 'react'

import { careerApi, downloadUrl } from '../api/client'
import { Feedback } from '../components/Feedback'
import { PageHeader } from '../components/PageHeader'
import type { AssetInput, CareerAsset, ImpactSummaryOption, Organisation, Theme } from '../types/career'

const categories = [
  'Experience',
  'Research Asset', 'Innovation Asset', 'Leadership Asset', 'Commercialisation Asset',
  'Award Asset', 'Funding Asset', 'Publication Asset', 'Patent Asset', 'Media Asset',
  'Relationship Asset', 'Board Asset', 'Committee Asset', 'Volunteer Asset',
  'Training Asset', 'Certification Asset', 'Teaching Asset', 'Defence Asset',
  'Public Health Asset', 'Industry Asset', 'Government Asset', 'Thought Leadership Asset',
  'Strategic Achievement',
]

const emptyAsset: AssetInput = {
  title: '', description: '', category: 'Leadership Asset', subcategory: '', start_date: null,
  end_date: null, date_precision: 'day', status: 'active', impact_summary: '',
  organisation_id: null, role: '', visibility: 'public', tags: [], keywords: [], theme_ids: [],
}

function assetToInput(asset: CareerAsset): AssetInput {
  return {
    title: asset.title,
    description: asset.description,
    category: asset.category,
    subcategory: asset.subcategory,
    start_date: asset.start_date,
    end_date: asset.end_date,
    date_precision: asset.date_precision,
    status: asset.status,
    impact_summary: asset.impact_summary,
    organisation_id: asset.organisation_id,
    role: asset.role,
    visibility: asset.visibility,
    tags: asset.tags,
    keywords: asset.keywords,
    theme_ids: asset.theme_ids,
  }
}

interface AssetDialogProps {
  open: boolean
  asset: CareerAsset | null
  themes: Theme[]
  organisations: Organisation[]
  onClose: () => void
  onSaved: (asset: CareerAsset) => boolean | void
}

function AssetDialog({ open, asset, themes, organisations, onClose, onSaved }: AssetDialogProps) {
  const [form, setForm] = useState<AssetInput>(emptyAsset)
  const [terms, setTerms] = useState('')
  const [saving, setSaving] = useState(false)
  const [generating, setGenerating] = useState(false)
  const [impactOptions, setImpactOptions] = useState<ImpactSummaryOption[]>([])
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    if (open) {
      if (asset) {
        setForm(assetToInput(asset))
        setTerms(asset.tags.join(', '))
      } else {
        setForm(emptyAsset)
        setTerms('')
      }
      setImpactOptions([])
      setError(null)
    }
  }, [asset, open])

  const set = <K extends keyof AssetInput>(key: K, value: AssetInput[K]) =>
    setForm((current) => ({ ...current, [key]: value }))

  async function submit(event: FormEvent) {
    event.preventDefault()
    setSaving(true)
    setError(null)
    try {
      const payload = { ...form, tags: terms.split(',').map((term) => term.trim()).filter(Boolean) }
      const saved = asset
        ? await careerApi.updateAsset(asset.id, payload)
        : await careerApi.createAsset(payload)
      const continueReview = onSaved(saved)
      if (!continueReview) onClose()
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to save career asset')
    } finally {
      setSaving(false)
    }
  }

  async function generateImpactOptions() {
    if (!asset) return
    setGenerating(true)
    setError(null)
    try {
      const result = await careerApi.generateImpactSummaries(asset.id)
      setImpactOptions(result.options)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to generate impact summaries')
    } finally {
      setGenerating(false)
    }
  }

  return (
    <Dialog open={open} onClose={onClose} fullWidth maxWidth="md">
      <Box component="form" onSubmit={(event) => void submit(event)}>
        <DialogTitle>{asset ? 'Edit career asset' : 'Add career asset'}</DialogTitle>
        <DialogContent>
          <Alert severity="info" sx={{ mb: 2 }}>Enter only publicly available professional information.</Alert>
          {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
          <Grid container spacing={2}>
            <Grid size={12}><TextField required autoFocus fullWidth label="Asset title" value={form.title} onChange={(event) => set('title', event.target.value)} /></Grid>
            <Grid size={{ xs: 12, md: 6 }}><TextField select fullWidth label="Category" value={form.category} onChange={(event) => set('category', event.target.value)}>{categories.map((category) => <MenuItem key={category} value={category}>{category}</MenuItem>)}</TextField></Grid>
            <Grid size={{ xs: 12, md: 6 }}><TextField fullWidth label="Subcategory" value={form.subcategory} onChange={(event) => set('subcategory', event.target.value)} /></Grid>
            <Grid size={{ xs: 12, md: 6 }}><TextField type="date" fullWidth label="Start date" slotProps={{ inputLabel: { shrink: true } }} value={form.start_date ?? ''} onChange={(event) => set('start_date', event.target.value || null)} /></Grid>
            <Grid size={{ xs: 12, md: 6 }}><TextField type="date" fullWidth label="End date" slotProps={{ inputLabel: { shrink: true } }} value={form.end_date ?? ''} onChange={(event) => set('end_date', event.target.value || null)} /></Grid>
            <Grid size={12}><TextField fullWidth multiline minRows={3} label="Description" value={form.description} onChange={(event) => set('description', event.target.value)} /></Grid>
            <Grid size={12}>
              <TextField fullWidth multiline minRows={3} label="Impact summary" helperText="Describe the outcome or value without adding unsupported claims. AI suggestions never overwrite this field automatically." value={form.impact_summary} onChange={(event) => set('impact_summary', event.target.value)} />
              {asset && <Button sx={{ mt: 1.5 }} variant="outlined" startIcon={generating ? <CircularProgress size={18} /> : <AutoAwesomeOutlined />} disabled={generating || saving} onClick={() => void generateImpactOptions()}>{generating ? 'Generating alternatives…' : impactOptions.length > 0 ? 'Generate different alternatives' : 'Generate AI impact summaries'}</Button>}
            </Grid>
            {impactOptions.length > 0 && <Grid size={12}>
              <Alert severity="info" sx={{ mb: 1.5 }}>Compare the evidence-grounded alternatives below. Selecting one copies it into the impact-summary field; the career asset changes only when you select <strong>Save asset</strong>.</Alert>
              <Stack spacing={1.5}>
                {impactOptions.map((option) => <Card key={`${option.label}-${option.summary}`} variant="outlined" sx={{ borderColor: form.impact_summary === option.summary ? 'secondary.main' : 'divider' }}>
                  <CardContent>
                    <Stack direction={{ xs: 'column', sm: 'row' }} justifyContent="space-between" gap={1}>
                      <Box><Typography fontWeight={800}>{option.label}</Typography><Typography variant="body2" color="text.secondary">{option.emphasis}</Typography></Box>
                      <Button size="small" variant={form.impact_summary === option.summary ? 'contained' : 'outlined'} color="secondary" onClick={() => set('impact_summary', option.summary)}>{form.impact_summary === option.summary ? 'Selected' : 'Use this summary'}</Button>
                    </Stack>
                    <Typography mt={1.5}>{option.summary}</Typography>
                  </CardContent>
                </Card>)}
              </Stack>
            </Grid>}
            <Grid size={{ xs: 12, md: 6 }}><TextField fullWidth label="Role" value={form.role} onChange={(event) => set('role', event.target.value)} /></Grid>
            <Grid size={{ xs: 12, md: 6 }}><TextField select fullWidth label="Organisation" value={form.organisation_id ?? ''} onChange={(event) => set('organisation_id', event.target.value || null)}><MenuItem value="">None</MenuItem>{organisations.map((organisation) => <MenuItem key={organisation.id} value={organisation.id}>{organisation.name}</MenuItem>)}</TextField></Grid>
            <Grid size={12}><TextField fullWidth label="Tags" helperText="Comma-separated manual tags. AI-derived tags arrive in Stage 4." value={terms} onChange={(event) => setTerms(event.target.value)} /></Grid>
            <Grid size={12}><TextField select fullWidth SelectProps={{ multiple: true }} label="Strategic themes" value={form.theme_ids} onChange={(event) => set('theme_ids', typeof event.target.value === 'string' ? event.target.value.split(',') : event.target.value)}>{themes.map((theme) => <MenuItem key={theme.id} value={theme.id}>{theme.name}</MenuItem>)}</TextField></Grid>
          </Grid>
        </DialogContent>
        <DialogActions><Button onClick={onClose}>Cancel</Button><Button type="submit" variant="contained" disabled={saving}>{saving ? 'Saving…' : 'Save asset'}</Button></DialogActions>
      </Box>
    </Dialog>
  )
}

interface DetailDialogProps {
  asset: CareerAsset | null
  onClose: () => void
  onEdit: () => void
  onChanged: (asset: CareerAsset) => void
}

function AssetDetailDialog({ asset, onClose, onEdit, onChanged }: DetailDialogProps) {
  const [title, setTitle] = useState('')
  const [description, setDescription] = useState('')
  const [sourceUrl, setSourceUrl] = useState('')
  const [file, setFile] = useState<File | null>(null)
  const [confirmed, setConfirmed] = useState(false)
  const [policy, setPolicy] = useState<'local_only' | 'ai_allowed' | 'redacted'>('local_only')
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [enrichment, setEnrichment] = useState<string | null>(null)

  useEffect(() => { setTitle(''); setDescription(''); setSourceUrl(''); setFile(null); setConfirmed(false); setError(null); setEnrichment(null) }, [asset?.id])
  if (!asset) return null
  const currentAsset = asset

  async function addEvidence(event: FormEvent) {
    event.preventDefault()
    setBusy(true)
    setError(null)
    try {
      let documentId: string | null = null
      if (file) {
        if (!confirmed) throw new Error('Confirm that the document contains only public professional information.')
        const formData = new FormData()
        formData.append('file', file)
        formData.append('ai_handling_policy', policy)
        formData.append('confirmed_public_information', 'true')
        documentId = (await careerApi.uploadDocument(formData)).id
      }
      await careerApi.createEvidence(currentAsset.id, { title, description, source_url: sourceUrl, document_id: documentId })
      onChanged(await careerApi.getAsset(currentAsset.id))
      setTitle(''); setDescription(''); setSourceUrl(''); setFile(null); setConfirmed(false)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to add evidence')
    } finally { setBusy(false) }
  }

  async function archive() {
    setBusy(true)
    try { onChanged(await careerApi.archiveAsset(currentAsset.id)); onClose() }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to archive asset') }
    finally { setBusy(false) }
  }

  async function enrich() {
    setBusy(true); setError(null)
    try {
      const result = await careerApi.enrichAsset(currentAsset.id)
      setEnrichment(`${result.provider} added ${result.tags_added.length} tags and ${result.themes_added.length} themes. ${result.summary}`)
      onChanged(await careerApi.getAsset(currentAsset.id))
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to enrich asset') }
    finally { setBusy(false) }
  }

  return (
    <Dialog open onClose={onClose} fullWidth maxWidth="md">
      <DialogTitle>
        <Stack direction="row" justifyContent="space-between" alignItems="center" gap={2}>
          <span>{asset.title}</span><Chip label={asset.category} color="primary" variant="outlined" />
        </Stack>
      </DialogTitle>
      <DialogContent>
        {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
        {enrichment && <Alert severity="success" sx={{ mb: 2 }}>{enrichment}</Alert>}
        <Typography color="text.secondary">{asset.description || 'No description yet.'}</Typography>
        {asset.impact_summary && <><Typography fontWeight={800} mt={3}>Impact</Typography><Typography>{asset.impact_summary}</Typography></>}
        <Stack direction="row" flexWrap="wrap" gap={1} mt={2}>{asset.themes.map((theme) => <Chip key={theme.id} label={theme.name} />)}{asset.tags.map((tag) => <Chip key={tag} label={tag} variant="outlined" />)}</Stack>
        <Divider sx={{ my: 3 }} />
        <Typography variant="h6" mb={2}>Evidence</Typography>
        <Stack spacing={1.5} mb={3}>
          {asset.evidence.map((item) => <Card key={item.id} variant="outlined"><CardContent><Typography fontWeight={800}>{item.title}</Typography><Typography color="text.secondary">{item.description}</Typography>{item.source_url && <Button href={item.source_url} target="_blank" size="small">Open public source</Button>}{item.document && <Button href={downloadUrl(`/documents/${item.document.id}/download`)} size="small" startIcon={<AttachFileOutlined />}>Download {item.document.original_filename}</Button>}</CardContent></Card>)}
          {asset.evidence.length === 0 && <Typography color="text.secondary">No evidence linked yet.</Typography>}
        </Stack>
        <Box component="form" onSubmit={(event) => void addEvidence(event)} sx={{ bgcolor: 'background.default', borderRadius: 2, p: 2 }}>
          <Typography fontWeight={800} mb={2}>Add supporting evidence</Typography>
          <Grid container spacing={2}>
            <Grid size={{ xs: 12, md: 6 }}><TextField required fullWidth label="Evidence title" value={title} onChange={(event) => setTitle(event.target.value)} /></Grid>
            <Grid size={{ xs: 12, md: 6 }}><TextField fullWidth label="Public source URL" value={sourceUrl} onChange={(event) => setSourceUrl(event.target.value)} /></Grid>
            <Grid size={12}><TextField fullWidth multiline minRows={2} label="What this evidence demonstrates" value={description} onChange={(event) => setDescription(event.target.value)} /></Grid>
            <Grid size={{ xs: 12, md: 6 }}><Button component="label" variant="outlined" startIcon={<AttachFileOutlined />}>{file?.name ?? 'Attach PDF, DOCX, TXT or JSON'}<input hidden type="file" accept=".pdf,.docx,.txt,.json" onChange={(event: ChangeEvent<HTMLInputElement>) => setFile(event.target.files?.[0] ?? null)} /></Button></Grid>
            {file && <><Grid size={{ xs: 12, md: 6 }}><TextField select fullWidth label="AI handling" value={policy} onChange={(event) => setPolicy(event.target.value as typeof policy)}><MenuItem value="local_only">Local only</MenuItem><MenuItem value="ai_allowed">AI allowed</MenuItem><MenuItem value="redacted">Redacted copy only</MenuItem></TextField></Grid><Grid size={12}><FormControlLabel control={<Checkbox checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />} label="I confirm this document contains only public professional information and no sensitive or confidential content." /></Grid></>}
            <Grid size={12}><Button type="submit" variant="contained" disabled={busy}>{busy ? 'Adding…' : 'Add evidence'}</Button></Grid>
          </Grid>
        </Box>
      </DialogContent>
      <DialogActions><Button startIcon={<AutoAwesomeOutlined />} onClick={() => void enrich()} disabled={busy}>AI enrich</Button><Button color="warning" startIcon={<ArchiveOutlined />} onClick={() => void archive()} disabled={busy}>Archive</Button><Button startIcon={<EditOutlined />} onClick={onEdit}>Edit</Button><Button onClick={onClose}>Close</Button></DialogActions>
    </Dialog>
  )
}

export function AssetsPage() {
  const [assets, setAssets] = useState<CareerAsset[] | null>(null)
  const [reviewAssets, setReviewAssets] = useState<CareerAsset[]>([])
  const [total, setTotal] = useState(0)
  const [themes, setThemes] = useState<Theme[]>([])
  const [organisations, setOrganisations] = useState<Organisation[]>([])
  const [search, setSearch] = useState('')
  const [category, setCategory] = useState('')
  const [status, setStatus] = useState('active')
  const [editorOpen, setEditorOpen] = useState(false)
  const [selected, setSelected] = useState<CareerAsset | null>(null)
  const [editing, setEditing] = useState<CareerAsset | null>(null)
  const [reviewingMissingImpact, setReviewingMissingImpact] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)

  const load = useCallback(async () => {
    const params = new URLSearchParams()
    if (search) params.set('search', search)
    if (category) params.set('category', category)
    if (status) params.set('asset_status', status)
    try {
      const [result, activeResult] = await Promise.all([
        careerApi.listAssets(params),
        careerApi.listAssets(new URLSearchParams({ asset_status: 'active' })),
      ])
      setAssets(result.items); setTotal(result.total); setError(null)
      setReviewAssets(activeResult.items)
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to load career assets') }
  }, [category, search, status])

  useEffect(() => { void load() }, [load])
  useEffect(() => { void Promise.all([careerApi.listThemes(), careerApi.listOrganisations()]).then(([themeItems, organisationItems]) => { setThemes(themeItems); setOrganisations(organisationItems) }).catch(() => undefined) }, [])

  function changed(asset: CareerAsset) {
    setSelected(asset)
    setAssets((current) => current?.map((item) => item.id === asset.id ? asset : item) ?? null)
    setReviewAssets((current) => current.map((item) => item.id === asset.id ? asset : item))
  }

  const missingExperienceImpact = reviewAssets.filter((asset) =>
    asset.status === 'active'
    && asset.category.toLowerCase().includes('experience')
    && !asset.impact_summary.trim()
  )

  function startMissingImpactReview() {
    const first = missingExperienceImpact[0]
    if (!first) return
    setReviewingMissingImpact(true)
    setEditing(first)
    setEditorOpen(true)
  }

  function savedAsset(asset: CareerAsset): boolean {
    changed(asset)
    void load()
    if (reviewingMissingImpact) {
      const next = missingExperienceImpact.find((item) => item.id !== asset.id)
      if (next) {
        setEditing(next)
        setFeedback(`Impact summary saved. ${missingExperienceImpact.length - 1} experience records remain for review.`)
        return true
      }
      setReviewingMissingImpact(false)
      setFeedback('All experience records now have an impact summary.')
      return false
    }
    setFeedback(editing ? 'Career asset updated.' : 'Career asset created.')
    return false
  }

  return (
    <>
      <PageHeader eyebrow="PERMANENT CAREER MEMORY" title="Career assets" description="Capture each achievement, role, output, and contribution as reusable, evidence-backed strategic capital." action={{ label: 'Add career asset', icon: <AddOutlined />, onClick: () => { setEditing(null); setEditorOpen(true) } }} />
      <Card sx={{ mb: 3 }}><CardContent><Grid container spacing={2}><Grid size={{ xs: 12, md: 6 }}><TextField fullWidth label="Search assets" value={search} onChange={(event) => setSearch(event.target.value)} slotProps={{ input: { startAdornment: <InputAdornment position="start"><SearchOutlined /></InputAdornment> } }} /></Grid><Grid size={{ xs: 12, sm: 6, md: 3 }}><TextField select fullWidth label="Category" value={category} onChange={(event) => setCategory(event.target.value)}><MenuItem value="">All categories</MenuItem>{categories.map((item) => <MenuItem key={item} value={item}>{item}</MenuItem>)}</TextField></Grid><Grid size={{ xs: 12, sm: 6, md: 3 }}><TextField select fullWidth label="Status" value={status} onChange={(event) => setStatus(event.target.value)}><MenuItem value="">All statuses</MenuItem><MenuItem value="active">Active</MenuItem><MenuItem value="draft">Draft</MenuItem><MenuItem value="archived">Archived</MenuItem></TextField></Grid></Grid></CardContent></Card>
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      {missingExperienceImpact.length > 0 && <Alert severity="info" sx={{ mb: 2 }} action={<Button color="inherit" startIcon={<AutoAwesomeOutlined />} onClick={startMissingImpactReview}>Review with AI</Button>}><strong>{missingExperienceImpact.length} experience record{missingExperienceImpact.length === 1 ? '' : 's'}</strong> {missingExperienceImpact.length === 1 ? 'does' : 'do'} not yet have an impact summary. Review AI-generated alternatives one record at a time.</Alert>}
      <Typography color="text.secondary" mb={2}>{total} career asset{total === 1 ? '' : 's'}</Typography>
      {!assets ? <CircularProgress aria-label="Loading career assets" /> : <Grid container spacing={2}>{assets.map((asset) => <Grid key={asset.id} size={{ xs: 12, md: 6, lg: 4 }}><Card sx={{ height: '100%' }}><CardActionArea onClick={() => setSelected(asset)} sx={{ height: '100%', alignItems: 'stretch' }}><CardContent><Stack direction="row" justifyContent="space-between" gap={1}><Typography color="secondary.main" fontWeight={800}>{asset.category}</Typography><Typography variant="caption">{asset.start_date ?? 'No date'}</Typography></Stack><Typography variant="h6" mt={1}>{asset.title}</Typography><Typography color="text.secondary" mt={1} sx={{ display: '-webkit-box', WebkitLineClamp: 3, WebkitBoxOrient: 'vertical', overflow: 'hidden' }}>{asset.impact_summary || asset.description || 'Add an impact summary.'}</Typography><Stack direction="row" gap={1} mt={2} flexWrap="wrap"><Chip size="small" label={`${asset.evidence.length} evidence`} /><Chip size="small" label={asset.source_kind} variant="outlined" />{asset.category.toLowerCase().includes('experience') && !asset.impact_summary.trim() && <Chip size="small" color="secondary" label="Impact review needed" />}</Stack></CardContent></CardActionArea></Card></Grid>)}</Grid>}
      {assets?.length === 0 && <Alert severity="info">No assets match these filters. Add an asset or adjust the search.</Alert>}
      <AssetDialog open={editorOpen} asset={editing} themes={themes} organisations={organisations} onClose={() => { setEditorOpen(false); setReviewingMissingImpact(false) }} onSaved={savedAsset} />
      <AssetDetailDialog asset={selected} onClose={() => setSelected(null)} onEdit={() => { setReviewingMissingImpact(false); setEditing(selected); setEditorOpen(true) }} onChanged={(asset) => { changed(asset); void load() }} />
      <Feedback message={feedback} onClose={() => setFeedback(null)} />
    </>
  )
}
