import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  TextField,
  Switch,
  FormControlLabel,
  Divider,
  Alert,
  Chip,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Select,
  MenuItem,
  FormControl,
  InputLabel,
  Slider,
  InputAdornment,
  IconButton,
  Tooltip
} from '@mui/material';
import {
  Settings as SettingsIcon,
  ExpandMore,
  Psychology,
  Storage,
  NetworkCheck,
  Security,
  Backup,
  Email,
  CloudUpload,
  Save,
  Refresh,
  WifiTethering as TestConnection
} from '@mui/icons-material';

interface LLMConfig {
  enabled: boolean;
  model: string;
  temperature: number;
  maxTokens: number;
  endpoint: string;
  apiKey: string;
  timeout: number;
}

interface NASConfig {
  enabled: boolean;
  server: string;
  path: string;
  username: string;
  password: string;
  mountPoint: string;
  autoMount: boolean;
}

interface EmailConfig {
  enabled: boolean;
  imapHost: string;
  imapPort: number;
  imapUsername: string;
  imapPassword: string;
  smtpHost: string;
  smtpPort: number;
  smtpUsername: string;
  smtpPassword: string;
}

interface SystemConfig {
  maxFileSize: number;
  allowedFileTypes: string[];
  backupRetention: number;
  processingWorkers: number;
  batchSize: number;
  enableCompression: boolean;
  enableEncryption: boolean;
}

const Settings: React.FC = () => {
  const [llmConfig, setLlmConfig] = useState<LLMConfig>({
    enabled: true,
    model: 'mistral-7b',
    temperature: 0.1,
    maxTokens: 100,
    endpoint: 'http://ollama:11434',
    apiKey: '',
    timeout: 30
  });

  const [nasConfig, setNasConfig] = useState<NASConfig>({
    enabled: false,
    server: '192.168.1.100',
    path: '/volume1/documents',
    username: '',
    password: '',
    mountPoint: '/mnt/nas',
    autoMount: true
  });

  const [emailConfig, setEmailConfig] = useState<EmailConfig>({
    enabled: false,
    imapHost: 'mail.company.com',
    imapPort: 993,
    imapUsername: '',
    imapPassword: '',
    smtpHost: 'mail.company.com',
    smtpPort: 587,
    smtpUsername: '',
    smtpPassword: ''
  });

  const [systemConfig, setSystemConfig] = useState<SystemConfig>({
    maxFileSize: 100,
    allowedFileTypes: ['pdf', 'doc', 'docx', 'xls', 'xlsx', 'jpg', 'png', 'txt'],
    backupRetention: 30,
    processingWorkers: 4,
    batchSize: 10,
    enableCompression: true,
    enableEncryption: false
  });

  const [saving, setSaving] = useState(false);
  const [testing, setTesting] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  const handleSave = async () => {
    setSaving(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1000));
      setMessage({ type: 'success', text: 'Settings saved successfully!' });
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to save settings' });
    } finally {
      setSaving(false);
    }
  };

  const handleTestConnection = async (type: 'llm' | 'nas' | 'email') => {
    setTesting(true);
    try {
      // Simulate connection test
      await new Promise(resolve => setTimeout(resolve, 2000));
      setMessage({ type: 'success', text: `${type.toUpperCase()} connection test successful!` });
    } catch (error) {
      setMessage({ type: 'error', text: `${type.toUpperCase()} connection test failed` });
    } finally {
      setTesting(false);
    }
  };

  const availableModels = [
    'mistral-7b',
    'llama-3-8b',
    'llama-3-70b',
    'codellama-7b',
    'phi-2',
    'gemma-2b',
    'gemma-7b'
  ];

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        System Settings
      </Typography>

      {message && (
        <Alert 
          severity={message.type} 
          sx={{ mb: 3 }}
          onClose={() => setMessage(null)}
        >
          {message.text}
        </Alert>
      )}

      <Grid container spacing={3}>
        {/* LLM Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Psychology sx={{ mr: 1 }} />
                <Typography variant="h6">LLM Configuration</Typography>
                <Chip 
                  label={llmConfig.enabled ? 'Enabled' : 'Disabled'} 
                  color={llmConfig.enabled ? 'success' : 'default'}
                  size="small"
                  sx={{ ml: 'auto' }}
                />
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={llmConfig.enabled}
                    onChange={(e) => setLlmConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                  />
                }
                label="Enable LLM Classification"
              />

              <TextField
                fullWidth
                label="Model"
                value={llmConfig.model}
                onChange={(e) => setLlmConfig(prev => ({ ...prev, model: e.target.value }))}
                select
                margin="normal"
                disabled={!llmConfig.enabled}
              >
                {availableModels.map((model) => (
                  <MenuItem key={model} value={model}>
                    {model}
                  </MenuItem>
                ))}
              </TextField>

              <TextField
                fullWidth
                label="Endpoint"
                value={llmConfig.endpoint}
                onChange={(e) => setLlmConfig(prev => ({ ...prev, endpoint: e.target.value }))}
                margin="normal"
                disabled={!llmConfig.enabled}
              />

              <Typography gutterBottom sx={{ mt: 2 }}>
                Temperature: {llmConfig.temperature}
              </Typography>
              <Slider
                value={llmConfig.temperature}
                onChange={(_, value) => setLlmConfig(prev => ({ ...prev, temperature: value as number }))}
                min={0}
                max={1}
                step={0.1}
                disabled={!llmConfig.enabled}
                marks={[
                  { value: 0, label: '0' },
                  { value: 0.5, label: '0.5' },
                  { value: 1, label: '1' }
                ]}
              />

              <TextField
                fullWidth
                label="Max Tokens"
                type="number"
                value={llmConfig.maxTokens}
                onChange={(e) => setLlmConfig(prev => ({ ...prev, maxTokens: parseInt(e.target.value) }))}
                margin="normal"
                disabled={!llmConfig.enabled}
              />

              <TextField
                fullWidth
                label="Timeout (seconds)"
                type="number"
                value={llmConfig.timeout}
                onChange={(e) => setLlmConfig(prev => ({ ...prev, timeout: parseInt(e.target.value) }))}
                margin="normal"
                disabled={!llmConfig.enabled}
              />

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<TestConnection />}
                  onClick={() => handleTestConnection('llm')}
                  disabled={!llmConfig.enabled || testing}
                >
                  Test Connection
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* NAS Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Storage sx={{ mr: 1 }} />
                <Typography variant="h6">NAS Configuration</Typography>
                <Chip 
                  label={nasConfig.enabled ? 'Enabled' : 'Disabled'} 
                  color={nasConfig.enabled ? 'success' : 'default'}
                  size="small"
                  sx={{ ml: 'auto' }}
                />
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={nasConfig.enabled}
                    onChange={(e) => setNasConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                  />
                }
                label="Enable NAS Mount"
              />

              <TextField
                fullWidth
                label="NAS Server"
                value={nasConfig.server}
                onChange={(e) => setNasConfig(prev => ({ ...prev, server: e.target.value }))}
                margin="normal"
                disabled={!nasConfig.enabled}
              />

              <TextField
                fullWidth
                label="Share Path"
                value={nasConfig.path}
                onChange={(e) => setNasConfig(prev => ({ ...prev, path: e.target.value }))}
                margin="normal"
                disabled={!nasConfig.enabled}
              />

              <TextField
                fullWidth
                label="Mount Point"
                value={nasConfig.mountPoint}
                onChange={(e) => setNasConfig(prev => ({ ...prev, mountPoint: e.target.value }))}
                margin="normal"
                disabled={!nasConfig.enabled}
              />

              <TextField
                fullWidth
                label="Username"
                value={nasConfig.username}
                onChange={(e) => setNasConfig(prev => ({ ...prev, username: e.target.value }))}
                margin="normal"
                disabled={!nasConfig.enabled}
              />

              <TextField
                fullWidth
                label="Password"
                type="password"
                value={nasConfig.password}
                onChange={(e) => setNasConfig(prev => ({ ...prev, password: e.target.value }))}
                margin="normal"
                disabled={!nasConfig.enabled}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={nasConfig.autoMount}
                    onChange={(e) => setNasConfig(prev => ({ ...prev, autoMount: e.target.checked }))}
                    disabled={!nasConfig.enabled}
                  />
                }
                label="Auto-mount on startup"
              />

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<TestConnection />}
                  onClick={() => handleTestConnection('nas')}
                  disabled={!nasConfig.enabled || testing}
                >
                  Test Connection
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* Email Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                <Email sx={{ mr: 1 }} />
                <Typography variant="h6">Email Integration</Typography>
                <Chip 
                  label={emailConfig.enabled ? 'Enabled' : 'Disabled'} 
                  color={emailConfig.enabled ? 'success' : 'default'}
                  size="small"
                  sx={{ ml: 'auto' }}
                />
              </Box>

              <FormControlLabel
                control={
                  <Switch
                    checked={emailConfig.enabled}
                    onChange={(e) => setEmailConfig(prev => ({ ...prev, enabled: e.target.checked }))}
                  />
                }
                label="Enable Email Processing"
              />

              <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>IMAP Settings</Typography>
              
              <TextField
                fullWidth
                label="IMAP Host"
                value={emailConfig.imapHost}
                onChange={(e) => setEmailConfig(prev => ({ ...prev, imapHost: e.target.value }))}
                margin="normal"
                disabled={!emailConfig.enabled}
              />

              <TextField
                fullWidth
                label="IMAP Port"
                type="number"
                value={emailConfig.imapPort}
                onChange={(e) => setEmailConfig(prev => ({ ...prev, imapPort: parseInt(e.target.value) }))}
                margin="normal"
                disabled={!emailConfig.enabled}
              />

              <TextField
                fullWidth
                label="IMAP Username"
                value={emailConfig.imapUsername}
                onChange={(e) => setEmailConfig(prev => ({ ...prev, imapUsername: e.target.value }))}
                margin="normal"
                disabled={!emailConfig.enabled}
              />

              <TextField
                fullWidth
                label="IMAP Password"
                type="password"
                value={emailConfig.imapPassword}
                onChange={(e) => setEmailConfig(prev => ({ ...prev, imapPassword: e.target.value }))}
                margin="normal"
                disabled={!emailConfig.enabled}
              />

              <Typography variant="subtitle2" sx={{ mt: 2, mb: 1 }}>SMTP Settings</Typography>
              
              <TextField
                fullWidth
                label="SMTP Host"
                value={emailConfig.smtpHost}
                onChange={(e) => setEmailConfig(prev => ({ ...prev, smtpHost: e.target.value }))}
                margin="normal"
                disabled={!emailConfig.enabled}
              />

              <TextField
                fullWidth
                label="SMTP Port"
                type="number"
                value={emailConfig.smtpPort}
                onChange={(e) => setEmailConfig(prev => ({ ...prev, smtpPort: parseInt(e.target.value) }))}
                margin="normal"
                disabled={!emailConfig.enabled}
              />

              <Box sx={{ mt: 2 }}>
                <Button
                  variant="outlined"
                  startIcon={<TestConnection />}
                  onClick={() => handleTestConnection('email')}
                  disabled={!emailConfig.enabled || testing}
                >
                  Test Connection
                </Button>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        {/* System Configuration */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
                             <Box sx={{ display: 'flex', alignItems: 'center', mb: 2 }}>
                 <SettingsIcon sx={{ mr: 1 }} />
                 <Typography variant="h6">System Configuration</Typography>
               </Box>

              <TextField
                fullWidth
                label="Max File Size (MB)"
                type="number"
                value={systemConfig.maxFileSize}
                onChange={(e) => setSystemConfig(prev => ({ ...prev, maxFileSize: parseInt(e.target.value) }))}
                margin="normal"
                InputProps={{
                  endAdornment: <InputAdornment position="end">MB</InputAdornment>,
                }}
              />

              <TextField
                fullWidth
                label="Processing Workers"
                type="number"
                value={systemConfig.processingWorkers}
                onChange={(e) => setSystemConfig(prev => ({ ...prev, processingWorkers: parseInt(e.target.value) }))}
                margin="normal"
                inputProps={{ min: 1, max: 16 }}
              />

              <TextField
                fullWidth
                label="Batch Size"
                type="number"
                value={systemConfig.batchSize}
                onChange={(e) => setSystemConfig(prev => ({ ...prev, batchSize: parseInt(e.target.value) }))}
                margin="normal"
                inputProps={{ min: 1, max: 100 }}
              />

              <TextField
                fullWidth
                label="Backup Retention (days)"
                type="number"
                value={systemConfig.backupRetention}
                onChange={(e) => setSystemConfig(prev => ({ ...prev, backupRetention: parseInt(e.target.value) }))}
                margin="normal"
                InputProps={{
                  endAdornment: <InputAdornment position="end">days</InputAdornment>,
                }}
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={systemConfig.enableCompression}
                    onChange={(e) => setSystemConfig(prev => ({ ...prev, enableCompression: e.target.checked }))}
                  />
                }
                label="Enable File Compression"
              />

              <FormControlLabel
                control={
                  <Switch
                    checked={systemConfig.enableEncryption}
                    onChange={(e) => setSystemConfig(prev => ({ ...prev, enableEncryption: e.target.checked }))}
                  />
                }
                label="Enable File Encryption"
              />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Buttons */}
      <Box sx={{ mt: 3, display: 'flex', gap: 2, justifyContent: 'flex-end' }}>
        <Button
          variant="outlined"
          startIcon={<Refresh />}
          onClick={() => window.location.reload()}
        >
          Reset
        </Button>
        <Button
          variant="contained"
          startIcon={<Save />}
          onClick={handleSave}
          disabled={saving}
        >
          {saving ? 'Saving...' : 'Save Settings'}
        </Button>
      </Box>
    </Box>
  );
};

export default Settings; 