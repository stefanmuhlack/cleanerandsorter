import React, { useEffect, useState } from 'react';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, TableContainer, Toolbar, TextField, Button, IconButton, Chip, LinearProgress, Alert, Dialog, DialogTitle, DialogContent, DialogActions } from '@mui/material';
import { Refresh as RefreshIcon, Delete as DeleteIcon, DriveFileMove as MoveIcon, ArrowUpward as PromoteIcon } from '@mui/icons-material';

interface DuplicateItem {
  customer_root: string;
  filename: string;
  path: string;
  size: number;
  mtime: number;
}

const Duplicates: React.FC = () => {
  const [items, setItems] = useState<DuplicateItem[]>([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(false);
  const [filterCustomer, setFilterCustomer] = useState('');
  const [moveDialog, setMoveDialog] = useState<{ open: boolean; path?: string }>({ open: false });
  const [moveTarget, setMoveTarget] = useState('');
  const [message, setMessage] = useState<{ type: 'success' | 'error' | 'info' | 'warning'; text: string } | null>(null);

  const load = async () => {
    setLoading(true);
    try {
      const token = localStorage.getItem('token');
      const headers = token ? { 'Authorization': `Bearer ${token}` } : undefined;
      const params = new URLSearchParams();
      if (filterCustomer) params.set('customer', filterCustomer);
      const res = await fetch(`/api/ingest/duplicates?${params.toString()}`, { headers });
      const data = await res.json();
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message || 'Load failed' });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); }, []);

  const promote = async (path: string) => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } as any;
      const res = await fetch('/api/ingest/duplicates/promote', { method: 'POST', headers, body: JSON.stringify({ path }) });
      const data = await res.json();
      if (res.ok) {
        setMessage({ type: 'success', text: 'Promoted duplicate to primary' });
        load();
      } else {
        setMessage({ type: 'error', text: data.detail || `HTTP ${res.status}` });
      }
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    }
  };

  const move = async () => {
    const path = moveDialog.path as string;
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } as any;
      const res = await fetch('/api/ingest/duplicates/move', { method: 'POST', headers, body: JSON.stringify({ path, target_dir: moveTarget }) });
      const data = await res.json();
      if (res.ok) {
        setMessage({ type: 'success', text: 'Moved duplicate' });
        setMoveDialog({ open: false });
        setMoveTarget('');
        load();
      } else {
        setMessage({ type: 'error', text: data.detail || `HTTP ${res.status}` });
      }
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    }
  };

  const del = async (path: string) => {
    try {
      const token = localStorage.getItem('token');
      const headers = { 'Content-Type': 'application/json', ...(token ? { 'Authorization': `Bearer ${token}` } : {}) } as any;
      const res = await fetch('/api/ingest/duplicates/delete', { method: 'POST', headers, body: JSON.stringify({ paths: [path] }) });
      const data = await res.json();
      if (res.ok) {
        setMessage({ type: 'success', text: `Deleted ${data.deleted} duplicate(s)` });
        load();
      } else {
        setMessage({ type: 'error', text: data.detail || `HTTP ${res.status}` });
      }
    } catch (e: any) {
      setMessage({ type: 'error', text: e.message });
    }
  };

  const formatSize = (bytes: number) => {
    const sizes = ['B','KB','MB','GB','TB'];
    if (!bytes) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return `${(bytes / Math.pow(1024, i)).toFixed(1)} ${sizes[i]}`;
  };

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Dublettenkorb</Typography>
      {message && (
        <Alert severity={message.type} sx={{ mb: 2 }} onClose={() => setMessage(null)}>{message.text}</Alert>
      )}
      <Toolbar sx={{ px: 0 }}>
        <TextField size="small" label="Kunde/Root" value={filterCustomer} onChange={(e) => setFilterCustomer(e.target.value)} sx={{ mr: 2 }} />
        <Button variant="outlined" startIcon={<RefreshIcon />} onClick={load}>Aktualisieren</Button>
      </Toolbar>
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Kunde</TableCell>
              <TableCell>Datei</TableCell>
              <TableCell>Pfad</TableCell>
              <TableCell>Größe</TableCell>
              <TableCell>Geändert</TableCell>
              <TableCell>Aktionen</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map((it) => (
              <TableRow key={it.path}>
                <TableCell><Chip label={it.customer_root} size="small" /></TableCell>
                <TableCell>{it.filename}</TableCell>
                <TableCell>{it.path}</TableCell>
                <TableCell>{formatSize(it.size)}</TableCell>
                <TableCell>{new Date(it.mtime * 1000).toLocaleString()}</TableCell>
                <TableCell>
                  <IconButton size="small" color="primary" onClick={() => promote(it.path)} title="Als Primär setzen">
                    <PromoteIcon />
                  </IconButton>
                  <IconButton size="small" onClick={() => setMoveDialog({ open: true, path: it.path })} title="Verschieben">
                    <MoveIcon />
                  </IconButton>
                  <IconButton size="small" color="error" onClick={() => del(it.path)} title="Löschen">
                    <DeleteIcon />
                  </IconButton>
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={6}>
                  <Alert severity="info">Keine Duplikate gefunden.</Alert>
                </TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={moveDialog.open} onClose={() => setMoveDialog({ open: false })}>
        <DialogTitle>Dublette verschieben</DialogTitle>
        <DialogContent>
          <TextField fullWidth label="Zielordner" value={moveTarget} onChange={(e) => setMoveTarget(e.target.value)} />
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setMoveDialog({ open: false })}>Abbrechen</Button>
          <Button variant="contained" onClick={move}>Verschieben</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Duplicates;


