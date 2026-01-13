import { useMemo } from "react";
import {
  Box,
  Dialog,
  DialogContent,
  IconButton,
  Typography,
  Divider,
  Tooltip,
} from "@mui/material";
import CloseIcon from "@mui/icons-material/Close";
import ArrowBackIosNewIcon from "@mui/icons-material/ArrowBackIosNew";
import ArrowForwardIosIcon from "@mui/icons-material/ArrowForwardIos";
import FavoriteBorderIcon from "@mui/icons-material/FavoriteBorder";
import FavoriteIcon from "@mui/icons-material/Favorite";
import BookmarkBorderIcon from "@mui/icons-material/BookmarkBorder";
import BookmarkIcon from "@mui/icons-material/Bookmark";
import DownloadIcon from "@mui/icons-material/Download";
import { CommentSection } from "./CommentSection";
import { Photo } from "../api/client";

interface PhotoViewerModalProps {
  open: boolean;
  photos: Photo[];
  index: number;
  onClose: () => void;
  onNavigate: (nextIndex: number) => void;
  onToggleLike: (photo: Photo, next: boolean) => void;
  onToggleFavourite: (photo: Photo, next: boolean) => void;
  onDownloadWatermarked: (photo: Photo) => void;
  onDownloadOriginal?: (photo: Photo) => void;
  canDownloadOriginal?: (photo: Photo) => boolean;
}

export function PhotoViewerModal({
  open,
  photos,
  index,
  onClose,
  onNavigate,
  onToggleLike,
  onToggleFavourite,
  onDownloadWatermarked,
  onDownloadOriginal,
  canDownloadOriginal,
}: PhotoViewerModalProps) {
  const photo = photos[index];

  const imageSrc = useMemo(() => {
    if (!photo) return "";
    return photo.image_original || photo.image_watermarked || photo.image_thumbnail || "";
  }, [photo]);

  const visibilityLabel: Record<string, string> = {
    public: "Public",
    private: "Private",
    event_only: "Event only",
    role_based: "Role based",
  };

  if (!photo) return null;

  const createdAt = new Date(photo.created_at).toLocaleString();
  const canDownloadOrig = canDownloadOriginal ? canDownloadOriginal(photo) : !!onDownloadOriginal;

  return (
    <Dialog
      open={open}
      onClose={onClose}
      maxWidth="lg"
      fullWidth
      aria-labelledby="photo-viewer-title"
    >
      <DialogContent sx={{ p: 0 }}>
        <Box display="flex" height={{ xs: "auto", md: "80vh" }}>
          {/* Image area */}
          <Box
            sx={{
              flex: 2,
              bgcolor: "black",
              display: "flex",
              alignItems: "center",
              justifyContent: "center",
              position: "relative",
            }}
          >
              loading="lazy"
            <img
              src={imageSrc}
              alt="Event"
              style={{
                maxWidth: "100%",
                maxHeight: "80vh",
                objectFit: "contain",
              }}
            />

            {/* Navigation arrows */}
            {photos.length > 1 && (
              <>
                <IconButton
                  aria-label="Previous photo"
                  onClick={() => onNavigate(index - 1 < 0 ? photos.length - 1 : index - 1)}
                  sx={{
                    position: "absolute",
                    left: 8,
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "white",
                    bgcolor: "rgba(0,0,0,0.4)",
                    "&:hover": { bgcolor: "rgba(0,0,0,0.6)" },
                  }}
                >
                  <ArrowBackIosNewIcon fontSize="small" />
                </IconButton>
                <IconButton
                  aria-label="Next photo"
                  onClick={() => onNavigate((index + 1) % photos.length)}
                  sx={{
                    position: "absolute",
                    right: 8,
                    top: "50%",
                    transform: "translateY(-50%)",
                    color: "white",
                    bgcolor: "rgba(0,0,0,0.4)",
                    "&:hover": { bgcolor: "rgba(0,0,0,0.6)" },
                  }}
                >
                  <ArrowForwardIosIcon fontSize="small" />
                </IconButton>
              </>
            )}
          </Box>

          {/* Right panel: header + actions + comments */}
          <Box
            sx={{
              flex: 1.3,
              display: "flex",
              flexDirection: "column",
              minWidth: 0,
            }}
          >
            {/* Header */}
            <Box
              display="flex"
              alignItems="center"
              justifyContent="space-between"
              px={2}
              py={1.5}
            >
              <Box>
                <Typography id="photo-viewer-title" variant="subtitle1" fontWeight={600}>
                  {photo.uploaded_by_email}
                </Typography>
                <Typography variant="caption" color="text.secondary">
                  {createdAt}
                </Typography>
                <Typography variant="caption" display="block" color={photo.visibility === "private" ? "error.main" : "text.secondary"}>
                  {visibilityLabel[photo.visibility] || photo.visibility}
                </Typography>
              </Box>

              <IconButton aria-label="Close viewer" onClick={onClose}>
                <CloseIcon />
              </IconButton>
            </Box>

            <Divider />

            {/* Actions row */}
            <Box display="flex" alignItems="center" px={2} py={1} gap={1.5}>
              <IconButton
                aria-label={photo.liked_by_user ? "Unlike" : "Like"}
                onClick={() => onToggleLike(photo, !photo.liked_by_user)}
              >
                {photo.liked_by_user ? (
                  <FavoriteIcon color="error" />
                ) : (
                  <FavoriteBorderIcon />
                )}
              </IconButton>

              <IconButton
                aria-label={photo.favourited_by_user ? "Remove from favourites" : "Favourite"}
                onClick={() => onToggleFavourite(photo, !photo.favourited_by_user)}
              >
                {photo.favourited_by_user ? (
                  <BookmarkIcon color="primary" />
                ) : (
                  <BookmarkBorderIcon />
                )}
              </IconButton>

              <Tooltip title="Download watermarked">
                <IconButton aria-label="Download watermarked" onClick={() => onDownloadWatermarked(photo)}>
                  <DownloadIcon />
                </IconButton>
              </Tooltip>

              {canDownloadOrig && onDownloadOriginal && (
                <Tooltip title="Download original">
                  <IconButton aria-label="Download original" onClick={() => onDownloadOriginal(photo)}>
                    <DownloadIcon fontSize="small" />
                  </IconButton>
                </Tooltip>
              )}

              <Box flexGrow={1} />

              <Typography variant="caption" color="text.secondary">
                {photo.likes_count} likes · {photo.favourites_count} favourites · {photo.comments_count} comments
              </Typography>
            </Box>

            <Divider />

            {/* Comment section fills remaining height */}
            <Box flex={1} minHeight={0} px={2} py={1}>
              <CommentSection photoId={photo.id} />
            </Box>
          </Box>
        </Box>
      </DialogContent>
    </Dialog>
  );
}
