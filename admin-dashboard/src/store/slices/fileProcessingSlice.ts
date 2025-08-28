import { createSlice, PayloadAction } from '@reduxjs/toolkit';

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
}

interface FileProcessingState {
  files: FileItem[];
  isProcessing: boolean;
  isPaused: boolean;
  settings: {
    enableOCR: boolean;
    extractMetadata: boolean;
    generateThumbnails: boolean;
    maxFileSize: number;
    allowedTypes: string[];
  };
}

const initialState: FileProcessingState = {
  files: [],
  isProcessing: false,
  isPaused: false,
  settings: {
    enableOCR: true,
    extractMetadata: true,
    generateThumbnails: true,
    maxFileSize: 100,
    allowedTypes: ['pdf', 'doc', 'docx', 'jpg', 'png', 'txt'],
  },
};

const fileProcessingSlice = createSlice({
  name: 'fileProcessing',
  initialState,
  reducers: {
    addFiles: (state, action: PayloadAction<FileItem[]>) => {
      state.files.push(...action.payload);
    },
    updateFileStatus: (state, action: PayloadAction<{ id: string; status: FileItem['status']; progress?: number; error?: string }>) => {
      const file = state.files.find(f => f.id === action.payload.id);
      if (file) {
        file.status = action.payload.status;
        if (action.payload.progress !== undefined) {
          file.progress = action.payload.progress;
        }
        if (action.payload.error !== undefined) {
          file.error = action.payload.error;
        }
        if (action.payload.status === 'completed') {
          file.processedAt = new Date();
        }
      }
    },
    removeFile: (state, action: PayloadAction<string>) => {
      state.files = state.files.filter(f => f.id !== action.payload);
    },
    setProcessing: (state, action: PayloadAction<boolean>) => {
      state.isProcessing = action.payload;
    },
    setPaused: (state, action: PayloadAction<boolean>) => {
      state.isPaused = action.payload;
    },
    updateSettings: (state, action: PayloadAction<Partial<FileProcessingState['settings']>>) => {
      state.settings = { ...state.settings, ...action.payload };
    },
    clearFiles: (state) => {
      state.files = [];
    },
  },
});

export const {
  addFiles,
  updateFileStatus,
  removeFile,
  setProcessing,
  setPaused,
  updateSettings,
  clearFiles,
} = fileProcessingSlice.actions;

export default fileProcessingSlice.reducer; 