import { useState } from "react";
import { useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { register } from "../../store/authSlice";
import { unwrapResult } from "@reduxjs/toolkit";

export function RegisterPage() {
  const dispatch = useAppDispatch();
  const { loading, error } = useAppSelector((s) => s.auth);
  const navigate = useNavigate();

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [fullName, setFullName] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const action = await dispatch(
        register({ email, password, full_name: fullName })
      );
      unwrapResult(action);
      navigate(`/verify-email?email=${encodeURIComponent(email)}`);
    } catch {
      // error handled in slice
    }
  };

  return (
    <Box display="flex" justifyContent="center" mt={4}>
      <Paper sx={{ p: 4, maxWidth: 450, width: "100%" }}>
        <Typography variant="h5" gutterBottom>
          Register
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Box component="form" onSubmit={handleSubmit}>
          <TextField
            label="Full Name"
            fullWidth
            margin="normal"
            value={fullName}
            onChange={(e) => setFullName(e.target.value)}
            required
          />
          <TextField
            label="Email"
            type="email"
            fullWidth
            margin="normal"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
          />
          <TextField
            label="Password"
            type="password"
            fullWidth
            margin="normal"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
          />
          <Button
            type="submit"
            variant="contained"
            color="primary"
            fullWidth
            sx={{ mt: 2 }}
            disabled={loading}
          >
            {loading ? "Registering..." : "Register"}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
