import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
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
  LinearProgress,
  IconButton,
  Tooltip,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  Email as EmailIcon,
  Refresh as RefreshIcon,
  PlayArrow as StartIcon,
  Stop as StopIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Upload as UploadIcon,
  Delete as DeleteIcon,
  Edit as EditIcon
} from '@mui/icons-material';

interface EmailAccount {
  name: string;
  imap_host: string;
  imap_port: number;
  imap_username: string;
  enabled: boolean;
  last_processed: string;
  status: 'active' | 'inactive' | 'error';
}

interface EmailFilter {
  name: string;
  enabled: boolean;
  filter_subject: string[];
  filter_from: string[];
  filter_attachment_types: string[];
  actions: string[];
}

interface ProcessingTask {
  id: string;
  account: string;
  status: 'processing' | 'completed' | 'failed';
  emails_processed: number;
  emails_failed: number;
  attachments_processed: number;
  attachments_failed: number;
  started_at: string;
  completed_at?: string;
  error?: string;
}

interface OTRSExport {
  id: string;
  status: 'processing' | 'completed' | 'failed';
  total_tickets: number;
  processed_tickets: number;
  failed_tickets: number;
  attachments_downloaded: number;
  classification_results: number;
  created_at: string;
  export_path?: string;
}

const EmailIntegration: React.FC = () => {
  const [emailAccounts, setEmailAccounts] = useState<EmailAccount[]>([]);
  const [emailFilters, setEmailFilters] = useState<EmailFilter[]>([]);
  const [processingTasks, setProcessingTasks] = useState<ProcessingTask[]>([]);
  const [otrsExports, setOtrsExports] = useState<OTRSExport[]>([]);
  const [loading, setLoading] = useState(false);
  const [selectedAccount, setSelectedAccount] = useState<string>('');
  const [processingDialog, setProcessingDialog] = useState(false);
  const [exportDialog, setExportDialog] = useState(false);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);

  // Mock data for demonstration
  useEffect(() => {
    setEmailAccounts([
      {
        name: 'OTRS Support',
        imap_host: 'mail.company.com',
        imap_port: 993,
        imap_username: 'support@company.com',
        enabled: true,
        last_processed: '2024-01-15T10:30:00Z',
        status: 'active'
      },
      {
        name: 'Vertrieb',
        imap_host: 'mail.company.com',
        imap_port: 993,
        imap_username: 'vertrieb@company.com',
        enabled: true,
        last_processed: '2024-01-15T09:15:00Z',
        status: 'active'
      },
      {
        name: 'General Support',
        imap_host: 'mail.company.com',
        imap_port: 993,
        imap_username: 'support@company.com',
        enabled: false,
        last_processed: '2024-01-14T16:45:00Z',
        status: 'inactive'
      }
    ]);

    setEmailFilters([
      {
        name: 'Support Tickets',
        enabled: true,
        filter_subject: ['support', 'ticket', 'help'],
        filter_from: ['support@', 'help@'],
        filter_attachment_types: ['pdf', 'doc', 'docx'],
        actions: ['tag', 'correspondent', 'delete']
      },
      {
        name: 'Invoice Attachments',
        enabled: true,
        filter_subject: ['rechnung', 'invoice', 'bill'],
        filter_from: ['billing@', 'finance@'],
        filter_attachment_types: ['pdf', 'doc', 'docx'],
        actions: ['tag', 'correspondent']
      }
    ]);

    setProcessingTasks([
      {
        id: 'task_1',
        account: 'OTRS Support',
        status: 'completed',
        emails_processed: 15,
        emails_failed: 0,
        attachments_processed: 23,
        attachments_failed: 1,
        started_at: '2024-01-15T10:00:00Z',
        completed_at: '2024-01-15T10:05:00Z'
      },
      {
        id: 'task_2',
        account: 'Vertrieb',
        status: 'processing',
        emails_processed: 8,
        emails_failed: 1,
        attachments_processed: 12,
        attachments_failed: 0,
        started_at: '2024-01-15T10:30:00Z'
      }
    ]);

    setOtrsExports([
      {
        id: 'export_1',
        status: 'completed',
        total_tickets: 45,
        processed_tickets: 43,
        failed_tickets: 2,
        attachments_downloaded: 67,
        classification_results: 43,
        created_at: '2024-01-15T09:00:00Z',
        export_path: '/mnt/nas/otrs-exports/export_20240115_090000'
      }
    ]);
  }, []);

  const handleStartProcessing = async (accountName: string) => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      const newTask: ProcessingTask = {
        id: `task_${Date.now()}`,
        account: accountName,
        status: 'processing',
        emails_processed: 0,
        emails_failed: 0,
        attachments_processed: 0,
        attachments_failed: 0,
        started_at: new Date().toISOString()
      };
      
      setProcessingTasks(prev => [newTask, ...prev]);
      setMessage({ type: 'success', text: `Started processing for ${accountName}` });
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to start processing' });
    } finally {
      setLoading(false);
      setProcessingDialog(false);
    }
  };

  const handleStartOTRSExport = async () => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      const newExport: OTRSExport = {
        id: `export_${Date.now()}`,
        status: 'processing',
        total_tickets: 0,
        processed_tickets: 0,
        failed_tickets: 0,
        attachments_downloaded: 0,
        classification_results: 0,
        created_at: new Date().toISOString()
      };
      
      setOtrsExports(prev => [newExport, ...prev]);
      setMessage({ type: 'success', text: 'OTRS export started' });
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Failed to start OTRS export' });
    } finally {
      setLoading(false);
      setExportDialog(false);
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return <SuccessIcon color="success" />;
      case 'processing':
        return <WarningIcon color="warning" />;
      case 'failed':
      case 'error':
        return <ErrorIcon color="error" />;
      default:
        return <WarningIcon color="disabled" />;
    }
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'active':
      case 'completed':
        return 'success';
      case 'processing':
        return 'warning';
      case 'failed':
      case 'error':
        return 'error';
      default:
        return 'default';
    }
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <EmailIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Email Integration
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
        {/* Email Accounts */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Email Accounts</Typography>
                <Button
                  startIcon={<RefreshIcon />}
                  onClick={() => setMessage({ type: 'info', text: 'Refreshed email accounts' })}
                >
                  Refresh
                </Button>
              </Box>
              
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell>Account</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Last Processed</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {emailAccounts.map((account) => (
                      <TableRow key={account.name}>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {getStatusIcon(account.status)}
                            <Typography sx={{ ml: 1 }}>{account.name}</Typography>
                          </Box>
                        </TableCell>
                        <TableCell>
                          <Chip 
                            label={account.status} 
                            color={getStatusColor(account.status) as any}
                            size="small"
                          />
                        </TableCell>
                        <TableCell>
                          {new Date(account.last_processed).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          <Tooltip title="Start Processing">
                            <IconButton
                              size="small"
                              onClick={() => {
                                setSelectedAccount(account.name);
                                setProcessingDialog(true);
                              }}
                              disabled={!account.enabled}
                            >
                              <StartIcon />
                            </IconButton>
                          </Tooltip>
                          <Tooltip title="Settings">
                            <IconButton size="small">
                              <SettingsIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* Email Filters */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" gutterBottom>Email Filters</Typography>
              
              {emailFilters.map((filter) => (
                <Accordion key={filter.name} sx={{ mb: 1 }}>
                  <AccordionSummary expandIcon={<ExpandMoreIcon />}>
                    <Box sx={{ display: 'flex', alignItems: 'center', width: '100%' }}>
                      <Switch
                        checked={filter.enabled}
                        size="small"
                        sx={{ mr: 1 }}
                      />
                      <Typography>{filter.name}</Typography>
                      <Chip 
                        label={filter.enabled ? 'Active' : 'Inactive'} 
                        color={filter.enabled ? 'success' : 'default'}
                        size="small"
                        sx={{ ml: 'auto' }}
                      />
                    </Box>
                  </AccordionSummary>
                  <AccordionDetails>
                    <Grid container spacing={2}>
                      <Grid item xs={6}>
                        <Typography variant="subtitle2">Subject Keywords:</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {filter.filter_subject.map((keyword) => (
                            <Chip key={keyword} label={keyword} size="small" />
                          ))}
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="subtitle2">From Keywords:</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {filter.filter_from.map((keyword) => (
                            <Chip key={keyword} label={keyword} size="small" />
                          ))}
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="subtitle2">File Types:</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {filter.filter_attachment_types.map((type) => (
                            <Chip key={type} label={type} size="small" />
                          ))}
                        </Box>
                      </Grid>
                      <Grid item xs={6}>
                        <Typography variant="subtitle2">Actions:</Typography>
                        <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                          {filter.actions.map((action) => (
                            <Chip key={action} label={action} size="small" />
                          ))}
                        </Box>
                      </Grid>
                    </Grid>
                  </AccordionDetails>
                </Accordion>
              ))}
            </CardContent>
          </Card>
        </Grid>

        {/* Processing Tasks */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">Processing Tasks</Typography>
                <Button
                  startIcon={<HistoryIcon />}
                  onClick={() => setMessage({ type: 'info', text: 'Refreshed processing tasks' })}
                >
                  Refresh
                </Button>
              </Box>
              
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Task ID</TableCell>
                      <TableCell>Account</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Emails Processed</TableCell>
                      <TableCell>Attachments Processed</TableCell>
                      <TableCell>Started</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {processingTasks.map((task) => (
                      <TableRow key={task.id}>
                        <TableCell>{task.id}</TableCell>
                        <TableCell>{task.account}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {getStatusIcon(task.status)}
                            <Chip 
                              label={task.status} 
                              color={getStatusColor(task.status) as any}
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          </Box>
                        </TableCell>
                        <TableCell>
                          {task.emails_processed} / {task.emails_processed + task.emails_failed}
                        </TableCell>
                        <TableCell>
                          {task.attachments_processed} / {task.attachments_processed + task.attachments_failed}
                        </TableCell>
                        <TableCell>
                          {new Date(task.started_at).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          {task.status === 'processing' && (
                            <Tooltip title="Stop Processing">
                              <IconButton size="small" color="error">
                                <StopIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="View Details">
                            <IconButton size="small">
                              <SettingsIcon />
                            </IconButton>
                          </Tooltip>
                        </TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </CardContent>
          </Card>
        </Grid>

        {/* OTRS Integration */}
        <Grid item xs={12}>
          <Card>
            <CardContent>
              <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', mb: 2 }}>
                <Typography variant="h6">OTRS Integration</Typography>
                <Button
                  variant="contained"
                  startIcon={<DownloadIcon />}
                  onClick={() => setExportDialog(true)}
                >
                  Start Export
                </Button>
              </Box>
              
              <TableContainer component={Paper} variant="outlined">
                <Table>
                  <TableHead>
                    <TableRow>
                      <TableCell>Export ID</TableCell>
                      <TableCell>Status</TableCell>
                      <TableCell>Tickets</TableCell>
                      <TableCell>Attachments</TableCell>
                      <TableCell>Classifications</TableCell>
                      <TableCell>Created</TableCell>
                      <TableCell>Actions</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {otrsExports.map((export_item) => (
                      <TableRow key={export_item.id}>
                        <TableCell>{export_item.id}</TableCell>
                        <TableCell>
                          <Box sx={{ display: 'flex', alignItems: 'center' }}>
                            {getStatusIcon(export_item.status)}
                            <Chip 
                              label={export_item.status} 
                              color={getStatusColor(export_item.status) as any}
                              size="small"
                              sx={{ ml: 1 }}
                            />
                          </Box>
                        </TableCell>
                        <TableCell>
                          {export_item.processed_tickets} / {export_item.total_tickets}
                        </TableCell>
                        <TableCell>{export_item.attachments_downloaded}</TableCell>
                        <TableCell>{export_item.classification_results}</TableCell>
                        <TableCell>
                          {new Date(export_item.created_at).toLocaleString()}
                        </TableCell>
                        <TableCell>
                          {export_item.status === 'completed' && (
                            <Tooltip title="Download Export">
                              <IconButton size="small">
                                <DownloadIcon />
                              </IconButton>
                            </Tooltip>
                          )}
                          <Tooltip title="Delete Export">
                            <IconButton size="small" color="error">
                              <DeleteIcon />
                            </IconButton>
                          </Tooltip>
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

      {/* Processing Dialog */}
      <Dialog open={processingDialog} onClose={() => setProcessingDialog(false)}>
        <DialogTitle>Start Email Processing</DialogTitle>
        <DialogContent>
          <Typography gutterBottom>
            Start processing emails for account: <strong>{selectedAccount}</strong>
          </Typography>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Folder</InputLabel>
            <Select value="INBOX" label="Folder">
              <MenuItem value="INBOX">INBOX</MenuItem>
              <MenuItem value="Sent">Sent</MenuItem>
              <MenuItem value="Archive">Archive</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Limit"
            type="number"
            defaultValue={50}
            sx={{ mt: 2 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setProcessingDialog(false)}>Cancel</Button>
          <Button 
            onClick={() => handleStartProcessing(selectedAccount)}
            disabled={loading}
            variant="contained"
          >
            {loading ? 'Starting...' : 'Start Processing'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Export Dialog */}
      <Dialog open={exportDialog} onClose={() => setExportDialog(false)}>
        <DialogTitle>Start OTRS Export</DialogTitle>
        <DialogContent>
          <FormControl fullWidth sx={{ mt: 2 }}>
            <InputLabel>Report Type</InputLabel>
            <Select value="renewal" label="Report Type">
              <MenuItem value="renewal">Renewal Report</MenuItem>
              <MenuItem value="billing">Billing Report</MenuItem>
              <MenuItem value="status">Status Report</MenuItem>
            </Select>
          </FormControl>
          <TextField
            fullWidth
            label="Start Date"
            type="date"
            defaultValue={new Date().toISOString().split('T')[0]}
            sx={{ mt: 2 }}
          />
          <TextField
            fullWidth
            label="End Date"
            type="date"
            defaultValue={new Date().toISOString().split('T')[0]}
            sx={{ mt: 2 }}
          />
          <FormControlLabel
            control={<Switch defaultChecked />}
            label="Include Attachments"
            sx={{ mt: 2 }}
          />
          <FormControlLabel
            control={<Switch defaultChecked />}
            label="Enable Classification"
            sx={{ mt: 1 }}
          />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setExportDialog(false)}>Cancel</Button>
          <Button 
            onClick={handleStartOTRSExport}
            disabled={loading}
            variant="contained"
          >
            {loading ? 'Starting...' : 'Start Export'}
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default EmailIntegration; 