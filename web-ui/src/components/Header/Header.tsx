import React from 'react';
import { Box, Typography, IconButton, Tooltip, alpha, useTheme } from '@mui/material';
import { 
  Settings as SettingsIcon, 
  Refresh as RefreshIcon,
  Lock as LockIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { useI18n } from '../../i18n';

interface HeaderProps {
  onSettingsClick: () => void;
  onRefreshClick: () => void;
}

export const Header: React.FC<HeaderProps> = ({ onSettingsClick, onRefreshClick }) => {
  const theme = useTheme();
  const isDark = theme.palette.mode === 'dark';
  const { t } = useI18n();
  
  return (
    <Box
      component="header"
      sx={{
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        py: 2,
        px: 3,
        borderBottom: `1px solid ${isDark ? 'rgba(255,255,255,0.1)' : 'rgba(0,0,0,0.1)'}`,
        background: alpha(theme.palette.background.paper, isDark ? 0.8 : 0.95),
        backdropFilter: 'blur(20px)',
        position: 'sticky',
        top: 0,
        zIndex: 100,
      }}
    >
      {/* Logo and Title */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
        <motion.div
          animate={{ rotate: [0, 10, -10, 0] }}
          transition={{ duration: 2, repeat: Infinity, repeatDelay: 3 }}
        >
          <Box
            sx={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              width: 48,
              height: 48,
              borderRadius: 2,
              background: `linear-gradient(135deg, ${theme.palette.primary.main} 0%, #a855f7 100%)`,
              boxShadow: `0 4px 20px ${alpha(theme.palette.primary.main, 0.4)}`,
            }}
          >
            <LockIcon sx={{ fontSize: 28, color: '#fff' }} />
          </Box>
        </motion.div>

        <Box>
          <Typography variant="h5" sx={{ fontWeight: 700, letterSpacing: '-0.02em' }}>
            {t('header.title')}
          </Typography>
          <Typography variant="caption" sx={{ color: 'text.secondary' }}>
            {t('header.subtitle')}
          </Typography>
        </Box>
      </Box>

      {/* Actions */}
      <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
        <Tooltip title={t('header.refresh')}>
          <IconButton 
            onClick={onRefreshClick}
            sx={{ 
              color: 'text.secondary',
              '&:hover': { color: theme.palette.primary.main },
            }}
          >
            <RefreshIcon />
          </IconButton>
        </Tooltip>

        <Tooltip title={t('header.settings')}>
          <IconButton 
            onClick={onSettingsClick}
            sx={{ 
              color: 'text.secondary',
              '&:hover': { color: theme.palette.primary.main },
            }}
          >
            <SettingsIcon />
          </IconButton>
        </Tooltip>
      </Box>
    </Box>
  );
};

export default Header;
