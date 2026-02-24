import { extendTheme } from '@chakra-ui/react'

const theme = extendTheme({
  config: {
    initialColorMode: 'light',
    useSystemColorMode: false,
  },
  styles: {
    global: {
      body: {
        bg: '#f8f9fb',
        color: '#1a1d26',
      },
      '::-webkit-scrollbar': {
        width: '6px',
      },
      '::-webkit-scrollbar-track': {
        bg: 'transparent',
      },
      '::-webkit-scrollbar-thumb': {
        bg: '#d0d4dc',
        borderRadius: 'full',
      },
    },
  },
  colors: {
    surface: {
      bg: '#f8f9fb',
      card: '#ffffff',
      cardHover: '#fafbfc',
      raised: '#f1f3f6',
      border: '#e2e5eb',
      borderLight: '#eceef2',
      borderHover: '#cdd1d9',
    },
    text: {
      primary: '#1a1d26',
      secondary: '#4a5068',
      tertiary: '#6b7280',
      muted: '#9ca3b0',
      faint: '#b8bec9',
    },
    brand: {
      50: '#ecfeff',
      100: '#cffafe',
      200: '#a5f3fc',
      300: '#67e8f9',
      400: '#22d3ee',
      500: '#0891b2',
      600: '#0e7490',
      700: '#155e75',
    },
    severity: {
      p1: '#e11d48',
      p1Light: '#fff1f3',
      p1Border: '#fecdd3',
      p1Text: '#be123c',
      p2: '#d97706',
      p2Light: '#fffbeb',
      p2Border: '#fde68a',
      p2Text: '#b45309',
      p3: '#0284c7',
      p3Light: '#f0f9ff',
      p3Border: '#bae6fd',
      p3Text: '#0369a1',
      p4: '#6366f1',
      p4Light: '#eef2ff',
      p4Border: '#c7d2fe',
      p4Text: '#4f46e5',
    },
    violet: {
      50: '#f5f3ff',
      100: '#ede9fe',
      200: '#ddd6fe',
      300: '#c4b5fd',
      400: '#a78bfa',
      500: '#8b5cf6',
      600: '#7c3aed',
    },
    emerald: {
      50: '#ecfdf5',
      100: '#d1fae5',
      400: '#34d399',
      500: '#10b981',
      600: '#059669',
    },
  },
  fonts: {
    heading: `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`,
    body: `'Inter', -apple-system, BlinkMacSystemFont, sans-serif`,
    mono: `'JetBrains Mono', 'SF Mono', 'Fira Code', monospace`,
  },
})

export default theme
