import React, { useState, useEffect } from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  CircularProgress,
  Button,
  TextField,
  alpha,
} from '@mui/material';
import { 
  Timer as TimerIcon,
  PlayArrow as PlayIcon,
  Stop as StopIcon,
} from '@mui/icons-material';
import { motion } from 'framer-motion';
import { colors } from '../../theme';
import type { Timer } from '../../types';
import { useI18n } from '../../i18n';

interface BlockTimerProps {
  timer: Timer;
  onSetTimer: (minutes: number) => void;
  onCancelTimer: () => void;
  isLoading?: boolean;
}

export const BlockTimer: React.FC<BlockTimerProps> = ({
  timer,
  onSetTimer,
  onCancelTimer,
  isLoading = false,
}) => {
  const [inputMinutes, setInputMinutes] = useState<string>('5');
  const [displayTime, setDisplayTime] = useState<string>('00:00');
  const { t } = useI18n();

  useEffect(() => {
    if (timer.active && timer.remainingSeconds > 0) {
      const minutes = Math.floor(timer.remainingSeconds / 60);
      const seconds = timer.remainingSeconds % 60;
      setDisplayTime(`${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`);
    } else {
      setDisplayTime('00:00');
    }
  }, [timer]);

  const progress = timer.active && timer.totalSeconds > 0
    ? (timer.remainingSeconds / timer.totalSeconds) * 100
    : 0;

  const handleStart = () => {
    const minutes = parseInt(inputMinutes, 10);
    if (minutes > 0 && minutes <= 480) { // Max 8 hours
      onSetTimer(minutes);
    }
  };

  return (
    <Card sx={{ height: '100%' }}>
      <CardContent sx={{ p: 3, textAlign: 'center' }}>
        <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 1, mb: 3 }}>
          <TimerIcon sx={{ color: colors.primary.main }} />
          <Typography variant="h6" sx={{ fontWeight: 600 }}>
            {t('timer.title')}
          </Typography>
        </Box>

        {/* Circular Progress Timer */}
        <Box sx={{ position: 'relative', display: 'inline-flex', mb: 3 }}>
          <CircularProgress
            variant="determinate"
            value={100}
            size={160}
            thickness={4}
            sx={{
              color: alpha(colors.primary.main, 0.1),
            }}
          />
          <CircularProgress
            variant="determinate"
            value={progress}
            size={160}
            thickness={4}
            sx={{
              color: timer.active ? colors.accent.orange : colors.primary.main,
              position: 'absolute',
              left: 0,
              '& .MuiCircularProgress-circle': {
                transition: 'stroke-dashoffset 0.5s ease-in-out',
              },
            }}
          />
          <Box
            sx={{
              top: 0,
              left: 0,
              bottom: 0,
              right: 0,
              position: 'absolute',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              flexDirection: 'column',
            }}
          >
            <motion.div
              animate={timer.active ? { scale: [1, 1.05, 1] } : {}}
              transition={{ duration: 1, repeat: Infinity }}
            >
              <Typography variant="h3" sx={{ fontWeight: 700, fontFamily: 'monospace' }}>
                {displayTime}
              </Typography>
            </motion.div>
            <Typography variant="caption" sx={{ color: 'text.secondary' }}>
              {timer.active ? t('timer.remaining') : t('timer.inactive')}
            </Typography>
          </Box>
        </Box>

        {/* Controls */}
        {!timer.active ? (
          <Box sx={{ display: 'flex', gap: 2, justifyContent: 'center', alignItems: 'center' }}>
            <TextField
              type="number"
              value={inputMinutes}
              onChange={(e) => setInputMinutes(e.target.value)}
              size="small"
              label={t('timer.minutesLabel')}
              inputProps={{ min: 1, max: 480 }}
              sx={{ width: 100 }}
            />
            <Button
              variant="contained"
              startIcon={<PlayIcon />}
              onClick={handleStart}
              disabled={isLoading}
              sx={{ px: 3 }}
            >
              {t('timer.start')}
            </Button>
          </Box>
        ) : (
          <Button
            variant="contained"
            color="error"
            startIcon={<StopIcon />}
            onClick={onCancelTimer}
            disabled={isLoading}
            sx={{ px: 3 }}
          >
            {t('timer.cancel')}
          </Button>
        )}

        {/* Quick presets */}
        {!timer.active && (
          <Box sx={{ mt: 2, display: 'flex', gap: 1, justifyContent: 'center', flexWrap: 'wrap' }}>
            {[5, 15, 30, 60].map((mins) => (
              <Button
                key={mins}
                size="small"
                variant="outlined"
                onClick={() => {
                  setInputMinutes(mins.toString());
                  onSetTimer(mins);
                }}
                disabled={isLoading}
                sx={{ minWidth: 'auto', px: 2 }}
              >
                {mins}m
              </Button>
            ))}
          </Box>
        )}
      </CardContent>
    </Card>
  );
};

export default BlockTimer;
