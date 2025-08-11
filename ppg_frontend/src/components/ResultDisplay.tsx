import React from 'react';
import { Box, Typography, Paper } from '@mui/material';

interface ResultDisplayProps {
  result: any;
}

const ResultDisplay: React.FC<ResultDisplayProps> = ({ result }) => {
  if (!result) return null;
  // TODO: Customize result rendering based on actual API response structure
  return (
    <Paper elevation={3} sx={{ p: 2 }}>
      <Typography variant="h6">분석 결과</Typography>
      <Box mt={1}>
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all' }}>{JSON.stringify(result, null, 2)}</pre>
      </Box>
    </Paper>
  );
};

export default ResultDisplay;
