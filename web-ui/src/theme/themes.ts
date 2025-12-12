import { createTheme, alpha, Theme } from '@mui/material/styles';

// Create a dark theme with given accent color
export const createDarkTheme = (accentColor: string = '#2196f3'): Theme => {
  const colors = {
    primary: {
      main: accentColor,
      light: alpha(accentColor, 0.7),
      dark: accentColor,
    },
    secondary: {
      main: '#00d4ff',
      light: '#33ddff',
      dark: '#00a8cc',
    },
    accent: {
      purple: '#a855f7',
      pink: '#ec4899',
      green: '#10b981',
      orange: '#f97316',
      red: '#ef4444',
    },
    background: {
      default: '#0a1929',
      paper: '#1e293b',
      elevated: '#283548',
      gradient: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)',
    },
    text: {
      primary: '#ffffff',
      secondary: 'rgba(255, 255, 255, 0.7)',
      disabled: 'rgba(255, 255, 255, 0.4)',
    },
    border: {
      light: 'rgba(255, 255, 255, 0.1)',
      medium: 'rgba(255, 255, 255, 0.2)',
      accent: alpha(accentColor, 0.3),
    },
  };

  return createTheme({
    palette: {
      mode: 'dark',
      primary: colors.primary,
      secondary: colors.secondary,
      background: {
        default: colors.background.default,
        paper: colors.background.paper,
      },
      text: colors.text,
      error: { main: colors.accent.red },
      success: { main: colors.accent.green },
      warning: { main: colors.accent.orange },
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
            background: `linear-gradient(180deg, ${colors.background.default} 0%, #0d1f35 100%)`,
            minHeight: '100vh',
            '&::-webkit-scrollbar': { width: 8 },
            '&::-webkit-scrollbar-track': { background: colors.background.paper },
            '&::-webkit-scrollbar-thumb': { background: accentColor, borderRadius: 4 },
          },
        },
      },
      MuiCard: {
        styleOverrides: {
          root: {
            backgroundImage: colors.background.gradient,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${colors.border.light}`,
            boxShadow: `0 8px 32px rgba(0, 0, 0, 0.3)`,
            transition: 'all 0.3s ease-in-out',
            '&:hover': {
              border: `1px solid ${colors.border.accent}`,
              boxShadow: `0 12px 40px ${alpha(accentColor, 0.15)}`,
              transform: 'translateY(-2px)',
            },
          },
        },
      },
      MuiPaper: {
        styleOverrides: {
          root: { backgroundImage: 'none' },
          elevation1: { boxShadow: '0 4px 20px rgba(0, 0, 0, 0.25)' },
          elevation2: { boxShadow: '0 8px 32px rgba(0, 0, 0, 0.3)' },
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
            boxShadow: `0 4px 20px ${alpha(accentColor, 0.4)}`,
            '&:hover': {
              background: `linear-gradient(135deg, ${alpha(accentColor, 0.9)} 0%, ${accentColor} 100%)`,
              boxShadow: `0 6px 24px ${alpha(accentColor, 0.5)}`,
            },
          },
          outlined: {
            borderColor: colors.border.accent,
            '&:hover': {
              borderColor: accentColor,
              background: alpha(accentColor, 0.1),
            },
          },
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
              '& .MuiSwitch-thumb': { backgroundColor: '#fff', boxShadow: `0 0 12px ${accentColor}` },
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
      MuiChip: {
        styleOverrides: {
          root: { borderRadius: 8, fontWeight: 500 },
          filled: {
            background: alpha(accentColor, 0.2),
            '&:hover': { background: alpha(accentColor, 0.3) },
          },
          outlined: { borderColor: colors.border.accent },
        },
      },
      MuiTooltip: {
        styleOverrides: {
          tooltip: {
            backgroundColor: colors.background.elevated,
            border: `1px solid ${colors.border.light}`,
            borderRadius: 8,
            fontSize: '0.8rem',
            boxShadow: '0 4px 20px rgba(0, 0, 0, 0.3)',
          },
          arrow: { color: colors.background.elevated },
        },
      },
      MuiDialog: {
        styleOverrides: {
          paper: {
            backgroundImage: colors.background.gradient,
            backdropFilter: 'blur(20px)',
            border: `1px solid ${colors.border.light}`,
          },
        },
      },
      MuiLinearProgress: {
        styleOverrides: {
          root: { borderRadius: 4, backgroundColor: alpha(accentColor, 0.2) },
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
          root: {
            boxShadow: `0 4px 20px ${alpha(accentColor, 0.4)}`,
          },
        },
      },
      MuiSlider: {
        styleOverrides: {
          root: { color: accentColor },
          thumb: { boxShadow: `0 0 10px ${alpha(accentColor, 0.5)}` },
        },
      },
    },
  });
};

// Default dark theme
export const darkTheme = createDarkTheme('#2196f3');

// Export default colors for use in components  
export const colors = {
  primary: { main: '#2196f3', light: '#64b5f6', dark: '#1976d2' },
  secondary: { main: '#00d4ff', light: '#33ddff', dark: '#00a8cc' },
  accent: { purple: '#a855f7', pink: '#ec4899', green: '#10b981', orange: '#f97316', red: '#ef4444' },
  background: { default: '#0a1929', paper: '#1e293b', elevated: '#283548', gradient: 'linear-gradient(135deg, #1e293b 0%, #0f172a 100%)' },
  text: { primary: '#ffffff', secondary: 'rgba(255, 255, 255, 0.7)', disabled: 'rgba(255, 255, 255, 0.4)' },
  border: { light: 'rgba(255, 255, 255, 0.1)', medium: 'rgba(255, 255, 255, 0.2)', accent: 'rgba(33, 150, 243, 0.3)' },
};
