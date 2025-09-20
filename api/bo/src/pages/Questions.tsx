// src/pages/Questions.tsx
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
} from "@mui/material";
import Navbar from "../components/Navbar";
import { API_BASE_URL } from "../config";


interface Question {
  _id: string;
  question: string;
  options: string[];
  correct: string;
}

export default function Questions() {
  const [questions, setQuestions] = useState<Question[]>([]);
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editedQuestion, setEditedQuestion] = useState<Partial<Question>>({});

  const fetchQuestions = () => {
    fetch(`${API_BASE_URL}/questions`)
      .then((res) => res.json())
      .then((data) => setQuestions(data))
      .catch((err) => console.error("Error al obtener preguntas:", err));
  };

  useEffect(() => {
    fetchQuestions();
  }, []);

  const handleDelete = (id: string) => {
    fetch(`${API_BASE_URL}/questions/${id}`, {
      method: "DELETE",
    })
      .then((res) => res.json())
      .then((data) => {
        if (data.deleted) setQuestions((prev) => prev.filter((q) => q._id !== id));
      });
  };

  const handleEdit = (q: Question) => {
    setEditingId(q._id);
    setEditedQuestion(q);
  };

  const handleSave = (id: string) => {
    fetch(`${API_BASE_URL}/questions/${id}`, {
      method: "PUT",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(editedQuestion),
    })
      .then((res) => res.json())
      .then(() => {
        setEditingId(null);
        setEditedQuestion({});
        fetchQuestions();
      });
  };

  return (
    <>
      <Navbar />
      <Box sx={{ p: 4, animation: "fadeIn 1s ease-out" }}>
        <Typography variant="h4" gutterBottom sx={{ color: "#fff" }}>
          Preguntas
        </Typography>
        <Paper sx={{ mt: 3, p: 2, backgroundColor: "#1e1e1e" }} elevation={3}>
          <List>
            {questions.map((q) => (
              <ListItem key={q._id} divider sx={{ color: "#fff" }}>
                {editingId === q._id ? (
                  <>
                    <TextField
                      fullWidth
                      variant="outlined"
                      label="Pregunta"
                      value={editedQuestion.question || ""}
                      onChange={(e) =>
                        setEditedQuestion({ ...editedQuestion, question: e.target.value })
                      }
                      sx={{ mr: 2 }}
                    />
                    <Button onClick={() => handleSave(q._id)} variant="contained" color="success">
                      Guardar
                    </Button>
                  </>
                ) : (
                  <>
                    <ListItemText
                      primary={<Typography color="white">{q.question}</Typography>}
                      secondary={
                        <Typography color="gray">
                          Correcta: {q.correct} | Opciones: {q.options.join(", ")}
                        </Typography>
                      }
                    />
                    <Button onClick={() => handleEdit(q)} variant="contained" color="primary" sx={{ mr: 1 }}>
                      Editar
                    </Button>
                    <Button onClick={() => handleDelete(q._id)} variant="contained" color="error">
                      Borrar
                    </Button>
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
