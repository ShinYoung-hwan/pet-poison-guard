import React, { useState } from 'react';
import { Card, CardContent, CardMedia, Typography, Box, Accordion, AccordionSummary, AccordionDetails, IconButton } from '@mui/material';
import ExpandMoreIcon from '@mui/icons-material/ExpandMore';

export interface PoisonResult {
  name: string;
  image: string;
  description: string;
}

interface PoisonResultListProps {
  results: PoisonResult[];
}

const PoisonResultList: React.FC<PoisonResultListProps> = ({ results }) => {
  const [expandedIdx, setExpandedIdx] = useState<number | null>(null);

  const handleToggle = (idx: number) => {
    setExpandedIdx(expandedIdx === idx ? null : idx);
  };

  return (
    <Box display="flex" flexDirection="column" gap={2}>
      {results.map((item, idx) => (
        <Accordion
          key={idx}
          expanded={expandedIdx === idx}
          onChange={() => handleToggle(idx)}
          sx={{ boxShadow: 'none', borderRadius: 2, border: '1px solid #eee' }}
          aria-expanded={expandedIdx === idx}
        >
          <AccordionSummary
            expandIcon={<ExpandMoreIcon />}
            aria-controls={`panel${idx}-content`}
            id={`panel${idx}-header`}
          >
            <Box display="flex" alignItems="center" width="100%">
              <CardMedia
                component="img"
                sx={{ width: 64, height: 64, objectFit: 'cover', borderRadius: 2, marginRight: 2 }}
                image={item.image || '/assets/ppg.png'}
                alt={item.name}
              />
              <Typography variant="h6" component="div" sx={{ flex: 1 }}>
                {item.name}
              </Typography>
            </Box>
          </AccordionSummary>
          <AccordionDetails>
            <Typography variant="body2" color="text.secondary">
              {item.description}
            </Typography>
          </AccordionDetails>
        </Accordion>
      ))}
    </Box>
  );
};

export default PoisonResultList;
