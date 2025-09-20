import { Button, Container, TextField, Typography } from "@mui/material";
import { useState } from "react";
import axios from "axios";
import { API_BASE_URL } from "../config";

type Props = {
  setUser: (user: string) => void;
};

export default function Login({ setUser }: Props) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");

  const handleLogin = async () => {
    try {
      const res = await axios.post(`${API_BASE_URL}/login`, {
        username,
        password,
      });
      localStorage.setItem("user", res.data.username);
      setUser(res.data.username);
    } catch {
      alert("Error al iniciar sesión");
    }
  };

  return (
    <Container maxWidth="sm">
      <Typography variant="h4" gutterBottom>Login</Typography>
      <TextField fullWidth label="Usuario" margin="normal" value={username} onChange={e => setUsername(e.target.value)} />
      <TextField fullWidth label="Contraseña" margin="normal" type="password" value={password} onChange={e => setPassword(e.target.value)} />
      <Button variant="contained" onClick={handleLogin} sx={{ mt: 2 }}>Entrar</Button>
    </Container>
  );
}
