import React, { useMemo } from 'react';
import { ThemeProvider, CssBaseline } from '@mui/material';
import { Dashboard } from './pages';
import { createDarkTheme } from './theme';
import { createLightTheme } from './theme';
import { SettingsProvider, useSettings } from './context';

const ThemedApp: React.FC = () => {
  const { settings } = useSettings();
  
  const theme = useMemo(() => {
    // Determine if we should use dark or light mode
    let isDark = settings.theme === 'dark';
    
    if (settings.theme === 'system') {
      // Check system preference
      isDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
    }
    
    // Create theme with selected accent color
    return isDark 
      ? createDarkTheme(settings.accentColor)
      : createLightTheme(settings.accentColor);
  }, [settings.theme, settings.accentColor]);

  return (
    <ThemeProvider theme={theme}>
      <CssBaseline />
      <Dashboard />
    </ThemeProvider>
  );
};

const App: React.FC = () => {
  return (
    <SettingsProvider>
      <ThemedApp />
    </SettingsProvider>
  );
};

export default App;
