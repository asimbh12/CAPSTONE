import BackupOutlined from '@mui/icons-material/BackupOutlined'
import DownloadOutlined from '@mui/icons-material/DownloadOutlined'
import UploadFileOutlined from '@mui/icons-material/UploadFileOutlined'
import {
  Alert,
  Button,
  Card,
  CardContent,
  Checkbox,
  FormControlLabel,
  Grid,
  LinearProgress,
  Stack,
  Typography,
} from '@mui/material'
import { type ChangeEvent, useState } from 'react'

import { apiBaseUrl, careerApi, downloadUrl } from '../api/client'
import { PageHeader } from '../components/PageHeader'
import type { BackupRecord, ImportReport } from '../types/career'

export function DataPage() {
  const [payload, setPayload] = useState<object | null>(null)
  const [filename, setFilename] = useState('')
  const [confirmed, setConfirmed] = useState(false)
  const [report, setReport] = useState<ImportReport | null>(null)
  const [backup, setBackup] = useState<BackupRecord | null>(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState<string | null>(null)

  async function chooseFile(event: ChangeEvent<HTMLInputElement>) {
    const file = event.target.files?.[0]
    if (!file) return
    setFilename(file.name); setReport(null); setError(null)
    try { setPayload(JSON.parse(await file.text()) as object) }
    catch { setPayload(null); setError('This file is not valid JSON.') }
  }

  async function runImport(mode: 'dry_run' | 'apply') {
    if (!payload || !confirmed) return
    setBusy(true); setError(null)
    try { setReport(await careerApi.importData(payload, mode)) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Import could not be validated') }
    finally { setBusy(false) }
  }

  async function createBackup() {
    setBusy(true); setError(null)
    try { setBackup(await careerApi.createBackup()) }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Backup could not be created') }
    finally { setBusy(false) }
  }

  return (
    <>
      <PageHeader eyebrow="LOCAL-FIRST DATA CONTROL" title="Data safety" description="Export portable JSON, validate imports before applying them, and create coordinated backups of SQLite and local documents." />
      {busy && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 6 }}><Card sx={{ height: '100%' }}><CardContent><Typography variant="h5" mb={1}>Export and templates</Typography><Typography color="text.secondary" mb={3}>Export all structured data using schema version 1.0, or download a safe template before preparing your personal seed data.</Typography><Stack direction={{ xs: 'column', sm: 'row' }} gap={1.5}><Button href={`${apiBaseUrl}/data/export`} startIcon={<DownloadOutlined />} variant="contained">Export CAPSTONE JSON</Button><Button href={`${apiBaseUrl}/data/template`} startIcon={<DownloadOutlined />} variant="outlined">Download import template</Button></Stack></CardContent></Card></Grid>
        <Grid size={{ xs: 12, lg: 6 }}><Card sx={{ height: '100%' }}><CardContent><Typography variant="h5" mb={1}>Full local backup</Typography><Typography color="text.secondary" mb={3}>Create a consistent SQLite snapshot plus original, derived, and generated files with a checksum manifest.</Typography><Button variant="contained" startIcon={<BackupOutlined />} onClick={() => void createBackup()} disabled={busy}>Create and verify backup</Button>{backup && <Alert severity={backup.verified ? 'success' : 'error'} sx={{ mt: 2 }}><Typography fontWeight={800}>{backup.verified ? 'Backup verified' : 'Backup requires attention'}</Typography><Typography>{backup.filename}</Typography><Typography variant="body2">{backup.file_count} files checked · SQLite integrity: {backup.database_integrity}</Typography><Button href={downloadUrl(backup.download_url)} startIcon={<DownloadOutlined />}>Download backup</Button></Alert>}</CardContent></Card></Grid>
        <Grid size={12}><Card><CardContent><Typography variant="h5" mb={1}>Import public professional data</Typography><Typography color="text.secondary" mb={2}>CAPSTONE always performs a dry run first. Existing asset titles are detected as duplicates and skipped during apply.</Typography><Alert severity="warning" sx={{ mb: 2 }}>Do not import confidential, classified, health, financial, private referee, or otherwise sensitive information.</Alert><Button component="label" variant="outlined" startIcon={<UploadFileOutlined />}>{filename || 'Choose JSON file'}<input hidden type="file" accept="application/json,.json" onChange={(event) => void chooseFile(event)} /></Button><FormControlLabel sx={{ display: 'block', mt: 2 }} control={<Checkbox checked={confirmed} onChange={(event) => setConfirmed(event.target.checked)} />} label="I confirm this file contains only publicly available professional information." /><Stack direction="row" gap={1.5} mt={2}><Button variant="contained" disabled={!payload || !confirmed || busy} onClick={() => void runImport('dry_run')}>Run validation</Button><Button color="warning" variant="outlined" disabled={!report?.valid || report.mode !== 'dry_run' || !confirmed || busy} onClick={() => void runImport('apply')}>Apply validated import</Button></Stack>{report && <Alert severity={report.valid ? report.applied ? 'success' : 'info' : 'error'} sx={{ mt: 3 }}><Typography fontWeight={800}>{report.applied ? 'Import applied' : report.valid ? 'Dry run passed' : 'Validation failed'}</Typography><Typography>{Object.entries(report.counts).map(([key, value]) => `${key}: ${value}`).join(' · ')}</Typography>{report.warnings.map((warning) => <Typography key={warning}>{warning}</Typography>)}{report.errors.map((item) => <Typography key={item}>{item}</Typography>)}</Alert>}</CardContent></Card></Grid>
      </Grid>
    </>
  )
}
