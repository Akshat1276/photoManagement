import { useEffect, useState, useRef } from "react";
import { useNotification } from "../components/NotificationProvider";
import Box from "@mui/material/Box";
import Tabs from "@mui/material/Tabs";
import Tab from "@mui/material/Tab";
import Card from "@mui/material/Card";
import CardContent from "@mui/material/CardContent";
import CardMedia from "@mui/material/CardMedia";
import CardActions from "@mui/material/CardActions";
import Grid from "@mui/material/Grid";
import Typography from "@mui/material/Typography";
import Button from "@mui/material/Button";
import Checkbox from "@mui/material/Checkbox";
import FormControlLabel from "@mui/material/FormControlLabel";
import DownloadIcon from '@mui/icons-material/Download';
import ThumbUpOffAltIcon from '@mui/icons-material/ThumbUpOffAlt';
import ThumbUpAltIcon from '@mui/icons-material/ThumbUpAlt';
import FavoriteBorderIcon from '@mui/icons-material/FavoriteBorder';
import FavoriteIcon from '@mui/icons-material/Favorite';
import {
  likePhotoRequest,
  unlikePhotoRequest,
  favouritePhotoRequest,
  unfavouritePhotoRequest,
  photoBatchOperationsRequest,
  downloadPhoto,
  downloadMultiplePhotos,
  fetchMyUploadsPageRequest,
  fetchMyLikesPageRequest,
  fetchMyFavouritesPageRequest,
  type Photo,
} from "../api/client";
import { PhotoViewerModal } from "../components/PhotoViewerModal";

/* ---------------- Utilities ---------------- */
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
export function MyLibraryPage() {
  const [tab, setTab] = useState(0);
  const [photos, setPhotos] = useState<Photo[]>([]);
  const [loading, setLoading] = useState(false);
  const [loadingMore, setLoadingMore] = useState(false);
  const [nextUrl, setNextUrl] = useState<string | null>(null);
  const [selectedIds, setSelectedIds] = useState<number[]>([]);
  const [downloading, setDownloading] = useState(false);
  const notify = useNotification();
  const [viewerOpen, setViewerOpen] = useState(false);
  const [viewerIndex, setViewerIndex] = useState(0);

  const loadMoreRef = useRef<HTMLDivElement | null>(null);

  /* ---------------- Fetching ---------------- */
  const loadInitialForTab = async (activeTab: number) => {
    setLoading(true);
    setPhotos([]);
    setNextUrl(null);
    try {
      if (activeTab === 0) {
        const page = await fetchMyUploadsPageRequest();
        setPhotos(page.results);
        setNextUrl(page.next);
      } else if (activeTab === 1) {
        const page = await fetchMyLikesPageRequest();
        setPhotos(page.results);
        setNextUrl(page.next);
      } else if (activeTab === 2) {
        const page = await fetchMyFavouritesPageRequest();
        setPhotos(page.results);
        setNextUrl(page.next);
      }
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    void loadInitialForTab(tab);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [tab]);

  // Infinite scroll per tab
  useEffect(() => {
    const el = loadMoreRef.current;
    if (!el) return;
    const observer = new IntersectionObserver((entries) => {
      const entry = entries[0];
      if (!entry.isIntersecting || !nextUrl || loadingMore) return;
      setLoadingMore(true);
      let fetchPage: (url: string) => Promise<any>;
      if (tab === 0) fetchPage = fetchMyUploadsPageRequest;
      else if (tab === 1) fetchPage = fetchMyLikesPageRequest;
      else fetchPage = fetchMyFavouritesPageRequest;
      fetchPage(nextUrl)
        .then((page) => {
          setPhotos((prev) => [...prev, ...page.results]);
          setNextUrl(page.next);
        })
        .finally(() => setLoadingMore(false));
    });
    observer.observe(el);
    return () => observer.disconnect();
  }, [tab, nextUrl, loadingMore]);

  /* ---------------- Selection ---------------- */
  const toggleSelected = (id: number) => {
    setSelectedIds((prev) =>
      prev.includes(id) ? prev.filter((x) => x !== id) : [...prev, id]
    );
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
      notify("Failed to download photo");
    }
  };

  const handleMultipleDownload = async (
    variant: "original" | "watermarked"
  ) => {
    if (!selectedIds.length) {
      notify("No photos selected");
      return;
    }

    setDownloading(true);
    try {
      const blob = await downloadMultiplePhotos(selectedIds, variant);
      triggerDownload(blob, `photos_${variant}.zip`);
    } catch {
      notify("Failed to download photos");
    } finally {
      setDownloading(false);
    }
  };

  const openViewerAt = (photoId: number) => {
    const idx = photos.findIndex((p) => p.id === photoId);
    if (idx === -1) return;
    setViewerIndex(idx);
    setViewerOpen(true);
  };

  /* ---------------- Render ---------------- */
  return (
    <Box>
      <Tabs value={tab} onChange={(_, v) => setTab(v)}>
        <Tab label="My Uploads" />
        <Tab label="Liked" />
        <Tab label="Favourite" />
      </Tabs>

      {selectedIds.length > 0 && (
        <Box mb={2} display="flex" gap={2}>
          <Button
            variant="outlined"
            color="error"
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

          <Button
            variant="contained"
            disabled={downloading}
            onClick={() => handleMultipleDownload("watermarked")}
          >
            Download Watermarked
          </Button>

          <Button
            variant="outlined"
            disabled={downloading}
            onClick={() => handleMultipleDownload("original")}
          >
            Download Original
          </Button>
        </Box>
      )}

      {!photos.length ? (
        <Typography mt={2}>
          {tab === 0 && "You haven't uploaded any photos yet."}
          {tab === 1 && "You haven't liked any photos yet."}
          {tab === 2 && "You haven't favourited any photos yet."}
        </Typography>
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
                  <CardMedia
                    component="img"
                    loading="lazy"
                    height="200"
                    image={src}
                    onClick={() => openViewerAt(photo.id)}
                    sx={{ cursor: "pointer" }}
                  />
                  <CardContent>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={selectedIds.includes(photo.id)}
                          onChange={() => toggleSelected(photo.id)}
                        />
                      }
                      label="Select"
                    />
                    <Typography variant="body2">
                      Uploaded by {photo.uploaded_by_name || photo.uploaded_by_email}
                    </Typography>
                    <Typography variant="body2">
                      Likes: {photo.likes_count} · Favourites:{" "}
                      {photo.favourites_count}
                    </Typography>

                    <Box mt={1} display="flex" gap={1}>
                      <Button size="small" onClick={() => handleSingleDownload(photo.id, "watermarked")} title="Download Watermarked">
                        <DownloadIcon /> <span style={{fontSize: '0.85em', marginLeft: 4}}>(watermarked)</span>
                      </Button>
                      <Button size="small" onClick={() => handleSingleDownload(photo.id, "original")} title="Download Original">
                        <DownloadIcon /> <span style={{fontSize: '0.85em', marginLeft: 4}}>(original)</span>
                      </Button>
                    </Box>
                  </CardContent>

                  <CardActions>
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={photo.liked_by_user || false}
                          onChange={(_, checked) => handleLike(photo.id, checked)}
							  icon={<ThumbUpOffAltIcon />}
							  checkedIcon={<ThumbUpAltIcon color="primary" />}
                        />
                      }
                      label=""
                    />
                    <FormControlLabel
                      control={
                        <Checkbox
                          checked={photo.favourited_by_user || false}
                          onChange={(_, checked) => handleFavourite(photo.id, checked)}
							  icon={<FavoriteBorderIcon />}
							  checkedIcon={<FavoriteIcon color="error" />}
                        />
                      }
                      label=""
                    />
                  </CardActions>
                </Card>
              </Grid>
            );
          })}
          {/* Sentinel for infinite scroll */}
          <Grid item xs={12} ref={loadMoreRef}>
            {(loading || loadingMore) && (
              <Typography align="center" variant="body2" sx={{ my: 2 }}>
                Loading photos...
              </Typography>
            )}
          </Grid>
        </Grid>
      )}

      <PhotoViewerModal
        open={viewerOpen}
        photos={photos}
        index={viewerIndex}
        onClose={() => setViewerOpen(false)}
        onNavigate={(nextIndex) => {
          if (!photos.length) return;
          const normalized = ((nextIndex % photos.length) + photos.length) % photos.length;
          setViewerIndex(normalized);
        }}
        onToggleLike={(photo, next) => handleLike(photo.id, next)}
        onToggleFavourite={(photo, next) => handleFavourite(photo.id, next)}
        onDownloadWatermarked={(photo) => handleSingleDownload(photo.id, "watermarked")}
        onDownloadOriginal={(photo) => handleSingleDownload(photo.id, "original")}
      />
    </Box>
  );
}
