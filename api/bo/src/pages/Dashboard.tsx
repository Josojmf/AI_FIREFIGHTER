import { Typography, Box, Paper } from "@mui/material";
import Navbar from "../components/Navbar";

export default function Dashboard() {
  return (
    <>
      <Navbar />
      <Box sx={{ p: 4, animation: "fadeIn 1s ease-out" }}>
        <Typography variant="h4" gutterBottom sx={{ color: "#fff" }}>Panel de Administración</Typography>
        <Paper sx={{ p: 3, mt: 2, backgroundColor: "#1e1e1e", color: "#ccc" }} elevation={3}>
          <Typography>Bienvenido al sistema de gestión. Usa la barra superior para navegar.</Typography>
        </Paper>
      </Box>
    </>
  );
}
