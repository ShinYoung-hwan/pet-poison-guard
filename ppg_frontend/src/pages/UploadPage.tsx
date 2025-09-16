import React, { useState } from 'react';
import { Container, Typography, Box } from '@mui/material';
import ImageUpload from '../components/ImageUpload';
import ResultDisplay from '../components/ResultDisplay';
import type { PoisonResult } from '../components/PoisonResultList';
import usePolling from '../services/usePolling';

const UploadPage: React.FC = () => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<PoisonResult[] | null>(null);

  usePolling({
    taskId,
    onCompleted: (data) => {
      // If API response is { result: [...] }, extract the array
      if (data && Array.isArray(data.result)) {
        setResult(data.result);
      } else if (Array.isArray(data)) {
        setResult(data);
      } else {
        setResult(null);
      }
    },
  });

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h5" align="center" gutterBottom>
        이미지 업로드
      </Typography>
      <ImageUpload onTaskId={setTaskId} />
      <Box mt={4}>
  <ResultDisplay result={result} />
      </Box>
    </Container>
  );
};

export default UploadPage;
