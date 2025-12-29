import { useEffect, useState } from "react";
import { useLocation, useNavigate } from "react-router-dom";
import {
  Alert,
  Box,
  Button,
  Paper,
  TextField,
  Typography,
} from "@mui/material";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { verifyEmail } from "../../store/authSlice";
import { unwrapResult } from "@reduxjs/toolkit";

function useQuery() {
  return new URLSearchParams(useLocation().search);
}

export function VerifyEmailPage() {
  const dispatch = useAppDispatch();
  const { loading, error } = useAppSelector((s) => s.auth);
  const navigate = useNavigate();
  const query = useQuery();

  const [email, setEmail] = useState("");
  const [code, setCode] = useState("");

  useEffect(() => {
    const qEmail = query.get("email");
    if (qEmail) {
      setEmail(qEmail);
    }
  }, [query]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      const action = await dispatch(verifyEmail({ email, code }));
      unwrapResult(action);
      navigate("/login");
    } catch {
      // error handled in slice
    }
  };

  return (
    <Box display="flex" justifyContent="center" mt={4}>
      <Paper sx={{ p: 4, maxWidth: 450, width: "100%" }}>
        <Typography variant="h5" gutterBottom>
          Verify Email
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
            label="Verification Code"
            fullWidth
            margin="normal"
            value={code}
            onChange={(e) => setCode(e.target.value)}
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
            {loading ? "Verifying..." : "Verify"}
          </Button>
        </Box>
      </Paper>
    </Box>
  );
}
