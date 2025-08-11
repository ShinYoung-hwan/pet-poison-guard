import React, { useState } from 'react';
import { Container, Typography, Box } from '@mui/material';
import ImageUpload from '../components/ImageUpload';
import ResultDisplay from '../components/ResultDisplay';
import { useNavigate } from 'react-router-dom';
import usePolling from '../services/usePolling';

const UploadPage: React.FC = () => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<any>(null);
  const navigate = useNavigate();

  usePolling({
    taskId,
    onCompleted: (data) => {
      setResult(data);
      navigate('/description', { state: { result: data } });
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
