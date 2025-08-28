import { createSlice, PayloadAction, createAsyncThunk } from '@reduxjs/toolkit';
import axios from 'axios';

interface ProcessingJob {
  id: string;
  name: string;
  status: 'pending' | 'processing' | 'completed' | 'failed';
  files: string[];
  processedFiles: string[];
  failedFiles: string[];
  duplicates: string[];
  createdAt: string;
  startedAt?: string;
  completedAt?: string;
  progress: number;
}

interface ProcessingStats {
  totalFiles: number;
  processedFiles: number;
  failedFiles: number;
  duplicateFiles: number;
  totalSize: number;
  averageProcessingTime: number;
  llmClassifications: number;
  rollbacks: number;
}

interface ProcessingConfig {
  enableDuplicateDetection: boolean;
  enableLLMClassification: boolean;
  enableBackup: boolean;
  maxWorkers: number;
  batchSize: number;
}

interface FileProcessingState {
  jobs: ProcessingJob[];
  stats: ProcessingStats | null;
  loading: boolean;
  error: string | null;
  processing: boolean;
  selectedFiles: File[];
}

const initialState: FileProcessingState = {
  jobs: [],
  stats: null,
  loading: false,
  error: null,
  processing: false,
  selectedFiles: []
};

// Async thunks
export const uploadFiles = createAsyncThunk(
  'fileProcessing/uploadFiles',
  async (formData: FormData) => {
    const response = await axios.post('/api/files/upload', formData, {
      headers: {
        'Content-Type': 'multipart/form-data',
      },
    });
    return response.data;
  }
);

export const processFiles = createAsyncThunk(
  'fileProcessing/processFiles',
  async (payload: { config: ProcessingConfig; files: string[] }) => {
    const response = await axios.post('/api/files/process', payload);
    return response.data;
  }
);

export const stopProcessing = createAsyncThunk(
  'fileProcessing/stopProcessing',
  async (jobId: string) => {
    const response = await axios.post(`/api/files/stop/${jobId}`);
    return response.data;
  }
);

export const rollbackJob = createAsyncThunk(
  'fileProcessing/rollbackJob',
  async (jobId: string) => {
    const response = await axios.post(`/api/files/rollback/${jobId}`);
    return response.data;
  }
);

export const fetchProcessingJobs = createAsyncThunk(
  'fileProcessing/fetchProcessingJobs',
  async () => {
    const response = await axios.get('/api/files/jobs');
    return response.data;
  }
);

export const fetchProcessingStats = createAsyncThunk(
  'fileProcessing/fetchProcessingStats',
  async () => {
    const response = await axios.get('/api/files/stats');
    return response.data;
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
    addSelectedFile: (state, action: PayloadAction<File>) => {
      state.selectedFiles.push(action.payload);
    },
    removeSelectedFile: (state, action: PayloadAction<string>) => {
      state.selectedFiles = state.selectedFiles.filter(
        file => file.name !== action.payload
      );
    },
    clearSelectedFiles: (state) => {
      state.selectedFiles = [];
    },
    updateJobProgress: (state, action: PayloadAction<{ jobId: string; progress: number }>) => {
      const job = state.jobs.find(j => j.id === action.payload.jobId);
      if (job) {
        job.progress = action.payload.progress;
      }
    },
    updateJobStatus: (state, action: PayloadAction<{ jobId: string; status: ProcessingJob['status'] }>) => {
      const job = state.jobs.find(j => j.id === action.payload.jobId);
      if (job) {
        job.status = action.payload.status;
        if (action.payload.status === 'processing' && !job.startedAt) {
          job.startedAt = new Date().toISOString();
        }
        if (action.payload.status === 'completed' || action.payload.status === 'failed') {
          job.completedAt = new Date().toISOString();
        }
      }
    }
  },
  extraReducers: (builder) => {
    // Upload files
    builder
      .addCase(uploadFiles.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(uploadFiles.fulfilled, (state, action) => {
        state.loading = false;
        // Handle successful upload
      })
      .addCase(uploadFiles.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Upload failed';
      });

    // Process files
    builder
      .addCase(processFiles.pending, (state) => {
        state.loading = true;
        state.processing = true;
        state.error = null;
      })
      .addCase(processFiles.fulfilled, (state, action) => {
        state.loading = false;
        state.processing = false;
        // Add new job to the list
        if (action.payload.job) {
          state.jobs.unshift(action.payload.job);
        }
      })
      .addCase(processFiles.rejected, (state, action) => {
        state.loading = false;
        state.processing = false;
        state.error = action.error.message || 'Processing failed';
      });

    // Stop processing
    builder
      .addCase(stopProcessing.pending, (state) => {
        state.loading = true;
      })
      .addCase(stopProcessing.fulfilled, (state, action) => {
        state.loading = false;
        // Update job status
        const job = state.jobs.find(j => j.id === action.payload.jobId);
        if (job) {
          job.status = 'failed';
          job.completedAt = new Date().toISOString();
        }
      })
      .addCase(stopProcessing.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to stop processing';
      });

    // Rollback job
    builder
      .addCase(rollbackJob.pending, (state) => {
        state.loading = true;
      })
      .addCase(rollbackJob.fulfilled, (state, action) => {
        state.loading = false;
        // Remove job from list or mark as rolled back
        state.jobs = state.jobs.filter(j => j.id !== action.payload.jobId);
      })
      .addCase(rollbackJob.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Rollback failed';
      });

    // Fetch processing jobs
    builder
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
      });

    // Fetch processing stats
    builder
      .addCase(fetchProcessingStats.pending, (state) => {
        state.loading = true;
      })
      .addCase(fetchProcessingStats.fulfilled, (state, action) => {
        state.loading = false;
        state.stats = action.payload.stats || null;
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
  addSelectedFile,
  removeSelectedFile,
  clearSelectedFiles,
  updateJobProgress,
  updateJobStatus
} = fileProcessingSlice.actions;

export default fileProcessingSlice.reducer; 