import React from 'react';
import { AppBar, Toolbar, Typography, IconButton, Box } from '@mui/material';
import { useNavigate } from 'react-router-dom';
import ppgLogo from '../assets/ppg.png';

const Header: React.FC = () => {
  const navigate = useNavigate();
  return (
    <AppBar position="fixed" color="primary" elevation={1}>
      <Toolbar>
        <IconButton edge="start" color="inherit" aria-label="home" onClick={() => navigate('/')} sx={{ mr: 2 }}>
          <Box
            component="img"
            src={ppgLogo}
            alt="home"
            sx={{ width: 32, height: 32 }}
          />
        </IconButton>
        <Typography variant="h6" component="div" sx={{ flexGrow: 1 }}>
          Pet Poison Guard
        </Typography>
      </Toolbar>
    </AppBar>
  );
};

export default Header;
