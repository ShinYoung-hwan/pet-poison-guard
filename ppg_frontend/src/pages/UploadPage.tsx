
import React, { useState } from 'react';
import { Container, Typography, Box } from '@mui/material';
import ImageUpload from '../components/ImageUpload';
import ResultDisplay from '../components/ResultDisplay';
import type { PoisonResult } from '../components/PoisonResultList';
import usePolling from '../services/usePolling';

type PollingStatus = 'idle' | 'pending' | 'completed' | 'error';

const UploadPage: React.FC = () => {
  const [taskId, setTaskId] = useState<string | null>(null);
  const [result, setResult] = useState<PoisonResult[] | null>(null);
  const [imageUploaded, setImageUploaded] = useState<boolean>(false);
  const [pollingStatus, setPollingStatus] = useState<PollingStatus>('idle');
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  usePolling({
    taskId,
    onCompleted: (data) => {
      setPollingStatus('completed');
      setErrorMsg(null);
      if (data && Array.isArray(data.result)) {
        setResult(data.result);
      } else if (Array.isArray(data)) {
        setResult(data);
      } else {
        setResult(null);
      }
    },
    onStatus: (status: string) => {
      if (status === 'pending') setPollingStatus('pending');
      if (status === 'completed') setPollingStatus('completed');
    },
    onError: (err: any) => {
      setPollingStatus('error');
      setErrorMsg('분석 중 오류가 발생했습니다.');
    },
  });

  // ImageUpload에서 이미지 업로드 시 imageUploaded를 true로 설정
  const handleImageUpload = (taskId: string | null) => {
    setTaskId(taskId);
    setImageUploaded(!!taskId);
    setResult(null); // 새 업로드 시 이전 결과 초기화
    setPollingStatus('pending');
    setErrorMsg(null);
  };

  return (
    <Container maxWidth="sm" sx={{ py: 4 }}>
      <Typography variant="h5" align="center" gutterBottom>
        이미지 업로드
      </Typography>
      <ImageUpload onTaskId={handleImageUpload} />
      <Box mt={4}>
        <ResultDisplay
          result={result}
          imageUploaded={imageUploaded}
          pollingStatus={pollingStatus}
          errorMsg={errorMsg}
        />
      </Box>
    </Container>
  );
};

export default UploadPage;
