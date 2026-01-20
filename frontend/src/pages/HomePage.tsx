import { Box, Button, Typography } from "@mui/material";
import { Link as RouterLink } from "react-router-dom";
import { useAppSelector } from "../store/hooks";

export function HomePage() {
  const user = useAppSelector((s) => s.auth.user);

  return (
    <Box textAlign="center" mt={6}>
      <Typography variant="h3" gutterBottom>
        Smart Event Photo Management
      </Typography>
      <Typography variant="h6" color="text.secondary" gutterBottom>
        Browse events, find your favourite moments, and manage your uploads.
      </Typography>
      <Box mt={4} display="flex" justifyContent="center" gap={2}>
        <Button
          variant="contained"
          size="large"
          color="primary"
          component={RouterLink}
          to="/events"
        >
          Browse Events
        </Button>
        {!user && (
          <Button
            variant="outlined"
            size="large"
            color="primary"
            component={RouterLink}
            to="/login"
          >
            Login / Register
          </Button>
        )}
      </Box>
    </Box>
  );
}
