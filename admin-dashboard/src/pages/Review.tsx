import React, { useEffect, useState } from 'react';
import { useDispatch, useSelector } from 'react-redux';
import { RootState } from '../store';
import { fetchPendingReviews, confirmReview } from '../store/slices/classificationReviewSlice';
import { Box, Typography, Paper, Table, TableHead, TableRow, TableCell, TableBody, TableContainer, LinearProgress, Alert, Button, Dialog, DialogTitle, DialogContent, DialogActions, Select, MenuItem, FormControl, InputLabel } from '@mui/material';

const Review: React.FC = () => {
  const dispatch = useDispatch<any>();
  const { items, loading, error } = useSelector((s: RootState) => s.classificationReview);
  const [dialog, setDialog] = useState<{ open: boolean; id?: string; category?: string }>({ open: false });
  const [previewId, setPreviewId] = useState<string | null>(null);

  useEffect(() => { dispatch(fetchPendingReviews()); }, [dispatch]);

  return (
    <Box sx={{ p: 3 }}>
      <Typography variant="h4" gutterBottom>Offene Zuordnungen</Typography>
      {loading && <LinearProgress sx={{ mb: 2 }} />}
      {error && <Alert severity="error" sx={{ mb: 2 }}>{error}</Alert>}
      <TableContainer component={Paper}>
        <Table size="small">
          <TableHead>
            <TableRow>
              <TableCell>Datei</TableCell>
              <TableCell>Pfad</TableCell>
              <TableCell>Vorschlag</TableCell>
              <TableCell>Confidence</TableCell>
              <TableCell>Aktion</TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {items.map(it => (
              <TableRow key={it.id}>
                <TableCell>{it.filename}</TableCell>
                <TableCell>{it.original_path}</TableCell>
                <TableCell>{it.suggested_category}</TableCell>
                <TableCell>{(it.confidence * 100).toFixed(1)}%</TableCell>
                <TableCell>
                  <Button size="small" sx={{ mr: 1 }} onClick={async () => {
                    const token = localStorage.getItem('token');
                    const res = await fetch(`/api/ingest/classification/download?id=${encodeURIComponent(it.id)}`, { headers: token ? { 'Authorization': `Bearer ${token}` } : undefined });
                    if (!res.ok) return;
                    const blob = await res.blob();
                    const url = URL.createObjectURL(blob);
                    const a = document.createElement('a'); a.href = url; a.download = it.filename; document.body.appendChild(a); a.click(); a.remove(); URL.revokeObjectURL(url);
                  }}>Download</Button>
                  <Button size="small" variant="contained" onClick={() => setDialog({ open: true, id: it.id, category: it.suggested_category })}>Bestätigen</Button>
                </TableCell>
              </TableRow>
            ))}
            {items.length === 0 && !loading && (
              <TableRow>
                <TableCell colSpan={5}><Alert severity="info">Keine offenen Reviews.</Alert></TableCell>
              </TableRow>
            )}
          </TableBody>
        </Table>
      </TableContainer>

      <Dialog open={dialog.open} onClose={() => setDialog({ open: false })}>
        <DialogTitle>Zuordnung bestätigen</DialogTitle>
        <DialogContent>
          <FormControl fullWidth>
            <InputLabel>Kategorie</InputLabel>
            <Select label="Kategorie" value={dialog.category || ''} onChange={(e) => setDialog({ ...dialog, category: String(e.target.value) })}>
              <MenuItem value="projekte">Projekte</MenuItem>
              <MenuItem value="portale">Portale</MenuItem>
              <MenuItem value="kampagnen">Kampagnen</MenuItem>
              <MenuItem value="angebote">Angebote</MenuItem>
              <MenuItem value="archiv">Archiv</MenuItem>
              <MenuItem value="allgemein">Allgemein</MenuItem>
              <MenuItem value="footage">Footage</MenuItem>
              <MenuItem value="finanzen">Finanzen</MenuItem>
              <MenuItem value="personal">Personal</MenuItem>
            </Select>
          </FormControl>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialog({ open: false })}>Abbrechen</Button>
          <Button variant="contained" onClick={async () => {
            if (!dialog.id || !dialog.category) return;
            await dispatch(confirmReview({ id: dialog.id, category: dialog.category }));
            setDialog({ open: false });
            dispatch(fetchPendingReviews());
          }}>Bestätigen</Button>
        </DialogActions>
      </Dialog>
    </Box>
  );
};

export default Review;


