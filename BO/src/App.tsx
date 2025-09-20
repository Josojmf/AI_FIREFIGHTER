import { BrowserRouter as Router, Routes, Route, Navigate } from "react-router-dom";
import Login from "./pages/Login";
import Register from "./pages/Register";
import Dashboard from "./pages/Dashboard";
import Users from "./pages/Users";
import Boxes from "./pages/Boxes";
import Questions from "./pages/Questions";
import { useEffect, useState } from "react";

function App() {
  const [user, setUser] = useState<string | null>(localStorage.getItem("user"));

  useEffect(() => {
    const stored = localStorage.getItem("user");
    if (stored) setUser(stored);
  }, []);

  return (
    <Router>
      <Routes>
        <Route path="/" element={user ? <Navigate to="/dashboard" /> : <Login setUser={setUser} />} />
        <Route path="/register" element={<Register />} />
        <Route path="/dashboard" element={user ? <Dashboard /> : <Navigate to="/" />} />
        <Route path="/users" element={user ? <Users /> : <Navigate to="/" />} />
        <Route path="/boxes" element={user ? <Boxes /> : <Navigate to="/" />} />
        <Route path="/questions" element={user ? <Questions /> : <Navigate to="/" />} />
      </Routes>
    </Router>
  );
}

export default App;
