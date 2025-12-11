import React, { createContext, useContext, useState, useEffect, ReactNode } from 'react';

export type AppSettings = {
  // General
  autoLockEnabled: boolean;
  autoLockTimeout: number;
  startMinimized: boolean;
  startOnBoot: boolean;
  // Notifications
  soundEnabled: boolean;
  notificationsEnabled: boolean;
  showLockNotification: boolean;
  showUnlockNotification: boolean;
  // Appearance
  theme: 'dark' | 'light' | 'system';
  accentColor: string;
  compactMode: boolean;
  // Security
  requireConfirmation: boolean;
  emergencyUnlockEnabled: boolean;
  hotkeyEnabled: boolean;
  // Advanced
  logRetentionDays: number;
  debugMode: boolean;
  // Localization
  language: 'en' | 'es';
};

const defaultSettings: AppSettings = {
  autoLockEnabled: false,
  autoLockTimeout: 5,
  startMinimized: false,
  startOnBoot: false,
  soundEnabled: true,
  notificationsEnabled: true,
  showLockNotification: true,
  showUnlockNotification: true,
  theme: 'dark',
  accentColor: '#2196f3',
  compactMode: false,
  requireConfirmation: false,
  emergencyUnlockEnabled: true,
  hotkeyEnabled: true,
  logRetentionDays: 7,
  debugMode: false,
  language: 'en',
};

type SettingsContextType = {
  settings: AppSettings;
  updateSetting: <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => void;
  resetSettings: () => void;
};

const SettingsContext = createContext<SettingsContextType | undefined>(undefined);

const STORAGE_KEY = 'input-locker-settings';

export const SettingsProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [settings, setSettings] = useState<AppSettings>(() => {
    // Load from localStorage on init
    try {
      const saved = localStorage.getItem(STORAGE_KEY);
      if (saved) {
        return { ...defaultSettings, ...JSON.parse(saved) };
      }
    } catch (e) {
      console.error('Failed to load settings:', e);
    }
    return defaultSettings;
  });

  // Save to localStorage when settings change
  useEffect(() => {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(settings));
    } catch (e) {
      console.error('Failed to save settings:', e);
    }
  }, [settings]);

  const updateSetting = <K extends keyof AppSettings>(key: K, value: AppSettings[K]) => {
    setSettings(prev => ({ ...prev, [key]: value }));
  };

  const resetSettings = () => {
    setSettings(defaultSettings);
  };

  return (
    <SettingsContext.Provider value={{ settings, updateSetting, resetSettings }}>
      {children}
    </SettingsContext.Provider>
  );
};

export const useSettings = () => {
  const context = useContext(SettingsContext);
  if (!context) {
    throw new Error('useSettings must be used within a SettingsProvider');
  }
  return context;
};

export { defaultSettings };
