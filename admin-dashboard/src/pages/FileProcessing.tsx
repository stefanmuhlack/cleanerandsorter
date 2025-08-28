import React, { useState, useCallback } from 'react';
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
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails
} from '@mui/material';
import {
  CloudUpload as CloudUploadIcon,
  FileCopy as FileIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  PlayArrow as PlayIcon,
  Pause as PauseIcon,
  Stop as StopIcon,
  Delete as DeleteIcon,
  Refresh as RefreshIcon,
  Settings as SettingsIcon,
  ExpandMore as ExpandMoreIcon,
  Description as DocumentIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  TableChart as TableIcon,
  Archive as ArchiveIcon,
  VideoFile as VideoIcon,
  AudioFile as AudioIcon,
  Code as CodeIcon
} from '@mui/icons-material';
import { useDropzone } from 'react-dropzone';

interface FileItem {
  id: string;
  name: string;
  size: number;
  type: string;
  status: 'pending' | 'processing' | 'completed' | 'error';
  progress: number;
  uploadedAt: Date;
  processedAt?: Date;
  error?: string;
  preview?: string;
}

interface ProcessingStats {
  totalFiles: number;
  processedFiles: number;
  pendingFiles: number;
  failedFiles: number;
  processingRate: number;
  averageTime: number;
}

const FileProcessing: React.FC = () => {
  const [files, setFiles] = useState<FileItem[]>([]);
  const [processing, setProcessing] = useState(false);
  const [paused, setPaused] = useState(false);
  const [settingsOpen, setSettingsOpen] = useState(false);
  const [selectedFile, setSelectedFile] = useState<FileItem | null>(null);
  const [processingSettings, setProcessingSettings] = useState({
    enableOCR: true,
    extractMetadata: true,
    generateThumbnails: true,
    maxFileSize: 100,
    allowedTypes: ['pdf', 'doc', 'docx', 'jpg', 'png', 'txt']
  });

  const [stats, setStats] = useState<ProcessingStats>({
    totalFiles: 1247,
    processedFiles: 1180,
    pendingFiles: 45,
    failedFiles: 22,
    processingRate: 12.5,
    averageTime: 2.3
  });

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const newFiles: FileItem[] = acceptedFiles.map((file, index) => ({
      id: `file-${Date.now()}-${index}`,
      name: file.name,
      size: file.size,
      type: file.type,
      status: 'pending',
      progress: 0,
      uploadedAt: new Date(),
      preview: file.type.startsWith('image/') ? URL.createObjectURL(file) : undefined
    }));

    setFiles(prev => [...prev, ...newFiles]);
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'application/pdf': ['.pdf'],
      'application/msword': ['.doc'],
      'application/vnd.openxmlformats-officedocument.wordprocessingml.document': ['.docx'],
      'image/*': ['.jpg', '.jpeg', '.png', '.gif'],
      'text/plain': ['.txt'],
      'application/vnd.ms-excel': ['.xls'],
      'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet': ['.xlsx']
    },
    maxSize: processingSettings.maxFileSize * 1024 * 1024 // Convert MB to bytes
  });

  const getFileIcon = (type: string) => {
    if (type.includes('pdf')) return <PdfIcon />;
    if (type.includes('image')) return <ImageIcon />;
    if (type.includes('document') || type.includes('word')) return <DocumentIcon />;
    if (type.includes('spreadsheet') || type.includes('excel')) return <TableIcon />;
    if (type.includes('video')) return <VideoIcon />;
    if (type.includes('audio')) return <AudioIcon />;
    if (type.includes('text')) return <DocumentIcon />;
    if (type.includes('zip') || type.includes('rar')) return <ArchiveIcon />;
    if (type.includes('code') || type.includes('script')) return <CodeIcon />;
    return <FileIcon />;
  };

  const getStatusColor = (status: string) => {
    switch (status) {
      case 'completed':
        return 'success';
      case 'processing':
        return 'primary';
      case 'error':
        return 'error';
      case 'pending':
        return 'warning';
      default:
        return 'default';
    }
  };

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon />;
      case 'processing':
        return <PlayIcon />;
      case 'error':
        return <ErrorIcon />;
      case 'pending':
        return <WarningIcon />;
      default:
        return <FileIcon />;
    }
  };

  const formatBytes = (bytes: number): string => {
    if (bytes === 0) return '0 Bytes';
    const k = 1024;
    const sizes = ['Bytes', 'KB', 'MB', 'GB'];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
  };

  const handleStartProcessing = () => {
    setProcessing(true);
    setPaused(false);
    
    // Simulate processing
    const pendingFiles = files.filter(f => f.status === 'pending');
    pendingFiles.forEach((file, index) => {
      setTimeout(() => {
        setFiles(prev => prev.map(f => 
          f.id === file.id 
            ? { ...f, status: 'processing', progress: 0 }
            : f
        ));
        
        // Simulate progress
        const interval = setInterval(() => {
          setFiles(prev => prev.map(f => {
            if (f.id === file.id && f.status === 'processing') {
              const newProgress = f.progress + Math.random() * 20;
              if (newProgress >= 100) {
                clearInterval(interval);
                return {
                  ...f,
                  status: 'completed',
                  progress: 100,
                  processedAt: new Date()
                };
              }
              return { ...f, progress: newProgress };
            }
            return f;
          }));
        }, 500);
      }, index * 1000);
    });
  };

  const handlePauseProcessing = () => {
    setPaused(true);
  };

  const handleResumeProcessing = () => {
    setPaused(false);
  };

  const handleStopProcessing = () => {
    setProcessing(false);
    setPaused(false);
    setFiles(prev => prev.map(f => 
      f.status === 'processing' 
        ? { ...f, status: 'pending', progress: 0 }
        : f
    ));
  };

  const handleDeleteFile = (fileId: string) => {
    setFiles(prev => prev.filter(f => f.id !== fileId));
  };

  const handleRetryFile = (fileId: string) => {
    setFiles(prev => prev.map(f => 
      f.id === fileId 
        ? { ...f, status: 'pending', progress: 0, error: undefined }
        : f
    ));
  };

  const pendingFiles = files.filter(f => f.status === 'pending');
  const processingFiles = files.filter(f => f.status === 'processing');
  const completedFiles = files.filter(f => f.status === 'completed');
  const errorFiles = files.filter(f => f.status === 'error');

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Dateiverarbeitung
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Laden Sie Dateien hoch und verarbeiten Sie sie automatisch
          </Typography>
        </Box>
        <Box display="flex" gap={1}>
          <Button
            variant="outlined"
            startIcon={<SettingsIcon />}
            onClick={() => setSettingsOpen(true)}
          >
            Einstellungen
          </Button>
          <Button
            variant="outlined"
            startIcon={<RefreshIcon />}
            onClick={() => window.location.reload()}
          >
            Aktualisieren
          </Button>
        </Box>
      </Box>

      {/* Statistics Cards */}
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
                    Verarbeitet
                  </Typography>
                  <Typography variant="h4" component="div" color="success.main">
                    {stats.processedFiles.toLocaleString()}
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
                    Wartend
                  </Typography>
                  <Typography variant="h4" component="div" color="warning.main">
                    {pendingFiles.length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'warning.main' }}>
                  <WarningIcon />
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
                    Fehler
                  </Typography>
                  <Typography variant="h4" component="div" color="error.main">
                    {errorFiles.length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'error.main' }}>
                  <ErrorIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Upload Area */}
      <Card sx={{ mb: 3 }}>
        <CardContent>
          <Box
            {...getRootProps()}
            sx={{
              border: '2px dashed',
              borderColor: isDragActive ? 'primary.main' : 'grey.300',
              borderRadius: 2,
              p: 4,
              textAlign: 'center',
              cursor: 'pointer',
              bgcolor: isDragActive ? 'primary.50' : 'grey.50',
              transition: 'all 0.3s ease',
              '&:hover': {
                borderColor: 'primary.main',
                bgcolor: 'primary.50'
              }
            }}
          >
            <input {...getInputProps()} />
            <CloudUploadIcon sx={{ fontSize: 48, color: 'primary.main', mb: 2 }} />
            <Typography variant="h6" gutterBottom>
              {isDragActive ? 'Dateien hier ablegen' : 'Dateien hier ablegen oder klicken zum Auswählen'}
            </Typography>
            <Typography variant="body2" color="textSecondary">
              Unterstützte Formate: PDF, DOC, DOCX, JPG, PNG, TXT, XLS, XLSX
            </Typography>
            <Typography variant="caption" color="textSecondary" display="block" mt={1}>
              Maximale Dateigröße: {processingSettings.maxFileSize} MB
            </Typography>
          </Box>
        </CardContent>
      </Card>

      {/* Processing Controls */}
      {files.length > 0 && (
        <Card sx={{ mb: 3 }}>
          <CardContent>
            <Box display="flex" alignItems="center" justifyContent="space-between" mb={2}>
              <Typography variant="h6">
                Verarbeitungssteuerung
              </Typography>
              <Box display="flex" gap={1}>
                {!processing ? (
                  <Button
                    variant="contained"
                    startIcon={<PlayIcon />}
                    onClick={handleStartProcessing}
                    disabled={pendingFiles.length === 0}
                  >
                    Verarbeitung starten
                  </Button>
                ) : (
                  <>
                    {paused ? (
                      <Button
                        variant="outlined"
                        startIcon={<PlayIcon />}
                        onClick={handleResumeProcessing}
                      >
                        Fortsetzen
                      </Button>
                    ) : (
                      <Button
                        variant="outlined"
                        startIcon={<PauseIcon />}
                        onClick={handlePauseProcessing}
                      >
                        Pausieren
                      </Button>
                    )}
                    <Button
                      variant="outlined"
                      color="error"
                      startIcon={<StopIcon />}
                      onClick={handleStopProcessing}
                    >
                      Stoppen
                    </Button>
                  </>
                )}
              </Box>
            </Box>

            {processing && (
              <Box>
                <Typography variant="body2" color="textSecondary" mb={1}>
                  Verarbeitung läuft... {processingFiles.length} Dateien werden verarbeitet
                </Typography>
                <LinearProgress 
                  variant="determinate" 
                  value={(completedFiles.length / files.length) * 100}
                  sx={{ height: 8, borderRadius: 4 }}
                />
              </Box>
            )}
          </CardContent>
        </Card>
      )}

      {/* File List */}
      {files.length > 0 && (
        <Card>
          <CardContent>
            <Typography variant="h6" gutterBottom>
              Dateien ({files.length})
            </Typography>
            
            <List>
              {files.map((file) => (
                <React.Fragment key={file.id}>
                  <ListItem>
                    <ListItemIcon>
                      {getFileIcon(file.type)}
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1" fontWeight="medium">
                            {file.name}
                          </Typography>
                          <Chip
                            label={file.status}
                            color={getStatusColor(file.status) as any}
                            size="small"
                            icon={getStatusIcon(file.status)}
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary">
                            {formatBytes(file.size)} • {file.type} • {file.uploadedAt.toLocaleString()}
                          </Typography>
                          {file.status === 'processing' && (
                            <Box mt={1}>
                              <LinearProgress 
                                variant="determinate" 
                                value={file.progress}
                                sx={{ height: 4, borderRadius: 2 }}
                              />
                              <Typography variant="caption" color="textSecondary">
                                {file.progress.toFixed(1)}% abgeschlossen
                              </Typography>
                            </Box>
                          )}
                          {file.error && (
                            <Alert severity="error" sx={{ mt: 1 }}>
                              {file.error}
                            </Alert>
                          )}
                        </Box>
                      }
                    />
                    <Box display="flex" gap={1}>
                      {file.status === 'error' && (
                        <Tooltip title="Wiederholen">
                          <IconButton 
                            size="small" 
                            onClick={() => handleRetryFile(file.id)}
                          >
                            <RefreshIcon />
                          </IconButton>
                        </Tooltip>
                      )}
                      <Tooltip title="Löschen">
                        <IconButton 
                          size="small" 
                          color="error"
                          onClick={() => handleDeleteFile(file.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
            </List>
          </CardContent>
        </Card>
      )}

      {/* Settings Dialog */}
      <Dialog open={settingsOpen} onClose={() => setSettingsOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>Verarbeitungseinstellungen</DialogTitle>
        <DialogContent>
          <Grid container spacing={3}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Verarbeitungsoptionen
              </Typography>
              <FormControlLabel
                control={
                  <Switch
                    checked={processingSettings.enableOCR}
                    onChange={(e) => setProcessingSettings(prev => ({
                      ...prev,
                      enableOCR: e.target.checked
                    }))}
                  />
                }
                label="OCR aktivieren"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={processingSettings.extractMetadata}
                    onChange={(e) => setProcessingSettings(prev => ({
                      ...prev,
                      extractMetadata: e.target.checked
                    }))}
                  />
                }
                label="Metadaten extrahieren"
              />
              <FormControlLabel
                control={
                  <Switch
                    checked={processingSettings.generateThumbnails}
                    onChange={(e) => setProcessingSettings(prev => ({
                      ...prev,
                      generateThumbnails: e.target.checked
                    }))}
                  />
                }
                label="Thumbnails generieren"
              />
            </Grid>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Dateibeschränkungen
              </Typography>
              <TextField
                fullWidth
                label="Maximale Dateigröße (MB)"
                type="number"
                value={processingSettings.maxFileSize}
                onChange={(e) => setProcessingSettings(prev => ({
                  ...prev,
                  maxFileSize: parseInt(e.target.value)
                }))}
                sx={{ mb: 2 }}
              />
              <FormControl fullWidth>
                <InputLabel>Erlaubte Dateitypen</InputLabel>
                <Select
                  multiple
                  value={processingSettings.allowedTypes}
                  onChange={(e) => setProcessingSettings(prev => ({
                    ...prev,
                    allowedTypes: e.target.value as string[]
                  }))}
                  renderValue={(selected) => selected.join(', ')}
                >
                  <MenuItem value="pdf">PDF</MenuItem>
                  <MenuItem value="doc">DOC</MenuItem>
                  <MenuItem value="docx">DOCX</MenuItem>
                  <MenuItem value="jpg">JPG</MenuItem>
                  <MenuItem value="png">PNG</MenuItem>
                  <MenuItem value="txt">TXT</MenuItem>
                  <MenuItem value="xls">XLS</MenuItem>
                  <MenuItem value="xlsx">XLSX</MenuItem>
                </Select>
              </FormControl>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSettingsOpen(false)}>Abbrechen</Button>
          <Button variant="contained" onClick={() => setSettingsOpen(false)}>
            Speichern
          </Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FileProcessing; 