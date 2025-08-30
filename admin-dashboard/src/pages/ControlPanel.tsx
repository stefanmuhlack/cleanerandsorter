import React, { useState, useEffect } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Chip,
  Button,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Paper,
  Tabs,
  Tab,
  Alert,
  CircularProgress,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
} from '@mui/material';
import {
  Dashboard as DashboardIcon,
  Settings as SettingsIcon,
  Security as SecurityIcon,
  People as PeopleIcon,
  Assessment as AssessmentIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  Visibility as VisibilityIcon,
  CheckCircle as CheckCircleIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  Info as InfoIcon,
} from '@mui/icons-material';

interface ServiceStatus {
  name: string;
  status: 'healthy' | 'warning' | 'error' | 'unknown';
  responseTime: number;
  uptime: number;
  lastCheck: string;
}

interface BusinessMetric {
  name: string;
  value: number;
  unit: string;
  trend: 'up' | 'down' | 'stable';
  change: number;
}

interface AuditLog {
  id: string;
  timestamp: string;
  user: string;
  action: string;
  resource: string;
  details: string;
  ip: string;
}

interface User {
  id: string;
  username: string;
  email: string;
  role: string;
  status: 'active' | 'inactive';
  lastLogin: string;
}

interface TabPanelProps {
  children?: React.ReactNode;
  index: number;
  value: number;
}

function TabPanel(props: TabPanelProps) {
  const { children, value, index, ...other } = props;

  return (
    <div
      role="tabpanel"
      hidden={value !== index}
      id={`control-panel-tabpanel-${index}`}
      aria-labelledby={`control-panel-tab-${index}`}
      {...other}
    >
      {value === index && <Box sx={{ p: 3 }}>{children}</Box>}
    </div>
  );
}

const ControlPanel: React.FC = () => {
  const [tabValue, setTabValue] = useState(0);
  const [loading, setLoading] = useState(true);
  const [services, setServices] = useState<ServiceStatus[]>([]);
  const [metrics, setMetrics] = useState<BusinessMetric[]>([]);
  const [auditLogs, setAuditLogs] = useState<AuditLog[]>([]);
  const [users, setUsers] = useState<User[]>([]);
  const [configDialog, setConfigDialog] = useState(false);
  const [userDialog, setUserDialog] = useState(false);
  const [selectedConfig, setSelectedConfig] = useState<any>(null);

  useEffect(() => {
    loadDashboardData();
    const interval = setInterval(loadDashboardData, 30000); // Refresh every 30 seconds
    return () => clearInterval(interval);
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      
      // Load service status
      const servicesResponse = await fetch('/api/health/all');
      const servicesData = await servicesResponse.json();
      setServices(servicesData.services || []);

      // Load business metrics
      const metricsResponse = await fetch('/api/metrics/business');
      const metricsData = await metricsResponse.json();
      setMetrics(metricsData.metrics || []);

      // Load audit logs
      const auditResponse = await fetch('/api/audit/logs?limit=50');
      const auditData = await auditResponse.json();
      setAuditLogs(auditData.logs || []);

      // Load users
      const usersResponse = await fetch('/api/users');
      const usersData = await usersResponse.json();
      setUsers(usersData.users || []);

    } catch (error) {
      console.error('Error loading dashboard data:', error);
    } finally {
      setLoading(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'healthy':
        return <CheckCircleIcon color="success" />;
      case 'warning':
        return <WarningIcon color="warning" />;
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <InfoIcon color="info" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'healthy':
        return 'success';
      case 'warning':
        return 'warning';
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  const handleTabChange = (event: React.SyntheticEvent, newValue: number) => {
    setTabValue(newValue);
  };

  const handleConfigEdit = (config: any) => {
    setSelectedConfig(config);
    setConfigDialog(true);
  };

  const handleUserEdit = (user: User) => {
    setSelectedConfig(user);
    setUserDialog(true);
  };

  const handleConfigSave = async () => {
    try {
      await fetch(`/api/config/${selectedConfig.type}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selectedConfig),
      });
      setConfigDialog(false);
      loadDashboardData();
    } catch (error) {
      console.error('Error saving configuration:', error);
    }
  };

  const handleUserSave = async () => {
    try {
      await fetch(`/api/users/${selectedConfig.id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(selectedConfig),
      });
      setUserDialog(false);
      loadDashboardData();
    } catch (error) {
      console.error('Error saving user:', error);
    }
  };

  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="400px">
        <CircularProgress />
      </Box>
    );
  }

  return (
    <Box sx={{ flexGrow: 1, p: 3 }}>
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Typography variant="h4" component="h1">
          Control Panel - Vogelperspektive
        </Typography>
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={loadDashboardData}
        >
          Aktualisieren
        </Button>
      </Box>

      {/* Key Metrics Overview */}
      <Grid container spacing={3} mb={3}>
        {metrics.map((metric) => (
          <Grid item xs={12} sm={6} md={3} key={metric.name}>
            <Card>
              <CardContent>
                <Typography color="textSecondary" gutterBottom>
                  {metric.name}
                </Typography>
                <Typography variant="h4" component="div">
                  {metric.value} {metric.unit}
                </Typography>
                <Box display="flex" alignItems="center" mt={1}>
                  <Chip
                    label={`${metric.change > 0 ? '+' : ''}${metric.change}%`}
                    color={metric.trend === 'up' ? 'success' : metric.trend === 'down' ? 'error' : 'default'}
                    size="small"
                  />
                </Box>
              </CardContent>
            </Card>
          </Grid>
        ))}
      </Grid>

      {/* Main Control Panel Tabs */}
      <Paper sx={{ width: '100%' }}>
        <Tabs
          value={tabValue}
          onChange={handleTabChange}
          aria-label="control panel tabs"
          variant="scrollable"
          scrollButtons="auto"
        >
          <Tab icon={<DashboardIcon />} label="Service Status" />
          <Tab icon={<SettingsIcon />} label="Konfiguration" />
          <Tab icon={<SecurityIcon />} label="Audit & Logs" />
          <Tab icon={<PeopleIcon />} label="Benutzer" />
          <Tab icon={<AssessmentIcon />} label="Reports" />
        </Tabs>

        {/* Service Status Tab */}
        <TabPanel value={tabValue} index={0}>
          <Grid container spacing={2}>
            {services.map((service) => (
              <Grid item xs={12} sm={6} md={4} key={service.name}>
                <Card>
                  <CardContent>
                    <Box display="flex" justifyContent="space-between" alignItems="center">
                      <Typography variant="h6">{service.name}</Typography>
                      {getStatusIcon(service.status)}
                    </Box>
                    <Typography color="textSecondary">
                      Response: {service.responseTime}ms
                    </Typography>
                    <Typography color="textSecondary">
                      Uptime: {service.uptime}%
                    </Typography>
                    <Typography variant="caption" color="textSecondary">
                      Letzter Check: {new Date(service.lastCheck).toLocaleString()}
                    </Typography>
                    <Box mt={1}>
                      <Chip
                        label={service.status}
                        color={getStatusColor(service.status) as any}
                        size="small"
                      />
                    </Box>
                  </CardContent>
                </Card>
              </Grid>
            ))}
          </Grid>
        </TabPanel>

        {/* Configuration Tab */}
        <TabPanel value={tabValue} index={1}>
          <Box mb={2}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setSelectedConfig({ type: 'new', name: '', value: '' });
                setConfigDialog(true);
              }}
            >
              Neue Konfiguration
            </Button>
          </Box>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Name</TableCell>
                  <TableCell>Typ</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Letzte Änderung</TableCell>
                  <TableCell>Aktionen</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {[
                  { name: 'Sortierregeln', type: 'sorting-rules', status: 'aktiv', lastModified: '2024-01-15' },
                  { name: 'Email-Konfiguration', type: 'email-config', status: 'aktiv', lastModified: '2024-01-14' },
                  { name: 'OTRS-Integration', type: 'otrs-config', status: 'aktiv', lastModified: '2024-01-13' },
                  { name: 'Backup-Strategie', type: 'backup-config', status: 'aktiv', lastModified: '2024-01-12' },
                ].map((config) => (
                  <TableRow key={config.name}>
                    <TableCell>{config.name}</TableCell>
                    <TableCell>{config.type}</TableCell>
                    <TableCell>
                      <Chip label={config.status} color="success" size="small" />
                    </TableCell>
                    <TableCell>{config.lastModified}</TableCell>
                    <TableCell>
                      <Tooltip title="Bearbeiten">
                        <IconButton onClick={() => handleConfigEdit(config)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Anzeigen">
                        <IconButton>
                          <VisibilityIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Audit & Logs Tab */}
        <TabPanel value={tabValue} index={2}>
          <Box mb={2}>
            <Button variant="outlined" onClick={() => window.open('/api/audit/export', '_blank')}>
              Audit-Logs exportieren
            </Button>
          </Box>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Zeitstempel</TableCell>
                  <TableCell>Benutzer</TableCell>
                  <TableCell>Aktion</TableCell>
                  <TableCell>Ressource</TableCell>
                  <TableCell>IP-Adresse</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {auditLogs.map((log) => (
                  <TableRow key={log.id}>
                    <TableCell>{new Date(log.timestamp).toLocaleString()}</TableCell>
                    <TableCell>{log.user}</TableCell>
                    <TableCell>{log.action}</TableCell>
                    <TableCell>{log.resource}</TableCell>
                    <TableCell>{log.ip}</TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Users Tab */}
        <TabPanel value={tabValue} index={3}>
          <Box mb={2}>
            <Button
              variant="contained"
              startIcon={<AddIcon />}
              onClick={() => {
                setSelectedConfig({ id: 'new', username: '', email: '', role: 'user', status: 'active' });
                setUserDialog(true);
              }}
            >
              Neuen Benutzer
            </Button>
          </Box>
          
          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Benutzername</TableCell>
                  <TableCell>Email</TableCell>
                  <TableCell>Rolle</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Letzter Login</TableCell>
                  <TableCell>Aktionen</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {users.map((user) => (
                  <TableRow key={user.id}>
                    <TableCell>{user.username}</TableCell>
                    <TableCell>{user.email}</TableCell>
                    <TableCell>{user.role}</TableCell>
                    <TableCell>
                      <Chip
                        label={user.status}
                        color={user.status === 'active' ? 'success' : 'default'}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>{new Date(user.lastLogin).toLocaleString()}</TableCell>
                    <TableCell>
                      <Tooltip title="Bearbeiten">
                        <IconButton onClick={() => handleUserEdit(user)}>
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Löschen">
                        <IconButton color="error">
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </TabPanel>

        {/* Reports Tab */}
        <TabPanel value={tabValue} index={4}>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    System-Performance
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    CPU-Auslastung: 45%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Speicher-Auslastung: 67%
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Disk-Auslastung: 23%
                  </Typography>
                  <Button variant="outlined" size="small" sx={{ mt: 1 }}>
                    Detaillierter Report
                  </Button>
                </CardContent>
              </Card>
            </Grid>
            
            <Grid item xs={12} md={6}>
              <Card>
                <CardContent>
                  <Typography variant="h6" gutterBottom>
                    Business-KPIs
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Dokumente verarbeitet: 1,234
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Durchschnittliche Verarbeitungszeit: 2.3s
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Erfolgsrate: 98.5%
                  </Typography>
                  <Button variant="outlined" size="small" sx={{ mt: 1 }}>
                    KPI-Report
                  </Button>
                </CardContent>
              </Card>
            </Grid>
          </Grid>
        </TabPanel>
      </Paper>

      {/* Configuration Dialog */}
      <Dialog open={configDialog} onClose={() => setConfigDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Konfiguration bearbeiten</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Name"
            value={selectedConfig?.name || ''}
            onChange={(e) => setSelectedConfig({ ...selectedConfig, name: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Wert"
            multiline
            rows={4}
            value={selectedConfig?.value || ''}
            onChange={(e) => setSelectedConfig({ ...selectedConfig, value: e.target.value })}
            margin="normal"
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setConfigDialog(false)}>Abbrechen</Button>
          <Button onClick={handleConfigSave} variant="contained">Speichern</Button>
        </DialogActions>
      </Dialog>

      {/* User Dialog */}
      <Dialog open={userDialog} onClose={() => setUserDialog(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Benutzer bearbeiten</DialogTitle>
        <DialogContent>
          <TextField
            fullWidth
            label="Benutzername"
            value={selectedConfig?.username || ''}
            onChange={(e) => setSelectedConfig({ ...selectedConfig, username: e.target.value })}
            margin="normal"
          />
          <TextField
            fullWidth
            label="Email"
            value={selectedConfig?.email || ''}
            onChange={(e) => setSelectedConfig({ ...selectedConfig, email: e.target.value })}
            margin="normal"
          />
          <FormControl fullWidth margin="normal">
            <InputLabel>Rolle</InputLabel>
            <Select
              value={selectedConfig?.role || ''}
              onChange={(e) => setSelectedConfig({ ...selectedConfig, role: e.target.value })}
            >
              <MenuItem value="user">User</MenuItem>
              <MenuItem value="admin">Admin</MenuItem>
              <MenuItem value="finance">Finance</MenuItem>
              <MenuItem value="sales">Sales</MenuItem>
              <MenuItem value="superadmin">Super Admin</MenuItem>
            </Select>
          </FormControl>
          <FormControlLabel
            control={
              <Switch
                checked={selectedConfig?.status === 'active'}
                onChange={(e) => setSelectedConfig({ ...selectedConfig, status: e.target.checked ? 'active' : 'inactive' })}
              />
            }
            label="Aktiv"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUserDialog(false)}>Abbrechen</Button>
          <Button onClick={handleUserSave} variant="contained">Speichern</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default ControlPanel;
