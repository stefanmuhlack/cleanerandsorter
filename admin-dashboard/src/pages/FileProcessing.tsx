import React, { useState, useEffect } from 'react';
import {
  Box,
  Card,
  CardContent,
  Typography,
  Button,
  Grid,
  Chip,
  LinearProgress,
  Alert,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Tooltip,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow
} from '@mui/material';
import {
  CloudUpload,
  PlayArrow,
  Stop,
  Refresh,
  Delete,
  Undo,
  CheckCircle,
  Error,
  Info,
  Timeline,
  Storage,
  Psychology,
  Settings as SettingsIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';
import { useAppDispatch, useAppSelector } from '../store/hooks';
import { 
  uploadFiles, 
  processFiles, 
  stopProcessing,
  rollbackJob,
  fetchProcessingJobs,
  fetchProcessingStats
} from '../store/slices/fileProcessingSlice';



const FileProcessing: React.FC = () => {
  const dispatch = useAppDispatch();
  const { jobs, stats, loading, error } = useAppSelector(state => state.fileProcessing);
  
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [processingConfig, setProcessingConfig] = useState({
    enableDuplicateDetection: true,
    enableLLMClassification: true,
    enableRollback: true,
    maxConcurrentJobs: 4,
    targetDirectory: '/mnt/nas/documents'
  });
  const [rollbackDialog, setRollbackDialog] = useState<{
    open: boolean;
    jobId: string | null;
  }>({ open: false, jobId: null });

  useEffect(() => {
    dispatch(fetchProcessingJobs());
    dispatch(fetchProcessingStats());
  }, [dispatch]);

  const onDrop = (acceptedFiles: File[]) => {
    setSelectedFiles(prev => [...prev, ...acceptedFiles]);
  };

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx'],
      'image/*': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff'],
      'video/*': ['.mp4', '.mov', '.avi', '.mkv'],
      'text/plain': ['.txt']
    }
  });

  const handleUpload = async () => {
    if (selectedFiles.length === 0) return;
    
    const formData = new FormData();
    selectedFiles.forEach(file => {
      formData.append('files', file);
    });
    
    await dispatch(uploadFiles(selectedFiles));
    setSelectedFiles([]);
  };

  const handleProcess = async () => {
    await dispatch(processFiles(processingConfig));
  };

  const handleRollback = async (jobId: string) => {
    await dispatch(rollbackJob(jobId));
    setRollbackDialog({ open: false, jobId: null });
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed': return 'success';
      case 'processing': return 'info';
      case 'failed': return 'error';
      default: return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed': return <CheckCircle />;
      case 'processing': return <Timeline />;
      case 'failed': return <Error />;
      default: return <Info />;
    }
  };

  const formatFileSize = (bytes: number) => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        File Processing
      </Typography>

      {/* Configuration Panel */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <SettingsIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
            Processing Configuration
          </Typography>
          <Grid container spacing={2}>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                Processing Features
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 1 }}>
                <Chip 
                  label="Duplicate Detection" 
                  color={processingConfig.enableDuplicateDetection ? 'success' : 'default'}
                  icon={<Storage />}
                  onClick={() => setProcessingConfig(prev => ({
                    ...prev,
                    enableDuplicateDetection: !prev.enableDuplicateDetection
                  }))}
                />
                <Chip 
                  label="LLM Classification" 
                  color={processingConfig.enableLLMClassification ? 'success' : 'default'}
                  icon={<Psychology />}
                  onClick={() => setProcessingConfig(prev => ({
                    ...prev,
                    enableLLMClassification: !prev.enableLLMClassification
                  }))}
                />
                <Chip 
                  label="Enable Rollback" 
                  color={processingConfig.enableRollback ? 'success' : 'default'}
                  icon={<Storage />}
                  onClick={() => setProcessingConfig(prev => ({
                    ...prev,
                    enableRollback: !prev.enableRollback
                  }))}
                />
              </Box>
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="subtitle2" gutterBottom>
                Performance Settings
              </Typography>
              <Box sx={{ display: 'flex', flexDirection: 'column', gap: 2 }}>
                <Box>
                  <Typography variant="body2">Max Concurrent Jobs: {processingConfig.maxConcurrentJobs}</Typography>
                  <input
                    type="range"
                    min="1"
                    max="8"
                    value={processingConfig.maxConcurrentJobs}
                    onChange={(e) => setProcessingConfig(prev => ({
                      ...prev,
                      maxConcurrentJobs: parseInt(e.target.value)
                    }))}
                    style={{ width: '100%' }}
                  />
                </Box>
                <Box>
                  <Typography variant="body2">Target Directory: {processingConfig.targetDirectory}</Typography>
                </Box>
              </Box>
            </Grid>
          </Grid>
        </CardContent>
      </Card>

      {/* Statistics Panel */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Files
              </Typography>
              <Typography variant="h4">
                {stats?.totalFiles || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Processed
              </Typography>
              <Typography variant="h4" color="success.main">
                {stats?.processedFiles || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Duplicates Found
              </Typography>
              <Typography variant="h4" color="warning.main">
                {stats?.duplicatesFound || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>

      </Grid>

      {/* File Upload Area */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Typography variant="h6" gutterBottom>
            <CloudUpload sx={{ mr: 1, verticalAlign: 'middle' }} />
            Upload Files
          </Typography>
          
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: 3,
              textAlign: 'center',
              cursor: 'pointer',
              backgroundColor: isDragActive ? 'action.hover' : 'background.paper',
              transition: 'all 0.2s'
            }}
          >
            <input {...getInputProps()} />
            <CloudUpload sx={{ fontSize: 48, color: 'grey.400', mb: 2 }} />
            <Typography variant="h6" color="textSecondary">
              {isDragActive ? 'Drop files here' : 'Drag & drop files here, or click to select'}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Supports PDF, DOC, DOCX, XLS, XLSX, images, videos, and text files
            </Typography>
          </Box>

          {selectedFiles.length > 0 && (
            <Box sx={{ mt: 2 }}>
              <Typography variant="subtitle2" gutterBottom>
                Selected Files ({selectedFiles.length})
              </Typography>
              <List dense>
                {selectedFiles.map((file, index) => (
                  <ListItem key={index}>
                    <ListItemText
                      primary={file.name}
                      secondary={`${formatFileSize(file.size)} - ${file.type}`}
                    />
                    <ListItemSecondaryAction>
                      <IconButton
                        edge="end"
                        onClick={() => setSelectedFiles(prev => prev.filter((_, i) => i !== index))}
                      >
                        <Delete />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
              
              <Box sx={{ mt: 2, display: 'flex', gap: 2 }}>
                <Button
                  variant="contained"
                  startIcon={<CloudUpload />}
                  onClick={handleUpload}
                  disabled={loading}
                >
                  Upload Files
                </Button>
                <Button
                  variant="outlined"
                  startIcon={<PlayArrow />}
                  onClick={handleProcess}
                  disabled={loading || selectedFiles.length === 0}
                >
                  Process Files
                </Button>
              </Box>
            </Box>
          )}
        </CardContent>
      </Card>

      {/* Processing Jobs */}
      <Card>
        <CardContent>
          <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 2 }}>
            <Typography variant="h6">
              Processing Jobs
            </Typography>
            <Button
              startIcon={<Refresh />}
              onClick={() => dispatch(fetchProcessingJobs())}
              disabled={loading}
            >
              Refresh
            </Button>
          </Box>

          {error && (
            <Alert severity="error" sx={{ mb: 2 }}>
              {error}
            </Alert>
          )}

          {loading && <LinearProgress sx={{ mb: 2 }} />}

          <TableContainer component={Paper}>
            <Table>
              <TableHead>
                <TableRow>
                  <TableCell>Job ID</TableCell>
                  <TableCell>Status</TableCell>
                  <TableCell>Files</TableCell>
                  <TableCell>Progress</TableCell>
                  <TableCell>Created</TableCell>
                  <TableCell>Actions</TableCell>
                </TableRow>
              </TableHead>
              <TableBody>
                {(Array.isArray(jobs) ? jobs : []).map((job: any) => (
                  <TableRow key={job.id}>
                    <TableCell>{job.id}</TableCell>
                    <TableCell>
                      <Chip
                        label={job.status}
                        color={getStatusColor(job.status) as any}
                        icon={getStatusIcon(job.status)}
                        size="small"
                      />
                    </TableCell>
                    <TableCell>
                      <Typography variant="body2">
                        {job.filename}
                      </Typography>
                      {job.isDuplicate && (
                        <Typography variant="caption" color="warning.main">
                          Duplicate detected
                        </Typography>
                      )}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', alignItems: 'center' }}>
                        <Box sx={{ width: '100%', mr: 1 }}>
                          <LinearProgress 
                            variant="determinate" 
                            value={job.progress} 
                            color={job.status === 'failed' ? 'error' : 'primary'}
                          />
                        </Box>
                        <Typography variant="body2" color="textSecondary">
                          {Math.round(job.progress)}%
                        </Typography>
                      </Box>
                    </TableCell>
                    <TableCell>
                      {new Date(job.startTime).toLocaleString()}
                    </TableCell>
                    <TableCell>
                      <Box sx={{ display: 'flex', gap: 1 }}>
                        {job.status === 'processing' && (
                          <Tooltip title="Stop Processing">
                            <IconButton
                              size="small"
                              onClick={() => dispatch(stopProcessing())}
                            >
                              <Stop />
                            </IconButton>
                          </Tooltip>
                        )}
                        {job.status === 'completed' && (
                          <Tooltip title="Rollback Job">
                            <IconButton
                              size="small"
                              onClick={() => setRollbackDialog({ open: true, jobId: job.id })}
                            >
                              <Undo />
                            </IconButton>
                          </Tooltip>
                        )}
                      </Box>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </TableContainer>
        </CardContent>
      </Card>

      {/* Rollback Confirmation Dialog */}
      <Dialog
        open={rollbackDialog.open}
        onClose={() => setRollbackDialog({ open: false, jobId: null })}
      >
        <DialogTitle>Confirm Rollback</DialogTitle>
        <DialogContent>
          <Typography>
            Are you sure you want to rollback this processing job? This will:
          </Typography>
          <List dense>
            <ListItem>
              <ListItemText primary="• Move processed files back to their original locations" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• Remove database entries for processed documents" />
            </ListItem>
            <ListItem>
              <ListItemText primary="• Restore the system to the state before processing" />
            </ListItem>
          </List>
          <Alert severity="warning" sx={{ mt: 2 }}>
            This action cannot be undone!
          </Alert>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setRollbackDialog({ open: false, jobId: null })}>
            Cancel
          </Button>
          <Button
            color="error"
            variant="contained"
            onClick={() => rollbackDialog.jobId && handleRollback(rollbackDialog.jobId)}
          >
            Rollback
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FileProcessing; 