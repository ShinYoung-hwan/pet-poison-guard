import React from 'react';
import { Container, Typography, List, ListItem, ListItemText } from '@mui/material';

const DescriptionPage: React.FC = () => (
  <Container maxWidth="sm" sx={{ py: 6 }}>
    <Typography variant="h4" gutterBottom>
      서비스 기능 안내
    </Typography>
    <List>
      <ListItem>
        <ListItemText primary="이미지로 음식 분석 및 위험도 판별" />
      </ListItem>
      <ListItem>
        <ListItemText primary="분석 결과에 따른 상세 설명 제공" />
      </ListItem>
      <ListItem>
        <ListItemText primary="다국어 지원 및 접근성 고려 UI" />
      </ListItem>
      <ListItem>
        <ListItemText primary="반려동물 보호를 위한 최신 데이터 반영" />
      </ListItem>
    </List>
  </Container>
);

export default DescriptionPage;
