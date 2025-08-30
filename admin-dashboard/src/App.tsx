import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import { ThemeProvider, createTheme } from '@mui/material/styles';
import { CssBaseline } from '@mui/material';
import { Provider } from 'react-redux';
import { store } from './store/index';

// Import components
import Layout from './components/Layout';
import Dashboard from './pages/Dashboard';
import FileProcessing from './pages/FileProcessing';
import SortingRules from './pages/SortingRules';
import Statistics from './pages/Statistics';
import Settings from './pages/Settings';
import EmailIntegration from './pages/EmailIntegration';
import FootageManagement from './pages/FootageManagement';
import Monitoring from './pages/Monitoring';

const theme = createTheme({
  palette: {
    primary: {
      main: '#1976d2',
    },
    secondary: {
      main: '#dc004e',
    },
  },
  typography: {
    fontFamily: '"Roboto", "Helvetica", "Arial", sans-serif',
  },
  components: {
    MuiCard: {
      styleOverrides: {
        root: {
          boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
          borderRadius: 8,
        },
      },
    },
    MuiButton: {
      styleOverrides: {
        root: {
          textTransform: 'none',
          borderRadius: 6,
        },
      },
    },
  },
});

function App() {
  return (
    <Provider store={store}>
      <ThemeProvider theme={theme}>
        <CssBaseline />
        <Router>
          <Layout>
            <Routes>
              <Route path="/" element={<Dashboard />} />
              <Route path="/dashboard" element={<Dashboard />} />
              <Route path="/file-processing" element={<FileProcessing />} />
              <Route path="/sorting-rules" element={<SortingRules />} />
              <Route path="/statistics" element={<Statistics />} />
              <Route path="/email-integration" element={<EmailIntegration />} />
              <Route path="/footage-management" element={<FootageManagement />} />
              <Route path="/monitoring" element={<Monitoring />} />
              <Route path="/settings" element={<Settings />} />
            </Routes>
          </Layout>
        </Router>
      </ThemeProvider>
    </Provider>
  );
}

export default App; 