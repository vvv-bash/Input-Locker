import React from 'react';
import { 
  Card, 
  CardContent, 
  Box, 
  Typography, 
  Switch, 
  Chip,
  alpha,
} from '@mui/material';
import { 
  Keyboard as KeyboardIcon,
  Mouse as MouseIcon,
  TouchApp as TouchpadIcon,
  Smartphone as TouchscreenIcon,
  DeviceUnknown as OtherIcon,
  Lock as LockIcon,
  LockOpen as UnlockIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import type { Device, DeviceType } from '../../types';
import { colors } from '../../theme';
import { useI18n } from '../../i18n';

interface DeviceCardProps {
  device: Device;
  onToggle: (devicePath: string) => void;
  isLoading?: boolean;
}

const deviceIcons: Record<DeviceType, React.ReactElement> = {
  keyboard: <KeyboardIcon sx={{ fontSize: 28 }} />,
  mouse: <MouseIcon sx={{ fontSize: 28 }} />,
  touchpad: <TouchpadIcon sx={{ fontSize: 28 }} />,
  touchscreen: <TouchscreenIcon sx={{ fontSize: 28 }} />,
  other: <OtherIcon sx={{ fontSize: 28 }} />,
};

const deviceColors: Record<DeviceType, string> = {
  keyboard: colors.primary.main,
  mouse: colors.secondary.main,
  touchpad: colors.accent.purple,
  touchscreen: colors.accent.green,
  other: colors.accent.orange,
};

export const DeviceCard: React.FC<DeviceCardProps> = ({ 
  device, 
  onToggle, 
  isLoading = false 
}) => {
  const { t } = useI18n();
  const Icon = deviceIcons[device.type] || deviceIcons.other;
  const accentColor = deviceColors[device.type] || deviceColors.other;

  const handleToggle = () => {
    if (!isLoading) {
      onToggle(device.path);
    }
  };

  return (
    <motion.div
      initial={{ opacity: 0, y: 20 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      whileHover={{ scale: 1.02 }}
    >
      <Card
        sx={{
          position: 'relative',
          overflow: 'hidden',
          minWidth: 200,
          '&::before': {
            content: '""',
            position: 'absolute',
            top: 0,
            left: 0,
            right: 0,
            height: 3,
            background: device.blocked 
              ? `linear-gradient(90deg, ${colors.accent.red} 0%, ${colors.accent.orange} 100%)`
              : `linear-gradient(90deg, ${accentColor} 0%, ${colors.secondary.main} 100%)`,
          },
        }}
      >
        <CardContent sx={{ p: 1.5 }}>
          {/* Header with icon and status */}
          <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 1 }}>
            <Box
              sx={{
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                width: 40,
                height: 40,
                borderRadius: 2,
                background: alpha(accentColor, 0.15),
                color: accentColor,
              }}
            >
              {Icon}
            </Box>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Chip
                icon={device.blocked ? <LockIcon /> : <UnlockIcon />}
                label={device.blocked ? t('device.status.blocked') : t('device.status.active')}
                size="small"
                color={device.blocked ? 'error' : 'success'}
                sx={{
                  fontWeight: 600,
                  height: 24,
                  '& .MuiChip-label': { px: 1, fontSize: '0.7rem' },
                  '& .MuiChip-icon': {
                    fontSize: 14,
                  },
                }}
              />
            </Box>
          </Box>

          {/* Device name and type */}
          <Typography variant="subtitle2" sx={{ mb: 0.25, fontWeight: 600, fontSize: '0.85rem' }} noWrap>
            {device.name}
          </Typography>
          <Typography 
            variant="caption" 
            sx={{ 
              color: 'text.secondary', 
              mb: 1,
              textTransform: 'capitalize',
              display: 'block',
            }}
          >
            {device.type}
          </Typography>

          {/* Toggle switch */}
          <Box 
            sx={{ 
              display: 'flex', 
              alignItems: 'center', 
              justifyContent: 'space-between',
              pt: 1,
              borderTop: `1px solid ${colors.border.light}`,
            }}
          >
            <Typography variant="caption" sx={{ color: 'text.secondary', fontSize: '0.7rem' }}>
              {device.blocked ? t('device.action.unblock') : t('device.action.block')}
            </Typography>
            <Switch
              checked={device.blocked}
              onChange={handleToggle}
              disabled={isLoading}
              size="small"
              sx={{
                '& .MuiSwitch-thumb': {
                  backgroundColor: device.blocked ? colors.accent.red : colors.accent.green,
                },
                '& .MuiSwitch-track': {
                  backgroundColor: device.blocked 
                    ? alpha(colors.accent.red, 0.3) 
                    : alpha(colors.accent.green, 0.3),
                },
              }}
            />
          </Box>
        </CardContent>
      </Card>
    </motion.div>
  );
};

export default DeviceCard;
