import AddOutlined from '@mui/icons-material/AddOutlined'
import SaveOutlined from '@mui/icons-material/SaveOutlined'
import DeleteOutlineOutlined from '@mui/icons-material/DeleteOutlineOutlined'
import {
  Alert,
  Box,
  Button,
  Card,
  CardContent,
  Chip,
  CircularProgress,
  Grid,
  MenuItem,
  Stack,
  TextField,
  Typography,
  Dialog,
  DialogActions,
  DialogContent,
  DialogTitle,
} from '@mui/material'
import { type FormEvent, useEffect, useState } from 'react'

import { careerApi } from '../api/client'
import { Feedback } from '../components/Feedback'
import { PageHeader } from '../components/PageHeader'
import type { Goal, ProfileInput, Theme } from '../types/career'

const emptyProfile: ProfileInput = {
  name: '', current_title: '', current_organisation: '', career_mission: '', career_narrative: '',
}

export function ProfilePage() {
  const [profile, setProfile] = useState<ProfileInput | null>(null)
  const [themes, setThemes] = useState<Theme[]>([])
  const [goals, setGoals] = useState<Goal[]>([])
  const [themeName, setThemeName] = useState('')
  const [goalTitle, setGoalTitle] = useState('')
  const [goalDescription, setGoalDescription] = useState('')
  const [goalHorizon, setGoalHorizon] = useState<Goal['horizon']>('medium_term')
  const [saving, setSaving] = useState(false)
  const [feedback, setFeedback] = useState<string | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [removingGoal, setRemovingGoal] = useState<Goal | null>(null)

  useEffect(() => {
    void Promise.all([careerApi.getProfile(), careerApi.listThemes(), careerApi.listGoals()])
      .then(([profileRecord, themeRecords, goalRecords]) => {
        setProfile(profileRecord ? {
          name: profileRecord.name,
          current_title: profileRecord.current_title,
          current_organisation: profileRecord.current_organisation,
          career_mission: profileRecord.career_mission,
          career_narrative: profileRecord.career_narrative,
        } : emptyProfile)
        setThemes(themeRecords); setGoals(goalRecords)
      })
      .catch((reason: unknown) => setError(reason instanceof Error ? reason.message : 'Unable to load profile'))
  }, [])

  if (!profile && !error) return <CircularProgress aria-label="Loading profile" />

  async function saveProfile(event: FormEvent) {
    event.preventDefault()
    if (!profile) return
    setSaving(true); setError(null)
    try { await careerApi.saveProfile(profile); setFeedback('Career profile saved.') }
    catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to save profile') }
    finally { setSaving(false) }
  }

  async function addTheme(event: FormEvent) {
    event.preventDefault()
    try {
      const theme = await careerApi.createTheme({ name: themeName, description: '' })
      setThemes((current) => [...current, theme].sort((a, b) => a.name.localeCompare(b.name)))
      setThemeName(''); setFeedback('Professional theme added.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to add theme') }
  }

  async function addGoal(event: FormEvent) {
    event.preventDefault()
    try {
      const goal = await careerApi.createGoal({ title: goalTitle, description: goalDescription, horizon: goalHorizon, target_date: null })
      setGoals((current) => [goal, ...current]); setGoalTitle(''); setGoalDescription(''); setFeedback('Strategic goal added.')
    } catch (reason) { setError(reason instanceof Error ? reason.message : 'Unable to add goal') }
  }

  async function removeGoal() {
    if (!removingGoal) return
    setSaving(true); setError(null)
    try {
      await careerApi.removeGoal(removingGoal.id)
      setGoals(current => current.filter(goal => goal.id !== removingGoal.id))
      setFeedback('Strategic goal removed. Its assessment history has been retained.')
      setRemovingGoal(null)
    } catch (reason) {
      setError(reason instanceof Error ? reason.message : 'Unable to remove goal')
    } finally { setSaving(false) }
  }

  return (
    <>
      <PageHeader eyebrow="USER-AUTHORITATIVE STRATEGY" title="Profile & goals" description="Define the mission, narrative, professional themes, and goals that future recommendations must serve." />
      {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
      {profile && <Card sx={{ mb: 4 }}><CardContent><Box component="form" onSubmit={(event) => void saveProfile(event)}><Typography variant="h5" mb={3}>Career profile</Typography><Grid container spacing={2}><Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Name" value={profile.name} onChange={(event) => setProfile({ ...profile, name: event.target.value })} /></Grid><Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Current title" value={profile.current_title} onChange={(event) => setProfile({ ...profile, current_title: event.target.value })} /></Grid><Grid size={{ xs: 12, md: 4 }}><TextField fullWidth label="Current organisation" value={profile.current_organisation} onChange={(event) => setProfile({ ...profile, current_organisation: event.target.value })} /></Grid><Grid size={12}><TextField fullWidth multiline minRows={2} label="Career mission" value={profile.career_mission} onChange={(event) => setProfile({ ...profile, career_mission: event.target.value })} /></Grid><Grid size={12}><TextField fullWidth multiline minRows={4} label="Career narrative" value={profile.career_narrative} onChange={(event) => setProfile({ ...profile, career_narrative: event.target.value })} /></Grid><Grid size={12}><Button type="submit" variant="contained" startIcon={<SaveOutlined />} disabled={saving}>{saving ? 'Saving…' : 'Save profile'}</Button></Grid></Grid></Box></CardContent></Card>}
      <Grid container spacing={3}>
        <Grid size={{ xs: 12, lg: 5 }}><Card sx={{ height: '100%' }}><CardContent><Typography variant="h5" mb={1}>Professional themes</Typography><Typography color="text.secondary" mb={2}>Reusable strategic topics that connect assets and future opportunities.</Typography><Stack direction="row" gap={1} flexWrap="wrap" mb={3}>{themes.map((theme) => <Chip key={theme.id} label={theme.name} />)}{themes.length === 0 && <Typography color="text.secondary">No themes yet.</Typography>}</Stack><Box component="form" onSubmit={(event) => void addTheme(event)}><Stack direction="row" gap={1}><TextField required size="small" fullWidth label="New theme" value={themeName} onChange={(event) => setThemeName(event.target.value)} /><Button type="submit" variant="outlined" startIcon={<AddOutlined />}>Add</Button></Stack></Box></CardContent></Card></Grid>
        <Grid size={{ xs: 12, lg: 7 }}><Card><CardContent><Typography variant="h5" mb={1}>Strategic goals</Typography><Typography color="text.secondary" mb={2}>Adopted goals remain user-authoritative. Remove goals that are achieved, obsolete, or no longer part of your intended trajectory.</Typography><Stack spacing={1.5} mb={3}>{goals.map((goal) => <Box key={goal.id} sx={{ p: 2, border: '1px solid', borderColor: 'divider', borderRadius: 2 }}><Stack direction="row" justifyContent="space-between" gap={2}><Box><Typography fontWeight={800}>{goal.title}</Typography><Chip sx={{ mt: 0.75 }} size="small" label={goal.horizon.replace('_', ' ')} /></Box><Button size="small" color="error" startIcon={<DeleteOutlineOutlined />} onClick={() => setRemovingGoal(goal)}>Remove</Button></Stack>{goal.description && <Typography color="text.secondary" mt={0.5}>{goal.description}</Typography>}</Box>)}{goals.length === 0 && <Typography color="text.secondary">No goals yet.</Typography>}</Stack><Box component="form" onSubmit={(event) => void addGoal(event)}><Grid container spacing={1.5}><Grid size={{ xs: 12, md: 7 }}><TextField required fullWidth size="small" label="Goal title" value={goalTitle} onChange={(event) => setGoalTitle(event.target.value)} /></Grid><Grid size={{ xs: 12, md: 5 }}><TextField select fullWidth size="small" label="Horizon" value={goalHorizon} onChange={(event) => setGoalHorizon(event.target.value as Goal['horizon'])}><MenuItem value="short_term">Short term</MenuItem><MenuItem value="medium_term">Medium term</MenuItem><MenuItem value="long_term">Long term</MenuItem></TextField></Grid><Grid size={12}><TextField fullWidth size="small" label="Description" value={goalDescription} onChange={(event) => setGoalDescription(event.target.value)} /></Grid><Grid size={12}><Button type="submit" variant="outlined" startIcon={<AddOutlined />}>Add goal</Button></Grid></Grid></Box></CardContent></Card></Grid>
      </Grid>
      <Feedback message={feedback} onClose={() => setFeedback(null)} />
      <Dialog open={Boolean(removingGoal)} onClose={() => setRemovingGoal(null)} maxWidth="sm" fullWidth>
        <DialogTitle>Remove strategic goal?</DialogTitle>
        <DialogContent><Typography>This will hide <strong>{removingGoal?.title}</strong> from Profile & goals and readiness planning. Existing assessment history will be retained for audit and recovery.</Typography></DialogContent>
        <DialogActions><Button onClick={() => setRemovingGoal(null)}>Cancel</Button><Button color="error" variant="contained" disabled={saving} onClick={() => void removeGoal()}>Remove goal</Button></DialogActions>
      </Dialog>
    </>
  )
}
