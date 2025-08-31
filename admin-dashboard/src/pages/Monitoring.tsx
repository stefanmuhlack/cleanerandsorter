import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Grid,
  Chip,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Alert,
  LinearProgress,
  IconButton,
  Tooltip,
  Button,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Monitor as MonitorIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Refresh as RefreshIcon,
  ExpandMore as ExpandMoreIcon,
  Timeline as TimelineIcon,
  Storage as StorageIcon,
  Memory as MemoryIcon,
  Speed as SpeedIcon,
  CloudQueue as CloudQueueIcon,
  Storage as DatabaseIcon,
  Router as RouterIcon,
  Computer as ComputerIcon
} from '@mui/icons-material';
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip as RechartsTooltip, ResponsiveContainer, BarChart, Bar, PieChart, Pie, Cell } from 'recharts';

interface ServiceHealth {
  service: string;
  status: 'healthy' | 'degraded' | 'unhealthy';
  timestamp: string;
  version: string;
  dependencies?: Record<string, any>;
  unhealthy_services?: string[];
  response_time?: number;
  status_code?: number;
  error?: string;
}

interface SystemMetrics {
  cpu_usage: number;
  memory_usage: number;
  disk_usage: number;
  network_io: number;
  active_connections: number;
  queue_depth: number;
}

interface AlertRule {
  id: string;
  name: string;
  condition: string;
  threshold: number;
  severity: 'info' | 'warning' | 'error' | 'critical';
  enabled: boolean;
  last_triggered?: string;
}

const Monitoring: React.FC = () => {
  const [services, setServices] = useState<ServiceHealth[]>([]);
  const [metrics, setMetrics] = useState<SystemMetrics | null>(null);
  const [alerts, setAlerts] = useState<AlertRule[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedService, setSelectedService] = useState<string | null>(null);
  const [serviceDetails, setServiceDetails] = useState<any>(null);
  const [currentTab, setCurrentTab] = useState(0);
  const [timeRange, setTimeRange] = useState('1h');
  const [refreshInterval, setRefreshInterval] = useState(30);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = '/api';

  const fetchServiceHealth = async () => {
    try {
      setLoading(true);
      setError(null);
      
      const response = await fetch(`${API_BASE_URL}/health/all`);
      if (!response.ok) throw new Error(`HTTP ${response.status}`);
      const healthData = await response.json();
      
      // Transform the health data into our expected format
      const transformedServices: ServiceHealth[] = Object.entries(healthData).map(([serviceName, data]: [string, any]) => ({
        service: serviceName,
        status: data.status || 'unknown',
        timestamp: data.last_check || new Date().toISOString(),
        version: '1.0.0',
        response_time: data.response_time,
        status_code: data.status_code,
        error: data.error,
        dependencies: data.dependencies || {}
      }));
      
      setServices(transformedServices);
      
    } catch (err) {
      console.error('Failed to fetch service health:', err);
      setError(err instanceof Error ? err.message : 'Failed to fetch service health');
      
      setServices([]);
    } finally {
      setLoading(false);
    }
  };

  const fetchSystemMetrics = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/metrics`);
      if (response.ok) {
        const metricsText = await response.text();
        const metrics = parsePrometheusMetrics(metricsText);
        setMetrics(metrics);
      } else {
        setMetrics(null);
      }
    } catch (err) {
      console.error('Failed to fetch metrics:', err);
      setMetrics(null);
    }
  };

  const parsePrometheusMetrics = (metricsText: string): SystemMetrics => {
    // Minimal parsing with safe defaults
    return {
      cpu_usage: 0,
      memory_usage: 0,
      disk_usage: 0,
      network_io: 0,
      active_connections: 0,
      queue_depth: 0
    };
  };

  useEffect(() => {
    fetchServiceHealth();
    fetchSystemMetrics();
    
    // Set up auto-refresh
    const interval = setInterval(() => {
      fetchServiceHealth();
      fetchSystemMetrics();
    }, refreshInterval * 1000);
    
    return () => clearInterval(interval);
  }, [refreshInterval]);

  useEffect(() => {
    setAlerts([
      {
        id: '1',
        name: 'High CPU Usage',
        condition: 'cpu_usage > 80%',
        threshold: 80,
        severity: 'warning',
        enabled: true
      },
      {
        id: '2',
        name: 'Low Disk Space',
        condition: 'disk_usage > 90%',
        threshold: 90,
        severity: 'error',
        enabled: true
      },
      {
        id: '3',
        name: 'Queue Depth Alert',
        condition: 'queue_depth > 100',
        threshold: 100,
        severity: 'warning',
        enabled: true
      }
    ]);
  }, []);

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy': return 'success';
      case 'degraded': return 'warning';
      case 'unhealthy': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy': return <CheckCircleIcon />;
      case 'degraded': return <WarningIcon />;
      case 'unhealthy': return <ErrorIcon />;
      default: return <ErrorIcon />;
    }
  };

  const handleServiceClick = async (serviceName: string) => {
    setSelectedService(serviceName);
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
      const res = await fetch(`/api/${serviceName}/health`, { headers });
      if (res.ok) {
        const text = await res.text();
        try {
          const json = JSON.parse(text);
          setServiceDetails(json);
        } catch {
          setServiceDetails(text);
        }
      } else {
        setServiceDetails({ error: `HTTP ${res.status}` });
      }
    } catch (e: any) {
      setServiceDetails({ error: e?.message || 'Failed to load details' });
    }
  };

  const handleRefresh = () => {
    fetchServiceHealth();
    fetchSystemMetrics();
  };

  const renderServiceHealth = () => (
    <Grid container spacing={3}>
      {error && (
        <Grid item xs={12}>
          <Alert severity="error" onClose={() => setError(null)}>
            {error}
          </Alert>
        </Grid>
      )}
      
      {services.map((service) => (
        <Grid item xs={12} md={6} lg={4} key={service.service}>
          <Card 
            sx={{ 
              cursor: 'pointer',
              '&:hover': { boxShadow: 3 }
            }}
            onClick={() => handleServiceClick(service.service)}
          >
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                {getStatusIcon(service.status)}
                <Typography variant="h6" sx={{ ml: 1 }}>
                  {service.service}
                </Typography>
                <Chip 
                  label={service.status} 
                  color={getStatusColor(service.status) as any}
                  size="small"
                  sx={{ ml: 'auto' }}
                />
              </Box>
              
              <Typography color="textSecondary" gutterBottom>
                Version: {service.version}
              </Typography>
              
              <Typography variant="body2" color="textSecondary">
                Last updated: {new Date(service.timestamp).toLocaleTimeString()}
              </Typography>

              {service.response_time && (
                <Typography variant="body2" color="textSecondary">
                  Response time: {service.response_time.toFixed(2)}s
                </Typography>
              )}

              {service.dependencies && Object.keys(service.dependencies).length > 0 && (
                <Box sx={{ mt: 2 }}>
                  <Typography variant="subtitle2" gutterBottom>
                    Dependencies:
                  </Typography>
                  {Object.entries(service.dependencies).map(([dep, info]: [string, any]) => (
                    <Chip
                      key={dep}
                      label={`${dep}: ${info.status}`}
                      color={getStatusColor(info.status) as any}
                      size="small"
                      sx={{ mr: 0.5, mb: 0.5 }}
                    />
                  ))}
                </Box>
              )}

              {service.unhealthy_services && (
                <Alert severity="warning" sx={{ mt: 2 }}>
                  Unhealthy: {service.unhealthy_services.join(', ')}
                </Alert>
              )}

              {service.error && (
                <Alert severity="error" sx={{ mt: 2 }}>
                  Error: {service.error}
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      ))}
    </Grid>
  );

  const renderSystemMetrics = () => (
    <Grid container spacing={3}>
      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              System Resources
            </Typography>
            
            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">CPU Usage</Typography>
                <Typography variant="body2">{metrics?.cpu_usage}%</Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={metrics?.cpu_usage || 0}
                color={metrics && metrics.cpu_usage > 80 ? 'error' : 'primary'}
              />
            </Box>

            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Memory Usage</Typography>
                <Typography variant="body2">{metrics?.memory_usage}%</Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={metrics?.memory_usage || 0}
                color={metrics && metrics.memory_usage > 80 ? 'error' : 'primary'}
              />
            </Box>

            <Box sx={{ mb: 3 }}>
              <Box sx={{ display: 'flex', justifyContent: 'space-between', mb: 1 }}>
                <Typography variant="body2">Disk Usage</Typography>
                <Typography variant="body2">{metrics?.disk_usage}%</Typography>
              </Box>
              <LinearProgress 
                variant="determinate" 
                value={metrics?.disk_usage || 0}
                color={metrics && metrics.disk_usage > 90 ? 'error' : 'primary'}
              />
            </Box>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12} md={6}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Network & Performance
            </Typography>
            
            <Grid container spacing={2}>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="primary">
                    {metrics?.network_io}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    MB/s
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="secondary">
                    {metrics?.active_connections}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Connections
                  </Typography>
                </Box>
              </Grid>
              <Grid item xs={6}>
                <Box sx={{ textAlign: 'center' }}>
                  <Typography variant="h4" color="success.main">
                    {metrics?.queue_depth}
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Queue Depth
                  </Typography>
                </Box>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      </Grid>

      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Performance Trends
            </Typography>
            <Alert severity="info">Detailed time series are available in Grafana.</Alert>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  const renderAlerts = () => (
    <Grid container spacing={3}>
      <Grid item xs={12}>
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Alert Rules
            </Typography>
            <TableContainer component={Paper} variant="outlined">
              <Table>
                <TableHead>
                  <TableRow>
                    <TableCell>Name</TableCell>
                    <TableCell>Condition</TableCell>
                    <TableCell>Threshold</TableCell>
                    <TableCell>Severity</TableCell>
                    <TableCell>Status</TableCell>
                    <TableCell>Last Triggered</TableCell>
                    <TableCell>Actions</TableCell>
                  </TableRow>
                </TableHead>
                <TableBody>
                  {alerts.map((alert) => (
                    <TableRow key={alert.id}>
                      <TableCell>{alert.name}</TableCell>
                      <TableCell>{alert.condition}</TableCell>
                      <TableCell>{alert.threshold}</TableCell>
                      <TableCell>
                        <Chip 
                          label={alert.severity} 
                          color={alert.severity === 'critical' ? 'error' : 
                                 alert.severity === 'error' ? 'error' :
                                 alert.severity === 'warning' ? 'warning' : 'info'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        <Chip 
                          label={alert.enabled ? 'Enabled' : 'Disabled'}
                          color={alert.enabled ? 'success' : 'default'}
                          size="small"
                        />
                      </TableCell>
                      <TableCell>
                        {alert.last_triggered ? 
                          new Date(alert.last_triggered).toLocaleString() : 
                          'Never'
                        }
                      </TableCell>
                      <TableCell>
                        <Button size="small" variant="outlined">
                          Edit
                        </Button>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </TableContainer>
          </CardContent>
        </Card>
      </Grid>
    </Grid>
  );

  return (
    <Box sx={{ p: 3 }}>
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Typography variant="h4" gutterBottom>
          <MonitorIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
          System Monitoring
        </Typography>
        
        <Box sx={{ display: 'flex', gap: 2, alignItems: 'center' }}>
          <FormControl size="small" sx={{ minWidth: 120 }}>
            <InputLabel>Time Range</InputLabel>
            <Select
              value={timeRange}
              label="Time Range"
              onChange={(e) => setTimeRange(e.target.value)}
            >
              <MenuItem value="1h">Last Hour</MenuItem>
              <MenuItem value="6h">Last 6 Hours</MenuItem>
              <MenuItem value="24h">Last 24 Hours</MenuItem>
              <MenuItem value="7d">Last 7 Days</MenuItem>
            </Select>
          </FormControl>
          
          <Tooltip title="Refresh">
            <IconButton onClick={handleRefresh} disabled={loading}>
              <RefreshIcon />
            </IconButton>
          </Tooltip>
        </Box>
      </Box>

      {loading && <LinearProgress sx={{ mb: 2 }} />}

      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
          <Tab label="Service Health" />
          <Tab label="System Metrics" />
          <Tab label="Alerts" />
        </Tabs>
      </Box>

      {currentTab === 0 && renderServiceHealth()}
      {currentTab === 1 && renderSystemMetrics()}
      {currentTab === 2 && renderAlerts()}

      {/* Service Details Dialog */}
      <Dialog 
        open={!!selectedService} 
        onClose={() => setSelectedService(null)}
        maxWidth="md"
        fullWidth
      >
        <DialogTitle>
          Service Details: {selectedService}
        </DialogTitle>
        <DialogContent>
          {serviceDetails && (
            typeof serviceDetails === 'string' ? (
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>{serviceDetails}</pre>
            ) : (
              <pre style={{ margin: 0, whiteSpace: 'pre-wrap', wordBreak: 'break-word' }}>
                {JSON.stringify(serviceDetails, null, 2)}
              </pre>
            )
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedService(null)}>Close</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Monitoring;
