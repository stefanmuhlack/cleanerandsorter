import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  TextField,
  Switch,
  FormControlLabel,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Alert,
  Chip,
  Avatar,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tabs,
  Tab,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  LinearProgress
} from '@mui/material';
import {
  Settings as SettingsIcon,
  Save as SaveIcon,
  Refresh as RefreshIcon,
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  ExpandMore as ExpandMoreIcon,
  Notifications as NotificationsIcon,
  Security as SecurityIcon,
  Storage as StorageIcon,
  CloudUpload as CloudUploadIcon,
  Language as LanguageIcon,
  Palette as PaletteIcon,
  Backup as BackupIcon,
  RestoreFromTrash as RestoreIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  Person as PersonIcon,
  Email as EmailIcon,
  Phone as PhoneIcon,
  Business as BusinessIcon
} from '@mui/icons-material';

interface SettingsData {
  system: {
    apiEndpoint: string;
    maxFileSize: number;
    allowedFileTypes: string[];
    autoProcessing: boolean;
    retentionDays: number;
    backupEnabled: boolean;
    backupFrequency: string;
  };
  notifications: {
    emailEnabled: boolean;
    emailAddress: string;
    slackEnabled: boolean;
    slackWebhook: string;
    processingAlerts: boolean;
    errorAlerts: boolean;
    successAlerts: boolean;
  };
  appearance: {
    theme: 'light' | 'dark' | 'auto';
    language: string;
    timezone: string;
    dateFormat: string;
  };
  security: {
    sessionTimeout: number;
    requireMFA: boolean;
    passwordPolicy: string;
    apiKeyRotation: number;
  };
  users: Array<{
    id: string;
    name: string;
    email: string;
    role: string;
    status: 'active' | 'inactive';
    lastLogin: Date;
  }>;
  backups: Array<{
    id: string;
    name: string;
    type: 'manual' | 'automatic';
    size: number;
    createdAt: Date;
    status: 'completed' | 'failed' | 'in_progress';
  }>;
}

const Settings: React.FC = () => {
  const [activeTab, setActiveTab] = useState(0);
  const [settings, setSettings] = useState<SettingsData>({
    system: {
      apiEndpoint: 'http://localhost:8000',
      maxFileSize: 100,
      allowedFileTypes: ['pdf', 'doc', 'docx', 'jpg', 'png'],
      autoProcessing: true,
      retentionDays: 365,
      backupEnabled: true,
      backupFrequency: 'daily'
    },
    notifications: {
      emailEnabled: true,
      emailAddress: 'admin@example.com',
      slackEnabled: false,
      slackWebhook: '',
      processingAlerts: true,
      errorAlerts: true,
      successAlerts: false
    },
    appearance: {
      theme: 'light',
      language: 'de',
      timezone: 'Europe/Berlin',
      dateFormat: 'DD.MM.YYYY'
    },
    security: {
      sessionTimeout: 30,
      requireMFA: false,
      passwordPolicy: 'strong',
      apiKeyRotation: 90
    },
    users: [
      {
        id: '1',
        name: 'Admin User',
        email: 'admin@example.com',
        role: 'Administrator',
        status: 'active',
        lastLogin: new Date('2024-01-16T10:30:00')
      },
      {
        id: '2',
        name: 'John Doe',
        email: 'john@example.com',
        role: 'User',
        status: 'active',
        lastLogin: new Date('2024-01-15T14:20:00')
      },
      {
        id: '3',
        name: 'Jane Smith',
        email: 'jane@example.com',
        role: 'Manager',
        status: 'inactive',
        lastLogin: new Date('2024-01-10T09:15:00')
      }
    ],
    backups: [
      {
        id: '1',
        name: 'Backup_2024-01-16_02:00',
        type: 'automatic',
        size: 2147483648, // 2 GB
        createdAt: new Date('2024-01-16T02:00:00'),
        status: 'completed'
      },
      {
        id: '2',
        name: 'Backup_2024-01-15_02:00',
        type: 'automatic',
        size: 2147483648,
        createdAt: new Date('2024-01-15T02:00:00'),
        status: 'completed'
      },
      {
        id: '3',
        name: 'Manual_Backup_2024-01-14',
        type: 'manual',
        size: 2147483648,
        createdAt: new Date('2024-01-14T15:30:00'),
        status: 'completed'
      }
    ]
  });

  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingUser, setEditingUser] = useState<any>(null);
  const [saving, setSaving] = useState(false);

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return 'success';
      case 'inactive':
      case 'failed':
        return 'error';
      case 'in_progress':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return <CheckCircleIcon />;
      case 'inactive':
      case 'failed':
        return <ErrorIcon />;
      case 'in_progress':
        return <WarningIcon />;
      default:
        return <CheckCircleIcon />;
    }
  };

  const handleSaveSettings = () => {
    setSaving(true);
    // Simulate API call
    setTimeout(() => {
      setSaving(false);
    }, 2000);
  };

  const handleCreateBackup = () => {
    // Simulate backup creation
    console.log('Creating backup...');
  };

  const handleRestoreBackup = (backupId: string) => {
    // Simulate backup restoration
    console.log('Restoring backup:', backupId);
  };

  const handleDeleteBackup = (backupId: string) => {
    // Simulate backup deletion
    console.log('Deleting backup:', backupId);
  };

  const handleEditUser = (user: any) => {
    setEditingUser(user);
    setDialogOpen(true);
  };

  const handleDeleteUser = (userId: string) => {
    // Simulate user deletion
    console.log('Deleting user:', userId);
  };

  const tabs = [
    { label: 'System', icon: <SettingsIcon /> },
    { label: 'Benachrichtigungen', icon: <NotificationsIcon /> },
    { label: 'Erscheinungsbild', icon: <PaletteIcon /> },
    { label: 'Sicherheit', icon: <SecurityIcon /> },
    { label: 'Benutzer', icon: <PersonIcon /> },
    { label: 'Backups', icon: <BackupIcon /> }
  ];

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Einstellungen
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Systemkonfiguration und Benutzereinstellungen verwalten
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<SaveIcon />}
          onClick={handleSaveSettings}
          disabled={saving}
        >
          {saving ? 'Speichern...' : 'Speichern'}
        </Button>
      </Box>

      {saving && <LinearProgress sx={{ mb: 3 }} />}

      {/* Tabs */}
      <Card sx={{ mb: 3 }}>
        <Tabs
          value={activeTab}
          onChange={(_, newValue) => setActiveTab(newValue)}
          variant="scrollable"
          scrollButtons="auto"
        >
          {tabs.map((tab, index) => (
            <Tab
              key={index}
              label={tab.label}
              icon={tab.icon}
              iconPosition="start"
            />
          ))}
        </Tabs>
      </Card>

      {/* Tab Content */}
      {activeTab === 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Systemeinstellungen
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="API Endpoint"
                  value={settings.system.apiEndpoint}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    system: { ...prev.system, apiEndpoint: e.target.value }
                  }))}
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="Maximale Dateigröße (MB)"
                  type="number"
                  value={settings.system.maxFileSize}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    system: { ...prev.system, maxFileSize: parseInt(e.target.value) }
                  }))}
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="Aufbewahrungszeit (Tage)"
                  type="number"
                  value={settings.system.retentionDays}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    system: { ...prev.system, retentionDays: parseInt(e.target.value) }
                  }))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.system.autoProcessing}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        system: { ...prev.system, autoProcessing: e.target.checked }
                      }))}
                    />
                  }
                  label="Automatische Verarbeitung"
                  sx={{ mb: 2 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.system.backupEnabled}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        system: { ...prev.system, backupEnabled: e.target.checked }
                      }))}
                    />
                  }
                  label="Automatische Backups"
                  sx={{ mb: 2 }}
                />
                <FormControl fullWidth>
                  <InputLabel>Backup-Frequenz</InputLabel>
                  <Select
                    value={settings.system.backupFrequency}
                    label="Backup-Frequenz"
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      system: { ...prev.system, backupFrequency: e.target.value }
                    }))}
                  >
                    <MenuItem value="daily">Täglich</MenuItem>
                    <MenuItem value="weekly">Wöchentlich</MenuItem>
                    <MenuItem value="monthly">Monatlich</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {activeTab === 1 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Benachrichtigungen
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  E-Mail Benachrichtigungen
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.emailEnabled}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        notifications: { ...prev.notifications, emailEnabled: e.target.checked }
                      }))}
                    />
                  }
                  label="E-Mail aktivieren"
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="E-Mail Adresse"
                  value={settings.notifications.emailAddress}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    notifications: { ...prev.notifications, emailAddress: e.target.value }
                  }))}
                  disabled={!settings.notifications.emailEnabled}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <Typography variant="subtitle1" gutterBottom>
                  Slack Integration
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.slackEnabled}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        notifications: { ...prev.notifications, slackEnabled: e.target.checked }
                      }))}
                    />
                  }
                  label="Slack aktivieren"
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="Slack Webhook URL"
                  value={settings.notifications.slackWebhook}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    notifications: { ...prev.notifications, slackWebhook: e.target.value }
                  }))}
                  disabled={!settings.notifications.slackEnabled}
                  sx={{ mb: 2 }}
                />
              </Grid>
              <Grid item xs={12}>
                <Typography variant="subtitle1" gutterBottom>
                  Benachrichtigungstypen
                </Typography>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.processingAlerts}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        notifications: { ...prev.notifications, processingAlerts: e.target.checked }
                      }))}
                    />
                  }
                  label="Verarbeitungsalerts"
                  sx={{ mr: 3 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.errorAlerts}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        notifications: { ...prev.notifications, errorAlerts: e.target.checked }
                      }))}
                    />
                  }
                  label="Fehleralerts"
                  sx={{ mr: 3 }}
                />
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.notifications.successAlerts}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        notifications: { ...prev.notifications, successAlerts: e.target.checked }
                      }))}
                    />
                  }
                  label="Erfolgsalerts"
                />
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {activeTab === 2 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Erscheinungsbild
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Theme</InputLabel>
                  <Select
                    value={settings.appearance.theme}
                    label="Theme"
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      appearance: { ...prev.appearance, theme: e.target.value as any }
                    }))}
                  >
                    <MenuItem value="light">Hell</MenuItem>
                    <MenuItem value="dark">Dunkel</MenuItem>
                    <MenuItem value="auto">Automatisch</MenuItem>
                  </Select>
                </FormControl>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Sprache</InputLabel>
                  <Select
                    value={settings.appearance.language}
                    label="Sprache"
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      appearance: { ...prev.appearance, language: e.target.value }
                    }))}
                  >
                    <MenuItem value="de">Deutsch</MenuItem>
                    <MenuItem value="en">English</MenuItem>
                    <MenuItem value="fr">Français</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControl fullWidth sx={{ mb: 2 }}>
                  <InputLabel>Zeitzone</InputLabel>
                  <Select
                    value={settings.appearance.timezone}
                    label="Zeitzone"
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      appearance: { ...prev.appearance, timezone: e.target.value }
                    }))}
                  >
                    <MenuItem value="Europe/Berlin">Europe/Berlin</MenuItem>
                    <MenuItem value="UTC">UTC</MenuItem>
                    <MenuItem value="America/New_York">America/New_York</MenuItem>
                  </Select>
                </FormControl>
                <FormControl fullWidth>
                  <InputLabel>Datumsformat</InputLabel>
                  <Select
                    value={settings.appearance.dateFormat}
                    label="Datumsformat"
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      appearance: { ...prev.appearance, dateFormat: e.target.value }
                    }))}
                  >
                    <MenuItem value="DD.MM.YYYY">DD.MM.YYYY</MenuItem>
                    <MenuItem value="MM/DD/YYYY">MM/DD/YYYY</MenuItem>
                    <MenuItem value="YYYY-MM-DD">YYYY-MM-DD</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {activeTab === 3 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Sicherheit
            </Typography>
            <Grid container spacing={3}>
              <Grid item xs={12} md={6}>
                <TextField
                  fullWidth
                  label="Session Timeout (Minuten)"
                  type="number"
                  value={settings.security.sessionTimeout}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    security: { ...prev.security, sessionTimeout: parseInt(e.target.value) }
                  }))}
                  sx={{ mb: 2 }}
                />
                <TextField
                  fullWidth
                  label="API Key Rotation (Tage)"
                  type="number"
                  value={settings.security.apiKeyRotation}
                  onChange={(e) => setSettings(prev => ({
                    ...prev,
                    security: { ...prev.security, apiKeyRotation: parseInt(e.target.value) }
                  }))}
                />
              </Grid>
              <Grid item xs={12} md={6}>
                <FormControlLabel
                  control={
                    <Switch
                      checked={settings.security.requireMFA}
                      onChange={(e) => setSettings(prev => ({
                        ...prev,
                        security: { ...prev.security, requireMFA: e.target.checked }
                      }))}
                    />
                  }
                  label="Multi-Faktor-Authentifizierung erforderlich"
                  sx={{ mb: 2 }}
                />
                <FormControl fullWidth>
                  <InputLabel>Passwort-Richtlinie</InputLabel>
                  <Select
                    value={settings.security.passwordPolicy}
                    label="Passwort-Richtlinie"
                    onChange={(e) => setSettings(prev => ({
                      ...prev,
                      security: { ...prev.security, passwordPolicy: e.target.value }
                    }))}
                  >
                    <MenuItem value="weak">Schwach</MenuItem>
                    <MenuItem value="medium">Mittel</MenuItem>
                    <MenuItem value="strong">Stark</MenuItem>
                  </Select>
                </FormControl>
              </Grid>
            </Grid>
          </CardContent>
        </Card>
      )}

      {activeTab === 4 && (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Benutzerverwaltung
              </Typography>
              <Button
                variant="contained"
                startIcon={<AddIcon />}
                onClick={() => {
                  setEditingUser(null);
                  setDialogOpen(true);
                }}
              >
                Benutzer hinzufügen
              </Button>
            </Box>
            <List>
              {settings.users.map((user) => (
                <React.Fragment key={user.id}>
                  <ListItem>
                    <ListItemIcon>
                      <Avatar>
                        <PersonIcon />
                      </Avatar>
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1" fontWeight="medium">
                            {user.name}
                          </Typography>
                          <Chip
                            label={user.status}
                            color={getStatusColor(user.status) as any}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            {user.email} • {user.role}
                          </Typography>
                          <Typography variant="caption" color="textSecondary">
                            Letzter Login: {user.lastLogin.toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box display="flex" gap={1}>
                        <Tooltip title="Bearbeiten">
                          <IconButton 
                            size="small"
                            onClick={() => handleEditUser(user)}
                          >
                            <EditIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Löschen">
                          <IconButton 
                            size="small"
                            color="error"
                            onClick={() => handleDeleteUser(user.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {activeTab === 5 && (
        <Card>
          <CardContent>
            <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
              <Typography variant="h6">
                Backup-Verwaltung
              </Typography>
              <Button
                variant="contained"
                startIcon={<BackupIcon />}
                onClick={handleCreateBackup}
              >
                Backup erstellen
              </Button>
            </Box>
            <List>
              {settings.backups.map((backup) => (
                <React.Fragment key={backup.id}>
                  <ListItem>
                    <ListItemIcon>
                      {getStatusIcon(backup.status)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1" fontWeight="medium">
                            {backup.name}
                          </Typography>
                          <Chip
                            label={backup.type}
                            size="small"
                            variant="outlined"
                          />
                          <Chip
                            label={backup.status}
                            color={getStatusColor(backup.status) as any}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            Größe: {formatBytes(backup.size)} • Erstellt: {backup.createdAt.toLocaleString()}
                          </Typography>
                        </Box>
                      }
                    />
                    <ListItemSecondaryAction>
                      <Box display="flex" gap={1}>
                        <Tooltip title="Wiederherstellen">
                          <IconButton 
                            size="small"
                            onClick={() => handleRestoreBackup(backup.id)}
                          >
                            <RestoreIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Herunterladen">
                          <IconButton size="small">
                            <DownloadIcon />
                          </IconButton>
                        </Tooltip>
                        <Tooltip title="Löschen">
                          <IconButton 
                            size="small"
                            color="error"
                            onClick={() => handleDeleteBackup(backup.id)}
                          >
                            <DeleteIcon />
                          </IconButton>
                        </Tooltip>
                      </Box>
                    </ListItemSecondaryAction>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* User Edit Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>
          {editingUser ? 'Benutzer bearbeiten' : 'Neuen Benutzer erstellen'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Name"
                defaultValue={editingUser?.name || ''}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="E-Mail"
                type="email"
                defaultValue={editingUser?.email || ''}
                sx={{ mb: 2 }}
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Rolle</InputLabel>
                <Select
                  defaultValue={editingUser?.role || 'User'}
                  label="Rolle"
                >
                  <MenuItem value="User">Benutzer</MenuItem>
                  <MenuItem value="Manager">Manager</MenuItem>
                  <MenuItem value="Administrator">Administrator</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Abbrechen</Button>
          <Button variant="contained" onClick={() => setDialogOpen(false)}>
            Speichern
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Settings; 