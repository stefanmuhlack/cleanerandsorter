import { createSlice, createAsyncThunk, PayloadAction } from '@reduxjs/toolkit';

export interface ReviewItem {
  id: string;
  original_path: string;
  filename: string;
  size: number;
  mtime: number;
  suggested_category: string;
  confidence: number;
  customer?: string;
  project?: string;
  tags: string[];
  metadata: Record<string, any>;
}

interface ReviewState {
  items: ReviewItem[];
  loading: boolean;
  error: string | null;
}

const initialState: ReviewState = {
  items: [],
  loading: false,
  error: null,
};

export const fetchPendingReviews = createAsyncThunk('review/fetchPending', async () => {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/ingest/classification/pending', { headers: token ? { 'Authorization': `Bearer ${token}` } : undefined });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  const data = await res.json();
  return data.items as ReviewItem[];
});

export const confirmReview = createAsyncThunk('review/confirm', async (payload: { id: string; category: string }) => {
  const token = localStorage.getItem('token');
  const res = await fetch('/api/ingest/classification/confirm', { method: 'POST', headers: { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } as any, body: JSON.stringify(payload) });
  if (!res.ok) throw new Error(`HTTP ${res.status}`);
  return payload.id;
});

const classificationReviewSlice = createSlice({
  name: 'classificationReview',
  initialState,
  reducers: {},
  extraReducers: (builder) => {
    builder
      .addCase(fetchPendingReviews.pending, (state) => { state.loading = true; state.error = null; })
      .addCase(fetchPendingReviews.fulfilled, (state, action: PayloadAction<ReviewItem[]>) => { state.loading = false; state.items = action.payload; })
      .addCase(fetchPendingReviews.rejected, (state, action) => { state.loading = false; state.error = action.error.message || 'Failed to load reviews'; })
      .addCase(confirmReview.fulfilled, (state, action: PayloadAction<string>) => { state.items = state.items.filter(i => i.id !== action.payload); })
  }
});

export default classificationReviewSlice.reducer;


