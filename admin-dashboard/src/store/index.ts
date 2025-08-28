import { configureStore } from '@reduxjs/toolkit';
import statisticsReducer from './slices/statisticsSlice';
import fileProcessingReducer from './slices/fileProcessingSlice';
import sortingRulesReducer from './slices/sortingRulesSlice';

export const store = configureStore({
  reducer: {
    statistics: statisticsReducer,
    fileProcessing: fileProcessingReducer,
    sortingRules: sortingRulesReducer,
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