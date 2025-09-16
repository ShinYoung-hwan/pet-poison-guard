import React from 'react';
import { Container, Typography, Button, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ppgLogo from '../assets/ppg.png';

const IntroPage: React.FC = () => {
  const navigate = useNavigate();
  return (
    <Container maxWidth="sm" sx={{ py: 6 }}>
      <Box display="flex" justifyContent="center" mb={1}>
        <Box component="img" src={ppgLogo} alt="logo" sx={{ width: 128, height: 128 }} />
      </Box>
      <Typography variant="h3" align="center" gutterBottom>
        Pet Poison Guard
      </Typography>
      <Typography align="center" sx={{ mb: 4 }}>
        반려동물의 안전을 위한 음식 분석 서비스
      </Typography>
      <Box display="flex" flexDirection="column" gap={2}>
        <Button variant="contained" size="large" onClick={() => navigate('/upload')}>
          이미지 분석 시작하기
        </Button>
        <Button variant="outlined" size="large" onClick={() => navigate('/description')}>
          서비스 설명 보기
        </Button>
      </Box>
    </Container>
  );
};

export default IntroPage;
