// src/components/Navbar.tsx
import { AppBar, Toolbar, Typography, Button, Box } from "@mui/material";
import { Link, useNavigate } from "react-router-dom";

export default function Navbar() {
  const navigate = useNavigate();

  const handleLogout = () => {
    localStorage.removeItem("user");
    navigate("/");
  };

  return (
    <AppBar position="static" sx={{ animation: "fadeIn 0.8s ease-out" }}>
      <Toolbar>
        <Typography variant="h6" sx={{ flexGrow: 1 }}>
          <span style={{ color: "#90caf9" }}>Back</span>
          <span style={{ color: "#ffffff" }}>Office</span>
        </Typography>
        <Box>
          <Button color="inherit" component={Link} to="/dashboard">Dashboard</Button>
          <Button color="inherit" component={Link} to="/users">Usuarios</Button>
          <Button color="inherit" component={Link} to="/boxes">Cajas</Button>
          <Button color="inherit" component={Link} to="/questions">Preguntas</Button>
          <Button color="inherit" onClick={handleLogout}>Salir</Button>
        </Box>
      </Toolbar>
    </AppBar>
  );
}
