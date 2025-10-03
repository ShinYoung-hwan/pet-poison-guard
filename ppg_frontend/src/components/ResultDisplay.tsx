import React from 'react';
import PoisonResultList, { type PoisonResult } from './PoisonResultList';
import { Alert } from '@mui/material';

interface ResultDisplayProps {
  result: PoisonResult[] | null;
  imageUploaded: boolean;
  pollingStatus?: 'idle' | 'pending' | 'completed' | 'error';
  errorMsg?: string | null;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result, imageUploaded, pollingStatus = 'idle', errorMsg }) => {
  if (!imageUploaded) return null;

  if (pollingStatus === 'pending') {
    return (
      <div style={{ marginTop: 16 }}>
        <h3>분석 결과</h3>
        <Alert severity="info" variant="outlined">분석 중입니다...</Alert>
      </div>
    );
  }

  if (pollingStatus === 'error') {
    return (
      <div style={{ marginTop: 16 }}>
        <h3>분석 결과</h3>
        <Alert severity="error" variant="outlined">{errorMsg || '분석 중 오류가 발생했습니다.'}</Alert>
      </div>
    );
  }

  // completed 상태에서 결과가 없을 때
  if (!result || result.length === 0) {
    return (
      <div style={{ marginTop: 16 }}>
        <h3>분석 결과</h3>
        <Alert severity="info" variant="outlined">결과가 없습니다.</Alert>
      </div>
    );
  }

  // 결과가 있을 때
  return (
    <div style={{ marginTop: 16 }}>
      <h3>분석 결과</h3>
      <PoisonResultList results={result} />
    </div>
  );
};

export default ResultDisplay;
