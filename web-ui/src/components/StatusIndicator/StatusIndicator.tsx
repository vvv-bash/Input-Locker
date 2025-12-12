import React from 'react';
import { Box, Typography, Chip, alpha } from '@mui/material';
import { 
  CheckCircle as OnlineIcon, 
  Error as OfflineIcon,
  Devices as DevicesIcon,
  Block as BlockIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { colors } from '../../theme';
import { useI18n } from '../../i18n';

interface StatusIndicatorProps {
  isRunning: boolean;
  activeBlocks: number;
  connectedDevices: number;
  uptime: number;
}

export const StatusIndicator: React.FC<StatusIndicatorProps> = ({
  isRunning,
  activeBlocks,
  connectedDevices,
  uptime,
}) => {
  const { t } = useI18n();
  const formatUptime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  return (
    <Box
      sx={{
        display: 'flex',
        alignItems: 'center',
        gap: 3,
        p: 2,
        borderRadius: 2,
        background: alpha(colors.background.paper, 0.5),
        backdropFilter: 'blur(10px)',
        border: `1px solid ${colors.border.light}`,
      }}
    >
      {/* System Status */}
      <motion.div
        animate={{ scale: isRunning ? [1, 1.1, 1] : 1 }}
        transition={{ duration: 2, repeat: Infinity }}
      >
        <Chip
          icon={isRunning ? <OnlineIcon /> : <OfflineIcon />}
          label={isRunning ? t('status.systemActive') : t('status.systemOffline')}
          color={isRunning ? 'success' : 'error'}
          variant="filled"
          sx={{
            fontWeight: 600,
            px: 1,
            '& .MuiChip-icon': {
              fontSize: 18,
            },
          }}
        />
      </motion.div>

      {/* Divider */}
      <Box sx={{ width: 1, height: 32, bgcolor: colors.border.light }} />

      {/* Stats */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <DevicesIcon sx={{ fontSize: 18, color: colors.primary.main }} />
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          <strong>{connectedDevices}</strong> {t('status.devicesLabel')}
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <BlockIcon sx={{ fontSize: 18, color: activeBlocks > 0 ? colors.accent.red : colors.text.disabled }} />
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          <strong>{activeBlocks}</strong> {t('status.blockedLabel')}
        </Typography>
      </Box>

      <Box sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
        <Typography variant="body2" sx={{ color: 'text.secondary' }}>
          {t('status.uptimeLabel')}: <strong>{formatUptime(uptime)}</strong>
        </Typography>
      </Box>
    </Box>
  );
};

export default StatusIndicator;
