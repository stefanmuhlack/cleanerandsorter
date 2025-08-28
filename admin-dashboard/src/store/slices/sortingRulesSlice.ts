import { createSlice, PayloadAction } from '@reduxjs/toolkit';

interface SortingRule {
  id: string;
  name: string;
  description: string;
  priority: number;
  enabled: boolean;
  conditions: {
    keywords: string[];
    fileTypes: string[];
    minSize?: number;
    maxSize?: number;
  };
  actions: {
    targetPath: string;
    createSubfolders: boolean;
    renameFile: boolean;
    addTags: string[];
  };
  statistics: {
    matches: number;
    lastUsed: Date;
    successRate: number;
  };
}

interface SortingRulesState {
  rules: SortingRule[];
  loading: boolean;
  error: string | null;
  selectedRule: SortingRule | null;
}

const initialState: SortingRulesState = {
  rules: [
    {
      id: '1',
      name: 'Rechnungen',
      description: 'Sortiert Rechnungen und Finanzdokumente',
      priority: 90,
      enabled: true,
      conditions: {
        keywords: ['rechnung', 'invoice', 'bill', 'zahlung', 'payment'],
        fileTypes: ['pdf', 'doc', 'docx'],
        minSize: 1024,
        maxSize: 10485760
      },
      actions: {
        targetPath: '/finanzen/rechnungen',
        createSubfolders: true,
        renameFile: false,
        addTags: ['finanzen', 'rechnung']
      },
      statistics: {
        matches: 156,
        lastUsed: new Date('2024-01-15'),
        successRate: 98.5
      }
    },
    {
      id: '2',
      name: 'Verträge',
      description: 'Sortiert Verträge und rechtliche Dokumente',
      priority: 85,
      enabled: true,
      conditions: {
        keywords: ['vertrag', 'contract', 'agreement', 'vereinbarung'],
        fileTypes: ['pdf', 'doc', 'docx'],
        minSize: 1024
      },
      actions: {
        targetPath: '/recht/vertraege',
        createSubfolders: true,
        renameFile: true,
        addTags: ['recht', 'vertrag']
      },
      statistics: {
        matches: 89,
        lastUsed: new Date('2024-01-14'),
        successRate: 95.2
      }
    }
  ],
  loading: false,
  error: null,
  selectedRule: null,
};

const sortingRulesSlice = createSlice({
  name: 'sortingRules',
  initialState,
  reducers: {
    setLoading: (state, action: PayloadAction<boolean>) => {
      state.loading = action.payload;
    },
    setError: (state, action: PayloadAction<string | null>) => {
      state.error = action.payload;
    },
    addRule: (state, action: PayloadAction<SortingRule>) => {
      state.rules.push(action.payload);
    },
    updateRule: (state, action: PayloadAction<SortingRule>) => {
      const index = state.rules.findIndex(rule => rule.id === action.payload.id);
      if (index !== -1) {
        state.rules[index] = action.payload;
      }
    },
    deleteRule: (state, action: PayloadAction<string>) => {
      state.rules = state.rules.filter(rule => rule.id !== action.payload);
    },
    toggleRule: (state, action: PayloadAction<string>) => {
      const rule = state.rules.find(r => r.id === action.payload);
      if (rule) {
        rule.enabled = !rule.enabled;
      }
    },
    setSelectedRule: (state, action: PayloadAction<SortingRule | null>) => {
      state.selectedRule = action.payload;
    },
    updateRulePriority: (state, action: PayloadAction<{ id: string; priority: number }>) => {
      const rule = state.rules.find(r => r.id === action.payload.id);
      if (rule) {
        rule.priority = action.payload.priority;
      }
    },
  },
});

export const {
  setLoading,
  setError,
  addRule,
  updateRule,
  deleteRule,
  toggleRule,
  setSelectedRule,
  updateRulePriority,
} = sortingRulesSlice.actions;

export default sortingRulesSlice.reducer; 