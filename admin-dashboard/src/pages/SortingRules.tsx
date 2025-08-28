import React, { useState } from 'react';
import {
  Box,
  Grid,
  Card,
  CardContent,
  Typography,
  Button,
  Chip,
  List,
  ListItem,
  ListItemText,
  ListItemIcon,
  IconButton,
  Tooltip,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  TextField,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Slider,
  Switch,
  FormControlLabel,
  Accordion,
  AccordionSummary,
  AccordionDetails,
  Alert,
  Divider,
  Paper,
  Avatar,
  Badge,
  Tabs,
  Tab
} from '@mui/material';
import {
  Add as AddIcon,
  Edit as EditIcon,
  Delete as DeleteIcon,
  PlayArrow as TestIcon,
  Save as SaveIcon,
  ExpandMore as ExpandMoreIcon,
  Rule as RuleIcon,
  Folder as FolderIcon,
  Description as DocumentIcon,
  Image as ImageIcon,
  PictureAsPdf as PdfIcon,
  TableChart as TableIcon,
  Archive as ArchiveIcon,
  VideoFile as VideoIcon,
  AudioFile as AudioIcon,
  Code as CodeIcon,
  Settings as SettingsIcon,
  Analytics as AnalyticsIcon,
  CheckCircle as CheckCircleIcon,
  Warning as WarningIcon,
  Error as ErrorIcon,
  DragIndicator as DragIcon
} from '@mui/icons-material';

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
    dateRange?: {
      from: Date;
      to: Date;
    };
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

const FileTypeIcons: { [key: string]: React.ReactElement } = {
  pdf: <PdfIcon />,
  doc: <DocumentIcon />,
  docx: <DocumentIcon />,
  xls: <TableIcon />,
  xlsx: <TableIcon />,
  jpg: <ImageIcon />,
  png: <ImageIcon />,
  gif: <ImageIcon />,
  mp4: <VideoIcon />,
  mp3: <AudioIcon />,
  zip: <ArchiveIcon />,
  txt: <DocumentIcon />,
  js: <CodeIcon />,
  py: <CodeIcon />,
  json: <CodeIcon />
};

const SortingRules: React.FC = () => {
  const [rules, setRules] = useState<SortingRule[]>([
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
    },
    {
      id: '3',
      name: 'Bilder',
      description: 'Sortiert Bilder und Fotos',
      priority: 70,
      enabled: true,
      conditions: {
        keywords: [],
        fileTypes: ['jpg', 'jpeg', 'png', 'gif', 'bmp'],
        maxSize: 52428800
      },
      actions: {
        targetPath: '/medien/bilder',
        createSubfolders: true,
        renameFile: false,
        addTags: ['medien', 'bild']
      },
      statistics: {
        matches: 423,
        lastUsed: new Date('2024-01-16'),
        successRate: 99.1
      }
    }
  ]);

  const [selectedTab, setSelectedTab] = useState(0);
  const [dialogOpen, setDialogOpen] = useState(false);
  const [editingRule, setEditingRule] = useState<SortingRule | null>(null);
  const [testDialogOpen, setTestDialogOpen] = useState(false);
  const [testFile, setTestFile] = useState<File | null>(null);
  const [testResults, setTestResults] = useState<any[]>([]);

  const fileTypes = [
    { value: 'pdf', label: 'PDF Dokumente', icon: <PdfIcon /> },
    { value: 'doc', label: 'Word Dokumente', icon: <DocumentIcon /> },
    { value: 'docx', label: 'Word Dokumente (DOCX)', icon: <DocumentIcon /> },
    { value: 'xls', label: 'Excel Tabellen', icon: <TableIcon /> },
    { value: 'xlsx', label: 'Excel Tabellen (XLSX)', icon: <TableIcon /> },
    { value: 'jpg', label: 'JPEG Bilder', icon: <ImageIcon /> },
    { value: 'png', label: 'PNG Bilder', icon: <ImageIcon /> },
    { value: 'gif', label: 'GIF Bilder', icon: <ImageIcon /> },
    { value: 'mp4', label: 'MP4 Videos', icon: <VideoIcon /> },
    { value: 'mp3', label: 'MP3 Audio', icon: <AudioIcon /> },
    { value: 'zip', label: 'ZIP Archive', icon: <ArchiveIcon /> },
    { value: 'txt', label: 'Text Dateien', icon: <DocumentIcon /> }
  ];

  const handleAddRule = () => {
    setEditingRule(null);
    setDialogOpen(true);
  };

  const handleEditRule = (rule: SortingRule) => {
    setEditingRule(rule);
    setDialogOpen(true);
  };

  const handleDeleteRule = (ruleId: string) => {
    setRules(prev => prev.filter(rule => rule.id !== ruleId));
  };

  const handleSaveRule = (ruleData: Partial<SortingRule>) => {
    if (editingRule) {
      setRules(prev => prev.map(rule => 
        rule.id === editingRule.id ? { ...rule, ...ruleData } : rule
      ));
    } else {
      const newRule: SortingRule = {
        id: Date.now().toString(),
        name: ruleData.name || '',
        description: ruleData.description || '',
        priority: ruleData.priority || 50,
        enabled: ruleData.enabled ?? true,
        conditions: ruleData.conditions || {
          keywords: [],
          fileTypes: []
        },
        actions: ruleData.actions || {
          targetPath: '',
          createSubfolders: false,
          renameFile: false,
          addTags: []
        },
        statistics: {
          matches: 0,
          lastUsed: new Date(),
          successRate: 0
        }
      };
      setRules(prev => [...prev, newRule]);
    }
    setDialogOpen(false);
  };

  const handleTestRule = (rule: SortingRule) => {
    setTestDialogOpen(true);
  };

  const handleFileUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      setTestFile(file);
      // Simulate rule testing
      const results = rules.map(rule => ({
        rule,
        matches: Math.random() > 0.5,
        confidence: Math.random() * 100,
        targetPath: rule.actions.targetPath
      }));
      setTestResults(results);
    }
  };

  const getPriorityColor = (priority: number) => {
    if (priority >= 80) return 'error';
    if (priority >= 60) return 'warning';
    return 'success';
  };

  const getSuccessRateColor = (rate: number) => {
    if (rate >= 95) return 'success';
    if (rate >= 80) return 'warning';
    return 'error';
  };

  const sortedRules = [...rules].sort((a, b) => b.priority - a.priority);

  return (
    <Box>
      {/* Header */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Box>
          <Typography variant="h4" component="h1" gutterBottom>
            Sortierregeln
          </Typography>
          <Typography variant="body1" color="textSecondary">
            Verwalten Sie automatische Sortierregeln für Ihre Dokumente
          </Typography>
        </Box>
        <Button
          variant="contained"
          startIcon={<AddIcon />}
          onClick={handleAddRule}
        >
          Neue Regel
        </Button>
      </Box>

      {/* Statistics Cards */}
      <Grid container spacing={3} mb={3}>
        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Aktive Regeln
                  </Typography>
                  <Typography variant="h4" component="div">
                    {rules.filter(r => r.enabled).length}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <RuleIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Gesamt Matches
                  </Typography>
                  <Typography variant="h4" component="div" color="success.main">
                    {rules.reduce((sum, rule) => sum + rule.statistics.matches, 0)}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'success.main' }}>
                  <CheckCircleIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Durchschnitt Erfolgsrate
                  </Typography>
                  <Typography variant="h4" component="div" color="primary.main">
                    {(rules.reduce((sum, rule) => sum + rule.statistics.successRate, 0) / rules.length).toFixed(1)}%
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'primary.main' }}>
                  <AnalyticsIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>

        <Grid item xs={12} sm={6} md={3}>
          <Card>
            <CardContent>
              <Box display="flex" alignItems="center" justifyContent="space-between">
                <Box>
                  <Typography color="textSecondary" gutterBottom>
                    Letzte Aktivität
                  </Typography>
                  <Typography variant="h6" component="div" color="textSecondary">
                    {new Date(Math.max(...rules.map(r => r.statistics.lastUsed.getTime()))).toLocaleDateString()}
                  </Typography>
                </Box>
                <Avatar sx={{ bgcolor: 'info.main' }}>
                  <SettingsIcon />
                </Avatar>
              </Box>
            </CardContent>
          </Card>
        </Grid>
      </Grid>

      {/* Rules List */}
      <Card>
        <CardContent>
          <Box display="flex" justifyContent="space-between" alignItems="center" mb={2}>
            <Typography variant="h6">
              Sortierregeln ({rules.length})
            </Typography>
            <Box display="flex" gap={1}>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setSelectedTab(0)}
              >
                Alle
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setSelectedTab(1)}
              >
                Aktiv
              </Button>
              <Button
                variant="outlined"
                size="small"
                onClick={() => setSelectedTab(2)}
              >
                Inaktiv
              </Button>
            </Box>
          </Box>

          <List>
            {sortedRules
              .filter(rule => {
                if (selectedTab === 1) return rule.enabled;
                if (selectedTab === 2) return !rule.enabled;
                return true;
              })
              .map((rule) => (
                <React.Fragment key={rule.id}>
                  <ListItem>
                    <ListItemIcon>
                      <DragIcon />
                    </ListItemIcon>
                    <ListItemText
                      primary={
                        <Box display="flex" alignItems="center" gap={1}>
                          <Typography variant="body1" fontWeight="medium">
                            {rule.name}
                          </Typography>
                          <Chip
                            label={`Priorität ${rule.priority}`}
                            color={getPriorityColor(rule.priority) as any}
                            size="small"
                          />
                          <Chip
                            label={rule.enabled ? 'Aktiv' : 'Inaktiv'}
                            color={rule.enabled ? 'success' : 'default'}
                            size="small"
                          />
                        </Box>
                      }
                      secondary={
                        <Box>
                          <Typography variant="body2" color="textSecondary" mb={1}>
                            {rule.description}
                          </Typography>
                          <Box display="flex" gap={2} flexWrap="wrap">
                            <Typography variant="caption" color="textSecondary">
                              Keywords: {rule.conditions.keywords.join(', ') || 'Keine'}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              Dateitypen: {rule.conditions.fileTypes.join(', ')}
                            </Typography>
                            <Typography variant="caption" color="textSecondary">
                              Ziel: {rule.actions.targetPath}
                            </Typography>
                          </Box>
                          <Box display="flex" gap={2} mt={1}>
                            <Chip
                              label={`${rule.statistics.matches} Matches`}
                              size="small"
                              variant="outlined"
                            />
                            <Chip
                              label={`${rule.statistics.successRate}% Erfolg`}
                              color={getSuccessRateColor(rule.statistics.successRate) as any}
                              size="small"
                              variant="outlined"
                            />
                            <Typography variant="caption" color="textSecondary">
                              Letztes: {rule.statistics.lastUsed.toLocaleDateString()}
                            </Typography>
                          </Box>
                        </Box>
                      }
                    />
                    <Box display="flex" gap={1}>
                      <Tooltip title="Regel testen">
                        <IconButton 
                          size="small"
                          onClick={() => handleTestRule(rule)}
                        >
                          <TestIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Bearbeiten">
                        <IconButton 
                          size="small"
                          onClick={() => handleEditRule(rule)}
                        >
                          <EditIcon />
                        </IconButton>
                      </Tooltip>
                      <Tooltip title="Löschen">
                        <IconButton 
                          size="small"
                          color="error"
                          onClick={() => handleDeleteRule(rule.id)}
                        >
                          <DeleteIcon />
                        </IconButton>
                      </Tooltip>
                    </Box>
                  </ListItem>
                  <Divider />
                </React.Fragment>
              ))}
          </List>
        </CardContent>
      </Card>

      {/* Rule Editor Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="md" fullWidth>
        <DialogTitle>
          {editingRule ? 'Regel bearbeiten' : 'Neue Regel erstellen'}
        </DialogTitle>
        <DialogContent>
          <Grid container spacing={3} sx={{ mt: 1 }}>
            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Grundinformationen
              </Typography>
              <TextField
                fullWidth
                label="Regelname"
                defaultValue={editingRule?.name}
                sx={{ mb: 2 }}
              />
              <TextField
                fullWidth
                label="Beschreibung"
                multiline
                rows={3}
                defaultValue={editingRule?.description}
                sx={{ mb: 2 }}
              />
              <Typography gutterBottom>
                Priorität: {editingRule?.priority || 50}
              </Typography>
              <Slider
                value={editingRule?.priority || 50}
                min={1}
                max={100}
                marks={[
                  { value: 1, label: 'Niedrig' },
                  { value: 50, label: 'Mittel' },
                  { value: 100, label: 'Hoch' }
                ]}
                sx={{ mb: 2 }}
              />
              <FormControlLabel
                control={
                  <Switch
                    defaultChecked={editingRule?.enabled ?? true}
                  />
                }
                label="Regel aktiv"
              />
            </Grid>

            <Grid item xs={12} md={6}>
              <Typography variant="h6" gutterBottom>
                Bedingungen
              </Typography>
              <TextField
                fullWidth
                label="Schlüsselwörter (kommagetrennt)"
                defaultValue={editingRule?.conditions.keywords.join(', ')}
                helperText="Wörter, die im Dateinamen oder Inhalt vorkommen müssen"
                sx={{ mb: 2 }}
              />
              <FormControl fullWidth sx={{ mb: 2 }}>
                <InputLabel>Dateitypen</InputLabel>
                <Select
                  multiple
                  defaultValue={editingRule?.conditions.fileTypes || []}
                  renderValue={(selected) => (
                    <Box sx={{ display: 'flex', flexWrap: 'wrap', gap: 0.5 }}>
                      {selected.map((value) => (
                        <Chip key={value} label={value} size="small" />
                      ))}
                    </Box>
                  )}
                >
                  {fileTypes.map((type) => (
                    <MenuItem key={type.value} value={type.value}>
                      <Box display="flex" alignItems="center" gap={1}>
                        {type.icon}
                        {type.label}
                      </Box>
                    </MenuItem>
                  ))}
                </Select>
              </FormControl>
              <Box display="flex" gap={2}>
                <TextField
                  label="Min. Größe (KB)"
                  type="number"
                  defaultValue={editingRule?.conditions.minSize ? editingRule.conditions.minSize / 1024 : undefined}
                  sx={{ flex: 1 }}
                />
                <TextField
                  label="Max. Größe (MB)"
                  type="number"
                  defaultValue={editingRule?.conditions.maxSize ? editingRule.conditions.maxSize / (1024 * 1024) : undefined}
                  sx={{ flex: 1 }}
                />
              </Box>
            </Grid>

            <Grid item xs={12}>
              <Typography variant="h6" gutterBottom>
                Aktionen
              </Typography>
              <TextField
                fullWidth
                label="Zielpfad"
                defaultValue={editingRule?.actions.targetPath}
                helperText="Pfad, in den die Dateien sortiert werden sollen"
                sx={{ mb: 2 }}
              />
              <Box display="flex" gap={2} mb={2}>
                <FormControlLabel
                  control={
                    <Switch
                      defaultChecked={editingRule?.actions.createSubfolders}
                    />
                  }
                  label="Unterordner erstellen"
                />
                <FormControlLabel
                  control={
                    <Switch
                      defaultChecked={editingRule?.actions.renameFile}
                    />
                  }
                  label="Datei umbenennen"
                />
              </Box>
              <TextField
                fullWidth
                label="Tags (kommagetrennt)"
                defaultValue={editingRule?.actions.addTags.join(', ')}
                helperText="Tags, die den Dateien hinzugefügt werden"
              />
            </Grid>
          </Grid>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Abbrechen</Button>
          <Button variant="contained" onClick={() => handleSaveRule({})}>
            Speichern
          </Button>
        </DialogActions>
      </Dialog>

      {/* Test Rule Dialog */}
      <Dialog open={testDialogOpen} onClose={() => setTestDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>Regel testen</DialogTitle>
        <DialogContent>
          <Typography variant="body2" color="textSecondary" mb={2}>
            Laden Sie eine Testdatei hoch, um zu sehen, welche Regeln greifen würden.
          </Typography>
          
          <Button
            variant="outlined"
            component="label"
            fullWidth
            sx={{ mb: 2 }}
          >
            Datei auswählen
            <input
              type="file"
              hidden
              onChange={handleFileUpload}
            />
          </Button>

          {testFile && (
            <Box>
              <Typography variant="subtitle2" gutterBottom>
                Testdatei: {testFile.name}
              </Typography>
              <Typography variant="body2" color="textSecondary" mb={2}>
                Größe: {(testFile.size / 1024).toFixed(1)} KB
              </Typography>

              <Typography variant="h6" gutterBottom>
                Testergebnisse:
              </Typography>
              {testResults.map((result, index) => (
                <Card key={index} sx={{ mb: 1 }}>
                  <CardContent sx={{ py: 1 }}>
                    <Box display="flex" alignItems="center" justifyContent="space-between">
                      <Typography variant="body2">
                        {result.rule.name}
                      </Typography>
                      <Chip
                        label={result.matches ? 'Match' : 'Kein Match'}
                        color={result.matches ? 'success' : 'default'}
                        size="small"
                      />
                    </Box>
                    {result.matches && (
                      <Typography variant="caption" color="textSecondary">
                        Ziel: {result.targetPath} • Konfidenz: {result.confidence.toFixed(1)}%
                      </Typography>
                    )}
                  </CardContent>
                </Card>
              ))}
            </Box>
          )}
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setTestDialogOpen(false)}>Schließen</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default SortingRules; 