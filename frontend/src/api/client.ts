// Upload reference selfie for face profile
export async function uploadReferenceSelfieRequest(file: File): Promise<any> {
  const formData = new FormData();
  formData.append("selfie", file);
  const res = await api.post("/auth/face-profile/upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}
// Fetch photos where the current user was detected (Photos of Me)
export async function fetchPhotosOfMeRequest(): Promise<Photo[]> {
  const res = await api.get<Photo[]>("/photos/photos-of-me/");
  return res.data;
}
// Download a single photo (returns a Blob)
export async function downloadPhoto(photoId: number, variant: "original" | "watermarked" = "watermarked"): Promise<Blob> {
  const res = await api.get(`/photos/${photoId}/download/?variant=${variant}`, {
    responseType: "blob",
  });
  return res.data;
}

// Download multiple photos as a zip (returns a Blob)
export async function downloadMultiplePhotos(photoIds: number[], variant: "original" | "watermarked" = "watermarked"): Promise<Blob> {
  const res = await api.post(
    "/photos/download-multiple/",
    { photo_ids: photoIds, variant },
    { responseType: "blob" }
  );
  return res.data;
}
// ...existing code...

// Fetch photos liked by the current user
export async function fetchMyLikesRequest(): Promise<Photo[]> {
  const res = await api.get<Photo[]>("/photos/my-likes/");
  return res.data;
}

// Fetch photos favourited by the current user
export async function fetchMyFavouritesRequest(): Promise<Photo[]> {
  const res = await api.get<Photo[]>("/photos/my-favourites/");
  return res.data;
}
import axios from "axios";

export const api = axios.create({
  baseURL: "/api",
  withCredentials: true,
});

api.defaults.xsrfCookieName = "csrftoken";
api.defaults.xsrfHeaderName = "X-CSRFToken";

// -------- Auth --------
export interface Profile {
  email: string;
  full_name: string;
  bio: string;
  batch: string;
  department: string;
  profile_pic_url: string;
  is_admin: boolean;
}

export async function loginRequest(data: { email: string; password: string }) {
  await api.post("/auth/login/", data);
}

export async function logoutRequest() {
  await api.post("/auth/logout/");
}

export async function registerRequest(data: {
  email: string;
  password: string;
  full_name: string;
}) {
  await api.post("/auth/register/", data);
}

export async function verifyEmailRequest(data: { email: string; code: string }) {
  await api.post("/auth/verify-email/", data);
}

export async function fetchProfileRequest(): Promise<Profile> {
  const res = await api.get<Profile>("/auth/me/");
  return res.data;
}
export interface Event {
  id: number;
  title: string;
  slug: string;
  description: string;
  start_datetime: string;
  end_datetime: string | null;
  cover_url: string;
  created_by: number;
  created_by_email: string;
  created_at: string;
}

export interface Photo {
  id: number;
  event: number;
  uploaded_by: number;
  uploaded_by_email: string;
  image_original: string;
  image_thumbnail: string | null;
  image_watermarked: string | null;
  taken_at: string | null;
  camera_model: string;
  visibility: string;
  metadata: Record<string, unknown>;
  created_at: string;
  likes_count: number;
  favourites_count: number;
  comments_count: number;
  liked_by_user?: boolean;
  favourited_by_user?: boolean;
}

// -------- Photo comments --------
export interface PhotoComment {
  id: number;
  photo: number;
  user: number;
  user_email: string;
  parent_comment: number | null;
  content: string;
  created_at: string;
}

export async function fetchPhotoCommentsRequest(photoId: number): Promise<PhotoComment[]> {
  const res = await api.get<PhotoComment[]>(`/photos/${photoId}/comments/`);
  return res.data;
}

export async function createPhotoCommentRequest(photoId: number, data: {
  content: string;
  parent_comment?: number | null;
}): Promise<PhotoComment> {
  const res = await api.post<PhotoComment>(`/photos/${photoId}/comments/`, data);
  return res.data;
}

export async function updatePhotoCommentRequest(commentId: number, data: {
  content: string;
}): Promise<PhotoComment> {
  const res = await api.patch<PhotoComment>(`/photos/comments/${commentId}/`, data);
  return res.data;
}

export async function deletePhotoCommentRequest(commentId: number): Promise<void> {
  await api.delete(`/photos/comments/${commentId}/`);
}
export const BACKEND_URL = "http://127.0.0.1:8000";


export interface PaginatedResponse<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export async function fetchEventsRequest(url: string = "/events/"): Promise<PaginatedResponse<Event>> {
  const res = await api.get<PaginatedResponse<Event>>(url);
  return res.data;
}

export async function fetchEventBySlugRequest(slug: string): Promise<Event> {
  const res = await api.get<Event>(`/events/${slug}/`);
  return res.data;
}

export async function fetchEventPhotosRequest(slug: string): Promise<Photo[]> {
  const res = await api.get<Photo[]>(`/events/${slug}/photos/`);
  return res.data;
}

export async function fetchMyUploadsRequest(): Promise<Photo[]> {
  const res = await api.get<Photo[]>("/photos/my-uploads/");
  return res.data;
}

export async function createEventRequest(data: {
  title: string;
  slug: string;
  description?: string;
  start_datetime: string;
  end_datetime?: string | null;
  cover_url?: string;
}): Promise<Event> {
  const res = await api.post<Event>("/events/", data);
  return res.data;
}

export async function deleteEventRequest(slug: string): Promise<void> {
  await api.delete(`/events/${slug}/`);
}

// Upload a single photo
export async function uploadPhotoRequest(params: {
  eventId: number;
  file: File;
  visibility?: string;
}): Promise<Photo> {
  const formData = new FormData();
  formData.append("event", String(params.eventId));
  formData.append("image_original", params.file);
  if (params.visibility) {
    formData.append("visibility", params.visibility);
  }
  const res = await api.post<Photo>("/photos/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// Batch upload multiple photos for an event
export async function batchUploadPhotosRequest(params: {
  eventId: number;
  files: File[];
  visibility?: string;
}): Promise<Photo[]> {
  const formData = new FormData();
  formData.append("event", String(params.eventId));
  if (params.visibility) {
    formData.append("visibility", params.visibility);
  }
  params.files.forEach((file) => {
    formData.append("images", file);
  });
  const res = await api.post<Photo[]>("/photos/batch-upload/", formData, {
    headers: { "Content-Type": "multipart/form-data" },
  });
  return res.data;
}

// Photo batch operations (delete, move, update_visibility, set_tags)
export interface PhotoBatchOperationsPayload {
  photo_ids: number[];
  action: "delete" | "move" | "update_visibility" | "set_tags";
  target_event?: number;
  visibility?: string;
  tags?: string[];
}

export async function photoBatchOperationsRequest(
  payload: PhotoBatchOperationsPayload,
): Promise<{ detail: string }> {
  const res = await api.post<{ detail: string }>(
    "/photos/batch-operations/",
    payload,
  );
  return res.data;
}

// Like / unlike
export interface LikeResponse {
  detail: string;
  liked: boolean;
  likes_count: number;
}

export async function likePhotoRequest(photoId: number): Promise<LikeResponse> {
  const res = await api.post<LikeResponse>(`/photos/${photoId}/like/`);
  return res.data;
}

export async function unlikePhotoRequest(
  photoId: number,
): Promise<LikeResponse> {
  const res = await api.delete<LikeResponse>(`/photos/${photoId}/like/`);
  return res.data;
}
// Favourite / unfavourite
export interface FavouriteResponse {
  detail: string;
  favourited: boolean;
  favourites_count: number;
}

export async function favouritePhotoRequest(
  photoId: number,
): Promise<FavouriteResponse> {
  const res = await api.post<FavouriteResponse>(
    `/photos/${photoId}/favourite/`,
  );
  return res.data;
}

export async function unfavouritePhotoRequest(
  photoId: number,
): Promise<FavouriteResponse> {
  const res = await api.delete<FavouriteResponse>(
    `/photos/${photoId}/favourite/`,
  );
  return res.data;
}
