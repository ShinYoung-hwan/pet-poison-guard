import React, { useState, useCallback } from 'react';
import { Container, Typography, Box } from '@mui/material';
import ImageUpload from '../components/ImageUpload';
import ResultDisplay from '../components/ResultDisplay';
import usePolling from '../services/usePolling';

const HomePage: React.FC = () => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);

  const handleCompleted = useCallback((data: any) => {
    setResult(data);
  }, []);

  usePolling({
    taskId,
    onCompleted: handleCompleted,
  });

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h4" align="center" gutterBottom>
        Pet Poison Guard
      </Typography>
      <ImageUpload onTaskId={setTaskId} />
      <Box mt={4}>
        <ResultDisplay result={result} imageUploaded={taskId !== null} />
      </Box>
    </Container>
  );
};

export default HomePage;
