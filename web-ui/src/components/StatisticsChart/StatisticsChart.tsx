import React from 'react';
import { 
  Box, 
  Card, 
  CardContent, 
  Typography, 
  Grid,
} from '@mui/material';
import { 
  Timeline as TimelineIcon,
  Block as BlockIcon,
  AccessTime as TimeIcon,
} from '@mui/icons-material';
import { 
  PieChart, 
  Pie, 
  Cell, 
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
} from 'recharts';
import { motion } from 'framer-motion';
import { colors } from '../../theme';
import type { Statistics } from '../../types';
import { useI18n } from '../../i18n';

interface StatisticsChartProps {
  statistics: Statistics;
}

const CHART_COLORS = [
  colors.primary.main,
  colors.secondary.main,
  colors.accent.purple,
  colors.accent.green,
  colors.accent.orange,
];

export const StatisticsChart: React.FC<StatisticsChartProps> = ({ statistics }) => {
  const { t } = useI18n();
  const formatTime = (seconds: number): string => {
    const hours = Math.floor(seconds / 3600);
    const minutes = Math.floor((seconds % 3600) / 60);
    if (hours > 0) {
      return `${hours}h ${minutes}m`;
    }
    return `${minutes}m`;
  };

  // Prepare data for pie chart
  const pieData = statistics.deviceStats.map((stat, index) => ({
    name: stat.deviceName.split(' ')[0], // Shorten name
    value: stat.totalBlockedTime,
    color: CHART_COLORS[index % CHART_COLORS.length],
  }));

  // Prepare data for area chart (last 7 events)
  const areaData = statistics.blockHistory
    .slice(-10)
    .map((event, index) => ({
      time: new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
      events: index + 1,
      duration: event.duration || 0,
    }));

  return (
    <Grid container spacing={3}>
      {/* Stats Cards */}
      <Grid item xs={12}>
        <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap' }}>
          {/* Total Blocked Time */}
          <motion.div style={{ flex: 1, minWidth: 200 }} whileHover={{ scale: 1.02 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <TimeIcon sx={{ fontSize: 40, color: colors.primary.main, mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {formatTime(statistics.totalBlockedTime)}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {t('stats.totalBlockedTime')}
                </Typography>
              </CardContent>
            </Card>
          </motion.div>

          {/* Blocked Events */}
          <motion.div style={{ flex: 1, minWidth: 200 }} whileHover={{ scale: 1.02 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <BlockIcon sx={{ fontSize: 40, color: colors.accent.red, mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {statistics.blockedEvents.toLocaleString()}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {t('stats.blockedEvents')}
                </Typography>
              </CardContent>
            </Card>
          </motion.div>

          {/* Session Count */}
          <motion.div style={{ flex: 1, minWidth: 200 }} whileHover={{ scale: 1.02 }}>
            <Card sx={{ height: '100%' }}>
              <CardContent sx={{ textAlign: 'center', py: 3 }}>
                <TimelineIcon sx={{ fontSize: 40, color: colors.accent.purple, mb: 1 }} />
                <Typography variant="h4" sx={{ fontWeight: 700, mb: 0.5 }}>
                  {statistics.blockHistory.length}
                </Typography>
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {t('stats.blockSessions')}
                </Typography>
              </CardContent>
            </Card>
          </motion.div>
        </Box>
      </Grid>

      {/* Pie Chart - Device Distribution */}
      <Grid item xs={12} md={5}>
        <Card sx={{ height: 320 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  {t('stats.timeByDevice')}
            </Typography>
            {pieData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <PieChart>
                  <Pie
                    data={pieData}
                    cx="50%"
                    cy="50%"
                    innerRadius={60}
                    outerRadius={90}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip
                    contentStyle={{
                      backgroundColor: colors.background.elevated,
                      border: `1px solid ${colors.border.light}`,
                      borderRadius: 8,
                    }}
                    formatter={(value: number) => formatTime(value)}
                  />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <Box 
                sx={{ 
                  height: 240, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center' 
                }}
              >
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {t('stats.noData')}
                </Typography>
              </Box>
            )}
            {/* Legend */}
            <Box sx={{ display: 'flex', gap: 2, flexWrap: 'wrap', justifyContent: 'center' }}>
              {pieData.map((entry, index) => (
                <Box key={index} sx={{ display: 'flex', alignItems: 'center', gap: 0.5 }}>
                  <Box 
                    sx={{ 
                      width: 10, 
                      height: 10, 
                      borderRadius: '50%', 
                      bgcolor: entry.color 
                    }} 
                  />
                  <Typography variant="caption">{entry.name}</Typography>
                </Box>
              ))}
            </Box>
          </CardContent>
        </Card>
      </Grid>

      {/* Area Chart - Activity Timeline */}
      <Grid item xs={12} md={7}>
        <Card sx={{ height: 320 }}>
          <CardContent>
            <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
                  {t('stats.activityTimeline')}
            </Typography>
            {areaData.length > 0 ? (
              <ResponsiveContainer width="100%" height={240}>
                <AreaChart data={areaData}>
                  <defs>
                    <linearGradient id="colorEvents" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="5%" stopColor={colors.primary.main} stopOpacity={0.8} />
                      <stop offset="95%" stopColor={colors.primary.main} stopOpacity={0} />
                    </linearGradient>
                  </defs>
                  <CartesianGrid strokeDasharray="3 3" stroke={colors.border.light} />
                  <XAxis 
                    dataKey="time" 
                    stroke={colors.text.secondary}
                    fontSize={12}
                  />
                  <YAxis 
                    stroke={colors.text.secondary}
                    fontSize={12}
                  />
                  <Tooltip
                    contentStyle={{
                      backgroundColor: colors.background.elevated,
                      border: `1px solid ${colors.border.light}`,
                      borderRadius: 8,
                    }}
                  />
                  <Area
                    type="monotone"
                    dataKey="events"
                    stroke={colors.primary.main}
                    fillOpacity={1}
                    fill="url(#colorEvents)"
                    strokeWidth={2}
                  />
                </AreaChart>
              </ResponsiveContainer>
            ) : (
              <Box 
                sx={{ 
                  height: 240, 
                  display: 'flex', 
                  alignItems: 'center', 
                  justifyContent: 'center' 
                }}
              >
                <Typography variant="body2" sx={{ color: 'text.secondary' }}>
                  {t('stats.noActivity')}
                </Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );
};

export default StatisticsChart;
