import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

interface Statistics {
  totalFiles: number;
  processedFiles: number;
  pendingFiles: number;
  failedFiles: number;
  totalStorage: number;
  storageUsed: number;
  recentActivity: Array<{
    timestamp: string;
    action: string;
    fileCount: number;
  }>;
  filesByType: Array<{
    type: string;
    count: number;
  }>;
  processingRate: number;
  averageProcessingTime: number;
}

interface StatisticsState {
  statistics: Statistics | null;
  loading: boolean;
  error: string | null;
}

const initialState: StatisticsState = {
  statistics: null,
  loading: false,
  error: null,
};

// Async thunk for fetching statistics
export const fetchStatistics = createAsyncThunk(
  'statistics/fetchStatistics',
  async () => {
    try {
      const response = await fetch('/api/statistics');
      if (!response.ok) {
        throw new Error('Failed to fetch statistics');
      }
      const data = await response.json();
      return data;
    } catch (error) {
      throw new Error(error instanceof Error ? error.message : 'Unknown error');
    }
  }
);

const statisticsSlice = createSlice({
  name: 'statistics',
  initialState,
  reducers: {
    setStatistics: (state, action: PayloadAction<Statistics>) => {
      state.statistics = action.payload;
      state.loading = false;
      state.error = null;
    },
    clearStatistics: (state) => {
      state.statistics = null;
      state.loading = false;
      state.error = null;
    },
  },
  extraReducers: (builder) => {
    builder
      .addCase(fetchStatistics.pending, (state) => {
        state.loading = true;
        state.error = null;
      })
      .addCase(fetchStatistics.fulfilled, (state, action) => {
        state.loading = false;
        state.statistics = action.payload;
        state.error = null;
      })
      .addCase(fetchStatistics.rejected, (state, action) => {
        state.loading = false;
        state.error = action.error.message || 'Failed to fetch statistics';
      });
  },
});

export const { setStatistics, clearStatistics } = statisticsSlice.actions;
export default statisticsSlice.reducer; 