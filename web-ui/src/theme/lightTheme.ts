import { createTheme, alpha, Theme } from '@mui/material/styles';

// Create a light theme with given accent color
export const createLightTheme = (accentColor: string = '#2196f3'): Theme => {
  const colors = {
    primary: {
      main: accentColor,
      light: alpha(accentColor, 0.7),
      dark: accentColor,
    },
    secondary: {
      main: '#00b8d4',
      light: '#33c9dc',
      dark: '#008c9e',
    },
    background: {
      default: '#f5f7fa',
      paper: '#ffffff',
      elevated: '#f0f4f8',
    },
    text: {
      primary: '#1a202c',
      secondary: 'rgba(26, 32, 44, 0.7)',
      disabled: 'rgba(26, 32, 44, 0.4)',
    },
    border: {
      light: 'rgba(0, 0, 0, 0.08)',
      medium: 'rgba(0, 0, 0, 0.15)',
      accent: alpha(accentColor, 0.3),
    },
  };

  return createTheme({
    palette: {
      mode: 'light',
      primary: colors.primary,
      secondary: colors.secondary,
      background: {
        default: colors.background.default,
        paper: colors.background.paper,
      },
      text: colors.text,
    },
    typography: {
      fontFamily: '"Inter", "Roboto", "Helvetica", "Arial", sans-serif',
      h1: { fontSize: '2.5rem', fontWeight: 700, letterSpacing: '-0.02em' },
      h2: { fontSize: '2rem', fontWeight: 600, letterSpacing: '-0.01em' },
      h3: { fontSize: '1.5rem', fontWeight: 600 },
      h4: { fontSize: '1.25rem', fontWeight: 600 },
      h5: { fontSize: '1rem', fontWeight: 600 },
      h6: { fontSize: '0.875rem', fontWeight: 600 },
      body1: { fontSize: '1rem', lineHeight: 1.6 },
      body2: { fontSize: '0.875rem', lineHeight: 1.5 },
      caption: { fontSize: '0.75rem', color: colors.text.secondary },
    },
    shape: { borderRadius: 12 },
    components: {
      MuiCssBaseline: {
        styleOverrides: {
          body: {
            background: `linear-gradient(180deg, ${colors.background.default} 0%, #e8ecf1 100%)`,
            minHeight: '100vh',
            '&::-webkit-scrollbar': { width: 8 },
            '&::-webkit-scrollbar-track': { background: colors.background.elevated },
            '&::-webkit-scrollbar-thumb': { background: accentColor, borderRadius: 4 },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            background: 'rgba(255, 255, 255, 0.9)',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${colors.border.light}`,
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.08)',
            transition: 'all 0.3s ease-in-out',
            '&:hover': {
              border: `1px solid ${colors.border.accent}`,
              boxShadow: `0 8px 30px ${alpha(accentColor, 0.15)}`,
              transform: 'translateY(-2px)',
            },
          },
        },
      },
      MuiButton: {
        styleOverrides: {
          root: {
            textTransform: 'none',
            fontWeight: 600,
            borderRadius: 8,
            padding: '10px 24px',
          },
          contained: {
            background: `linear-gradient(135deg, ${accentColor} 0%, ${alpha(accentColor, 0.8)} 100%)`,
            boxShadow: `0 4px 14px ${alpha(accentColor, 0.35)}`,
            color: '#ffffff',
            '&:hover': {
              background: `linear-gradient(135deg, ${alpha(accentColor, 0.9)} 0%, ${accentColor} 100%)`,
              boxShadow: `0 6px 20px ${alpha(accentColor, 0.45)}`,
            },
          },
          outlined: {
            borderColor: colors.border.accent,
            '&:hover': {
              borderColor: accentColor,
              background: alpha(accentColor, 0.08),
            },
          },
        },
      },
      MuiChip: {
        styleOverrides: {
          root: { fontWeight: 500, borderRadius: 8 },
          filled: {
            background: alpha(accentColor, 0.15),
            '&:hover': { background: alpha(accentColor, 0.25) },
          },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            background: 'rgba(255, 255, 255, 0.98)',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${colors.border.light}`,
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: { backgroundImage: 'none' },
        },
      },
      MuiSwitch: {
        styleOverrides: {
          root: { width: 52, height: 28, padding: 0 },
          switchBase: {
            padding: 2,
            '&.Mui-checked': {
              transform: 'translateX(24px)',
              '& + .MuiSwitch-track': { backgroundColor: accentColor, opacity: 1 },
              '& .MuiSwitch-thumb': { backgroundColor: '#fff', boxShadow: `0 0 8px ${accentColor}` },
            },
          },
          thumb: {
            width: 24,
            height: 24,
            backgroundColor: colors.text.secondary,
            transition: 'all 0.3s ease',
          },
          track: {
            borderRadius: 14,
            backgroundColor: colors.background.elevated,
            opacity: 1,
            border: `1px solid ${colors.border.medium}`,
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: { borderRadius: 4, backgroundColor: alpha(accentColor, 0.15) },
          bar: {
            borderRadius: 4,
            background: `linear-gradient(90deg, ${accentColor} 0%, ${colors.secondary.main} 100%)`,
          },
        },
      },
      MuiTabs: {
        styleOverrides: {
          indicator: { backgroundColor: accentColor },
        },
      },
      MuiTab: {
        styleOverrides: {
          root: {
            '&.Mui-selected': { color: accentColor },
          },
        },
      },
      MuiFab: {
        styleOverrides: {
          root: { boxShadow: `0 4px 20px ${alpha(accentColor, 0.4)}` },
        },
      },
      MuiSlider: {
        styleOverrides: {
          root: { color: accentColor },
          thumb: { boxShadow: `0 0 10px ${alpha(accentColor, 0.5)}` },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: colors.background.paper,
            color: colors.text.primary,
            border: `1px solid ${colors.border.light}`,
            borderRadius: 8,
            fontSize: '0.8rem',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.1)',
          },
        },
      },
    },
  });
};

export const lightTheme = createLightTheme('#2196f3');
