import React, { useState, useEffect, useCallback } from 'react';
import {
  Box,
  Container,
  Grid,
  Typography,
  Button,
  Snackbar,
  Alert,
  Fab,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Skeleton,
  Card,
  CardContent,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Divider,
  Avatar,
  Paper,
  Switch,
  FormControlLabel,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  Tabs,
  Tab,
  IconButton,
  useTheme,
  TextField,
} from '@mui/material';
import {
  LockOutlined as LockAllIcon,
  LockOpenOutlined as UnlockAllIcon,
  Refresh as RefreshIcon,
  Security as SecurityIcon,
  Shield as ShieldIcon,
  ChildCare as ChildIcon,
  Work as WorkIcon,
  Gamepad as GameIcon,
  History as HistoryIcon,
  Schedule as ScheduleIcon,
  Info as InfoIcon,
  Speed as SpeedIcon,
  Memory as MemoryIcon,
  Storage as StorageIcon,
  Close as CloseIcon,
  Notifications as NotificationsIcon,
  Palette as PaletteIcon,
  Tune as TuneIcon,
  RestartAlt as ResetIcon,
} from '@mui/icons-material';
import { motion, AnimatePresence } from 'framer-motion';

import {
  Header,
  DeviceCard,
  StatusIndicator,
  BlockTimer,
  StatisticsChart,
} from '../../components';
import { api, wsService } from '../../services';
import { useSettings, type AppSettings } from '../../context';
import type { Device, Statistics, Timer, SystemStatus, Settings } from '../../types';
import { useI18n } from '../../i18n';

// Security profile configuration
const securityProfiles = [
  {
    id: 'focus',
    name: 'Focus Mode',
    icon: <WorkIcon />,
    description: 'Block all except essential mouse',
    color: '#2196f3',
    devices: ['keyboard', 'touchpad', 'touchscreen'],
  },
  {
    id: 'child',
    name: 'Child Lock',
    icon: <ChildIcon />,
    description: 'Block all input devices',
    color: '#ff9800',
    devices: ['keyboard', 'mouse', 'touchpad', 'touchscreen'],
  },
  {
    id: 'gaming',
    name: 'Gaming Mode',
    icon: <GameIcon />,
    description: 'Block touchpad only',
    color: '#9c27b0',
    devices: ['touchpad'],
  },
  {
    id: 'presentation',
    name: 'Presentation',
    icon: <SecurityIcon />,
    description: 'Block keyboard only',
    color: '#4caf50',
    devices: ['keyboard'],
  },
];

export const Dashboard: React.FC = () => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const { t } = useI18n();
  
  // Dynamic card background based on theme
  const cardBg = isDark 
    ? 'linear-gradient(135deg, rgba(30, 41, 59, 0.8) 0%, rgba(15, 23, 42, 0.9) 100%)'
    : 'linear-gradient(135deg, rgba(255, 255, 255, 0.9) 0%, rgba(248, 250, 252, 0.95) 100%)';
  const cardBorder = isDark ? 'rgba(255, 255, 255, 0.1)' : 'rgba(0, 0, 0, 0.08)';
  
  // State
  const [devices, setDevices] = useState<Device[]>([]);
  const [statistics, setStatistics] = useState<Statistics>({
    totalBlockedTime: 0,
    blockedEvents: 0,
    blockHistory: [],
    deviceStats: [],
  });
  const [timer, setTimer] = useState<Timer>({
    active: false,
    remainingSeconds: 0,
    totalSeconds: 0,
  });
  const [systemStatus, setSystemStatus] = useState<SystemStatus>({
    running: false,
    activeBlocks: 0,
    connectedDevices: 0,
    uptime: 0,
  });
  
  const [loading, setLoading] = useState(true);
  const [apiReady, setApiReady] = useState(false);
  const [backendUnavailable, setBackendUnavailable] = useState(false);
  const [retryCount, setRetryCount] = useState(0);
  const [actionLoading, setActionLoading] = useState<string | null>(null);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [onboardingOpen, setOnboardingOpen] = useState(false);
  const [settingsTab, setSettingsTab] = useState(0);
  const [snackbar, setSnackbar] = useState<{
    open: boolean;
    message: string;
    severity: 'success' | 'error' | 'info' | 'warning';
  }>({ open: false, message: '', severity: 'info' });
  const [activeProfile, setActiveProfile] = useState<string | null>(null);
  const [activityLog, setActivityLog] = useState<{
    id: number;
    timestamp: Date;
    action: string;
    device?: string;
    type: 'lock' | 'unlock' | 'timer' | 'system';
  }[]>([]);
  const [backendSettings, setBackendSettings] = useState<Settings | null>(null);
  const [backendHotkeyInput, setBackendHotkeyInput] = useState('');
  const [backendPatternInput, setBackendPatternInput] = useState('');
  const [backendSaving, setBackendSaving] = useState(false);
  
  // App Settings from context (persistent)
  const { settings, updateSetting, resetSettings } = useSettings();

  // Add activity to log
  const addActivity = useCallback((action: string, device?: string, type: 'lock' | 'unlock' | 'timer' | 'system' = 'system') => {
    setActivityLog(prev => [{
      id: Date.now(),
      timestamp: new Date(),
      action,
      device,
      type,
    }, ...prev].slice(0, 50)); // Keep last 50 entries
  }, []);

  // Fetch data with retry logic
  const fetchData = useCallback(async () => {
    try {
      const [devicesRes, statsRes, timerRes, statusRes] = await Promise.all([
        api.getDevices(),
        api.getStats(),
        api.getTimerStatus(),
        api.getSystemStatus(),
      ]);

      setDevices(devicesRes);
      setStatistics(statsRes);
      setTimer(timerRes);
      setSystemStatus(statusRes);
      setApiReady(true);
      setBackendUnavailable(false);
      setLoading(false);
      setRetryCount(0);
    } catch (error) {
      console.log(`Waiting for API... (attempt ${retryCount + 1})`);
      setRetryCount(prev => prev + 1);
      // Retry after 1 second if API not ready yet (max 30 attempts = 30 seconds)
      if (retryCount < 30) {
        setTimeout(() => {
          fetchData();
        }, 1000);
      } else {
        setLoading(false);
        setBackendUnavailable(true);
        setSnackbar({
          open: true,
          message: 'Could not connect to API server. Please ensure the backend service is running.',
          severity: 'error',
        });
      }
    }
  }, [retryCount]);

  // Load backend settings (hotkey, emergency pattern, theme)
  const fetchBackendSettings = useCallback(async () => {
    try {
      const s = await api.getSettings();
      setBackendSettings(s);
      setBackendHotkeyInput((s.hotkey || []).join(' + '));
      setBackendPatternInput((s.emergencyPattern || []).join(' '));
    } catch (error) {
      console.error('Failed to load backend settings:', error);
    }
  }, []);

  // First-run onboarding state (local to web UI for now)
  useEffect(() => {
    try {
      const stored = localStorage.getItem('input-locker-onboarding-completed');
      if (!stored) {
        setOnboardingOpen(true);
      }
    } catch (e) {
      console.error('Failed to read onboarding flag:', e);
    }
  }, []);

  // Initial load and WebSocket setup
  useEffect(() => {
    fetchData();
    fetchBackendSettings();

    // Connect WebSocket
    wsService.connect();

    // Subscribe to updates
    const unsubDevice = wsService.onDeviceUpdate((device) => {
      setDevices((prev) =>
        prev.map((d) =>
          d.path === device.path ? { ...d, blocked: device.blocked } : d
        )
      );
    });

    // Subscribe to full devices list updates (from hotkey/pattern actions)
    const unsubDevices = wsService.onDevicesUpdate((updatedDevices) => {
      console.log('📱 Updating devices from WebSocket:', updatedDevices.length);
      setDevices(updatedDevices);
    });

    const unsubTimer = wsService.onTimerUpdate((timerUpdate) => {
      setTimer(timerUpdate);
    });

    const unsubStatus = wsService.onStatusUpdate((status) => {
      console.log('📊 Updating status from WebSocket:', status);
      setSystemStatus(status);
    });

    // Subscribe to hotkey actions for notifications
    const unsubHotkey = wsService.onHotkeyAction((action) => {
      const isLock = action.action === 'locked';
      setSnackbar({
        open: true,
        message: isLock 
          ? '🔐 All devices locked via hotkey (Ctrl+Alt+L)' 
          : '🔓 All devices unlocked via ' + (action.type === 'pattern' ? 'pattern (↑↑↓↓Enter)' : 'hotkey'),
        severity: isLock ? 'warning' : 'success',
      });
      // Refresh devices after a short delay to ensure backend has updated
      setTimeout(async () => {
        try {
          const devicesRes = await api.getDevices();
          console.log('🔄 Refreshed devices after hotkey:', devicesRes.length);
          setDevices(devicesRes);
        } catch (e) {
          console.error('Error refreshing devices:', e);
        }
      }, 100);
    });

    // Subscribe to stats updates for real-time statistics
    const unsubStats = wsService.onStatsUpdate((stats) => {
      setStatistics(stats);
    });

    // Cleanup
    return () => {
      unsubDevice();
      unsubDevices();
      unsubTimer();
      unsubStatus();
      unsubHotkey();
      unsubStats();
      wsService.disconnect();
    };
  }, [fetchData, fetchBackendSettings]);

  // Handlers
  const handleToggleDevice = async (devicePath: string) => {
    setActionLoading(devicePath);
    try {
      await api.toggleBlock(devicePath);
      
      // Update local state
      setDevices((prev) =>
        prev.map((d) =>
          d.path === devicePath ? { ...d, blocked: !d.blocked } : d
        )
      );
      
      const device = devices.find((d) => d.path === devicePath);
      const action = device?.blocked ? 'Unblocked' : 'Blocked';
      
      setSnackbar({
        open: true,
        message: `${action}: ${device?.name || devicePath}`,
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to toggle device',
        severity: 'error',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleBlockAll = async () => {
    setActionLoading('block-all');
    try {
      await api.blockAll();
      await fetchData();
      addActivity('All devices blocked', undefined, 'lock');
      setSnackbar({
        open: true,
        message: 'All devices blocked',
        severity: 'warning',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to block all devices',
        severity: 'error',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleUnblockAll = async () => {
    setActionLoading('unblock-all');
    try {
      await api.unblockAll();
      await fetchData();
      addActivity('All devices unlocked', undefined, 'unlock');
      setSnackbar({
        open: true,
        message: 'All devices unblocked',
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to unblock all devices',
        severity: 'error',
      });
    } finally {
      setActionLoading(null);
    }
  };

  const handleSetTimer = async (minutes: number) => {
    try {
      const result = await api.setTimer(minutes);
      setTimer(result);
      addActivity(`Timer set for ${minutes} minutes`, undefined, 'timer');
      setSnackbar({
        open: true,
        message: `Timer set for ${minutes} minutes`,
        severity: 'info',
      });
      await fetchData();
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to set timer',
        severity: 'error',
      });
    }
  };

  const handleCancelTimer = async () => {
    try {
      await api.cancelTimer();
      setTimer({ active: false, remainingSeconds: 0, totalSeconds: 0 });
      addActivity('Timer cancelled', undefined, 'timer');
      setSnackbar({
        open: true,
        message: 'Timer cancelled',
        severity: 'info',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to cancel timer',
        severity: 'error',
      });
    }
  };

  const handleRefresh = async () => {
    setLoading(true);
    await fetchData();
    addActivity('Devices refreshed', undefined, 'system');
    setSnackbar({
      open: true,
      message: 'Devices refreshed',
      severity: 'info',
    });
  };

  // Apply security profile
  const handleApplyProfile = async (profile: typeof securityProfiles[0]) => {
    setActionLoading(profile.id);
    try {
      // Use the new lockByTypes endpoint to lock only specific device types
      await api.lockByTypes(profile.devices);
      
      setActiveProfile(profile.id);
      await fetchData();
      addActivity(`Profile "${profile.name}" activated`, undefined, 'lock');
      setSnackbar({
        open: true,
        message: `${profile.name} profile activated`,
        severity: 'success',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to apply profile',
        severity: 'error',
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Deactivate profile
  const handleDeactivateProfile = async () => {
    setActionLoading('deactivate');
    try {
      await api.unblockAll();
      setActiveProfile(null);
      await fetchData();
      addActivity('Profile deactivated', undefined, 'unlock');
      setSnackbar({
        open: true,
        message: 'Profile deactivated',
        severity: 'info',
      });
    } catch (error) {
      setSnackbar({
        open: true,
        message: 'Failed to deactivate profile',
        severity: 'error',
      });
    } finally {
      setActionLoading(null);
    }
  };

  // Format time for activity log
  const formatTime = (date: Date) => {
    return date.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit', second: '2-digit' });
  };

  // Filter only important device types (keyboard, mouse, touchpad, touchscreen)
  const importantTypes = ['keyboard', 'mouse', 'touchpad', 'touchscreen'];
  const filteredDevices = devices.filter(d => importantTypes.includes(d.type));
  
  // Group filtered devices by type
  const groupedDevices = filteredDevices.reduce<Record<string, Device[]>>((acc, device) => {
    const type = device.type || 'other';
    if (!acc[type]) acc[type] = [];
    acc[type].push(device);
    return acc;
  }, {});

  const blockedCount = devices.filter((d: Device) => d.blocked).length;

  // Show loading screen while waiting for API
  if (loading && !apiReady) {
    return (
      <Box
        sx={{
          minHeight: '100vh',
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 3,
          background: isDark
            ? 'linear-gradient(135deg, #0a1929 0%, #1a2744 100%)'
            : 'linear-gradient(135deg, #f5f7fa 0%, #e4e8ec 100%)',
        }}
      >
        <motion.div
          initial={{ scale: 0.8, opacity: 0 }}
          animate={{ scale: 1, opacity: 1 }}
          transition={{ duration: 0.5 }}
        >
          <SecurityIcon sx={{ fontSize: 80, color: 'primary.main', mb: 2 }} />
        </motion.div>
        <Typography variant="h4" sx={{ fontWeight: 600 }}>
          Input Locker
        </Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <LinearProgress sx={{ width: 200 }} />
        </Box>
        <Typography variant="body2" color="text.secondary">
          {retryCount === 0 
            ? t('dashboard.loading.connecting') 
            : `${t('dashboard.loading.waiting')} (${retryCount}s)`}
        </Typography>
        <Typography variant="caption" color="text.disabled">
          {t('dashboard.loading.passwordHint')}
        </Typography>
      </Box>
    );
  }

  return (
    <Box sx={{ minHeight: '100vh', pb: 4 }}>
      {/* Header */}
      <Header
        onSettingsClick={() => {
          setSettingsOpen(true);
          fetchBackendSettings();
        }}
        onRefreshClick={handleRefresh}
      />

      <Container maxWidth="xl" sx={{ mt: 3 }}>
        {backendUnavailable && (
          <Box sx={{ mb: 2 }}>
            <Alert severity="error" variant="outlined">
              Cannot reach backend API on 127.0.0.1:8080. If you are using the systemd service, check that it is running (e.g. <Typography component="span" sx={{ fontFamily: 'monospace' }}>sudo systemctl status input-locker-backend.service</Typography>).
            </Alert>
          </Box>
        )}
        {/* Status Bar */}
        <motion.div
          initial={{ opacity: 0, y: -20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
        >
          <StatusIndicator
            isRunning={systemStatus.running}
            activeBlocks={blockedCount}
            connectedDevices={devices.length}
            uptime={systemStatus.uptime}
          />
        </motion.div>

        {/* Quick Actions */}
        <Box sx={{ display: 'flex', gap: 2, my: 3, flexWrap: 'wrap' }}>
          <Button
            variant="contained"
            color="error"
            startIcon={<LockAllIcon />}
            onClick={handleBlockAll}
            disabled={actionLoading === 'block-all'}
            sx={{ px: 3 }}
          >
            {t('dashboard.actions.lockAll')}
          </Button>
          <Button
            variant="contained"
            color="success"
            startIcon={<UnlockAllIcon />}
            onClick={handleUnblockAll}
            disabled={actionLoading === 'unblock-all'}
            sx={{ px: 3 }}
          >
            {t('dashboard.actions.unlockAll')}
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
            disabled={loading}
          >
            {t('dashboard.actions.refresh')}
          </Button>
        </Box>

        <Grid container spacing={3}>
          {/* Devices Section */}
          <Grid item xs={12} lg={8}>
            <Typography variant="h5" sx={{ mb: 2, fontWeight: 600 }}>
              {t('dashboard.section.devicesTitle')}
            </Typography>

            {loading ? (
              <Grid container spacing={1.5}>
                {[1, 2, 3, 4].map((i) => (
                  <Grid item xs={6} sm={4} md={3} lg={2} key={i}>
                    <Skeleton
                      variant="rectangular"
                      height={120}
                      sx={{ borderRadius: 2 }}
                    />
                  </Grid>
                ))}
              </Grid>
            ) : (
              <AnimatePresence>
                {Object.entries(groupedDevices).map(([type, typeDevices]) => (
                  <Box key={type} sx={{ mb: 2 }}>
                    <Typography
                      variant="subtitle2"
                      sx={{
                        mb: 1,
                        color: 'text.secondary',
                        textTransform: 'capitalize',
                        display: 'flex',
                        alignItems: 'center',
                        gap: 0.5,
                        fontSize: '0.8rem',
                      }}
                    >
                      {type === 'keyboard' && '⌨️'}
                      {type === 'mouse' && '🖱️'}
                      {type === 'touchpad' && '👆'}
                      {type === 'touchscreen' && '📱'}
                      {type === 'other' && '🔌'}
                      {type}s ({typeDevices.length})
                    </Typography>
                    <Grid container spacing={1.5}>
                      {typeDevices.map((device) => (
                        <Grid item xs={6} sm={4} md={3} lg={2} key={device.path}>
                          <DeviceCard
                            device={device}
                            onToggle={handleToggleDevice}
                            isLoading={actionLoading === device.path}
                          />
                        </Grid>
                      ))}
                    </Grid>
                  </Box>
                ))}
              </AnimatePresence>
            )}

            {!loading && filteredDevices.length === 0 && (
              <Box
                sx={{
                  textAlign: 'center',
                  py: 4,
                  color: 'text.secondary',
                }}
              >
                <Typography variant="subtitle1">{t('dashboard.noDevices.title')}</Typography>
                <Typography variant="caption">
                  {t('dashboard.noDevices.subtitle')}
                </Typography>
              </Box>
            )}
          </Grid>

          {/* Sidebar */}
          <Grid item xs={12} lg={4}>
            {/* Timer */}
            <Box sx={{ mb: 3 }}>
              <BlockTimer
                timer={timer}
                onSetTimer={handleSetTimer}
                onCancelTimer={handleCancelTimer}
              />
            </Box>

            {/* Security Profiles */}
            <Card
              component={motion.div}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.2 }}
              sx={{
                mb: 3,
                background: cardBg,
                backdropFilter: 'blur(20px)',
                border: `1px solid ${cardBorder}`,
              }}
            >
              <CardContent>
                <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                  <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                    <ShieldIcon color="primary" />
                    {t('dashboard.section.securityProfilesTitle')}
                  </Typography>
                  {activeProfile && (
                    <Chip 
                      label={t('dashboard.profile.activeLabel')} 
                      size="small" 
                      color="success" 
                      onDelete={handleDeactivateProfile}
                    />
                  )}
                </Box>
                <Grid container spacing={1}>
                  {securityProfiles.map((profile) => (
                    <Grid item xs={6} key={profile.id}>
                      <Paper
                        sx={{
                          p: 1.5,
                          cursor: 'pointer',
                          textAlign: 'center',
                          background: activeProfile === profile.id
                            ? `linear-gradient(135deg, ${profile.color}40 0%, ${profile.color}20 100%)`
                            : isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.02)',
                          border: activeProfile === profile.id
                            ? `2px solid ${profile.color}`
                            : `1px solid ${cardBorder}`,
                          transition: 'all 0.3s',
                          '&:hover': {
                            background: `${profile.color}20`,
                            transform: 'scale(1.02)',
                          },
                        }}
                        onClick={() => handleApplyProfile(profile)}
                      >
                        <Avatar
                          sx={{
                            bgcolor: profile.color,
                            width: 36,
                            height: 36,
                            mx: 'auto',
                            mb: 1,
                          }}
                        >
                          {profile.icon}
                        </Avatar>
                        <Typography variant="caption" sx={{ fontWeight: 600, display: 'block' }}>
                          {t(`profile.${profile.id}.name` as any)}
                        </Typography>
                        <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.65rem' }}>
                          {t(`profile.${profile.id}.description` as any)}
                        </Typography>
                      </Paper>
                    </Grid>
                  ))}
                </Grid>
              </CardContent>
            </Card>

            {/* System Health */}
            <Card
              component={motion.div}
              initial={{ opacity: 0, x: 20 }}
              animate={{ opacity: 1, x: 0 }}
              transition={{ delay: 0.3 }}
              sx={{
                mb: 3,
                background: cardBg,
                backdropFilter: 'blur(20px)',
                border: `1px solid ${cardBorder}`,
              }}
            >
              <CardContent>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <SpeedIcon color="primary" />
                  {t('dashboard.systemHealth.title')}
                </Typography>
                <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <MemoryIcon fontSize="small" /> {t('dashboard.systemHealth.apiStatus')}
                      </Typography>
                      <Chip
                        label={systemStatus.running ? 'Online' : 'Offline'}
                        size="small"
                        color={systemStatus.running ? 'success' : 'error'}
                        sx={{ height: 18, fontSize: '0.65rem' }}
                      />
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={systemStatus.running ? 100 : 0}
                      color={systemStatus.running ? 'success' : 'error'}
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <StorageIcon fontSize="small" /> {t('dashboard.systemHealth.devicesDetected')}
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                        {devices.length}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={Math.min((devices.length / 15) * 100, 100)}
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>
                  <Box>
                    <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 0.5 }}>
                      <Typography variant="caption" sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                        <LockAllIcon fontSize="small" /> {t('dashboard.systemHealth.activeLocks')}
                      </Typography>
                      <Typography variant="caption" sx={{ fontWeight: 600 }}>
                        {blockedCount} / {filteredDevices.length}
                      </Typography>
                    </Box>
                    <LinearProgress
                      variant="determinate"
                      value={filteredDevices.length > 0 ? (blockedCount / filteredDevices.length) * 100 : 0}
                      color="warning"
                      sx={{ height: 4, borderRadius: 2 }}
                    />
                  </Box>
                </Box>
              </CardContent>
            </Card>
          </Grid>

          {/* Activity Log - Full width */}
          <Grid item xs={12}>
            <Card
              component={motion.div}
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ delay: 0.5 }}
              sx={{
                background: cardBg,
                backdropFilter: 'blur(20px)',
                border: `1px solid ${cardBorder}`,
              }}
            >
              <CardContent>
                <Typography variant="h6" sx={{ display: 'flex', alignItems: 'center', gap: 1, mb: 2 }}>
                  <HistoryIcon color="primary" />
                  {t('dashboard.activity.title')}
                </Typography>
                {activityLog.length === 0 ? (
                  <Box sx={{ textAlign: 'center', py: 3, color: 'text.secondary' }}>
                    <HistoryIcon sx={{ fontSize: 40, opacity: 0.3, mb: 1 }} />
                      <Typography variant="body2">{t('dashboard.activity.emptyTitle')}</Typography>
                      <Typography variant="caption">{t('dashboard.activity.emptySubtitle')}</Typography>
                  </Box>
                ) : (
                  <List dense sx={{ maxHeight: 250, overflow: 'auto' }}>
                    {activityLog.slice(0, 20).map((entry, index) => (
                      <ListItem
                        key={entry.id}
                        component={motion.div}
                        initial={{ opacity: 0, x: -10 }}
                        animate={{ opacity: 1, x: 0 }}
                        transition={{ delay: index * 0.05 }}
                        sx={{
                          px: 1,
                          borderRadius: 1,
                          mb: 0.5,
                          bgcolor: isDark ? 'rgba(255, 255, 255, 0.02)' : 'rgba(0, 0, 0, 0.02)',
                        }}
                      >
                        <ListItemIcon sx={{ minWidth: 32 }}>
                          {entry.type === 'lock' && <LockAllIcon fontSize="small" color="error" />}
                          {entry.type === 'unlock' && <UnlockAllIcon fontSize="small" color="success" />}
                          {entry.type === 'timer' && <ScheduleIcon fontSize="small" color="info" />}
                          {entry.type === 'system' && <InfoIcon fontSize="small" color="primary" />}
                        </ListItemIcon>
                        <ListItemText
                          primary={entry.action}
                          secondary={formatTime(entry.timestamp)}
                          primaryTypographyProps={{ fontSize: '0.8rem' }}
                          secondaryTypographyProps={{ fontSize: '0.65rem' }}
                        />
                      </ListItem>
                    ))}
                  </List>
                )}
              </CardContent>
            </Card>
          </Grid>

          {/* Statistics */}
          <Grid item xs={12}>
            <Typography variant="h5" sx={{ mb: 2, mt: 2, fontWeight: 600 }}>
              {t('dashboard.statistics.title')}
            </Typography>
            <StatisticsChart statistics={statistics} />
          </Grid>
        </Grid>
      </Container>

      {/* Onboarding Dialog (first run) */}
      <Dialog
        open={onboardingOpen}
        onClose={() => {
          setOnboardingOpen(false);
          try {
            localStorage.setItem('input-locker-onboarding-completed', '1');
          } catch (e) {
            console.error('Failed to persist onboarding flag:', e);
          }
        }}
        maxWidth="sm"
        fullWidth
      >
        <DialogTitle>
          {t('onboarding.title')}
        </DialogTitle>
        <DialogContent dividers>
          <Typography variant="body1" gutterBottom>
            {t('onboarding.intro')}
          </Typography>

          <Box sx={{ mt: 2, mb: 2 }}>
            <Typography variant="subtitle2" gutterBottom>
              {t('onboarding.devicesTitle')}
            </Typography>
            {devices.length === 0 ? (
              <Typography variant="caption" color="text.secondary">
                {t('onboarding.noDevices')}
              </Typography>
            ) : (
              <List dense>
                {devices.map((d) => (
                  <ListItem key={d.path}>
                    <ListItemText
                      primary={d.name || d.path}
                      secondary={`${d.type} • ${d.blocked ? 'blocked' : 'allowed'}`}
                    />
                  </ListItem>
                ))}
              </List>
            )}
          </Box>

          <Divider sx={{ my: 2 }} />

          <Typography variant="subtitle2" gutterBottom>
            {t('onboarding.quickPrefsTitle')}
          </Typography>

          <FormControlLabel
            control={
              <Switch
                checked={settings.notificationsEnabled}
                onChange={(e) => updateSetting('notificationsEnabled', e.target.checked)}
              />
            }
            label={
              <Box>
                <Typography variant="body2">{t('onboarding.notifications.title')}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('onboarding.notifications.desc')}
                </Typography>
              </Box>
            }
          />

          <FormControlLabel
            control={
              <Switch
                checked={settings.startMinimized}
                onChange={(e) => updateSetting('startMinimized', e.target.checked)}
              />
            }
            label={
              <Box>
                <Typography variant="body2">{t('onboarding.startMinimized.title')}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('onboarding.startMinimized.desc')}
                </Typography>
              </Box>
            }
          />

          <FormControlLabel
            control={
              <Switch
                checked={settings.emergencyUnlockEnabled}
                onChange={(e) => updateSetting('emergencyUnlockEnabled', e.target.checked)}
              />
            }
            label={
              <Box>
                <Typography variant="body2">{t('security.emergency.title')}</Typography>
                <Typography variant="caption" color="text.secondary">
                  {t('security.emergency.subtitle')}
                </Typography>
              </Box>
            }
          />
        </DialogContent>
        <DialogActions>
          <Button
            onClick={() => {
              setOnboardingOpen(false);
              try {
                localStorage.setItem('input-locker-onboarding-completed', '1');
              } catch (e) {
                console.error('Failed to persist onboarding flag:', e);
              }
            }}
          >
            {t('onboarding.getStarted')}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Floating Action Buttons */}
      <Box
        sx={{
          position: 'fixed',
          bottom: 24,
          right: 24,
          display: 'flex',
          flexDirection: 'column',
          gap: 2,
        }}
      >
        {blockedCount > 0 && (
          <motion.div
            initial={{ scale: 0 }}
            animate={{ scale: 1 }}
            exit={{ scale: 0 }}
          >
            <Tooltip title={t('dashboard.actions.unlockAll')} placement="left">
              <Fab
                color="success"
                onClick={handleUnblockAll}
                disabled={actionLoading === 'unblock-all'}
              >
                <UnlockAllIcon />
              </Fab>
            </Tooltip>
          </motion.div>
        )}
      </Box>

      {/* Settings Dialog */}
      <Dialog
        open={settingsOpen}
        onClose={() => setSettingsOpen(false)}
        maxWidth="md"
        fullWidth
        PaperProps={{
          sx: {
            background: isDark 
              ? 'linear-gradient(135deg, rgba(30, 41, 59, 0.98) 0%, rgba(15, 23, 42, 0.99) 100%)'
              : 'linear-gradient(135deg, rgba(255, 255, 255, 0.98) 0%, rgba(248, 250, 252, 0.99) 100%)',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${cardBorder}`,
            minHeight: '70vh',
          }
        }}
      >
        <DialogTitle sx={{ 
          display: 'flex', 
          alignItems: 'center', 
          justifyContent: 'space-between',
          borderBottom: `1px solid ${cardBorder}`,
          pb: 2,
        }}>
          <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
            <TuneIcon color="primary" />
            <Typography variant="h6">{t('settings.title')}</Typography>
          </Box>
          <IconButton onClick={() => setSettingsOpen(false)} size="small">
            <CloseIcon />
          </IconButton>
        </DialogTitle>
        
        <Box sx={{ borderBottom: 1, borderColor: 'divider' }}>
          <Tabs 
            value={settingsTab} 
            onChange={(_, v) => setSettingsTab(v)}
            variant="fullWidth"
            sx={{ 
              '& .MuiTab-root': { 
                minHeight: 56,
                textTransform: 'none',
                fontWeight: 500,
              }
            }}
          >
            <Tab icon={<TuneIcon />} label={t('settings.tab.general')} iconPosition="start" />
            <Tab icon={<NotificationsIcon />} label={t('settings.tab.notifications')} iconPosition="start" />
            <Tab icon={<SecurityIcon />} label={t('settings.tab.security')} iconPosition="start" />
            <Tab icon={<PaletteIcon />} label={t('settings.tab.appearance')} iconPosition="start" />
            <Tab icon={<InfoIcon />} label={t('settings.tab.diagnostics')} iconPosition="start" />
          </Tabs>
        </Box>

        <DialogContent sx={{ p: 3 }}>
          {/* General Tab */}
          {settingsTab === 0 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.general.startupTitle')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.startOnBoot}
                    onChange={(e) => updateSetting('startOnBoot', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.general.startOnBoot.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.general.startOnBoot.desc')}
                    </Typography>
                  </Box>
                }
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.startMinimized}
                    onChange={(e) => updateSetting('startMinimized', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.general.startMinimized.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.general.startMinimized.desc')}
                    </Typography>
                  </Box>
                }
              />

              <Divider sx={{ my: 1 }} />
              
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.general.autoLockTitle')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.autoLockEnabled}
                    onChange={(e) => updateSetting('autoLockEnabled', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.general.autoLockEnabled.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.general.autoLockEnabled.desc')}
                    </Typography>
                  </Box>
                }
              />
              
              {settings.autoLockEnabled && (
                <Box sx={{ pl: 2 }}>
                  <Typography variant="body2" gutterBottom>
                    Idle Timeout: {settings.autoLockTimeout} minutes
                  </Typography>
                  <Slider
                    value={settings.autoLockTimeout}
                    onChange={(_, v) => updateSetting('autoLockTimeout', v as number)}
                    min={1}
                    max={60}
                    step={1}
                    marks={[
                      { value: 1, label: '1m' },
                      { value: 15, label: '15m' },
                      { value: 30, label: '30m' },
                      { value: 60, label: '60m' },
                    ]}
                    sx={{ maxWidth: 400 }}
                  />
                </Box>
              )}

              <Divider sx={{ my: 1 }} />
              
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.general.dataTitle')}
              </Typography>
              
              <Box>
                <Typography variant="body2" gutterBottom>
                  {t('settings.general.logRetention')}: {settings.logRetentionDays} days
                </Typography>
                <Slider
                  value={settings.logRetentionDays}
                  onChange={(_, v) => updateSetting('logRetentionDays', v as number)}
                  min={1}
                  max={30}
                  step={1}
                  marks={[
                    { value: 1, label: '1d' },
                    { value: 7, label: '7d' },
                    { value: 14, label: '14d' },
                    { value: 30, label: '30d' },
                  ]}
                  sx={{ maxWidth: 400 }}
                />
              </Box>
            </Box>
          )}

          {/* Notifications Tab */}
          {settingsTab === 1 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.notifications.title')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.notificationsEnabled}
                    onChange={(e) => updateSetting('notificationsEnabled', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.notifications.enable.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.notifications.enable.desc')}
                    </Typography>
                  </Box>
                }
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.soundEnabled}
                    onChange={(e) => updateSetting('soundEnabled', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.notifications.sound.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.notifications.sound.desc')}
                    </Typography>
                  </Box>
                }
              />

              <Divider sx={{ my: 1 }} />
              
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.notifications.typesTitle')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showLockNotification}
                    onChange={(e) => updateSetting('showLockNotification', e.target.checked)}
                    disabled={!settings.notificationsEnabled}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.notifications.lock.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.notifications.lock.desc')}
                    </Typography>
                  </Box>
                }
              />
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.showUnlockNotification}
                    onChange={(e) => updateSetting('showUnlockNotification', e.target.checked)}
                    disabled={!settings.notificationsEnabled}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.notifications.unlock.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.notifications.unlock.desc')}
                    </Typography>
                  </Box>
                }
              />
            </Box>
          )}

          {/* Security Tab */}
          {settingsTab === 2 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.security.keyboardShortcutsTitle')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.hotkeyEnabled}
                    onChange={(e) => updateSetting('hotkeyEnabled', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.security.hotkeyEnabled.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.security.hotkeyEnabled.desc')}
                    </Typography>
                  </Box>
                }
              />

              {/* TODO: In a next step, read the actual hotkey/pattern
                  from api.getSettings() and display it here, and
                  optionally allow editing it from the web UI. For
                  now the text remains static while the backend
                  supports configuration via the Qt app. */}
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.emergencyUnlockEnabled}
                    onChange={(e) => updateSetting('emergencyUnlockEnabled', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('security.emergency.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('security.emergency.subtitle')}
                    </Typography>
                  </Box>
                }
              />

              {backendSettings && (
                <Box
                  sx={{
                    p: 2,
                    borderRadius: 2,
                    border: `1px solid ${theme.palette.divider}`,
                    bgcolor: isDark
                      ? 'rgba(255, 255, 255, 0.03)'
                      : 'rgba(0, 0, 0, 0.02)',
                  }}
                >
                  <Typography variant="subtitle2" sx={{ mb: 0.5 }}>
                    {t('security.backend.title')}
                  </Typography>
                  <Typography variant="caption" color="text.secondary" sx={{ display: 'block', mb: 1.5 }}>
                    {t('security.backend.description')}
                  </Typography>

                  <Box sx={{ mb: 1.5 }}>
                    <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
                      {t('security.backend.hotkey')}
                    </Typography>
                    <TextField
                      fullWidth
                      size="small"
                      value={backendHotkeyInput}
                      onChange={(e) => setBackendHotkeyInput(e.target.value)}
                      placeholder="Ctrl + Alt + L"
                      helperText={t('security.backend.hotkey.helper')}
                    />
                  </Box>

                  <Box>
                    <Typography variant="caption" sx={{ display: 'block', mb: 0.5 }}>
                      {t('security.backend.pattern')}
                    </Typography>
                    <TextField
                      fullWidth
                      size="small"
                      value={backendPatternInput}
                      onChange={(e) => setBackendPatternInput(e.target.value)}
                      placeholder="Up Up Down Down Enter"
                      helperText={t('security.backend.pattern.helper')}
                    />
                  </Box>
                  <Divider sx={{ my: 1.5 }} />

                  <Typography variant="subtitle2" sx={{ mb: 1 }}>
                    {t('security.backend.behavior')}
                  </Typography>

                  <FormControlLabel
                    control={
                      <Switch
                        checked={backendSettings.autoBlockOnStart}
                        onChange={(e) =>
                          setBackendSettings((prev) =>
                            prev ? { ...prev, autoBlockOnStart: e.target.checked } : prev
                          )
                        }
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">{t('security.backend.autoBlock.title')}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t('security.backend.autoBlock.desc')}
                        </Typography>
                      </Box>
                    }
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={backendSettings.showNotifications}
                        onChange={(e) =>
                          setBackendSettings((prev) =>
                            prev ? { ...prev, showNotifications: e.target.checked } : prev
                          )
                        }
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">{t('security.backend.notifications.title')}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t('security.backend.notifications.desc')}
                        </Typography>
                      </Box>
                    }
                  />

                  <FormControlLabel
                    control={
                      <Switch
                        checked={backendSettings.allowTouchscreenUnlock}
                        onChange={(e) =>
                          setBackendSettings((prev) =>
                            prev ? { ...prev, allowTouchscreenUnlock: e.target.checked } : prev
                          )
                        }
                      />
                    }
                    label={
                      <Box>
                        <Typography variant="body2">{t('security.backend.touchscreen.title')}</Typography>
                        <Typography variant="caption" color="text.secondary">
                          {t('security.backend.touchscreen.desc')}
                        </Typography>
                      </Box>
                    }
                  />
                </Box>
              )}

              <Divider sx={{ my: 1 }} />
              
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.security.confirmationTitle')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.requireConfirmation}
                    onChange={(e) => updateSetting('requireConfirmation', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.security.requireConfirmation.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.security.requireConfirmation.desc')}
                    </Typography>
                  </Box>
                }
              />

              <Divider sx={{ my: 1 }} />
              
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.security.shortcutReferenceTitle')}
              </Typography>
              
              <Box sx={{ 
                bgcolor: isDark ? 'rgba(255, 255, 255, 0.03)' : 'rgba(0, 0, 0, 0.03)', 
                borderRadius: 2, 
                p: 2,
                border: `1px solid ${theme.palette.divider}`,
              }}>
                <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1.5 }}>
                  <Typography variant="body2">{t('settings.security.shortcut.toggleLock')}</Typography>
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Chip label="Ctrl" size="small" sx={{ height: 24 }} />
                    <Chip label="Alt" size="small" sx={{ height: 24 }} />
                    <Chip label="L" size="small" sx={{ height: 24 }} />
                  </Box>
                </Box>
                <Box sx={{ display: 'flex', justifyContent: 'space-between' }}>
                  <Typography variant="body2">{t('settings.security.shortcut.emergency')}</Typography>
                  
                  <Box sx={{ display: 'flex', gap: 0.5 }}>
                    <Chip label="↑↑↓↓" size="small" sx={{ height: 24 }} />
                    <Chip label="Enter" size="small" sx={{ height: 24 }} />
                  </Box>
                </Box>
              </Box>
            </Box>
          )}

          {/* Appearance Tab */}
          {settingsTab === 3 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 3 }}>
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.appearance.themeTitle')}
              </Typography>
              
              <FormControl fullWidth size="small">
                <InputLabel>{t('settings.appearance.themeLabel')}</InputLabel>
                <Select
                  value={settings.theme}
                  label={t('settings.appearance.themeLabel')}
                  onChange={(e) => updateSetting('theme', e.target.value as AppSettings['theme'])}
                >
                  <MenuItem value="dark">{t('settings.appearance.theme.dark')}</MenuItem>
                  <MenuItem value="light">{t('settings.appearance.theme.light')}</MenuItem>
                  <MenuItem value="system">{t('settings.appearance.theme.system')}</MenuItem>
                </Select>
              </FormControl>

              <Box>
                <Typography variant="body2" gutterBottom>
                  {t('settings.appearance.accentTitle')}
                </Typography>
                <Box sx={{ display: 'flex', gap: 1.5, flexWrap: 'wrap' }}>
                  {['#2196f3', '#4caf50', '#ff9800', '#f44336', '#9c27b0', '#00bcd4', '#e91e63', '#673ab7'].map((color) => (
                    <Box
                      key={color}
                      onClick={() => updateSetting('accentColor', color)}
                      sx={{
                        width: 36,
                        height: 36,
                        borderRadius: '50%',
                        bgcolor: color,
                        cursor: 'pointer',
                        border: settings.accentColor === color ? `3px solid ${theme.palette.text.primary}` : '3px solid transparent',
                        transition: 'all 0.2s',
                        '&:hover': {
                          transform: 'scale(1.1)',
                        },
                      }}
                    />
                  ))}
                </Box>
              </Box>

              <Divider sx={{ my: 1 }} />
              
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.appearance.layoutTitle')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.compactMode}
                    onChange={(e) => updateSetting('compactMode', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.appearance.compactMode.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.appearance.compactMode.desc')}
                    </Typography>
                  </Box>
                }
              />

              <Divider sx={{ my: 1 }} />
              
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.appearance.advancedTitle')}
              </Typography>
              
              <FormControlLabel
                control={
                  <Switch
                    checked={settings.debugMode}
                    onChange={(e) => updateSetting('debugMode', e.target.checked)}
                  />
                }
                label={
                  <Box>
                    <Typography variant="body2">{t('settings.appearance.debugMode.title')}</Typography>
                    <Typography variant="caption" color="text.secondary">
                      {t('settings.appearance.debugMode.desc')}
                    </Typography>
                  </Box>
                }
              />

              <Divider sx={{ my: 1 }} />

              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600, mb: 1 }}>
                {t('settings.appearance.languageTitle')}
              </Typography>

              <FormControl fullWidth size="small">
                <InputLabel>Language</InputLabel>
                <Select
                  value={settings.language}
                  label="Language"
                  onChange={(e) => updateSetting('language', e.target.value as AppSettings['language'])}
                >
                  <MenuItem value="en">English</MenuItem>
                  <MenuItem value="es">Español</MenuItem>
                </Select>
              </FormControl>
            </Box>
          )}

          {/* Diagnostics Tab */}
          {settingsTab === 4 && (
            <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
              <Typography variant="subtitle2" color="primary" sx={{ fontWeight: 600 }}>
                {t('diagnostics.summaryTitle')}
              </Typography>
              <Box
                component="pre"
                sx={{
                  p: 2,
                  borderRadius: 2,
                  border: `1px solid ${cardBorder}`,
                  bgcolor: isDark
                    ? 'rgba(15, 23, 42, 0.9)'
                    : 'rgba(248, 250, 252, 0.95)',
                  fontFamily: 'Monospace, monospace',
                  fontSize: '0.75rem',
                  maxHeight: 260,
                  overflow: 'auto',
                }}
              >
                {(() => {
                  const lines: string[] = [];
                  const hotkey = backendSettings?.hotkey || [];
                  const pattern = backendSettings?.emergencyPattern || [];
                  lines.push(`Input Locker Diagnostics - ${new Date().toISOString()}`);
                  lines.push('');
                  lines.push('[System]');
                  lines.push(`API running: ${systemStatus.running ? 'yes' : 'no'}`);
                  lines.push(`Uptime (s): ${systemStatus.uptime}`);
                  lines.push(`Connected devices (reported): ${systemStatus.connectedDevices}`);
                  lines.push('');
                  lines.push('[Devices]');
                  lines.push(`Total devices: ${devices.length}`);
                  const blocked = devices.filter((d) => d.blocked).length;
                  lines.push(`Blocked devices: ${blocked}`);
                  devices.slice(0, 20).forEach((d) => {
                    lines.push(`- ${d.type} | ${d.name || d.path} | ${d.blocked ? 'blocked' : 'allowed'}`);
                  });
                  if (devices.length > 20) {
                    lines.push(`... and ${devices.length - 20} more`);
                  }
                  lines.push('');
                  lines.push('[Statistics]');
                  lines.push(`Total blocked time (s): ${statistics.totalBlockedTime}`);
                  lines.push(`Blocked events: ${statistics.blockedEvents}`);
                  lines.push('');
                  lines.push('[Backend settings]');
                  if (backendSettings) {
                    lines.push(
                      `Hotkey: ${hotkey.length > 0 ? hotkey.join(' + ') : 'n/a'}`
                    );
                    lines.push(
                      `Emergency pattern: ${pattern.length > 0 ? pattern.join(' ') : 'n/a'}`
                    );
                    lines.push(`Auto block on start: ${backendSettings.autoBlockOnStart}`);
                    lines.push(`Show notifications: ${backendSettings.showNotifications}`);
                    lines.push(`Allow touchscreen unlock: ${backendSettings.allowTouchscreenUnlock}`);
                    lines.push(`Theme: ${backendSettings.theme}`);
                  } else {
                    lines.push('Not loaded');
                  }
                  return lines.join('\n');
                })()}
              </Box>
              <Box sx={{ display: 'flex', justifyContent: 'flex-end' }}>
                <Button
                  variant="outlined"
                  size="small"
                  onClick={async () => {
                    const text = (() => {
                      const lines: string[] = [];
                      const hotkey = backendSettings?.hotkey || [];
                      const pattern = backendSettings?.emergencyPattern || [];
                      lines.push(`Input Locker Diagnostics - ${new Date().toISOString()}`);
                      lines.push('');
                      lines.push('[System]');
                      lines.push(`API running: ${systemStatus.running ? 'yes' : 'no'}`);
                      lines.push(`Uptime (s): ${systemStatus.uptime}`);
                      lines.push(`Connected devices (reported): ${systemStatus.connectedDevices}`);
                      lines.push('');
                      lines.push('[Devices]');
                      lines.push(`Total devices: ${devices.length}`);
                      const blocked = devices.filter((d) => d.blocked).length;
                      lines.push(`Blocked devices: ${blocked}`);
                      devices.slice(0, 50).forEach((d) => {
                        lines.push(`- ${d.type} | ${d.name || d.path} | ${d.blocked ? 'blocked' : 'allowed'}`);
                      });
                      if (devices.length > 50) {
                        lines.push(`... and ${devices.length - 50} more`);
                      }
                      lines.push('');
                      lines.push('[Statistics]');
                      lines.push(`Total blocked time (s): ${statistics.totalBlockedTime}`);
                      lines.push(`Blocked events: ${statistics.blockedEvents}`);
                      lines.push('');
                      lines.push('[Backend settings]');
                      if (backendSettings) {
                        lines.push(
                          `Hotkey: ${hotkey.length > 0 ? hotkey.join(' + ') : 'n/a'}`
                        );
                        lines.push(
                          `Emergency pattern: ${pattern.length > 0 ? pattern.join(' ') : 'n/a'}`
                        );
                        lines.push(`Auto block on start: ${backendSettings.autoBlockOnStart}`);
                        lines.push(`Show notifications: ${backendSettings.showNotifications}`);
                        lines.push(`Allow touchscreen unlock: ${backendSettings.allowTouchscreenUnlock}`);
                        lines.push(`Theme: ${backendSettings.theme}`);
                      } else {
                        lines.push('Not loaded');
                      }
                      return lines.join('\n');
                    })();

                    try {
                      await navigator.clipboard.writeText(text);
                      setSnackbar({
                        open: true,
                        message: t('diagnostics.copied'),
                        severity: 'success',
                      });
                    } catch (error) {
                      console.error('Failed to copy diagnostics:', error);
                      setSnackbar({
                        open: true,
                        message: t('diagnostics.copyError'),
                        severity: 'error',
                      });
                    }
                  }}
                >
                  {t('diagnostics.copy')}
                </Button>
              </Box>
            </Box>
          )}
        </DialogContent>

        <DialogActions sx={{ 
          borderTop: `1px solid ${cardBorder}`, 
          p: 2,
          justifyContent: 'space-between',
        }}>
          <Button 
            startIcon={<ResetIcon />}
            onClick={() => {
              resetSettings();
              addActivity('Settings reset to defaults', undefined, 'system');
              setSnackbar({
                open: true,
                message: t('settings.actions.reset'),
                severity: 'info',
              });
            }}
            color="inherit"
          >
            {t('settings.actions.reset')}
          </Button>
          <Box sx={{ display: 'flex', gap: 1 }}>
            <Button onClick={() => setSettingsOpen(false)}>{t('settings.actions.cancel')}</Button>
            <Button 
              variant="contained" 
              disabled={backendSaving}
              onClick={async () => {
                // Persist backend settings (hotkey & emergency pattern) if changed
                if (backendSettings) {
                  const parseCombo = (raw: string): string[] => {
                    return raw
                      .split(/[+\s]+/)
                      .map((p) => p.trim())
                      .filter((p) => p.length > 0);
                  };

                  const payload: Partial<Settings> = {};
                  const hotkeyTokens = parseCombo(backendHotkeyInput);
                  const patternTokens = backendPatternInput
                    .split(/\s+/)
                    .map((p) => p.trim())
                    .filter((p) => p.length > 0);

                  if (hotkeyTokens.length > 0) {
                    payload.hotkey = hotkeyTokens;
                  }
                  if (patternTokens.length > 0) {
                    payload.emergencyPattern = patternTokens;
                  }

                  // Always send current backend flags so they are persisted
                  payload.autoBlockOnStart = backendSettings.autoBlockOnStart;
                  payload.showNotifications = backendSettings.showNotifications;
                  payload.allowTouchscreenUnlock = backendSettings.allowTouchscreenUnlock;

                  if (Object.keys(payload).length > 0) {
                    try {
                      setBackendSaving(true);
                      const updated = await api.updateSettings(payload);
                      setBackendSettings(updated);
                      setBackendHotkeyInput((updated.hotkey || []).join(' + '));
                      setBackendPatternInput((updated.emergencyPattern || []).join(' '));
                    } catch (error) {
                      console.error('Failed to update backend settings:', error);
                      setSnackbar({
                        open: true,
                        message: t('settings.actions.backendSaveError'),
                        severity: 'error',
                      });
                      setBackendSaving(false);
                      return;
                    }
                    setBackendSaving(false);
                  }
                }

                setSettingsOpen(false);
                addActivity('Settings saved', undefined, 'system');
                setSnackbar({
                  open: true,
                  message: t('settings.actions.saveSuccess'),
                  severity: 'success',
                });
              }}
            >
              {t('settings.actions.save')}
            </Button>
          </Box>
        </DialogActions>
      </Dialog>

      {/* Snackbar */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={4000}
        onClose={() => setSnackbar(s => ({ ...s, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          onClose={() => setSnackbar(s => ({ ...s, open: false }))}
          severity={snackbar.severity}
          variant="filled"
          sx={{ width: '100%' }}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>
    </Box>
  );
};

export default Dashboard;
