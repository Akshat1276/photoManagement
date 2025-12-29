import DownloadIcon from '@mui/icons-material/Download';
import DownloadForOfflineIcon from '@mui/icons-material/DownloadForOffline';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import BookmarkBorderIcon from '@mui/icons-material/BookmarkBorder';
import {
  downloadPhoto,
  downloadMultiplePhotos,
  batchUploadPhotosRequest,
  fetchEventBySlugRequest,
  fetchEventPhotosRequest,
  likePhotoRequest,
  unlikePhotoRequest,
  favouritePhotoRequest,
  unfavouritePhotoRequest,
  photoBatchOperationsRequest,
  type Event,
  type Photo,
} from "../api/client";

import { useEffect, useState, ChangeEvent, FormEvent } from "react";
import { useNotification } from "../components/NotificationProvider";
import { useParams } from "react-router-dom";
import {
  Box,
  Button,
  Card,
  CardActions,
  CardContent,
  CardMedia,
  Checkbox,
  FormControlLabel,
  Grid,
  MenuItem,
  Select,
  Typography,
} from "@mui/material";
import { useAppSelector } from "../store/hooks";

// --- Permission helpers ---
function isEventAdmin(user: any) {
  // Only true if user has custom Admin role (is_admin from backend)
  return !!user?.is_admin;
}
function isEventCoordinator(user: any, event: any) {
  return event?.coordinators?.includes(user?.email);
}
function isEventPhotographer(user: any, event: any) {
  return event?.photographers?.includes(user?.email);
}
function canUpload(user: any, event: any) {
  // Explicitly check is_admin in addition to other roles
  return isEventAdmin(user) || isEventCoordinator(user, event) || isEventPhotographer(user, event);
}
function canEditPhoto(user: any, event: any, photo: any) {
  return isEventAdmin(user) || isEventCoordinator(user, event) || photo.uploaded_by_email === user?.email;
}
function canDownloadOriginal(user: any, event: any, photo: any) {
  // Only allow if admin, coordinator, photographer, or photo is public/event_only/role_based/private
  if (!user) return false;
  if (isEventAdmin(user) || isEventCoordinator(user, event) || isEventPhotographer(user, event)) return true;
  return ["public", "event_only", "role_based", "private"].includes(photo.visibility);
}

/* ---------------- Utility ---------------- */
function triggerDownload(blob: Blob, filename: string) {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement("a");
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  a.remove();
  window.URL.revokeObjectURL(url);
}

/* ---------------- Component ---------------- */
export function EventGalleryPage() {
  const { slug } = useParams<{ slug: string }>();
  const user = useAppSelector((s) => s.auth.user);
  const notify = useNotification();

  const [event, setEvent] = useState<Event & { coordinators?: string[]; photographers?: string[] } | null>(null);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const [uploading, setUploading] = useState(false);
  const [files, setFiles] = useState<File[]>([]);
  const [visibility, setVisibility] = useState("public");

  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [downloading, setDownloading] = useState(false);

  /* ---------------- Initial Load ---------------- */
  useEffect(() => {
    if (!slug) return;

    const load = async () => {
      try {
        setLoading(true);
        const [eventData, photosData] = await Promise.all([
          fetchEventBySlugRequest(slug),
          fetchEventPhotosRequest(slug),
        ]);
        // Assume backend returns coordinators/photographers as emails array
        setEvent(eventData);
        setPhotos(photosData);
      } catch (err: any) {
        setError(err.response?.data?.detail || "Failed to load event or photos.");
      } finally {
        setLoading(false);
      }
    };

    load();
  }, [slug]);

  /* ---------------- Upload ---------------- */
  const handleFileChange = (e: ChangeEvent<HTMLInputElement>) => {
    setFiles(Array.from(e.target.files ?? []));
  };

  const handleUpload = async (e: FormEvent) => {
    e.preventDefault();
    if (!event || !files.length) return;

    try {
      setUploading(true);
      const newPhotos = await batchUploadPhotosRequest({
        eventId: event.id,
        files,
        visibility,
      });
      setPhotos((prev) => [...newPhotos, ...prev]);
      setFiles([]);
      notify("Photo(s) uploaded successfully");
    } catch (err: any) {
      setError(err.response?.data?.detail || "Failed to upload photos.");
    } finally {
      setUploading(false);
    }
  };

  /* ---------------- Like / Favourite ---------------- */
  const handleLike = async (photoId: number, checked: boolean) => {
    setPhotos((prev) =>
      prev.map((p) =>
        p.id === photoId
          ? {
              ...p,
              likes_count: checked
                ? p.likes_count + 1
                : Math.max(0, p.likes_count - 1),
              liked_by_user: checked,
            }
          : p
      )
    );

    checked
      ? await likePhotoRequest(photoId)
      : await unlikePhotoRequest(photoId);

    notify(checked ? "Photo liked" : "Photo unliked");

    if (slug) setPhotos(await fetchEventPhotosRequest(slug));
  };

  const handleFavourite = async (photoId: number, checked: boolean) => {
    setPhotos((prev) =>
      prev.map((p) =>
        p.id === photoId
          ? {
              ...p,
              favourites_count: checked
                ? p.favourites_count + 1
                : Math.max(0, p.favourites_count - 1),
              favourited_by_user: checked,
            }
          : p
      )
    );

    checked
      ? await favouritePhotoRequest(photoId)
      : await unfavouritePhotoRequest(photoId);

    notify(checked ? "Photo favourited" : "Photo unfavourited");

    if (slug) setPhotos(await fetchEventPhotosRequest(slug));
  };

  /* ---------------- Selection ---------------- */
  const toggleSelected = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
  };

  /* ---------------- Downloads ---------------- */
  const handleSingleDownload = async (
    photoId: number,
    variant: "original" | "watermarked" = "watermarked"
  ) => {
    try {
      const blob = await downloadPhoto(photoId, variant);
      triggerDownload(blob, `photo_${photoId}_${variant}.jpg`);
    } catch {
      notify("Failed to download photo.");
    }
  };

  const handleMultipleDownload = async (
    variant: "original" | "watermarked"
  ) => {
    if (!selectedIds.length) {
      notify("No photos selected.");
      return;
    }

    setDownloading(true);
    try {
      const blob = await downloadMultiplePhotos(selectedIds, variant);
      triggerDownload(blob, `photos_${variant}.zip`);
    } catch {
      notify("Failed to download photos.");
    } finally {
      setDownloading(false);
    }
  };

  /* ---------------- Render ---------------- */
  return (
    <Box>
      {/* Debug info for troubleshooting permissions */}
      <Box mb={2} p={2} bgcolor="#f5f5f5" borderRadius={2} fontSize={13}>
        <b>Debug Info:</b>
        <pre style={{ whiteSpace: 'pre-wrap', wordBreak: 'break-all', fontSize: 12 }}>
          user: {JSON.stringify(user, null, 2)}
          {"\n"}
          event: {JSON.stringify(event, null, 2)}
        </pre>
      </Box>
      {event && (
        <Box mb={3}>
          <Typography variant="h5">{event.title}</Typography>
          {event.description && (
            <Typography color="text.secondary">
              {event.description}
            </Typography>
          )}
        </Box>
      )}

      {user && event && canUpload(user, event) && (
        <Box
          component="form"
          onSubmit={handleUpload}
          mb={3}
          display="flex"
          gap={2}
          alignItems="center"
          flexWrap="wrap"
        >
          <Button variant="outlined" component="label">
            Select Photos
            <input hidden multiple type="file" accept="image/*" onChange={handleFileChange} />
          </Button>

          <Typography variant="body2">
            {files.length ? `${files.length} file(s) selected` : "No files selected"}
          </Typography>

          <Select
            size="small"
            value={visibility}
            onChange={(e) => setVisibility(e.target.value)}
          >
            <MenuItem value="public">Public</MenuItem>
            <MenuItem value="private">Private</MenuItem>
            <MenuItem value="event_only">Event only</MenuItem>
            <MenuItem value="role_based">Role based</MenuItem>
          </Select>

          <Button type="submit" variant="contained" disabled={!files.length || uploading}>
            {uploading ? "Uploading..." : "Upload"}
          </Button>
        </Box>
      )}

      {user && selectedIds.length > 0 && (
        <Box mb={2} display="flex" gap={2}>
          {/* Only allow delete if user can edit all selected */}
          {selectedIds.every(id => {
            const photo = photos.find(p => p.id === id);
            return photo && canEditPhoto(user, event, photo);
          }) && (
            <Button
              color="error"
              variant="outlined"
              onClick={async () => {
                await photoBatchOperationsRequest({
                  photo_ids: selectedIds,
                  action: "delete",
                });
                setPhotos((prev) =>
                  prev.filter((p) => !selectedIds.includes(p.id))
                );
                setSelectedIds([]);
                notify("Photo(s) deleted");
              }}
            >
              Delete Selected
            </Button>
          )}

          <Button
            variant="contained"
            disabled={downloading}
            onClick={() => handleMultipleDownload("watermarked")}
          >
            Download Watermarked
          </Button>

          {/* Only allow download original if user can download all originals */}
          {selectedIds.every(id => {
            const photo = photos.find(p => p.id === id);
            return photo && canDownloadOriginal(user, event, photo);
          }) && (
            <Button
              variant="outlined"
              disabled={downloading}
              onClick={() => handleMultipleDownload("original")}
            >
              Download Original
            </Button>
          )}
        </Box>
      )}

      {!photos.length ? (
        <Typography>No photos for this event yet.</Typography>
      ) : (
        <Grid container spacing={2}>
          {photos.map((photo) => {
            const src =
              photo.image_thumbnail ||
              photo.image_watermarked ||
              photo.image_original;

            return (
              <Grid item xs={12} sm={6} md={4} key={photo.id}>
                <Card>
                  <CardMedia component="img" height="200" image={src} />
                  <CardContent>
                    {user && (
                      <FormControlLabel
                        control={
                          <Checkbox
                            checked={selectedIds.includes(photo.id)}
                            onChange={() => toggleSelected(photo.id)}
                          />
                        }
                        label="Select"
                      />
                    )}

                    <Typography variant="body2">
                      Uploaded by {photo.uploaded_by_email}
                    </Typography>

                    <Typography variant="body2">
                      Likes: {photo.likes_count} · Favourites: {photo.favourites_count}
                    </Typography>

                    <Box mt={1} display="flex" gap={1}>
                      <Button size="small" onClick={() => handleSingleDownload(photo.id, "watermarked")} title="Download Watermarked">
                        <DownloadIcon /> <span style={{fontSize: '0.85em', marginLeft: 4}}>(watermarked)</span>
                      </Button>
                      {canDownloadOriginal(user, event, photo) && (
                        <Button size="small" onClick={() => handleSingleDownload(photo.id, "original")} title="Download Original">
                          <DownloadIcon /> <span style={{fontSize: '0.85em', marginLeft: 4}}>(original)</span>
                        </Button>
                      )}
                    </Box>
                  </CardContent>

                  {user && (
                    <CardActions>
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={photo.liked_by_user || false}
                              onChange={(_, checked) => handleLike(photo.id, checked)}
                              icon={<FavoriteBorderIcon />}
                              checkedIcon={<FavoriteBorderIcon color="error" />}
                            />
                          }
                          label=""
                        />
                        <FormControlLabel
                          control={
                            <Checkbox
                              checked={photo.favourited_by_user || false}
                              onChange={(_, checked) => handleFavourite(photo.id, checked)}
                              icon={<BookmarkBorderIcon />}
                              checkedIcon={<BookmarkBorderIcon color="primary" />}
                            />
                          }
                          label=""
                        />
                    </CardActions>
                  )}
                </Card>
              </Grid>
            );
          })}
        </Grid>
      )}
    </Box>
  );
}
