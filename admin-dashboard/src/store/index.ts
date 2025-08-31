import { configureStore } from '@reduxjs/toolkit';
import statisticsReducer from './slices/statisticsSlice';
import fileProcessingReducer from './slices/fileProcessingSlice';
import sortingRulesReducer from './slices/sortingRulesSlice';
import classificationReviewReducer from './slices/classificationReviewSlice';

export const store = configureStore({
  reducer: {
    statistics: statisticsReducer,
    fileProcessing: fileProcessingReducer,
    sortingRules: sortingRulesReducer,
    classificationReview: classificationReviewReducer,
  },
  middleware: (getDefaultMiddleware) =>
    getDefaultMiddleware({
      serializableCheck: {
        ignoredActions: ['persist/PERSIST'],
      },
    }),
});

export type RootState = ReturnType<typeof store.getState>;
export type AppDispatch = typeof store.dispatch; 