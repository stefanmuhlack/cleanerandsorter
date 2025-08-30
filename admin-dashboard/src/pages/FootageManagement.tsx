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
  AccordionDetails,
  ImageList,
  ImageListItem,
  ImageListItemBar,
  Pagination,
  Tabs,
  Tab
} from '@mui/material';
import {
  VideoLibrary as VideoIcon,
  Image as ImageIcon,
  Brush as DesignIcon,
  Upload as UploadIcon,
  Search as SearchIcon,
  Settings as SettingsIcon,
  History as HistoryIcon,
  CheckCircle as SuccessIcon,
  Error as ErrorIcon,
  Warning as WarningIcon,
  ExpandMore as ExpandMoreIcon,
  Download as DownloadIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Visibility as ViewIcon,
  Refresh as RefreshIcon,
  FilterList as FilterIcon,
  Sort as SortIcon
} from '@mui/icons-material';

interface MediaFile {
  id: string;
  filename: string;
  original_path: string;
  file_type: string;
  mime_type: string;
  size: number;
  hash: string;
  customer?: string;
  project?: string;
  category: string;
  tags: string[];
  metadata: Record<string, any>;
  thumbnail_path?: string;
  created_at: string;
  updated_at: string;
}

interface UploadRequest {
  customer?: string;
  project?: string;
  category?: string;
  tags?: string[];
  generate_thumbnail: boolean;
  extract_metadata: boolean;
  enable_classification: boolean;
}

interface SearchRequest {
  customer?: string;
  project?: string;
  category?: string;
  tags?: string[];
  file_type?: string;
  date_from?: string;
  date_to?: string;
  size_min?: number;
  size_max?: number;
}

interface Statistics {
  total_files: number;
  total_size: number;
  by_type: Record<string, number>;
  by_customer: Record<string, number>;
  by_category: Record<string, number>;
  recent_uploads: number;
}

const FootageManagement: React.FC = () => {
  const [mediaFiles, setMediaFiles] = useState<MediaFile[]>([]);
  const [statistics, setStatistics] = useState<Statistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [uploadDialog, setUploadDialog] = useState(false);
  const [searchDialog, setSearchDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<MediaFile | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [currentTab, setCurrentTab] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize] = useState(20);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info'; text: string } | null>(null);
  const [generateThumbnail, setGenerateThumbnail] = useState(true);
  const [extractMetadata, setExtractMetadata] = useState(true);
  const [enableClassification, setEnableClassification] = useState(true);

  // Mock data for demonstration
  useEffect(() => {
    setMediaFiles([
      {
        id: '1',
        filename: 'company_logo.png',
        original_path: '/mnt/nas/footage/client1/project1/company_logo.png',
        file_type: 'image',
        mime_type: 'image/png',
        size: 2048576,
        hash: 'abc123',
        customer: 'Client One',
        project: 'Branding',
        category: 'design_assets',
        tags: ['logo', 'branding', 'png'],
        metadata: { width: 1024, height: 768, format: 'PNG' },
        thumbnail_path: '/mnt/nas/thumbnails/1/abc123.jpg',
        created_at: '2024-01-15T10:00:00Z',
        updated_at: '2024-01-15T10:00:00Z'
      },
      {
        id: '2',
        filename: 'product_video.mp4',
        original_path: '/mnt/nas/footage/client2/project2/product_video.mp4',
        file_type: 'video',
        mime_type: 'video/mp4',
        size: 52428800,
        hash: 'def456',
        customer: 'Client Two',
        project: 'Marketing',
        category: 'marketing_materials',
        tags: ['video', 'product', 'marketing'],
        metadata: { width: 1920, height: 1080, duration: 120, fps: 30 },
        thumbnail_path: '/mnt/nas/thumbnails/2/def456.jpg',
        created_at: '2024-01-14T15:30:00Z',
        updated_at: '2024-01-14T15:30:00Z'
      },
      {
        id: '3',
        filename: 'website_design.psd',
        original_path: '/mnt/nas/footage/client1/project3/website_design.psd',
        file_type: 'design',
        mime_type: 'image/vnd.adobe.photoshop',
        size: 10485760,
        hash: 'ghi789',
        customer: 'Client One',
        project: 'Web Design',
        category: 'design_assets',
        tags: ['design', 'website', 'photoshop'],
        metadata: { layers: 15, resolution: 300 },
        created_at: '2024-01-13T09:15:00Z',
        updated_at: '2024-01-13T09:15:00Z'
      }
    ]);

    setStatistics({
      total_files: 156,
      total_size: 2147483648,
      by_type: {
        image: 89,
        video: 34,
        design: 23,
        document: 10
      },
      by_customer: {
        'Client One': 67,
        'Client Two': 45,
        'Client Three': 44
      },
      by_category: {
        design_assets: 45,
        marketing_materials: 38,
        raw_footage: 34,
        processed_footage: 29,
        documentation: 10
      },
      recent_uploads: 12
    });
  }, []);

  const handleUpload = async (request: UploadRequest) => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 3000));
      
      setMessage({ type: 'success', text: 'File uploaded successfully' });
      setUploadDialog(false);
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Upload failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async (request: SearchRequest) => {
    setLoading(true);
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 2000));
      
      setMessage({ type: 'success', text: 'Search completed' });
      setSearchDialog(false);
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Search failed' });
    } finally {
      setLoading(false);
    }
  };

  const formatFileSize = (bytes: number): string => {
    const sizes = ['Bytes', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 Bytes';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return Math.round(bytes / Math.pow(1024, i) * 100) / 100 + ' ' + sizes[i];
  };

  const getFileTypeIcon = (fileType: string) => {
    switch (fileType) {
      case 'image':
        return <ImageIcon />;
      case 'video':
        return <VideoIcon />;
      case 'design':
        return <DesignIcon />;
      default:
        return <ImageIcon />;
    }
  };

  const getFileTypeColor = (fileType: string) => {
    switch (fileType) {
      case 'image':
        return 'primary';
      case 'video':
        return 'secondary';
      case 'design':
        return 'success';
      default:
        return 'default';
    }
  };

  const renderGridView = () => (
    <ImageList cols={4} gap={16}>
      {mediaFiles.map((file) => (
        <ImageListItem key={file.id} sx={{ cursor: 'pointer' }}>
          <Box
            sx={{
              width: '100%',
              height: 200,
              bgcolor: 'grey.200',
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'center',
              borderRadius: 1
            }}
          >
            {getFileTypeIcon(file.file_type)}
          </Box>
          <ImageListItemBar
            title={file.filename}
            subtitle={`${formatFileSize(file.size)} • ${file.customer || 'Unknown'}`}
            actionIcon={
              <Box>
                <Tooltip title="View Details">
                  <IconButton
                    size="small"
                    onClick={() => setSelectedFile(file)}
                  >
                    <ViewIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download">
                  <IconButton size="small">
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
              </Box>
            }
          />
        </ImageListItem>
      ))}
    </ImageList>
  );

  const renderListView = () => (
    <TableContainer component={Paper} variant="outlined">
      <Table>
        <TableHead>
          <TableRow>
            <TableCell>File</TableCell>
            <TableCell>Type</TableCell>
            <TableCell>Size</TableCell>
            <TableCell>Customer</TableCell>
            <TableCell>Project</TableCell>
            <TableCell>Category</TableCell>
            <TableCell>Tags</TableCell>
            <TableCell>Created</TableCell>
            <TableCell>Actions</TableCell>
          </TableRow>
        </TableHead>
        <TableBody>
          {mediaFiles.map((file) => (
            <TableRow key={file.id}>
              <TableCell>
                <Box sx={{ display: 'flex', alignItems: 'center' }}>
                  {getFileTypeIcon(file.file_type)}
                  <Typography sx={{ ml: 1 }}>{file.filename}</Typography>
                </Box>
              </TableCell>
              <TableCell>
                <Chip 
                  label={file.file_type} 
                  color={getFileTypeColor(file.file_type) as any}
                  size="small"
                />
              </TableCell>
              <TableCell>{formatFileSize(file.size)}</TableCell>
              <TableCell>{file.customer || 'Unknown'}</TableCell>
              <TableCell>{file.project || 'Unknown'}</TableCell>
              <TableCell>
                <Chip label={file.category} size="small" />
              </TableCell>
              <TableCell>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                  {file.tags.slice(0, 3).map((tag) => (
                    <Chip key={tag} label={tag} size="small" />
                  ))}
                  {file.tags.length > 3 && (
                    <Chip label={`+${file.tags.length - 3}`} size="small" />
                  )}
                </Box>
              </TableCell>
              <TableCell>
                {new Date(file.created_at).toLocaleDateString()}
              </TableCell>
              <TableCell>
                <Tooltip title="View Details">
                  <IconButton
                    size="small"
                    onClick={() => setSelectedFile(file)}
                  >
                    <ViewIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download">
                  <IconButton size="small">
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
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
  );

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>
        <VideoIcon sx={{ mr: 1, verticalAlign: 'middle' }} />
        Footage Management
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

      {/* Statistics Cards */}
      <Grid container spacing={3} sx={{ mb: 3 }}>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Files
              </Typography>
              <Typography variant="h4">
                {statistics?.total_files || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Total Size
              </Typography>
              <Typography variant="h4">
                {statistics ? formatFileSize(statistics.total_size) : '0 B'}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Recent Uploads
              </Typography>
              <Typography variant="h4">
                {statistics?.recent_uploads || 0}
              </Typography>
            </CardContent>
          </Card>
        </Grid>
        <Grid item xs={12} md={3}>
          <Card>
            <CardContent>
              <Typography color="textSecondary" gutterBottom>
                Storage Used
              </Typography>
              <Typography variant="h4">
                75%
              </Typography>
              <LinearProgress variant="determinate" value={75} sx={{ mt: 1 }} />
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Action Bar */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mb: 3 }}>
        <Box sx={{ display: 'flex', gap: 1 }}>
          <Button
            variant="contained"
            startIcon={<UploadIcon />}
            onClick={() => setUploadDialog(true)}
          >
            Upload Media
          </Button>
          <Button
            startIcon={<SearchIcon />}
            onClick={() => setSearchDialog(true)}
          >
            Search
          </Button>
          <Button
            startIcon={<FilterIcon />}
          >
            Filter
          </Button>
        </Box>
        
        <Box sx={{ display: 'flex', gap: 1, alignItems: 'center' }}>
          <Button
            variant={viewMode === 'grid' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setViewMode('grid')}
          >
            Grid
          </Button>
          <Button
            variant={viewMode === 'list' ? 'contained' : 'outlined'}
            size="small"
            onClick={() => setViewMode('list')}
          >
            List
          </Button>
          <IconButton onClick={() => setMessage({ type: 'info', text: 'Refreshed' })}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Tabs */}
      <Box sx={{ borderBottom: 1, borderColor: 'divider', mb: 3 }}>
        <Tabs value={currentTab} onChange={(_, newValue) => setCurrentTab(newValue)}>
          <Tab label="All Media" />
          <Tab label="Images" />
          <Tab label="Videos" />
          <Tab label="Designs" />
          <Tab label="Recent" />
        </Tabs>
      </Box>

      {/* Content */}
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      
      {viewMode === 'grid' ? renderGridView() : renderListView()}

      {/* Pagination */}
      <Box sx={{ display: 'flex', justifyContent: 'center', mt: 3 }}>
        <Pagination 
          count={Math.ceil(mediaFiles.length / pageSize)} 
          page={page} 
          onChange={(_, newPage) => setPage(newPage)}
        />
      </Box>

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Upload Media File</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Button
                variant="outlined"
                component="label"
                fullWidth
                sx={{ height: 100 }}
              >
                <UploadIcon sx={{ fontSize: 40, mb: 1 }} />
                <Typography>Click to select file or drag and drop</Typography>
                <input type="file" hidden />
              </Button>
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Customer"
                placeholder="Enter customer name"
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Project"
                placeholder="Enter project name"
              />
            </Grid>
            <Grid item xs={12}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select label="Category">
                  <MenuItem value="raw_footage">Raw Footage</MenuItem>
                  <MenuItem value="processed_footage">Processed Footage</MenuItem>
                  <MenuItem value="design_assets">Design Assets</MenuItem>
                  <MenuItem value="marketing_materials">Marketing Materials</MenuItem>
                  <MenuItem value="documentation">Documentation</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Tags"
                placeholder="Enter tags separated by commas"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={generateThumbnail} onChange={(e) => setGenerateThumbnail(e.target.checked)} />}
                label="Generate Thumbnail"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={extractMetadata} onChange={(e) => setExtractMetadata(e.target.checked)} />}
                label="Extract Metadata"
              />
            </Grid>
            <Grid item xs={4}>
              <FormControlLabel
                control={<Switch checked={enableClassification} onChange={(e) => setEnableClassification(e.target.checked)} />}
                label="Auto Classify"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setUploadDialog(false)}>Cancel</Button>
          <Button 
            onClick={() => handleUpload({
              generate_thumbnail: generateThumbnail,
              extract_metadata: extractMetadata,
              enable_classification: enableClassification
            })}
            disabled={loading}
            variant="contained"
          >
            {loading ? 'Uploading...' : 'Upload'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Search Dialog */}
      <Dialog open={searchDialog} onClose={() => setSearchDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Search Media Files</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Customer"
                placeholder="Enter customer name"
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Project"
                placeholder="Enter project name"
              />
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>Category</InputLabel>
                <Select label="Category">
                  <MenuItem value="">All Categories</MenuItem>
                  <MenuItem value="raw_footage">Raw Footage</MenuItem>
                  <MenuItem value="processed_footage">Processed Footage</MenuItem>
                  <MenuItem value="design_assets">Design Assets</MenuItem>
                  <MenuItem value="marketing_materials">Marketing Materials</MenuItem>
                  <MenuItem value="documentation">Documentation</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <FormControl fullWidth>
                <InputLabel>File Type</InputLabel>
                <Select label="File Type">
                  <MenuItem value="">All Types</MenuItem>
                  <MenuItem value="image">Images</MenuItem>
                  <MenuItem value="video">Videos</MenuItem>
                  <MenuItem value="design">Designs</MenuItem>
                </Select>
              </FormControl>
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Date From"
                type="date"
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField
                fullWidth
                label="Date To"
                type="date"
                InputLabelProps={{ shrink: true }}
              />
            </Grid>
            <Grid item xs={12}>
              <TextField
                fullWidth
                label="Tags"
                placeholder="Enter tags separated by commas"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSearchDialog(false)}>Cancel</Button>
          <Button 
            onClick={() => handleSearch({})}
            disabled={loading}
            variant="contained"
          >
            {loading ? 'Searching...' : 'Search'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* File Details Dialog */}
      <Dialog open={!!selectedFile} onClose={() => setSelectedFile(null)} maxWidth="md" fullWidth>
        <DialogTitle>File Details</DialogTitle>
        <DialogContent>
          {selectedFile && (
            <Grid container spacing={2} sx={{ mt: 1 }}>
              <Grid item xs={12}>
                <Typography variant="h6">{selectedFile.filename}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography><strong>Type:</strong> {selectedFile.file_type}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography><strong>Size:</strong> {formatFileSize(selectedFile.size)}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography><strong>Customer:</strong> {selectedFile.customer || 'Unknown'}</Typography>
              </Grid>
              <Grid item xs={6}>
                <Typography><strong>Project:</strong> {selectedFile.project || 'Unknown'}</Typography>
              </Grid>
              <Grid item xs={12}>
                <Typography><strong>Tags:</strong></Typography>
                <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5, mt: 1 }}>
                  {selectedFile.tags.map((tag) => (
                    <Chip key={tag} label={tag} size="small" />
                  ))}
                </Box>
              </Grid>
              <Grid item xs={12}>
                <Typography><strong>Metadata:</strong></Typography>
                <Paper variant="outlined" sx={{ p: 2, mt: 1 }}>
                  <pre style={{ margin: 0, fontSize: '12px' }}>
                    {JSON.stringify(selectedFile.metadata, null, 2)}
                  </pre>
                </Paper>
              </Grid>
            </Grid>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setSelectedFile(null)}>Close</Button>
          <Button startIcon={<DownloadIcon />}>Download</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default FootageManagement; 