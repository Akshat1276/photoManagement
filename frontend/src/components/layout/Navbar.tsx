import React from "react";
import {
  AppBar,
  Box,
  Button,
  Divider,
  Drawer,
  IconButton,
  List,
  ListItemButton,
  ListItemText,
  Toolbar,
  Typography,
  useMediaQuery,
} from "@mui/material";
import PhotoCameraIcon from "@mui/icons-material/PhotoCamera";
import MenuIcon from "@mui/icons-material/Menu";
import DarkModeIcon from "@mui/icons-material/DarkMode";
import LightModeIcon from "@mui/icons-material/LightMode";
import { Link as RouterLink, useNavigate } from "react-router-dom";
import { useAppDispatch, useAppSelector } from "../../store/hooks";
import { logout } from "../../store/authSlice";
import { useTheme } from "@mui/material/styles";
import { useColorMode } from "../../theme/CustomThemeProvider";

const drawerWidth = 260;

export function Navbar() {
  const navigate = useNavigate();
  const dispatch = useAppDispatch();
  const { user } = useAppSelector((s) => s.auth);
  const theme = useTheme();
  const { mode, toggleColorMode } = useColorMode();
  const isMobile = useMediaQuery(theme.breakpoints.down("md"));
  const [mobileOpen, setMobileOpen] = React.useState(false);

  const handleLogout = () => {
    dispatch(logout()).then(() => navigate("/"));
  };

  const handleDrawerToggle = () => {
    setMobileOpen((prev) => !prev);
  };

  const commonLinks = (
    <>
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
    </>
  );

  const drawer = (
    <Box sx={{ width: drawerWidth }} role="presentation" onClick={handleDrawerToggle}>
      <Box sx={{ p: 2 }}>
        <Typography variant="subtitle1" fontWeight={600} gutterBottom>
          Smart Event Photos
        </Typography>
      </Box>
      <Divider />
      <List>
        <ListItemButton component={RouterLink} to="/events">
          <ListItemText primary="Events" />
        </ListItemButton>
        {user && (
          <>
            <ListItemButton component={RouterLink} to="/my-library">
              <ListItemText primary="My Library" />
            </ListItemButton>
            <ListItemButton component={RouterLink} to="/photos-of-me">
              <ListItemText primary="Photos of Me" />
            </ListItemButton>
          </>
        )}
      </List>
      <Divider />
      <List>
        {!user ? (
          <>
            <ListItemButton component={RouterLink} to="/login">
              <ListItemText primary="Login" />
            </ListItemButton>
            <ListItemButton component={RouterLink} to="/register">
              <ListItemText primary="Register" />
            </ListItemButton>
          </>
        ) : (
          <ListItemButton onClick={handleLogout}>
            <ListItemText primary="Logout" />
          </ListItemButton>
        )}
      </List>
    </Box>
  );

  return (
    <>
      <AppBar
        position="sticky"
        color="transparent"
        elevation={0}
        sx={{
          borderBottom: 1,
          borderColor: "divider",
          bgcolor: "background.paper",
        }}
      >
        <Toolbar>
          <IconButton
            edge="start"
            color="inherit"
            sx={{ mr: 1 }}
            disabled
            style={{ pointerEvents: "none" }}
          >
            <PhotoCameraIcon />
          </IconButton>
          <Typography
            variant="h6"
            component={RouterLink}
            to="/"
            color="inherit"
            sx={{ textDecoration: "none", flexGrow: 1, fontWeight: 600 }}
          >
            Smart Event Photos
          </Typography>
          <Box sx={{ display: { xs: "none", md: "flex" }, alignItems: "center", gap: 1 }}>
            {commonLinks}
            <IconButton color="inherit" onClick={toggleColorMode} aria-label="Toggle light/dark theme">
              {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
          </Box>
          <Box sx={{ display: { xs: "flex", md: "none" }, alignItems: "center", gap: 0.5 }}>
            <IconButton color="inherit" onClick={toggleColorMode} aria-label="Toggle light/dark theme">
              {mode === "dark" ? <LightModeIcon /> : <DarkModeIcon />}
            </IconButton>
            <IconButton color="inherit" edge="end" onClick={handleDrawerToggle} aria-label="Open navigation menu">
              <MenuIcon />
            </IconButton>
          </Box>
        </Toolbar>
      </AppBar>
      <Drawer
        anchor="right"
        open={mobileOpen}
        onClose={handleDrawerToggle}
        ModalProps={{ keepMounted: true }}
        sx={{
          display: { xs: "block", md: "none" },
          "& .MuiDrawer-paper": { width: drawerWidth },
        }}
      >
        {drawer}
      </Drawer>
    </>
  );
}
