import { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  IconButton,
} from "@mui/material";
import Navbar from "../components/Navbar";
import { API_BASE_URL } from "../config";


interface User {
  _id: string;
  username: string;
}

export default function Users() {
  const [users, setUsers] = useState<User[]>([]);

  const fetchUsers = () => {
    fetch(`${API_BASE_URL}/admin/users`)
      .then((res) => res.json())
      .then((data) => setUsers(data))
      .catch((err) => console.error("Error al obtener usuarios:", err));
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const handleDelete = async (id: string) => {
    const confirm = window.confirm("¿Seguro que deseas eliminar este usuario?");
    if (!confirm) return;

    const res = await fetch(`${API_BASE_URL}/admin/users/${id}`, {
      method: "DELETE",
    });

    const result = await res.json();
    if (result.deleted) {
      setUsers((prev) => prev.filter((u) => u._id !== id));
    } else {
      alert("No se pudo eliminar el usuario.");
    }
  };

  return (
    <>
      <Navbar />
      <Box sx={{ p: 4, animation: "fadeIn 1s ease-out" }}>
        <Typography variant="h4" gutterBottom sx={{ color: "#fff" }}>
          Usuarios registrados
        </Typography>
        <Paper sx={{ mt: 3, p: 2, backgroundColor: "#1e1e1e" }} elevation={3}>
          <List>
            {users.map((user) => (
              <ListItem
                key={user._id}
                divider
                sx={{
                  color: "#fff",
                  display: "flex",
                  justifyContent: "space-between",
                }}
              >
                <ListItemText
                  primary={
                    <Typography color="white">{user.username}</Typography>
                  }
                  secondary={
                    <Typography color="gray" fontSize={12}>
                      {user._id}
                    </Typography>
                  }
                />
                <IconButton
                  onClick={() => handleDelete(user._id)}
                  edge="end"
                  color="error"
                  title="Eliminar usuario"
                >
                  <svg
                    xmlns="http://www.w3.org/2000/svg"
                    width="24"
                    height="24"
                    viewBox="0 0 24 24"
                    fill="none"
                    stroke="currentColor"
                    strokeWidth="2"
                    strokeLinecap="round"
                    strokeLinejoin="round"
                    className="feather feather-trash-2"
                  >
                    <polyline points="3 6 5 6 21 6" />
                    <path d="M19 6l-1.5 14.25a2.25 2.25 0 01-2.25 2.25H8.75a2.25 2.25 0 01-2.25-2.25L5 6" />
                    <path d="M10 11v6" />
                    <path d="M14 11v6" />
                  </svg>
                </IconButton>
              </ListItem>
            ))}
          </List>
        </Paper>
      </Box>
    </>
  );
}
