import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

interface ProcessingJob {
  id?: string;
  filename?: string;
  status?: 'pending' | 'processing' | 'completed' | 'failed' | 'rolled_back' | string;
  progress?: number;
  startTime?: string;
  created_at?: string;
  endTime?: string;
  error?: string;
  targetPath?: string;
  classification?: string;
  isDuplicate?: boolean;
}

interface ProcessingStats {
  totalFiles: number;
  processedFiles: number;
  failedFiles: number;
  duplicatesFound: number;
  averageProcessingTime: number;
  lastProcessed: string;
}

interface ProcessingConfig {
  enableDuplicateDetection: boolean;
  enableLLMClassification: boolean;
  enableRollback: boolean;
  maxConcurrentJobs: number;
  targetDirectory: string;
}

interface FileProcessingState {
  jobs: ProcessingJob[];
  stats: ProcessingStats;
  config: ProcessingConfig;
  loading: boolean;
  error: string | null;
  processing: boolean;
  selectedFiles: File[];
  uploadedPaths: string[];
}

const initialState: FileProcessingState = {
  jobs: [],
  stats: {
    totalFiles: 0,
    processedFiles: 0,
    failedFiles: 0,
    duplicatesFound: 0,
    averageProcessingTime: 0,
    lastProcessed: ''
  },
  config: {
    enableDuplicateDetection: true,
    enableLLMClassification: true,
    enableRollback: true,
    maxConcurrentJobs: 5,
    targetDirectory: '/mnt/nas/documents'
  },
  loading: false,
  error: null,
  processing: false,
  selectedFiles: [],
  uploadedPaths: []
};

// Async thunks
export const uploadFiles = createAsyncThunk(
  'fileProcessing/uploadFiles',
  async (files: File[]) => {
    // Simulate API call
    const formData = new FormData();
    files.forEach(file => formData.append('files', file));
    
    const token = localStorage.getItem('token');
    const response = await fetch('/api/ingest/upload', {
      method: 'POST',
      body: formData,
      headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
    });
    
    if (!response.ok) {
      throw new Error('Upload failed');
    }
    
    return await response.json();
  }
);

export const processFiles = createAsyncThunk(
  'fileProcessing/processFiles',
  async (payload: { files: string[]; config?: Partial<ProcessingConfig> }) => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/ingest/processing/start', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        ...(token ? { 'Authorization': `Bearer ${token}` } : {})
      },
      body: JSON.stringify({ files: payload.files, ...(payload.config ? { config: payload.config } : {}) })
    });
    
    if (!response.ok) {
      throw new Error('Processing failed');
    }
    
    return await response.json();
  }
);

export const stopProcessing = createAsyncThunk(
  'fileProcessing/stopProcessing',
  async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/ingest/processing/stop', {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
    });
    
    if (!response.ok) {
      throw new Error('Stop processing failed');
    }
    
    return await response.json();
  }
);

export const rollbackJob = createAsyncThunk(
  'fileProcessing/rollbackJob',
  async (jobId: string) => {
    const token = localStorage.getItem('token');
    const response = await fetch(`/api/ingest/processing/rollback/${jobId}`, {
      method: 'POST',
      headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
    });
    
    if (!response.ok) {
      throw new Error('Rollback failed');
    }
    
    return await response.json();
  }
);

export const fetchProcessingJobs = createAsyncThunk(
  'fileProcessing/fetchJobs',
  async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/ingest/processing/jobs', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch jobs');
    }
    
    return await response.json();
  }
);

export const fetchProcessingStats = createAsyncThunk(
  'fileProcessing/fetchStats',
  async () => {
    const token = localStorage.getItem('token');
    const response = await fetch('/api/ingest/processing/stats', {
      headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
    });
    
    if (!response.ok) {
      throw new Error('Failed to fetch stats');
    }
    
    return await response.json();
  }
);

const fileProcessingSlice = createSlice({
  name: 'fileProcessing',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    setProcessing: (state, action: PayloadAction<boolean>) => {
      state.processing = action.payload;
    },
    setSelectedFiles: (state, action: PayloadAction<File[]>) => {
      state.selectedFiles = action.payload;
    },
    setUploadedPaths: (state, action: PayloadAction<string[]>) => {
      state.uploadedPaths = action.payload || [];
    },
    updateJobProgress: (state, action: PayloadAction<{ id: string; progress: number }>) => {
      const job = state.jobs.find(j => j.id === action.payload.id);
      if (job) {
        job.progress = action.payload.progress;
      }
    },
    updateJobStatus: (state, action: PayloadAction<{ id: string; status: ProcessingJob['status']; error?: string }>) => {
      const job = state.jobs.find(j => j.id === action.payload.id);
      if (job) {
        job.status = action.payload.status;
        if (action.payload.error) {
          job.error = action.payload.error;
        }
        if (action.payload.status === 'completed' || action.payload.status === 'failed') {
          job.endTime = new Date().toISOString();
        }
      }
    },
    updateConfig: (state, action: PayloadAction<Partial<ProcessingConfig>>) => {
      state.config = { ...state.config, ...action.payload };
    },
    clearJobs: (state) => {
      state.jobs = [];
    },
    removeJob: (state, action: PayloadAction<string>) => {
      state.jobs = state.jobs.filter(job => job.id !== action.payload);
    }
  },
  extraReducers: (builder) => {
    builder
      // Upload files
      .addCase(uploadFiles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadFiles.fulfilled, (state, action) => {
        state.loading = false;
        // Store uploaded file paths for subsequent processing
        state.uploadedPaths = action.payload?.files || [];
      })
      .addCase(uploadFiles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Upload failed';
      })
      
      // Process files
      .addCase(processFiles.pending, (state) => {
        state.processing = true;
        state.error = null;
      })
      .addCase(processFiles.fulfilled, (state, action) => {
        state.processing = false;
        if (action.payload?.batch?.files) {
          state.jobs = action.payload.batch.files;
        } else if (action.payload?.file) {
          state.jobs = [action.payload.file];
        } else if (Array.isArray(action.payload?.files)) {
          state.jobs = action.payload.files;
        }
      })
      .addCase(processFiles.rejected, (state, action) => {
        state.processing = false;
        state.error = action.error.message || 'Processing failed';
      })
      
      // Stop processing
      .addCase(stopProcessing.pending, (state) => {
        state.processing = false;
      })
      .addCase(stopProcessing.fulfilled, (state) => {
        state.processing = false;
      })
      .addCase(stopProcessing.rejected, (state, action) => {
        state.error = action.error.message || 'Stop processing failed';
      })
      
      // Rollback job
      .addCase(rollbackJob.pending, (state, action) => {
        const job = state.jobs.find(j => j.id === action.meta.arg);
        if (job) {
          job.status = 'processing';
        }
      })
      .addCase(rollbackJob.fulfilled, (state, action) => {
        const job = state.jobs.find(j => j.id === action.meta.arg);
        if (job) {
          job.status = 'rolled_back';
          job.endTime = new Date().toISOString();
        }
      })
      .addCase(rollbackJob.rejected, (state, action) => {
        state.error = action.error.message || 'Rollback failed';
      })
      
      // Fetch jobs
      .addCase(fetchProcessingJobs.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProcessingJobs.fulfilled, (state, action) => {
        state.loading = false;
        state.jobs = action.payload.jobs || [];
      })
      .addCase(fetchProcessingJobs.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch jobs';
      })
      
      // Fetch stats
      .addCase(fetchProcessingStats.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProcessingStats.fulfilled, (state, action) => {
        state.loading = false;
        const backend = action.payload || {};
        state.stats = {
          totalFiles: backend.total_files_processed ?? 0,
          processedFiles: backend.successful_files ?? 0,
          failedFiles: backend.failed_files ?? 0,
          duplicatesFound: backend.files_by_status?.duplicate ?? 0,
          averageProcessingTime: 0,
          lastProcessed: ''
        };
      })
      .addCase(fetchProcessingStats.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch stats';
      });
  }
});

export const {
  setLoading,
  setError,
  setProcessing,
  setSelectedFiles,
  updateJobProgress,
  updateJobStatus,
  updateConfig,
  clearJobs,
  removeJob
} = fileProcessingSlice.actions;

export default fileProcessingSlice.reducer; 