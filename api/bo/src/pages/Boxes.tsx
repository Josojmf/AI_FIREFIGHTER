// src/pages/Boxes.tsx
import { useEffect, useState } from "react";
import {
  Box,
  Typography,
  Paper,
  List,
  ListItem,
  ListItemText,
  Button,
  TextField,
  IconButton,
} from "@mui/material";
import Navbar from "../components/Navbar";
import { API_BASE_URL } from "../config";



interface StudyBox {
  _id: string;
  title: string;
  description: string;
  cards: string[];
}

export default function Boxes() {
  const [boxes, setBoxes] = useState<StudyBox[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editedBox, setEditedBox] = useState<Partial<StudyBox>>({});

  const fetchBoxes = () => {
    fetch(`${API_BASE_URL}/study`)
      .then((res) => res.json())
      .then((data) => {
        // eslint-disable-next-line @typescript-eslint/no-explicit-any
        const transformed = Object.entries(data).map(([id, value]: any) => ({
          _id: id,
          ...value,
        }));
        setBoxes(transformed);
      })
      .catch((err) => console.error("Error al obtener cajas:", err));
  };

  useEffect(() => {
    fetchBoxes();
  }, []);

  const handleDelete = (id: string) => {
    fetch(`${API_BASE_URL}/study/${id}`, {
      method: "DELETE",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.deleted) setBoxes((prev) => prev.filter((b) => b._id !== id));
      });
  };

  const handleEdit = (box: StudyBox) => {
    setEditingId(box._id);
    setEditedBox({ title: box.title, description: box.description });
  };

  const handleSave = (id: string) => {
    fetch(`${API_BASE_URL}/study/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(editedBox),
    })
      .then((res) => res.json())
      .then(() => {
        setEditingId(null);
        setEditedBox({});
        fetchBoxes();
      });
  };

  return (
    <>
      <Navbar />
      <Box sx={{ p: 4, animation: "fadeIn 1s ease-out" }}>
        <Typography variant="h4" gutterBottom sx={{ color: "#fff" }}>
          Cajas Leitner
        </Typography>
        <Paper sx={{ mt: 3, p: 2, backgroundColor: "#1e1e1e" }} elevation={3}>
          <List>
            {boxes.map((box) => (
              <ListItem key={box._id} divider sx={{ color: "#fff" }}>
                {editingId === box._id ? (
                  <>
                    <TextField
                      fullWidth
                      variant="outlined"
                      label="Título"
                      value={editedBox.title || ""}
                      onChange={(e) =>
                        setEditedBox({ ...editedBox, title: e.target.value })
                      }
                      sx={{ mr: 2 }}
                    />
                    <TextField
                      fullWidth
                      variant="outlined"
                      label="Descripción"
                      value={editedBox.description || ""}
                      onChange={(e) =>
                        setEditedBox({
                          ...editedBox,
                          description: e.target.value,
                        })
                      }
                    />
                    <IconButton onClick={() => handleSave(box._id)} color="success">
                        <Button variant="contained" color="success">
                            Guardar
                        </Button>
                    </IconButton>
                  </>
                ) : (
                  <>
                    <ListItemText
                      primary={<Typography color="white">{box.title}</Typography>}
                      secondary={<Typography color="gray">{box.description}</Typography>}
                    />
                    <IconButton onClick={() => handleEdit(box)} color="primary">
                        <Button variant="contained" color="primary">
                            Editar
                        </Button>
                    </IconButton>
                    <IconButton onClick={() => handleDelete(box._id)} color="error">
                        <Button variant="contained" color="error">
                            Borrar
                        </Button>
                    </IconButton>
                  </>
                )}
              </ListItem>
            ))}
          </List>
        </Paper>
      </Box>
    </>
  );
}
