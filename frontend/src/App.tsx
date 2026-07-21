import AutoAwesomeOutlined from '@mui/icons-material/AutoAwesomeOutlined'
import DescriptionOutlined from '@mui/icons-material/DescriptionOutlined'
import EmojiEventsOutlined from '@mui/icons-material/EmojiEventsOutlined'
import FolderCopyOutlined from '@mui/icons-material/FolderCopyOutlined'
import InsightsOutlined from '@mui/icons-material/InsightsOutlined'
import WorkOutline from '@mui/icons-material/WorkOutline'
import {
  Alert,
  AppBar,
  Box,
  Card,
  CardContent,
  Chip,
  Container,
  Grid,
  Stack,
  Toolbar,
  Typography,
} from '@mui/material'
import type { ReactNode } from 'react'

import { useApiHealth } from './hooks/useApiHealth'

interface FoundationCardProps {
  icon: ReactNode
  title: string
  description: string
  stage: string
}

function FoundationCard({ icon, title, description, stage }: FoundationCardProps) {
  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: 3 }}>
        <Stack direction="row" alignItems="center" justifyContent="space-between" mb={2}>
          <Box sx={{ color: 'primary.main', display: 'flex' }}>{icon}</Box>
          <Chip size="small" label={stage} variant="outlined" />
        </Stack>
        <Typography variant="h6" component="h2" gutterBottom>
          {title}
        </Typography>
        <Typography color="text.secondary">{description}</Typography>
      </CardContent>
    </Card>
  )
}

export function App() {
  const health = useApiHealth()
  const statusLabel =
    health.status === 'online'
      ? `API online · v${health.data.version}`
      : health.status === 'checking'
        ? 'Checking API…'
        : 'API offline'

  return (
    <Box minHeight="100vh">
      <AppBar position="static" color="transparent" elevation={0}>
        <Toolbar sx={{ borderBottom: '1px solid', borderColor: 'divider' }}>
          <InsightsOutlined sx={{ mr: 1.5, color: 'primary.main' }} />
          <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 800 }}>
            CAPSTONE
          </Typography>
          <Chip
            label={statusLabel}
            color={health.status === 'online' ? 'success' : health.status === 'offline' ? 'error' : 'default'}
            variant="outlined"
            aria-live="polite"
          />
        </Toolbar>
      </AppBar>

      <Container maxWidth="lg" sx={{ py: { xs: 5, md: 8 } }}>
        <Grid container spacing={5} alignItems="center" mb={7}>
          <Grid size={{ xs: 12, md: 8 }}>
            <Typography color="secondary.main" fontWeight={800} letterSpacing="0.12em" mb={1}>
              CAREER INTELLIGENCE, LOCALLY CONTROLLED
            </Typography>
            <Typography variant="h1" fontSize={{ xs: '2.6rem', md: '4.6rem' }} mb={2}>
              Turn career experience into strategic momentum.
            </Typography>
            <Typography variant="h6" color="text.secondary" maxWidth={760} fontWeight={400}>
              CAPSTONE will connect your career assets, opportunities, targets, and evidence to help
              identify the highest-value action to take next.
            </Typography>
          </Grid>
          <Grid size={{ xs: 12, md: 4 }}>
            <Box
              sx={{
                borderRadius: 4,
                p: 3,
                color: 'white',
                background: 'linear-gradient(145deg, #17213c, #3157a4)',
              }}
            >
              <AutoAwesomeOutlined fontSize="large" />
              <Typography variant="h5" component="h2" fontWeight={700} mt={2}>
                Stage 2 foundation
              </Typography>
              <Typography sx={{ opacity: 0.82, mt: 1 }}>
                The local application shell, API, database migration, and test framework are ready
                for the first career-asset workflow.
              </Typography>
            </Box>
          </Grid>
        </Grid>

        {health.status === 'offline' && (
          <Alert severity="warning" sx={{ mb: 4 }}>
            The web interface is running, but the local API could not be reached. Start the backend
            or Docker Compose, then reload this page.
          </Alert>
        )}

        <Typography variant="h4" component="h2" mb={3}>
          Product foundations
        </Typography>
        <Grid container spacing={3}>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <FoundationCard icon={<FolderCopyOutlined />} title="Career assets" description="Build a reusable, evidence-backed repository of professional achievements and experience." stage="Stage 3" />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <FoundationCard icon={<WorkOutline />} title="Opportunities" description="Compare opportunities using transparent strategic value, probability, and effort scores." stage="Stage 5" />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <FoundationCard icon={<DescriptionOutlined />} title="Job applications" description="Map verified evidence to job requirements and create grounded application drafts." stage="Stage 7" />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <FoundationCard icon={<EmojiEventsOutlined />} title="Targets and readiness" description="Define desired trajectories and understand the strongest evidence and most important gaps." stage="Stage 6" />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <FoundationCard icon={<AutoAwesomeOutlined />} title="AI enrichment" description="Automatically enrich derived metadata without overwriting user-provided facts." stage="Stage 4" />
          </Grid>
          <Grid size={{ xs: 12, sm: 6, md: 4 }}>
            <FoundationCard icon={<InsightsOutlined />} title="Next best action" description="Bring evidence, goals, readiness, and opportunity value together in one recommendation." stage="MVP" />
          </Grid>
        </Grid>
      </Container>
    </Box>
  )
}
