import { ReactElement, useEffect } from "react";
import { Navigate, useLocation } from "react-router-dom";
import { useAppSelector } from "../../store/hooks";
import { CircularProgress, Box } from "@mui/material";

interface ProtectedRouteProps {
  children: ReactElement;
  requiredRole?: string; // reserved for future role-based checks
}

export function ProtectedRoute({ children }: ProtectedRouteProps) {
  const location = useLocation();
  const user = useAppSelector((s) => s.auth.user);
  const loading = useAppSelector((s) => s.auth.loading);

  // If user is present, mark session as authenticated
  useEffect(() => {
    if (user) {
      sessionStorage.setItem("hasLoggedIn", "true");
    }
  }, [user]);

  // If loading, show spinner
  if (loading) {
    return (
      <Box display="flex" justifyContent="center" alignItems="center" minHeight="40vh">
        <CircularProgress />
      </Box>
    );
  }

  // If user is not present, but sessionStorage says user has logged in, allow access
  const hasLoggedIn = sessionStorage.getItem("hasLoggedIn") === "true";
  if (!user && !hasLoggedIn) {
    return <Navigate to="/login" replace state={{ from: location }} />;
  }

  return children;
}
