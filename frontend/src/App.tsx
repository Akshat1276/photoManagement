
import { Box } from "@mui/material";
import { NotificationProvider } from "./components/NotificationProvider";
import { Routes, Route, Navigate } from "react-router-dom";
import { useEffect } from "react";
import { useAppDispatch } from "./store/hooks";
import { fetchProfile } from "./store/authSlice";
import { AppLayout } from "./components/layout/AppLayout";
import { LoginPage } from "./components/auth/LoginPage";
import { RegisterPage } from "./components/auth/RegisterPage";
import { VerifyEmailPage } from "./components/auth/VerifyEmailPage";
import { HomePage } from "./pages/HomePage";
import { EventsPage } from "./pages/EventsPage";
import { EventGalleryPage } from "./pages/EventGalleryPage";
import { MyLibraryPage } from "./pages/MyLibraryPage";
import { PhotographerDashboardPage } from "./pages/PhotographerDashboardPage";
import { ProtectedRoute } from "./components/common/ProtectedRoute";
import { PhotosOfMePage } from "./pages/PhotosOfMePage";

export default function App() {
  const dispatch = useAppDispatch();
  useEffect(() => {
    dispatch(fetchProfile());
  }, [dispatch]);
  return (
    <NotificationProvider>
      <Box sx={{ minHeight: "100vh", bgcolor: "background.default" }}>
        <AppLayout>
          <Routes>
            <Route path="/" element={<HomePage />} />
            <Route path="/login" element={<LoginPage />} />
            <Route path="/register" element={<RegisterPage />} />
            <Route path="/verify-email" element={<VerifyEmailPage />} />
            <Route path="/events" element={<EventsPage />} />
            <Route path="/events/:slug" element={<EventGalleryPage />} />
            <Route
              path="/my-library"
              element={
                <ProtectedRoute>
                  <MyLibraryPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/photos-of-me"
              element={
                <ProtectedRoute>
                  <PhotosOfMePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="/photographer/dashboard"
              element={
                <ProtectedRoute requiredRole="Photographer">
                  <PhotographerDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </AppLayout>
      </Box>
    </NotificationProvider>
  );
}
