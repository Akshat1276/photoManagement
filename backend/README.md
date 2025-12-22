
# Backend API Overview

This Django REST Framework backend powers the Smart Event Photo Management platform.
Below is a high-level summary of the main API endpoints that the frontend will use.

Base URL in development:

- `http://127.0.0.1:8000/api/`

### API Documentation (Swagger / OpenAPI)

- OpenAPI schema (machine-readable): `GET /api/schema/`
- Swagger UI (interactive docs): `GET /api/docs/`
- ReDoc UI: `GET /api/redoc/`

These are powered by `drf-spectacular` and are available when the backend is running locally.

## Media Storage (Local vs S3)

The project supports two media storage modes, controlled by an environment flag.

- Local filesystem (default for graders/development)
	- `.env` contains `USE_S3_MEDIA=False` (or the variable is omitted).
	- Uploaded images are stored under `backend/media/` and served at `/media/` when `DEBUG=True`.

- AWS S3 (production-style mode)
	- `.env` contains `USE_S3_MEDIA=True` and the following variables:
		- `AWS_ACCESS_KEY_ID`
		- `AWS_SECRET_ACCESS_KEY`
		- `AWS_STORAGE_BUCKET_NAME` (e.g. `photo-management-app`)
		- `AWS_S3_REGION_NAME` (e.g. `eu-north-1`)
	- Django uses `storages.backends.s3boto3.S3Boto3Storage` as the default file storage via the `STORAGES` setting.
	- Image fields (`image_original`, `image_thumbnail`, `image_watermarked`) are written directly to S3; no `media/` folder is created locally.
	- `MEDIA_URL` points at the S3 bucket domain, and S3 bucket policy controls public read access.

If S3 is not configured or credentials are missing, set `USE_S3_MEDIA=False` so the app falls back to local storage.

## Authentication

- `POST /api/auth/register/`
	- Body: `{ "email": string, "password": string, "full_name": string }`
	- Creates a new user and profile.
	- Sends a 6-digit OTP code to the user's email for verification.

- `POST /api/auth/login/`
	- Body: `{ "email": string, "password": string }`
	- Starts a session using Django's session authentication.
	- Only works after the user's email has been verified.

- `POST /api/auth/verify-email/`
	- Body: `{ "email": string, "code": string }`
	- Verifies the OTP sent to the user's email and marks the account as verified.

- `POST /api/auth/logout/`
	- Logs out the current user (ends the session).

- `GET /api/auth/me/`
	- Returns and allows updating the current user's profile.

- Omniport OAuth 2.0 login
	- `GET /api/auth/omniport/login/`
		- Returns an `authorization_url` to redirect the user to Omniport's login/consent page.
	- `GET /api/auth/omniport/callback/`
		- Callback URL configured in Omniport.
		- Exchanges the authorization code for an access token, fetches user data from Omniport, creates/updates a local user (marked as verified), and starts a session.

## Roles and Access Control

The backend defines the following logical roles using the `Role` / `UserRole` models:

- Admin
- Event Coordinator
- Photographer
- IMG Member
- Guest

Roles are assigned via the Django admin. Views use these roles together with Django's
`is_staff` / `is_superuser` flags to decide who can perform certain actions.

High-level rules:

- Event creation is limited to Admins and Event Coordinators (and staff/superusers).
- Photo upload is limited to Admins, Event Coordinators, Photographers, and IMG Members
	(and staff/superusers).
- Object updates/deletes are restricted to the owner (creator/uploader) or admins.

## Events

- `GET /api/events/`
	- List all events, newest first.

- `POST /api/events/` *(Event Coordinator / Admin required)*
	- Create a new event; `created_by` is set to the current user.

- `GET /api/events/<slug>/`
	- Retrieve details for a single event.

- `PUT/PATCH/DELETE /api/events/<slug>/` *(owner or admin only)*
	- Update or delete an event.

- `GET /api/events/<slug>/photos/`
	- List all photos belonging to a given event.

## Photos

- `GET /api/photos/`
	- List all photos, newest first by default.
	- Supports advanced filters and sorting via query parameters:
		- `event` (integer): filter by event ID.
		- `event_slug` (string): filter by event slug.
		- `uploaded_by` (integer): filter by uploader user ID.
		- `camera_model` (string): case-insensitive match on camera model.
		- `visibility` (string): one of `public`, `private`, `event_only`, `role_based`.
		- `taken_from` / `taken_to` (ISO datetime): filter by `taken_at` range.
		- `created_from` / `created_to` (ISO datetime): filter by upload time range.
		- `q` (string): text search across event title and camera model.
		- `sort` (string):
			- `newest` (default): newest uploads first.
			- `oldest`: oldest uploads first.
			- `most_liked`: photos with the most likes first.
			- `most_favourited`: photos with the most favourites first.
			- `most_commented`: photos with the most comments first.

- `GET /api/photos/my-uploads/` *(auth required)*
	- List all photos uploaded by the current user.

- `GET /api/photos/my-favourites/` *(auth required)*
	- List all photos the current user has marked as favourite.

- `POST /api/photos/` *(Photographer / IMG Member / Event Coordinator / Admin required)*
	- Upload a photo.
	- Important fields:
		- `event` (integer event ID, required)
		- `image_original` (file upload, required)
		- Optional: `taken_at`, `camera_model`, `visibility`, `metadata` (JSON).

- `POST /api/photos/batch-upload/` *(Photographer / IMG Member / Event Coordinator / Admin required)*
	- Upload **multiple photos** for a single event in one request.
	- Multipart form fields:
		- `event` (integer event ID, required)
		- `visibility` (optional; defaults to `public`)
		- `images` (one or more files using the same field name)
	- The API creates a `Photo` for each file and enqueues the background processing task for EXIF, thumbnails, and watermarks.

- `POST /api/photos/batch-operations/` *(Photographer / IMG Member / Event Coordinator / Admin required)*
	- Perform bulk actions on multiple photos owned by the current user (admins can act on any photos).
	- JSON body:
		- `photo_ids`: list of photo IDs (required)
		- `action`: one of `"delete"`, `"move"`, `"update_visibility"`, `"set_tags"` (required)
		- For `move`: `target_event` (integer event ID)
		- For `update_visibility`: `visibility` (one of the Photo.Visibility values)
		- For `set_tags`: `tags` (list of strings, replaces manual tags)

### ML/AI Auto-Tagging

The backend includes optional support for automatic photo tagging using a pre-trained
ResNet50 image classification model:

- Controlled by the `ENABLE_AI_TAGGING` environment variable (default: `False`).
- When enabled and if `torch`/`torchvision` are installed, the `process_photo` Celery
	task runs the model on each uploaded image and attaches the top predictions as
	AI tags using the `Tag`/`PhotoTag` models.
- If the ML dependencies are not available, tagging is skipped without affecting the
	rest of the processing pipeline.

- `GET /api/photos/<id>/`
	- Retrieve a single photo.

- `PUT/PATCH/DELETE /api/photos/<id>/` *(uploader or admin only)*
	- Update or delete a photo.

## Photo Engagement

- Likes
	- `POST /api/photos/<id>/like/` *(auth required)*
		- Like the photo for the current user (idempotent).
	- `DELETE /api/photos/<id>/like/` *(auth required)*
		- Remove the current user's like.

- Favourites
	- `POST /api/photos/<id>/favourite/` *(auth required)*
		- Mark the photo as favourite for the current user.
	- `DELETE /api/photos/<id>/favourite/` *(auth required)*
		- Remove the favourite.

- Comments
	- `GET /api/photos/<id>/comments/`
		- List top-level comments for a photo (newest first).
	- `POST /api/photos/<id>/comments/` *(auth required)*
		- Body: `{ "content": string, "parent_comment": optional integer }`
		- Creates a new comment on that photo; optionally as a reply.
	- `GET /api/photos/comments/<comment_id>/`
	- `PUT/PATCH/DELETE /api/photos/comments/<comment_id>/` *(comment author or admin only)*

## Notifications

- `GET /api/notifications/` *(auth required)*
	- List notifications for the current user (newest first).
	- Currently created when other users like or comment on your photo.

- `POST /api/notifications/<id>/read/` *(auth required)*
	- Mark a single notification as read.

## Permissions Summary

- Unauthenticated users
	- Can read public data: list events, list photos, view details, list comments.

- Authenticated users
	- Can create events (if they have the Event Coordinator role), upload photos (if they have a content role), like/favourite/comment on photos.
	- Can edit or delete **their own** events, photos, and comments.

- Admin users (staff or superuser)
	- Can edit or delete any event, photo, or comment.