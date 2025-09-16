import React from 'react';
import { Card, CardContent, CardMedia, Typography, Box } from '@mui/material';

export interface PoisonResult {
  name: string;
  image: string;
  description: string;
}

interface PoisonResultListProps {
  results: PoisonResult[];
}

const PoisonResultList: React.FC<PoisonResultListProps> = ({ results }) => {
  return (
    <Box display="flex" flexDirection="column" gap={2}>
      {results.map((item, idx) => (
        <Card key={idx} sx={{ display: 'flex', alignItems: 'center', minHeight: 120 }}>
          <CardMedia
            component="img"
            sx={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 2, marginLeft: 2 }}
            image={item.image || '/assets/ppg.png'}
            alt={item.name}
          />
          <CardContent sx={{ flex: 1 }}>
            <Typography variant="h6" component="div">
              {item.name}
            </Typography>
            <Typography variant="body2" color="text.secondary">
              {item.description}
            </Typography>
          </CardContent>
        </Card>
      ))}
    </Box>
  );
};

export default PoisonResultList;
