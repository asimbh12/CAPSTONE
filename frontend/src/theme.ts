import { createTheme } from '@mui/material/styles'

export const capstoneTheme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#3157a4', dark: '#17213c' },
    secondary: { main: '#b86b2e' },
    background: { default: '#f4f6fa', paper: '#ffffff' },
    text: { primary: '#17213c', secondary: '#5d6475' },
  },
  typography: {
    fontFamily: 'Inter, Segoe UI, Arial, sans-serif',
    h1: { fontWeight: 700, letterSpacing: '-0.04em' },
    h2: { fontWeight: 700, letterSpacing: '-0.025em' },
    button: { fontWeight: 700, textTransform: 'none' },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: { border: '1px solid #e3e7ef', boxShadow: '0 8px 28px rgba(23,33,60,.06)' },
      },
    },
  },
})

