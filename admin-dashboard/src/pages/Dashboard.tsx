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
  Paper,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions
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
  const [stats, setStats] = useState<SystemStats | null>(null);

  const [loading, setLoading] = useState(false);

  const [processingData, setProcessingData] = useState<Array<{time: string; files: number}>>([]);

  const [fileTypeData, setFileTypeData] = useState<Array<{ name: string; value: number; color: string }>>([]);

  const [errorDialog, setErrorDialog] = useState<{open: boolean; title: string; details: string}>(
    { open: false, title: '', details: '' }
  );

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

  const loadData = async () => {
    try {
      setLoading(true);
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
      // Health/services
      const healthRes = await fetch('/api/health/all', { headers });
      const health = healthRes.ok ? await healthRes.json() : {};
      type ServiceItem = { name: string; status: 'running' | 'warning' | 'error'; uptime: string };
      const services: ServiceItem[] = Object.entries(health)
        .filter(([k]) => k !== 'cache_time')
        .map(([name, v]: any) => {
          const status: 'running' | 'warning' | 'error' = v?.status === 'healthy' ? 'running' : v?.status === 'unhealthy' ? 'error' : 'warning';
          return {
            name,
            status,
            uptime: v?.last_check ? new Date(v.last_check).toLocaleString() : '-'
          };
        });
      // Ingest stats (basic)
      const ingestStatsRes = await fetch('/api/ingest/processing/stats', { headers });
      const ingestStats = ingestStatsRes.ok ? await ingestStatsRes.json() : {};
      // Build dashboard stats
      const totalFiles = (ingestStats.total_files_processed || 0) + (ingestStats.failed_files || 0);
      const processedFiles = ingestStats.successful_files || 0;
      const failedFiles = ingestStats.failed_files || 0;
      const pendingFiles = 0;
      const processingRate = 0;
      const averageProcessingTime = 0;
      const systemHealth = services.every(s => s.status === 'running') ? 'healthy' : services.some(s => s.status === 'error') ? 'error' : 'warning';
      setStats({
        totalFiles,
        processedFiles,
        pendingFiles,
        failedFiles,
        storageUsed: 0,
        storageTotal: 0,
        processingRate,
        averageProcessingTime,
        systemHealth: systemHealth as any,
        services,
        recentActivity: []
      });
      setProcessingData([]);
      setFileTypeData([]);
    } catch (e) {
      setStats(null);
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = () => { loadData(); };

  useEffect(() => { loadData(); }, []);

  const totalFilesVal = stats?.totalFiles ?? 0;
  const processedFilesVal = stats?.processedFiles ?? 0;
  const storageUsedVal = stats?.storageUsed ?? 0;
  const storageTotalVal = stats?.storageTotal ?? 0;
  const successRate = totalFilesVal > 0 ? (processedFilesVal / totalFilesVal) * 100 : 0;
  const storagePercentage = storageTotalVal > 0 ? (storageUsedVal / storageTotalVal) * 100 : 0;

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
                    {stats ? stats.totalFiles.toLocaleString() : 0}
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
                    {stats ? stats.processedFiles : 0} von {stats ? stats.totalFiles : 0} verarbeitet
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
                  label={stats?.systemHealth ?? 'healthy'}
                  color={getStatusColor(stats?.systemHealth ?? 'healthy') as any}
                  icon={getStatusIcon(stats?.systemHealth ?? 'healthy')}
                  sx={{ mr: 2 }}
                />
                <Typography variant="body2" color="textSecondary">
                  Alle Services laufen optimal
                </Typography>
              </Box>
              <List dense>
                {(stats?.services || []).map((service) => (
                  <ListItem key={service.name} disablePadding
                    onClick={() => {
                      if (service.status !== 'running') {
                        // fetch latest health for this service to show details
                        fetch(`/health/all`).then(r => r.json()).then((all) => {
                          const raw = all && all[service.name] ? all[service.name] : {};
                          const details = typeof raw === 'object' ? JSON.stringify(raw, null, 2) : String(raw);
                          setErrorDialog({ open: true, title: `${service.name} status`, details });
                        }).catch(() => setErrorDialog({ open: true, title: `${service.name} status`, details: 'No details available' }));
                      }
                    }}
                    sx={{ cursor: service.status !== 'running' ? 'pointer' : 'default' }}
                  >
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
                {(stats?.recentActivity || []).map((activity) => (
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
                  {stats ? formatBytes(stats.storageUsed) : '0 B'} von {stats ? formatBytes(stats.storageTotal) : '0 B'}
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
                  {(stats ? stats.processedFiles : 0)} von {(stats ? stats.totalFiles : 0)} Dateien
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

      <Dialog open={errorDialog.open} onClose={() => setErrorDialog({ open: false, title: '', details: '' })} maxWidth="md" fullWidth>
        <DialogTitle>{errorDialog.title}</DialogTitle>
        <DialogContent>
          <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{errorDialog.details}</pre>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setErrorDialog({ open: false, title: '', details: '' })}>Schließen</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Dashboard; 