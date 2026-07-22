import { createTheme } from '@mui/material/styles'

export const capstoneTheme = createTheme({
  palette: {
    mode: 'light',
    primary: { main: '#3157a4', dark: '#17213c' },
    secondary: { main: '#b86b2e' },
    background: { default: '#f6f7fa', paper: '#ffffff' },
    text: { primary: '#17213c', secondary: '#5d6475' },
  },
  typography: {
    fontFamily: 'Inter, Segoe UI, Arial, sans-serif',
    h1: { fontWeight: 800, letterSpacing: '-0.04em' },
    h2: { fontWeight: 800, letterSpacing: '-0.025em' },
    h3: { fontWeight: 800, letterSpacing: '-0.025em' },
    h4: { fontWeight: 800, letterSpacing: '-0.015em' },
    button: { fontWeight: 700, textTransform: 'none' },
  },
  shape: { borderRadius: 12 },
  components: {
    MuiCard: {
      styleOverrides: {
        root: { border: '1px solid #e5e8ef', boxShadow: '0 3px 14px rgba(23,33,60,.045)', backgroundImage: 'none' },
      },
    },
    MuiButton: { styleOverrides: { root: { borderRadius: 10, minHeight: 38 } } },
    MuiAlert: { styleOverrides: { root: { borderRadius: 10, alignItems: 'flex-start' } } },
    MuiAccordion: { styleOverrides: { root: { border: '1px solid #e5e8ef', boxShadow: 'none', borderRadius: '12px !important', overflow: 'hidden', '&:before': { display: 'none' } } } },
    MuiAccordionSummary: { styleOverrides: { root: { minHeight: 64, paddingLeft: 20, paddingRight: 20 }, content: { margin: '14px 0' } } },
    MuiChip: { styleOverrides: { root: { fontWeight: 650 } } },
  },
})
