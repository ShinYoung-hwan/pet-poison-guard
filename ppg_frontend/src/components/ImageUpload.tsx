import React, { useRef, useState } from 'react';
import { Box, Button, CircularProgress, Typography } from '@mui/material';
import CloudUploadIcon from '@mui/icons-material/CloudUpload';
import api from '../services/api';

interface ImageUploadProps {
  onTaskId: (taskId: string) => void;
}

const ImageUpload: React.FC<ImageUploadProps> = ({ onTaskId }) => {
  const inputRef = useRef<HTMLInputElement>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleFileChange = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setError(null);
    setLoading(true);
    try {
      const result = await api.uploadImage(file);
      if (result && result.taskId) {
        onTaskId(result.taskId);
      } else {
        setError('서버에서 taskId를 반환하지 않았습니다.');
      }
    } catch (err: any) {
      setError('Failed to analyze image.');
    } finally {
      setLoading(false);
    }
  };

  return (
    <Box textAlign="center">
      <input
        type="file"
        accept="image/*"
        style={{ display: 'none' }}
        ref={inputRef}
        onChange={handleFileChange}
      />
      <Button
        variant="contained"
        startIcon={<CloudUploadIcon />}
        onClick={() => inputRef.current?.click()}
        disabled={loading}
        sx={{ minWidth: 180 }}
      >
        {loading ? <CircularProgress size={24} color="inherit" /> : 'Upload Image'}
      </Button>
      {error && <Typography color="error" mt={2}>{error}</Typography>}
    </Box>
  );
};

export default ImageUpload;
