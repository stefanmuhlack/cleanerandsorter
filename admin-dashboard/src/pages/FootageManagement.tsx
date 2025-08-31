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
  Tab,
  Checkbox
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
  Sort as SortIcon,
  FolderOpen as FolderOpenIcon
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
  const [uploadSelectedFile, setUploadSelectedFile] = useState<File | null>(null);
  const [uploadQueue, setUploadQueue] = useState<File[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadQueueProgress, setUploadQueueProgress] = useState<Record<string, number>>({});
  const [searchDialog, setSearchDialog] = useState(false);
  const [selectedFile, setSelectedFile] = useState<MediaFile | null>(null);
  const [viewMode, setViewMode] = useState<'grid' | 'list'>('grid');
  const [currentTab, setCurrentTab] = useState(0);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(20);
  const [total, setTotal] = useState(0);
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning'; text: string } | null>(null);
  const [generateThumbnail, setGenerateThumbnail] = useState(true);
  const [extractMetadata, setExtractMetadata] = useState(true);
  const [enableClassification, setEnableClassification] = useState(true);
  const [selectedIds, setSelectedIds] = useState<Set<string>>(new Set());
  const [filterCustomer, setFilterCustomer] = useState<string>('');
  const [filterProject, setFilterProject] = useState<string>('');
  const [filterCategory, setFilterCategory] = useState<string>('');
  const [filterFileType, setFilterFileType] = useState<string>('');
  const [uploadProgress, setUploadProgress] = useState<number>(0);
  const [sortBy, setSortBy] = useState<string>('created_at');
  const [sortDir, setSortDir] = useState<'asc' | 'desc'>('desc');
  const [importDialog, setImportDialog] = useState(false);
  const [importUrl, setImportUrl] = useState('http://cas_storage_manager:8000');
  const [importShare, setImportShare] = useState<any>({ url: 'file:///mnt/nas', policy: { read: true } });
  const [importPath, setImportPath] = useState<string>('');
  const [importEntries, setImportEntries] = useState<any[]>([]);
  const [importSelection, setImportSelection] = useState<Set<string>>(new Set());
  const [importBusy, setImportBusy] = useState(false);

  const buildQuery = () => {
    const params = new URLSearchParams();
    params.set('limit', String(pageSize));
    params.set('offset', String((page - 1) * pageSize));
    if (filterCustomer) params.set('customer', filterCustomer);
    if (filterProject) params.set('project', filterProject);
    if (filterCategory) params.set('category', filterCategory);
    if (filterFileType) params.set('file_type', filterFileType);
    if (sortBy) params.set('sort_by', sortBy);
    if (sortDir) params.set('sort_dir', sortDir);
    return params.toString();
  };

  useEffect(() => {
    const load = async () => {
      setLoading(true);
      try {
        const token = localStorage.getItem('token');
        const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
        const resFiles = await fetch(`/api/footage/files?${buildQuery()}`, { headers });
        const dataFiles = resFiles.ok ? await resFiles.json() : { items: [], total: 0 } as any;
        setMediaFiles(Array.isArray(dataFiles.items) ? dataFiles.items : []);
        setTotal(typeof dataFiles.total === 'number' ? dataFiles.total : 0);
        const resStats = await fetch('/api/footage/statistics', { headers });
        const dataStats = resStats.ok ? await resStats.json() : null;
        setStatistics(dataStats);
      } catch (e) {
        setMessage({ type: 'error', text: 'Failed to load media files' });
        setMediaFiles([]);
        setStatistics(null);
      } finally {
        setLoading(false);
      }
    };
    load();
  }, [page, pageSize, filterCustomer, filterProject, filterCategory, filterFileType, sortBy, sortDir]);

  // Prefetch thumbnails
  const [thumbUrls, setThumbUrls] = useState<Record<string, string>>({});
  useEffect(() => {
    let aborted = false;
    const token = localStorage.getItem('token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
    const controller = new AbortController();
    const fetchThumb = async (id: string) => {
      try {
        const res = await fetch(`/api/footage/files/${encodeURIComponent(id)}/thumbnail`, { headers, signal: controller.signal });
        if (!res.ok) return;
        const blob = await res.blob();
        if (aborted) return;
        const url = URL.createObjectURL(blob);
        setThumbUrls(prev => ({ ...prev, [id]: url }));
      } catch {}
    };
    setThumbUrls(prev => {
      Object.values(prev).forEach(u => URL.revokeObjectURL(u));
      return {};
    });
    mediaFiles
      .filter(f => f && (f.file_type === 'image' || f.file_type === 'video'))
      .forEach(f => fetchThumb(f.id));
    return () => {
      aborted = true;
      controller.abort();
      setThumbUrls(prev => {
        Object.values(prev).forEach(u => URL.revokeObjectURL(u));
        return prev;
      });
    };
  }, [mediaFiles]);

  const handleUpload = async (request: UploadRequest) => {
    setLoading(true);
    try {
      // If queue has items, perform batch upload; else single upload
      const token = localStorage.getItem('token');
      if (uploadQueue.length > 0) {
        setUploading(true);
        const perFileProgress: Record<string, number> = {};
        setUploadQueueProgress({});
        for (const f of uploadQueue) {
          perFileProgress[f.name] = 0;
          setUploadQueueProgress({ ...perFileProgress });
          await new Promise<void>((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            xhr.open('POST', '/api/footage/upload', true);
            if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
            xhr.upload.onprogress = (e) => {
              if (e.lengthComputable) {
                perFileProgress[f.name] = Math.round((e.loaded / e.total) * 100);
                setUploadQueueProgress({ ...perFileProgress });
              }
            };
            xhr.onreadystatechange = () => {
              if (xhr.readyState === 4) {
                if (xhr.status >= 200 && xhr.status < 300) resolve();
                else reject(new Error(`HTTP ${xhr.status}`));
              }
            };
            const form = new FormData();
            form.append('file', f);
            if (request.customer) form.append('customer', request.customer);
            if (request.project) form.append('project', request.project);
            if (request.category) form.append('category', request.category);
            if (request.tags && request.tags.length) form.append('tags', request.tags.join(','));
            form.append('generate_thumbnail', String(request.generate_thumbnail));
            form.append('extract_metadata', String(request.extract_metadata));
            form.append('enable_classification', String(request.enable_classification));
            xhr.send(form);
          });
        }
        setMessage({ type: 'success', text: `Uploaded ${uploadQueue.length} file(s)` });
        setUploadQueue([]);
        setUploadQueueProgress({});
        setUploading(false);
      } else {
        if (!uploadSelectedFile) {
          setMessage({ type: 'warning', text: 'Please select a file to upload.' });
          return;
        }
        setUploadProgress(0);
        const url = '/api/footage/upload';
        await new Promise<void>((resolve, reject) => {
          const xhr = new XMLHttpRequest();
          xhr.open('POST', url, true);
          if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
          xhr.upload.onprogress = (e) => {
            if (e.lengthComputable) setUploadProgress(Math.round((e.loaded / e.total) * 100));
          };
          xhr.onreadystatechange = () => {
            if (xhr.readyState === 4) {
              if (xhr.status >= 200 && xhr.status < 300) resolve();
              else reject(new Error(`HTTP ${xhr.status}`));
            }
          };
          const form = new FormData();
          form.append('file', uploadSelectedFile);
          if (request.customer) form.append('customer', request.customer);
          if (request.project) form.append('project', request.project);
          if (request.category) form.append('category', request.category);
          if (request.tags && request.tags.length) form.append('tags', request.tags.join(','));
          form.append('generate_thumbnail', String(request.generate_thumbnail));
          form.append('extract_metadata', String(request.extract_metadata));
          form.append('enable_classification', String(request.enable_classification));
          xhr.send(form);
        });
        setMessage({ type: 'success', text: 'File uploaded successfully' });
        setUploadSelectedFile(null);
      }
      setUploadDialog(false);
      // refresh current page
      const token2 = localStorage.getItem('token');
      const headers2 = token2 ? { 'Authorization': `Bearer ${token2}` } : undefined;
      const resFiles = await fetch(`/api/footage/files?${buildQuery()}`, { headers: headers2 });
      const dataFiles = resFiles.ok ? await resFiles.json() : { items: [], total: 0 } as any;
      setMediaFiles(Array.isArray(dataFiles.items) ? dataFiles.items : []);
      setTotal(typeof dataFiles.total === 'number' ? dataFiles.total : 0);
      
    } catch (error) {
      setMessage({ type: 'error', text: 'Upload failed' });
    } finally {
      setLoading(false);
      setUploadProgress(0);
    }
  };

  const handleSearch = async (request: SearchRequest) => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } as any;
      const res = await fetch('/api/footage/search', { method: 'POST', headers, body: JSON.stringify(request) });
      if (res.ok) {
        const data = await res.json();
        setMediaFiles(Array.isArray(data) ? data : []);
        setMessage({ type: 'success', text: 'Search completed' });
        setSearchDialog(false);
      } else {
        setMessage({ type: 'error', text: `Search failed (HTTP ${res.status})` });
      }
      
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

  const handleRefresh = async () => {
    const token = localStorage.getItem('token');
    const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
    try {
      setLoading(true);
      const resFiles = await fetch(`/api/footage/files?${buildQuery()}`, { headers });
      const dataFiles = resFiles.ok ? await resFiles.json() : { items: [], total: 0 };
      setMediaFiles(Array.isArray(dataFiles.items) ? dataFiles.items : []);
      const resStats = await fetch('/api/footage/statistics', { headers });
      const dataStats = resStats.ok ? await resStats.json() : null;
      setStatistics(dataStats);
    } catch {
      setMessage({ type: 'error', text: 'Refresh failed' });
    } finally {
      setLoading(false);
    }
  };

  const handleDownload = async (file: MediaFile) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
      const res = await fetch(`/api/footage/files/${encodeURIComponent(file.id)}/download`, { headers });
      if (!res.ok) {
        setMessage({ type: 'error', text: `Download failed (HTTP ${res.status})` });
        return;
      }
      const blob = await res.blob();
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = file.filename;
      document.body.appendChild(a);
      a.click();
      a.remove();
      URL.revokeObjectURL(url);
    } catch {
      setMessage({ type: 'error', text: 'Download failed' });
    }
  };

  const handleDelete = async (file: MediaFile) => {
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
      const res = await fetch(`/api/footage/files/${encodeURIComponent(file.id)}`, { method: 'DELETE', headers });
      if (!res.ok) {
        setMessage({ type: 'error', text: `Delete failed (HTTP ${res.status})` });
        return;
      }
      setMessage({ type: 'success', text: 'File deleted' });
      setMediaFiles(prev => prev.filter(f => f.id !== file.id));
    } catch {
      setMessage({ type: 'error', text: 'Delete failed' });
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
            {thumbUrls[file.id] ? (
              // eslint-disable-next-line jsx-a11y/img-redundant-alt
              <img src={thumbUrls[file.id]} alt={file.filename} style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'cover', borderRadius: 4 }} />
            ) : (
              getFileTypeIcon(file.file_type)
            )}
          </Box>
          <ImageListItemBar
            title={file.filename}
            subtitle={`${formatFileSize(file.size)} • ${file.customer || 'Unknown'}`}
            actionIcon={
              <Box>
                <Checkbox
                  size="small"
                  checked={selectedIds.has(file.id)}
                  onChange={(e) => {
                    setSelectedIds(prev => {
                      const next = new Set(prev);
                      if (e.target.checked) next.add(file.id); else next.delete(file.id);
                      return next;
                    });
                  }}
                  sx={{ color: 'white' }}
                />
                <Tooltip title="View Details">
                  <IconButton
                    size="small"
                    onClick={() => setSelectedFile(file)}
                  >
                    <ViewIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Download">
                  <IconButton size="small" onClick={() => handleDownload(file)}>
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton size="small" color="error" onClick={() => handleDelete(file)}>
                    <DeleteIcon />
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
            <TableCell padding="checkbox">
              <Checkbox
                indeterminate={selectedIds.size > 0 && selectedIds.size < mediaFiles.length}
                checked={mediaFiles.length > 0 && selectedIds.size === mediaFiles.length}
                onChange={(e) => {
                  if (e.target.checked) setSelectedIds(new Set(mediaFiles.map(f => f.id)));
                  else setSelectedIds(new Set());
                }}
              />
            </TableCell>
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
              <TableCell padding="checkbox">
                <Checkbox
                  checked={selectedIds.has(file.id)}
                  onChange={(e) => {
                    setSelectedIds(prev => {
                      const next = new Set(prev);
                      if (e.target.checked) next.add(file.id); else next.delete(file.id);
                      return next;
                    });
                  }}
                />
              </TableCell>
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
                  <IconButton size="small" onClick={() => handleDownload(file)}>
                    <DownloadIcon />
                  </IconButton>
                </Tooltip>
                <Tooltip title="Delete">
                  <IconButton size="small" color="error" onClick={() => handleDelete(file)}>
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
          <Button
            startIcon={<FolderOpenIcon />}
            onClick={() => setImportDialog(true)}
          >
            Import from Share
          </Button>
          {selectedIds.size > 0 && (
            <>
              <Button color="error" startIcon={<DeleteIcon />} onClick={async () => {
                const token = localStorage.getItem('token');
                const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
                let ok = 0, fail = 0;
                for (const id of Array.from(selectedIds)) {
                  try {
                    const res = await fetch(`/api/footage/files/${encodeURIComponent(id)}`, { method: 'DELETE', headers });
                    if (res.ok) ok++; else fail++;
                  } catch { fail++; }
                }
                setMessage({ type: fail ? 'error' : 'success', text: `Deleted ${ok}, failed ${fail}` });
                setSelectedIds(new Set());
                handleRefresh();
              }}>Delete Selected</Button>
              <Button startIcon={<DownloadIcon />} onClick={async () => {
                const token = localStorage.getItem('token');
                const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
                for (const id of Array.from(selectedIds)) {
                  const f = mediaFiles.find(x => x.id === id);
                  if (!f) continue;
                  try {
                    const res = await fetch(`/api/footage/files/${encodeURIComponent(id)}/download`, { headers });
                    if (!res.ok) continue;
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url; a.download = f.filename; document.body.appendChild(a); a.click(); a.remove();
                    URL.revokeObjectURL(url);
                  } catch {}
                }
              }}>Download Selected</Button>
            </>
          )}
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
          <IconButton onClick={handleRefresh}>
            <RefreshIcon />
          </IconButton>
        </Box>
      </Box>

      {/* Sort/Filter Controls */}
      <Box sx={{ display: 'flex', gap: 2, mb: 2 }}>
        <FormControl size="small">
          <InputLabel>Sort By</InputLabel>
          <Select label="Sort By" value={sortBy} onChange={(e) => setSortBy(e.target.value)}>
            <MenuItem value="created_at">Created</MenuItem>
            <MenuItem value="updated_at">Updated</MenuItem>
            <MenuItem value="size">Size</MenuItem>
            <MenuItem value="filename">Filename</MenuItem>
          </Select>
        </FormControl>
        <FormControl size="small">
          <InputLabel>Direction</InputLabel>
          <Select label="Direction" value={sortDir} onChange={(e) => setSortDir(e.target.value as any)}>
            <MenuItem value="asc">Ascending</MenuItem>
            <MenuItem value="desc">Descending</MenuItem>
          </Select>
        </FormControl>
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
      
      {!loading && mediaFiles.length === 0 && (
        <Alert severity="info" sx={{ mb: 2 }}>No media files found.</Alert>
      )}
      {viewMode === 'grid' ? renderGridView() : renderListView()}

      {/* Pagination */}
      <Box sx={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', mt: 3 }}>
        <Typography variant="body2">{total} items</Typography>
        <Box sx={{ display: 'flex', alignItems: 'center', gap: 2 }}>
          <FormControl size="small">
            <InputLabel>Page Size</InputLabel>
            <Select label="Page Size" value={pageSize} onChange={(e) => { setPageSize(Number(e.target.value)); setPage(1); }}>
              <MenuItem value={10}>10</MenuItem>
              <MenuItem value={20}>20</MenuItem>
              <MenuItem value={50}>50</MenuItem>
              <MenuItem value={100}>100</MenuItem>
            </Select>
          </FormControl>
          <Pagination 
            count={Math.max(1, Math.ceil(total / pageSize))} 
            page={page} 
            onChange={(_, newPage) => setPage(newPage)}
          />
        </Box>
      </Box>

      {/* Upload Dialog */}
      <Dialog open={uploadDialog} onClose={() => setUploadDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Upload Media File</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <Grid container spacing={2}>
                <Grid item xs={12} md={6}>
                  <Button
                    variant="outlined"
                    component="label"
                    fullWidth
                    sx={{ height: 100 }}
                  >
                    <UploadIcon sx={{ fontSize: 40, mb: 1 }} />
                    <Typography>{uploadSelectedFile ? uploadSelectedFile.name : 'Click to select file'}</Typography>
                    <input type="file" hidden onChange={(e) => setUploadSelectedFile(e.target.files && e.target.files[0] ? e.target.files[0] : null)} />
                  </Button>
                  {uploadProgress > 0 && (
                    <Box sx={{ mt: 1 }}>
                      <LinearProgress variant="determinate" value={uploadProgress} />
                      <Typography variant="caption">{uploadProgress}%</Typography>
                    </Box>
                  )}
                </Grid>
                <Grid item xs={12} md={6}>
                  <Button
                    variant="outlined"
                    component="label"
                    fullWidth
                    sx={{ height: 100 }}
                  >
                    <UploadIcon sx={{ fontSize: 40, mb: 1 }} />
                    <Typography>{uploadQueue.length ? `${uploadQueue.length} files queued` : 'Click to select multiple files'}</Typography>
                    <input multiple type="file" hidden onChange={(e) => {
                      const files = Array.from(e.target.files || []);
                      setUploadQueue(files);
                    }} />
                  </Button>
                  {uploading && (
                    <Box sx={{ mt: 1, maxHeight: 120, overflow: 'auto' }}>
                      {uploadQueue.map(f => (
                        <Box key={f.name} sx={{ mb: 1 }}>
                          <Typography variant="caption">{f.name}</Typography>
                          <LinearProgress variant="determinate" value={uploadQueueProgress[f.name] || 0} />
                        </Box>
                      ))}
                    </Box>
                  )}
                </Grid>
              </Grid>
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

      {/* Import from Share Dialog */}
      <Dialog open={importDialog} onClose={() => setImportDialog(false)} maxWidth="md" fullWidth>
        <DialogTitle>Import from External Share</DialogTitle>
        <DialogContent>
          <Grid container spacing={2} sx={{ mt: 1 }}>
            <Grid item xs={12}>
              <TextField fullWidth label="Storage Manager URL" value={importUrl} onChange={(e) => setImportUrl(e.target.value)} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Share URL (smb://, file://, davs://, https://...sharepoint)"
                value={importShare.url}
                onChange={(e) => setImportShare({ ...importShare, url: e.target.value })}
              />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth label="Username" value={importShare.credentials?.username || ''}
                onChange={(e) => setImportShare({ ...importShare, credentials: { ...(importShare.credentials || {}), username: e.target.value } })} />
            </Grid>
            <Grid item xs={6}>
              <TextField fullWidth label="Password" type="password" value={importShare.credentials?.password || ''}
                onChange={(e) => setImportShare({ ...importShare, credentials: { ...(importShare.credentials || {}), password: e.target.value } })} />
            </Grid>
            <Grid item xs={12}>
              <TextField fullWidth label="Base Path (optional)" value={importShare.base_path || ''}
                onChange={(e) => setImportShare({ ...importShare, base_path: e.target.value })} />
            </Grid>
            <Grid item xs={12}>
              <Box sx={{ display: 'flex', gap: 1 }}>
                <Button disabled={importBusy} onClick={async () => {
                  try {
                    const res = await fetch(`${importUrl.replace(/\/$/, '')}/detect`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(importShare) });
                    const data = await res.json();
                    setMessage({ type: data.supported ? 'success' : 'warning', text: `Detected: ${data.type}${data.supported ? '' : ' (not supported)'}` });
                  } catch (e: any) {
                    setMessage({ type: 'error', text: `Detect failed: ${e.message}` });
                  }
                }}>Detect</Button>
                <Button disabled={importBusy} onClick={async () => {
                  try {
                    const res = await fetch(`${importUrl.replace(/\/$/, '')}/test`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify(importShare) });
                    const ok = res.ok; const data = await res.json().catch(() => ({}));
                    setMessage({ type: ok ? 'success' : 'error', text: ok ? 'Share test successful' : `Share test failed: ${data.detail || res.status}` });
                  } catch (e: any) {
                    setMessage({ type: 'error', text: `Share test failed: ${e.message}` });
                  }
                }}>Test</Button>
                <TextField fullWidth label="Path" value={importPath} onChange={(e) => setImportPath(e.target.value)} />
                <Button disabled={importBusy} onClick={async () => {
                  try {
                    setImportBusy(true);
                    const res = await fetch(`${importUrl.replace(/\/$/, '')}/list`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ share: importShare, path: importPath }) });
                    const data = await res.json();
                    setImportEntries(Array.isArray(data) ? data : []);
                  } catch (e: any) {
                    setMessage({ type: 'error', text: `List failed: ${e.message}` });
                    setImportEntries([]);
                  } finally {
                    setImportBusy(false);
                  }
                }}>Browse</Button>
              </Box>
            </Grid>
            <Grid item xs={12}>
              <TableContainer component={Paper} variant="outlined">
                <Table size="small">
                  <TableHead>
                    <TableRow>
                      <TableCell padding="checkbox"></TableCell>
                      <TableCell>Name</TableCell>
                      <TableCell>Dir</TableCell>
                      <TableCell>Size</TableCell>
                    </TableRow>
                  </TableHead>
                  <TableBody>
                    {importEntries.map((it) => (
                      <TableRow key={it.path}>
                        <TableCell padding="checkbox">
                          <Checkbox checked={importSelection.has(it.path)} onChange={(e) => setImportSelection(prev => { const next = new Set(prev); if (e.target.checked) next.add(it.path); else next.delete(it.path); return next; })} />
                        </TableCell>
                        <TableCell>{it.name}</TableCell>
                        <TableCell>{it.is_dir ? 'Yes' : 'No'}</TableCell>
                        <TableCell>{it.size}</TableCell>
                      </TableRow>
                    ))}
                  </TableBody>
                </Table>
              </TableContainer>
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setImportDialog(false)}>Cancel</Button>
          <Button disabled={importBusy || importSelection.size === 0} variant="contained" onClick={async () => {
            try {
              setImportBusy(true);
              const token = localStorage.getItem('token');
              const headers = { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } as any;
              const body = {
                storage_manager_url: importUrl,
                share: importShare,
                paths: Array.from(importSelection),
                customer: filterCustomer || undefined,
                project: filterProject || undefined,
                category: filterCategory || undefined,
                generate_thumbnail: true,
                extract_metadata: true,
                enable_classification: false
              };
              const res = await fetch('/api/footage/import-from-share', { method: 'POST', headers, body: JSON.stringify(body) });
              const data = await res.json();
              if (res.ok) {
                setMessage({ type: data.errors && data.errors.length ? 'warning' : 'success', text: `Imported ${data.imported?.length || 0}, errors ${data.errors?.length || 0}` });
                setImportDialog(false);
                setImportSelection(new Set());
                handleRefresh();
              } else {
                setMessage({ type: 'error', text: `Import failed: ${data.detail || res.status}` });
              }
            } catch (e: any) {
              setMessage({ type: 'error', text: `Import failed: ${e.message}` });
            } finally {
              setImportBusy(false);
            }
          }}>Start Import</Button>
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