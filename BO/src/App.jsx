import React from 'react';
import { Container, Typography, Button, Box } from '@mui/material';

function App() {
  return (
    <Container maxWidth="lg">
      <Box sx={{ my: 4 }}>
        <Typography variant="h3" component="h1" gutterBottom>
          🔥 AI Firefighter BackOffice
        </Typography>
        <Typography variant="h6" color="text.secondary" gutterBottom>
          Panel de administración funcionando correctamente
        </Typography>
        <Button variant="contained" color="primary">
          Sistema Operativo
        </Button>
      </Box>
    </Container>
  );
}

export default App;
