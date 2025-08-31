import React, { useEffect, useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  ToggleButton,
  ToggleButtonGroup,
  IconButton,
  Tooltip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  LinearProgress,
  Avatar,
  Divider
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  Refresh as RefreshIcon,
  Download as DownloadIcon,
  CalendarToday as CalendarIcon,
  Analytics as AnalyticsIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  FileCopy as FileIcon,
  PictureAsPdf as PdfIcon,
  Image as ImageIcon,
  TableChart as TableIcon,
  Archive as ArchiveIcon
} from '@mui/icons-material';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip as RechartsTooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  BarChart,
  Bar,
  AreaChart,
  Area
} from 'recharts';

interface StatisticsData {
  timeRange: string;
  totalFiles: number;
  processedFiles: number;
  failedFiles: number;
  averageProcessingTime: number;
  storageUsed: number;
  storageTotal: number;
  processingRate: number;
  successRate: number;
  fileTypeDistribution: Array<{
    type: string;
    count: number;
    percentage: number;
    color: string;
  }>;
  processingTrend: Array<{
    date: string;
    processed: number;
    failed: number;
    rate: number;
  }>;
  hourlyActivity: Array<{
    hour: string;
    files: number;
    processingTime: number;
  }>;
  topKeywords: Array<{
    keyword: string;
    count: number;
    successRate: number;
  }>;
  performanceMetrics: Array<{
    metric: string;
    value: number;
    unit: string;
    trend: 'up' | 'down' | 'stable';
    change: number;
  }>;
}

const Statistics: React.FC = () => {
  const [timeRange, setTimeRange] = useState('7d');
  const [selectedMetric, setSelectedMetric] = useState('processing');

  const [stats, setStats] = useState<StatisticsData | null>(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    const load = async () => {
      try {
        setLoading(true);
        const token = localStorage.getItem('token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
        const ingest = await fetch('/api/ingest/processing/stats', { headers });
        const s = ingest.ok ? await ingest.json() : {};
        setStats({
          timeRange,
          totalFiles: (s.total_files_processed || 0) + (s.failed_files || 0),
          processedFiles: s.successful_files || 0,
          failedFiles: s.failed_files || 0,
          averageProcessingTime: 0,
          storageUsed: 0,
          storageTotal: 0,
          processingRate: 0,
          successRate: s.total_files_processed ? Math.round((s.successful_files || 0) / (s.total_files_processed) * 1000) / 10 : 0,
          fileTypeDistribution: [],
          processingTrend: [],
          hourlyActivity: [],
          topKeywords: [],
          performanceMetrics: []
        });
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [timeRange]);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const formatPercentage = (value: number, total: number): string => {
    return total > 0 ? `${((value / total) * 100).toFixed(1)}%` : '0%';
  };

  const getTrendIcon = (trend: string) => {
    switch (trend) {
      case 'up':
        return <TrendingUpIcon color="success" />;
      case 'down':
        return <TrendingDownIcon color="error" />;
      default:
        return <TrendingUpIcon color="disabled" />;
    }
  };

  const getTrendColor = (trend: string) => {
    switch (trend) {
      case 'up':
        return 'success.main';
      case 'down':
        return 'error.main';
      default:
        return 'text.secondary';
    }
  };

  const getFileTypeIcon = (type: string) => {
    switch (type.toLowerCase()) {
      case 'pdf':
        return <PdfIcon />;
      case 'dokumente':
        return <FileIcon />;
      case 'bilder':
        return <ImageIcon />;
      case 'tabellen':
        return <TableIcon />;
      case 'archive':
        return <ArchiveIcon />;
      default:
        return <FileIcon />;
    }
  };

  const handleExport = () => {
    // Simulate export functionality
    console.log('Exporting statistics...');
  };

  const handleRefresh = () => {
    // Simulate data refresh
    console.log('Refreshing statistics...');
  };

  const storagePercentage = stats ? (stats.storageTotal > 0 ? (stats.storageUsed / stats.storageTotal) * 100 : 0) : 0;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Statistiken
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Detaillierte Analysen und Performance-Metriken
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<CalendarIcon />}
            onClick={() => setTimeRange('7d')}
          >
            {timeRange === '7d' ? '7 Tage' : 'Zeitraum'}
          </Button>
          <Button
            variant="outlined"
            startIcon={<DownloadIcon />}
            onClick={handleExport}
          >
            Export
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={handleRefresh}
          >
            Aktualisieren
          </Button>
        </Box>
      </Box>

      {/* Time Range Selector */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box display="flex" alignItems="center" gap={2}>
            <Typography variant="subtitle1" fontWeight="bold">
              Zeitraum:
            </Typography>
            <ToggleButtonGroup
              value={timeRange}
              exclusive
              onChange={(_, value) => value && setTimeRange(value)}
              size="small"
            >
              <ToggleButton value="1d">1 Tag</ToggleButton>
              <ToggleButton value="7d">7 Tage</ToggleButton>
              <ToggleButton value="30d">30 Tage</ToggleButton>
              <ToggleButton value="90d">90 Tage</ToggleButton>
            </ToggleButtonGroup>
          </Box>
        </CardContent>
      </Card>

      {/* Key Metrics */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Gesamt Dateien
                  </Typography>
                  <Typography variant="h4" component="div">
                    {stats ? stats.totalFiles.toLocaleString() : 0}
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    {getTrendIcon('up')}
                    <Typography variant="body2" color="success.main" ml={0.5}>
                      +12% vs. letzter Zeitraum
                    </Typography>
                  </Box>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <FileIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Erfolgsrate
                  </Typography>
                  <Typography variant="h4" component="div" color="success.main">
                    {stats ? stats.successRate : 0}%
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    {getTrendIcon('up')}
                    <Typography variant="body2" color="success.main" ml={0.5}>
                      +2.1% vs. letzter Zeitraum
                    </Typography>
                  </Box>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <CheckCircleIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Verarbeitungsrate
                  </Typography>
                  <Typography variant="h4" component="div" color="primary.main">
                    {stats ? stats.processingRate : 0}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" mt={1}>
                    Dateien pro Minute
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <SpeedIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Speicherverbrauch
                  </Typography>
                  <Typography variant="h4" component="div" color="warning.main">
                    {stats ? formatBytes(stats.storageUsed) : '0 B'}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" mt={1}>
                    {stats ? formatPercentage(stats.storageUsed, stats.storageTotal) : '0%'} von {stats ? formatBytes(stats.storageTotal) : '0 B'}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <StorageIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Charts */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={8}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Verarbeitungstrend ({timeRange})
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <AreaChart data={stats ? stats.processingTrend : []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="date" />
                  <YAxis />
                  <RechartsTooltip />
                  <Area 
                    type="monotone" 
                    dataKey="processed" 
                    stackId="1"
                    stroke="#8884d8" 
                    fill="#8884d8" 
                    fillOpacity={0.6}
                  />
                  <Area 
                    type="monotone" 
                    dataKey="failed" 
                    stackId="1"
                    stroke="#ff7300" 
                    fill="#ff7300" 
                    fillOpacity={0.6}
                  />
                </AreaChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Dateitypen Verteilung
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={stats ? stats.fileTypeDistribution : []}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ type, percentage }) => `${type} ${percentage}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="count"
                  >
                    {(stats ? stats.fileTypeDistribution : []).map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <RechartsTooltip />
                </PieChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Performance Metrics */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Performance Metriken
              </Typography>
              <Grid container spacing={2}>
                {(stats ? stats.performanceMetrics : []).map((metric, index) => (
                  <Grid item xs={12} sm={6} md={3} key={index}>
                    <Box display="flex" alignItems="center" justifyContent="space-between" p={2} border={1} borderColor="divider" borderRadius={1}>
                      <Box>
                        <Typography variant="body2" color="textSecondary">
                          {metric.metric}
                        </Typography>
                        <Typography variant="h6" fontWeight="bold">
                          {metric.value} {metric.unit}
                        </Typography>
                        <Box display="flex" alignItems="center" mt={0.5}>
                          {getTrendIcon(metric.trend)}
                          <Typography 
                            variant="caption" 
                            color={getTrendColor(metric.trend)}
                            ml={0.5}
                          >
                            {metric.change > 0 ? '+' : ''}{metric.change}%
                          </Typography>
                        </Box>
                      </Box>
                    </Box>
                  </Grid>
                ))}
              </Grid>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Detailed Tables */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Top Schlüsselwörter
              </Typography>
              <TableContainer>
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Schlüsselwort</TableCell>
                      <TableCell align="right">Anzahl</TableCell>
                      <TableCell align="right">Erfolgsrate</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {(stats ? stats.topKeywords : []).map((keyword, index) => (
                      <TableRow key={index}>
                        <TableCell>
                          <Box display="flex" alignItems="center" gap={1}>
                            <Typography variant="body2" fontWeight="medium">
                              {keyword.keyword}
                            </Typography>
                          </Box>
                        </TableCell>
                        <TableCell align="right">
                          <Chip label={keyword.count} size="small" />
                        </TableCell>
                        <TableCell align="right">
                          <Typography 
                            variant="body2" 
                            color={keyword.successRate >= 95 ? 'success.main' : keyword.successRate >= 80 ? 'warning.main' : 'error.main'}
                          >
                            {keyword.successRate}%
                          </Typography>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Stündliche Aktivität
              </Typography>
              <ResponsiveContainer width="100%" height={250}>
                <BarChart data={stats ? stats.hourlyActivity : []}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="hour" />
                  <YAxis />
                  <RechartsTooltip />
                  <Bar dataKey="files" fill="#8884d8" />
                </BarChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Storage Usage */}
      <Card sx={{ mt: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            Speicherverbrauch Details
          </Typography>
          <Box display="flex" alignItems="center" mb={2}>
            <Typography variant="body2" color="textSecondary" sx={{ flexGrow: 1 }}>
              {stats ? formatBytes(stats.storageUsed) : '0 B'} von {stats ? formatBytes(stats.storageTotal) : '0 B'} verwendet
            </Typography>
            <Typography variant="body2" fontWeight="bold">
              {storagePercentage.toFixed(1)}%
            </Typography>
          </Box>
          <LinearProgress
            variant="determinate"
            value={storagePercentage}
            color={storagePercentage > 80 ? 'error' : storagePercentage > 60 ? 'warning' : 'primary'}
            sx={{ height: 8, borderRadius: 4 }}
          />
          <Box display="flex" justifyContent="space-between" mt={1}>
            <Typography variant="caption" color="textSecondary">
              Verfügbar: {stats ? formatBytes(stats.storageTotal - stats.storageUsed) : '0 B'}
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Verwendet: {stats ? formatBytes(stats.storageUsed) : '0 B'}
            </Typography>
          </Box>
        </CardContent>
      </Card>
    </Box>
  );
};

export default Statistics; 