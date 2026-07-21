import { Alert, Snackbar } from '@mui/material'

interface FeedbackProps {
  message: string | null
  severity?: 'success' | 'error' | 'warning' | 'info'
  onClose: () => void
}

export function Feedback({ message, severity = 'success', onClose }: FeedbackProps) {
  return (
    <Snackbar open={Boolean(message)} autoHideDuration={5000} onClose={onClose}>
      <Alert severity={severity} onClose={onClose} variant="filled">
        {message}
      </Alert>
    </Snackbar>
  )
}

