import { useState } from "react";
import { useNavigate, useLocation } from "react-router-dom";
import {
  Box,
  Button,
  Divider,
  Paper,
  TextField,
  Typography,
  Alert,
} from "@mui/material";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { login } from "../../store/authSlice";
import { unwrapResult } from "@reduxjs/toolkit";
import { api } from "../../api/client";

export function LoginPage() {
  const dispatch = useAppDispatch();
  const { loading, error } = useAppSelector((s) => s.auth);
  const navigate = useNavigate();
  const location = useLocation() as any;
  const from = location.state?.from?.pathname || "/";

  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const action = await dispatch(login({ email, password }));
      unwrapResult(action);
      navigate(from, { replace: true });
    } catch {
      // error already handled in slice
    }
  };

  const handleOmniportLogin = async () => {
    try {
      const res = await api.get<{ authorization_url: string }>(
        "/auth/omniport/login/",
      );
      const url = res.data.authorization_url;
      if (url) {
        window.location.href = url;
      }
    } catch {
      // If Omniport is not configured, do nothing for now
    }
  };

  return (
    <Box display="flex" justifyContent="center" mt={4}>
      <Paper sx={{ p: 4, maxWidth: 400, width: "100%" }}>
        <Typography variant="h5" gutterBottom>
          Login
        </Typography>
        {error && (
          <Alert severity="error" sx={{ mb: 2 }}>
            {error}
          </Alert>
        )}
        <Box component="form" onSubmit={handleSubmit}>
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
            {loading ? "Logging in..." : "Login"}
          </Button>
        </Box>
        <Divider sx={{ my: 3 }}>or</Divider>
        <Button
          variant="outlined"
          color="primary"
          fullWidth
          onClick={handleOmniportLogin}
        >
          Login with Omniport
        </Button>
      </Paper>
    </Box>
  );
}
