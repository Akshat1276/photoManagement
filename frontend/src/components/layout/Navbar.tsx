import {
  AppBar,
  Box,
  Button,
  IconButton,
  Toolbar,
  Typography,
} from "@mui/material";
import PhotoCameraIcon from "@mui/icons-material/PhotoCamera";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { logout } from "../../store/authSlice";

export function Navbar() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((s) => s.auth);

  const handleLogout = () => {
    dispatch(logout()).then(() => navigate("/"));
  };

  return (
    <AppBar position="static" color="primary">
      <Toolbar>
        <IconButton edge="start" color="inherit" sx={{ mr: 1 }} disabled tabIndex={-1} style={{ pointerEvents: "none" }}>
          <PhotoCameraIcon />
        </IconButton>
        <Typography
          variant="h6"
          component={RouterLink}
          to="/"
          color="inherit"
          sx={{ textDecoration: "none", flexGrow: 1 }}
        >
          Smart Event Photos
        </Typography>
        <Box sx={{ display: "flex", gap: 1 }}>
          <Button color="inherit" component={RouterLink} to="/events">
            Events
          </Button>
          {user && (
            <>
              <Button color="inherit" component={RouterLink} to="/my-library">
                My Library
              </Button>
              <Button color="inherit" component={RouterLink} to="/photos-of-me">
                Photos of Me
              </Button>
              <Button
                color="inherit"
                component={RouterLink}
                to="/photographer/dashboard"
              >
                Photographer
              </Button>
            </>
          )}
          {!user ? (
            <>
              <Button color="inherit" component={RouterLink} to="/login">
                Login
              </Button>
              <Button color="inherit" component={RouterLink} to="/register">
                Register
              </Button>
            </>
          ) : (
            <Button color="inherit" onClick={handleLogout}>
              Logout
            </Button>
          )}
        </Box>
      </Toolbar>
    </AppBar>
  );
}
