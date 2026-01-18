import { useEffect, useState, useRef, ChangeEvent, FormEvent } from "react";
import { Photo, fetchPhotosOfMePageRequest, uploadReferenceSelfieRequest, refreshPhotosOfMeRequest } from "../api/client";
import Box from "@mui/material/Box";
import Grid from "@mui/material/Grid";
import Card from "@mui/material/Card";
import CardMedia from "@mui/material/CardMedia";
import CardContent from "@mui/material/CardContent";
import Typography from "@mui/material/Typography";
import CircularProgress from "@mui/material/CircularProgress";
import Button from "@mui/material/Button";
import Alert from "@mui/material/Alert";

export function PhotosOfMePage() {
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(true);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [selfie, setSelfie] = useState<File | null>(null);
  const [uploading, setUploading] = useState(false);
  const [uploadError, setUploadError] = useState<string | null>(null);
  const [uploadSuccess, setUploadSuccess] = useState<string | null>(null);
  const [refreshing, setRefreshing] = useState(false);
  const [refreshMessage, setRefreshMessage] = useState<string | null>(null);

  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  const loadMatches = async () => {
    setLoading(true);
    try {
      const page = await fetchPhotosOfMePageRequest();
      setPhotos(page.results);
      setNextUrl(page.next);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    // Initial load uses cached matches only (no heavy scan)
    void loadMatches();
  }, []);

  // Infinite scroll for cached matches
  useEffect(() => {
    const el = loadMoreRef.current;
    if (!el) return;
    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0];
      if (!entry.isIntersecting || !nextUrl || loadingMore) return;
      setLoadingMore(true);
      fetchPhotosOfMePageRequest(nextUrl)
        .then((page) => {
          setPhotos((prev) => [...prev, ...page.results]);
          setNextUrl(page.next);
        })
        .finally(() => setLoadingMore(false));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [nextUrl, loadingMore]);

  const handleSelfieChange = (e: ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setSelfie(e.target.files[0]);
    }
  };

  const handleSelfieUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!selfie) return;
    setUploading(true);
    setUploadError(null);
    setUploadSuccess(null);
    try {
      await uploadReferenceSelfieRequest(selfie);
      setUploadSuccess("Selfie uploaded successfully! Use Refresh to scan photos for matches.");
    } catch (err: any) {
      setUploadError(err?.response?.data?.detail || "Upload failed. Try again.");
    } finally {
      setUploading(false);
    }
  };

  const handleRefresh = async () => {
    setRefreshing(true);
    setRefreshMessage(null);
    try {
      const result = await refreshPhotosOfMeRequest();
      await loadMatches();
      setRefreshMessage(
        `Processed ${result.processed_photos} new photo(s), found ${result.new_matches} new match(es). Total matches: ${result.total_matches}.`
      );
    } catch (err: any) {
      setRefreshMessage(err?.response?.data?.detail || "Failed to refresh matches.");
    } finally {
      setRefreshing(false);
    }
  };

  return (
    <Box sx={{ p: 2 }}>
      <Typography variant="h4" gutterBottom>
        Photos of Me
      </Typography>
      <Box sx={{ display: "flex", alignItems: "center", gap: 2, mb: 2 }}>
        <Button variant="outlined" onClick={handleRefresh} disabled={refreshing}>
          {refreshing ? "Refreshing..." : "Refresh matches"}
        </Button>
        {refreshMessage && (
          <Typography variant="body2" color="text.secondary">
            {refreshMessage}
          </Typography>
        )}
      </Box>
      <Box component="form" onSubmit={handleSelfieUpload} sx={{ mb: 3 }}>
        <Typography variant="h6">Upload Reference Selfie</Typography>
        <input
          type="file"
          accept="image/*"
          onChange={handleSelfieChange}
          disabled={uploading}
          style={{ marginTop: 8, marginBottom: 8 }}
        />
        <Button type="submit" variant="contained" disabled={!selfie || uploading}>
          {uploading ? "Uploading..." : "Upload Selfie"}
        </Button>
        {uploadError && <Alert severity="error" sx={{ mt: 2 }}>{uploadError}</Alert>}
        {uploadSuccess && <Alert severity="success" sx={{ mt: 2 }}>{uploadSuccess}</Alert>}
      </Box>
      {loading ? (
        <Box sx={{ display: "flex", justifyContent: "center", mt: 4 }}>
          <CircularProgress />
        </Box>
      ) : photos.length === 0 ? (
        <Typography>No photos found where you were detected.</Typography>
      ) : (
        <Grid container spacing={2}>
          {photos.map((photo) => (
            <Grid item xs={12} sm={6} md={4} lg={3} key={photo.id}>
              <Card>
                <CardMedia
                  component="img"
                  loading="lazy"
                  height="200"
                  image={photo.image_thumbnail || photo.image_watermarked || photo.image_original}
                  alt={"Photo #" + photo.id}
                />
                <CardContent>
                  <Typography variant="body2" color="text.secondary">
          Uploaded by: {photo.uploaded_by_name || photo.uploaded_by_email}
          </Typography>
                  <Typography variant="caption" color="text.secondary">
                    {new Date(photo.created_at).toLocaleString()}
                  </Typography>
                </CardContent>
              </Card>
            </Grid>
          ))}
          {/* Sentinel for infinite scroll */}
          <Grid item xs={12} ref={loadMoreRef}>
            {loadingMore && (
              <Typography align="center" variant="body2" sx={{ my: 2 }}>
                Loading more matches...
              </Typography>
            )}
          </Grid>
        </Grid>
      )}
    </Box>
  );
}
