import { Box, Button, Stack, Typography } from '@mui/material'
import type { ReactNode } from 'react'

interface PageHeaderProps {
  eyebrow?: string
  title: string
  description: string
  action?: { label: string; icon?: ReactNode; onClick: () => void }
}

export function PageHeader({ eyebrow, title, description, action }: PageHeaderProps) {
  return (
    <Stack direction={{ xs: 'column', md: 'row' }} justifyContent="space-between" gap={3} mb={4}>
      <Box maxWidth={820}>
        {eyebrow && (
          <Typography color="secondary.main" fontWeight={800} letterSpacing="0.1em" mb={0.5}>
            {eyebrow}
          </Typography>
        )}
        <Typography variant="h3" component="h1" mb={1}>
          {title}
        </Typography>
        <Typography color="text.secondary" variant="h6" fontWeight={400}>
          {description}
        </Typography>
      </Box>
      {action && (
        <Button
          variant="contained"
          size="large"
          startIcon={action.icon}
          onClick={action.onClick}
          sx={{ alignSelf: { xs: 'stretch', md: 'center' } }}
        >
          {action.label}
        </Button>
      )}
    </Stack>
  )
}

