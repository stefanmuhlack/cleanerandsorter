import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  LinearProgress,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  Avatar,
  IconButton,
  Tooltip,
  Alert,
  Divider,
  Paper
} from '@mui/material';
import {
  TrendingUp as TrendingUpIcon,
  TrendingDown as TrendingDownIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Upload as UploadIcon,
  Storage as StorageIcon,
  Speed as SpeedIcon,
  Schedule as ScheduleIcon,
  FileCopy as FileIcon,
  Folder as FolderIcon,
  CloudUpload as CloudUploadIcon,
  Analytics as AnalyticsIcon
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
  Bar
} from 'recharts';

interface SystemStats {
  totalFiles: number;
  processedFiles: number;
  pendingFiles: number;
  failedFiles: number;
  storageUsed: number;
  storageTotal: number;
  processingRate: number;
  averageProcessingTime: number;
  systemHealth: 'healthy' | 'warning' | 'error';
  services: Array<{
    name: string;
    status: 'running' | 'warning' | 'error';
    uptime: string;
  }>;
  recentActivity: Array<{
    id: string;
    type: 'upload' | 'process' | 'error' | 'system';
    message: string;
    timestamp: string;
    status: 'success' | 'warning' | 'error';
  }>;
}

const COLORS = ['#0088FE', '#00C49F', '#FFBB28', '#FF8042', '#8884D8'];

const Dashboard: React.FC = () => {
  const [stats, setStats] = useState<SystemStats>({
    totalFiles: 1247,
    processedFiles: 1180,
    pendingFiles: 45,
    failedFiles: 22,
    storageUsed: 64424509440, // 60 GB
    storageTotal: 107374182400, // 100 GB
    processingRate: 12.5,
    averageProcessingTime: 2.3,
    systemHealth: 'healthy',
    services: [
      { name: 'Ingest Service', status: 'running', uptime: '2d 14h 32m' },
      { name: 'Elasticsearch', status: 'running', uptime: '5d 8h 15m' },
      { name: 'MinIO Storage', status: 'running', uptime: '1d 22h 47m' },
      { name: 'PostgreSQL', status: 'running', uptime: '3d 6h 12m' },
      { name: 'RabbitMQ', status: 'running', uptime: '4d 1h 33m' },
    ],
    recentActivity: [
      { id: '1', type: 'upload', message: 'Neue Dateien hochgeladen', timestamp: '2 min', status: 'success' },
      { id: '2', type: 'process', message: 'Batch-Verarbeitung abgeschlossen', timestamp: '5 min', status: 'success' },
      { id: '3', type: 'error', message: 'OCR-Fehler bei Dokument', timestamp: '8 min', status: 'warning' },
      { id: '4', type: 'system', message: 'Backup abgeschlossen', timestamp: '1 h', status: 'success' },
      { id: '5', type: 'upload', message: 'Große Datei verarbeitet', timestamp: '2 h', status: 'success' },
    ]
  });

  const [loading, setLoading] = useState(false);

  const processingData = [
    { time: '00:00', files: 12 },
    { time: '04:00', files: 8 },
    { time: '08:00', files: 45 },
    { time: '12:00', files: 67 },
    { time: '16:00', files: 89 },
    { time: '20:00', files: 34 },
  ];

  const fileTypeData = [
    { name: 'PDF', value: 456, color: '#0088FE' },
    { name: 'Dokumente', value: 234, color: '#00C49F' },
    { name: 'Bilder', value: 345, color: '#FFBB28' },
    { name: 'Tabellen', value: 156, color: '#FF8042' },
    { name: 'Archive', value: 56, color: '#8884D8' },
  ];

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

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'running':
      case 'success':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'running':
      case 'success':
        return <CheckCircleIcon fontSize="small" />;
      case 'warning':
        return <WarningIcon fontSize="small" />;
      case 'error':
        return <ErrorIcon fontSize="small" />;
      default:
        return <CheckCircleIcon fontSize="small" />;
    }
  };

  const getActivityIcon = (type: string) => {
    switch (type) {
      case 'upload':
        return <CloudUploadIcon />;
      case 'process':
        return <AnalyticsIcon />;
      case 'error':
        return <ErrorIcon />;
      case 'system':
        return <StorageIcon />;
      default:
        return <FileIcon />;
    }
  };

  const handleRefresh = () => {
    setLoading(true);
    // Simulate API call
    setTimeout(() => {
      setLoading(false);
    }, 1000);
  };

  const successRate = stats.totalFiles > 0 ? (stats.processedFiles / stats.totalFiles) * 100 : 0;
  const storagePercentage = (stats.storageUsed / stats.storageTotal) * 100;

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Dashboard
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Übersicht über das CAS Document Management System
          </Typography>
        </Box>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={handleRefresh}
          disabled={loading}
        >
          Aktualisieren
        </Button>
      </Box>

      {loading && <LinearProgress sx={{ mb: 3 }} />}

      {/* Key Metrics */}
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
                    {stats.totalFiles.toLocaleString()}
                  </Typography>
                  <Box display="flex" alignItems="center" mt={1}>
                    <TrendingUpIcon color="success" sx={{ fontSize: 16, mr: 0.5 }} />
                    <Typography variant="body2" color="success.main">
                      +12% diese Woche
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
                    {successRate.toFixed(1)}%
                  </Typography>
                  <Typography variant="body2" color="textSecondary" mt={1}>
                    {stats.processedFiles} von {stats.totalFiles} verarbeitet
                  </Typography>
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
                    {stats.processingRate}
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
                    {formatBytes(stats.storageUsed)}
                  </Typography>
                  <Typography variant="body2" color="textSecondary" mt={1}>
                    {formatPercentage(stats.storageUsed, stats.storageTotal)} von {formatBytes(stats.storageTotal)}
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

      {/* System Health & Services */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                System Health
              </Typography>
              <Box display="flex" alignItems="center" mb={2}>
                <Chip
                  label={stats.systemHealth}
                  color={getStatusColor(stats.systemHealth) as any}
                  icon={getStatusIcon(stats.systemHealth)}
                  sx={{ mr: 2 }}
                />
                <Typography variant="body2" color="textSecondary">
                  Alle Services laufen optimal
                </Typography>
              </Box>
              <List dense>
                {stats.services.map((service) => (
                  <ListItem key={service.name} disablePadding>
                    <ListItemIcon>
                      {getStatusIcon(service.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={service.name}
                      secondary={`Uptime: ${service.uptime}`}
                    />
                    <Chip
                      label={service.status}
                      color={getStatusColor(service.status) as any}
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Letzte Aktivitäten
              </Typography>
              <List dense>
                {stats.recentActivity.map((activity) => (
                  <ListItem key={activity.id} disablePadding>
                    <ListItemIcon>
                      {getActivityIcon(activity.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={activity.message}
                      secondary={activity.timestamp}
                    />
                    <Chip
                      label={activity.status}
                      color={getStatusColor(activity.status) as any}
                      size="small"
                    />
                  </ListItem>
                ))}
              </List>
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
                Verarbeitungsleistung (24h)
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <LineChart data={processingData}>
                  <CartesianGrid strokeDasharray="3 3" />
                  <XAxis dataKey="time" />
                  <YAxis />
                  <RechartsTooltip />
                  <Line type="monotone" dataKey="files" stroke="#8884d8" strokeWidth={2} />
                </LineChart>
              </ResponsiveContainer>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Dateien nach Typ
              </Typography>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={fileTypeData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={({ name, value }) => `${name} ${value}`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {fileTypeData.map((entry, index) => (
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

      {/* Progress Indicators */}
      <Grid container spacing={3}>
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Speicherverbrauch
              </Typography>
              <Box display="flex" alignItems="center" mb={1}>
                <Typography variant="body2" color="textSecondary" sx={{ flexGrow: 1 }}>
                  {formatBytes(stats.storageUsed)} von {formatBytes(stats.storageTotal)}
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
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>
                Verarbeitungsfortschritt
              </Typography>
              <Box display="flex" alignItems="center" mb={1}>
                <Typography variant="body2" color="textSecondary" sx={{ flexGrow: 1 }}>
                  {stats.processedFiles} von {stats.totalFiles} Dateien
                </Typography>
                <Typography variant="body2" fontWeight="bold">
                  {successRate.toFixed(1)}%
                </Typography>
              </Box>
              <LinearProgress
                variant="determinate"
                value={successRate}
                color="success"
                sx={{ height: 8, borderRadius: 4 }}
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  );
};

export default Dashboard; 