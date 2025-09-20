import { Button, Container, TextField, Typography } from "@mui/material";
import { useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";


export default function Register() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleRegister = async () => {
    try {
      await axios.post(`${API_BASE_URL}/register`, { username, password });
      alert("Usuario registrado correctamente");
    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    } catch (err) {
      alert("Error en el registro");
    }
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" gutterBottom>Registro</Typography>
      <TextField fullWidth label="Usuario" margin="normal" value={username} onChange={e => setUsername(e.target.value)} />
      <TextField fullWidth label="Contraseña" margin="normal" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <Button variant="contained" onClick={handleRegister} sx={{ mt: 2 }}>Registrar</Button>
    </Container>
  );
}
