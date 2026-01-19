
# Smart Event Photo Management

Instagram-style event photo platform with strong privacy controls, face-recognition based "Photos of Me", real-time notifications/comments, and an industry-grade React + Material UI frontend. The backend is built with Django REST Framework, Channels, Celery, PostgreSQL, Redis, and optional S3 storage.

---

## Features

- **Event galleries**
	- Create events and upload photos per event.
	- Infinite scroll and lazy loading in galleries.
	- Quick stats: likes, favourites, and comments per photo.

- **Photo privacy & permissions**
	- Per-photo visibility: `public`, `private`, `event_only`, `role_based`.
	- Strict download rules for original vs. watermarked images.
	- Role-based access: Admin, Event Coordinator, Photographer, IMG Member, Guest.

- **Uploads & batch operations**
	- Single and **batch upload** for event photos.
	- Background processing via Celery: EXIF extraction, thumbnail generation, watermarking.
	- Bulk actions: delete, move between events, change visibility, retag.

- **Engagement (likes, favourites, comments)**
	- Like / favourite photos (thumbs-up + heart icons in the UI).
	- Threaded comments with edit/delete for owners.
	- Real-time comment stream via WebSockets (Django Channels).

- **Notifications & real-time updates**
	- Per-user notification feed when others like, favourite, or comment on your photos.
	- Live updates over WebSockets.

- **"Photos of Me" (face recognition)**
	- Users upload a reference selfie once.
	- Background jobs scan event photos and match faces using `face_recognition`.
	- Dedicated "Photos of Me" gallery with infinite scroll.

- **Authentication & security**
	- Email/password auth with OTP email verification (Gmail SMTP in dev).
	- Optional Omniport OAuth 2.0 login integration.
	- Session-based authentication for the SPA.

- **Modern UI/UX**
	- React + TypeScript + Vite frontend.
	- Material UI theme with **light/dark mode toggle**.
	- Responsive layout with a mobile **hamburger navbar**.
	- Password visibility toggles on login/register.
	- Uploader shown by **full name** (with email fallback).

- **Developer experience**
	- Dockerised stack: Postgres, Redis, Django+Channels, Celery worker/beat, Vite frontend.
	- OpenAPI/Swagger docs via `drf-spectacular`.

---

## Tech Stack

- **Backend**
	- Django 6
	- Django REST Framework
	- Django Channels (WebSockets) + Redis
	- Celery + Redis (broker & result backend)
	- PostgreSQL
	- `face_recognition`, Pillow, NumPy (face matching and image processing)
	- `django-storages` + S3 (optional media backend)
	- `drf-spectacular` for API docs

- **Frontend**
	- React 18 + TypeScript
	- Vite 6
	- Material UI (MUI v6)
	- Redux Toolkit
	- Axios

- **Infrastructure & tooling**
	- Docker & Docker Compose
	- Node 20 / npm for frontend tooling

---

## Project Structure

```text
photoManagement/
	backend/
		backend/           # Django project (settings, urls, asgi/wsgi)
		core/              # App: models, views, serializers, tasks, etc.
		manage.py
		requirements.txt
		.env.example       # Backend environment template (copy to .env)

	frontend/
		src/               # React + TS source
		package.json
		vite.config.ts
		.env               # (optional) frontend-only env vars

	docker-compose.yml   # Multi-service dev stack (db, redis, backend, celery, frontend)
	.env.example         # Root env for docker-compose (copy to .env)
	README.md
```

---

## Getting Started

You can run the project either via **Docker (recommended for a quick start)** or by running backend and frontend directly on your machine.

### 1. Prerequisites

- Docker Desktop (for Docker-based setup)
- Or, for manual setup:
	- Python 3.12+
	- Node.js 20+
	- PostgreSQL 14+ and Redis 6+

---

## Option A: Run with Docker (recommended)

This uses [docker-compose.yml](docker-compose.yml) to start Postgres, Redis, Django (via Daphne), Celery worker/beat, and the Vite frontend.

### Step 1: Clone the repo

```bash
git clone <your-repo-url>
cd photoManagement
```

### Step 2: Configure environment

1. **Backend env** (for Django):

	 - Copy the example file and edit as needed:

	 ```bash
	 cd backend
	 cp .env.example .env
	 # edit .env to plug in your own secrets (DB password, email, S3, Omniport, etc.)
	 cd ..
	 ```

2. **Root env** (for docker-compose):

	 - From the project root, copy the example:

	 ```bash
	 cp .env.example .env
	 # keep values in sync with backend/.env (DB_NAME, DB_USER, DB_PASSWORD, DJANGO_SECRET_KEY)
	 ```

By default, [docker-compose.yml](docker-compose.yml) reads `DJANGO_SECRET_KEY`, `DB_NAME`, `DB_USER`, and `DB_PASSWORD` from the root `.env`. Inside the backend, `backend/.env` is loaded via `python-dotenv` for Django settings like email/S3.

### Step 3: Build and run

From the project root:

```bash
docker compose up --build
```

This will:

- Start **Postgres** on 5432 (inside Docker network as `db`).
- Start **Redis** on 6379 (inside Docker network as `redis`).
- Build the **backend** image, run `python manage.py migrate`, then launch Daphne on `0.0.0.0:8000`.
- Start **Celery worker** and **Celery beat**.
- Build and start the **frontend** (Vite dev server) on `0.0.0.0:5173`.

### Step 4: Access the app

- Frontend SPA: http://127.0.0.1:5173/
- API root: http://127.0.0.1:8000/api/
- Swagger / OpenAPI docs:
	- Schema: http://127.0.0.1:8000/api/schema/
	- Swagger UI: http://127.0.0.1:8000/api/docs/
	- ReDoc: http://127.0.0.1:8000/api/redoc/

To stop all services:

```bash
docker compose down
```

---

## Option B: Run locally without Docker

This is useful if you prefer running services directly on your machine.

### 1. Backend (Django + Celery)

From [backend](backend):

```bash
cd backend
python -m venv .venv
.venv\Scripts\activate  # On Windows

pip install --upgrade pip
pip install -r requirements.txt
```

Create and configure `backend/.env`:

```bash
cp .env.example .env
# edit .env with your DB credentials, email, S3, Omniport, etc.
```

Make sure Postgres and Redis are running locally and that `DB_*` and `REDIS_URL` in `.env` match your setup.

Apply migrations and start the ASGI server (Daphne):

```bash
python manage.py migrate
daphne -b 0.0.0.0 -p 8000 backend.asgi:application
```

In separate terminals (with the virtualenv activated), start Celery worker and beat:

```bash
celery -A backend worker -l info
celery -A backend beat -l info
```

> You can also use `python manage.py runserver` for a simple dev server (without production-grade ASGI), but Daphne is recommended to exercise Channels.

### 2. Frontend (React + Vite)

From [frontend](frontend):

```bash
cd frontend
npm install
npm run dev -- --host 0.0.0.0 --port 5173
```

Open http://127.0.0.1:5173/ in your browser.

The frontend is configured to talk to the backend at `http://127.0.0.1:8000/api/` and to use WebSockets for notifications and live comments.

---

## Environment Configuration

### Backend `.env` (loaded by Django)

See [backend/.env.example](backend/.env.example) for a complete template. Key groups:

- **Core Django**
	- `DJANGO_SECRET_KEY`
	- `DEBUG`
	- `ALLOWED_HOSTS`

- **Database**
	- `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

- **Redis / Celery / Channels**
	- `REDIS_URL` (used as both Celery broker and result backend)

- **Email (Gmail example)**
	- `EMAIL_BACKEND`, `EMAIL_HOST`, `EMAIL_PORT`, `EMAIL_USE_TLS`
	- `EMAIL_HOST_USER`, `EMAIL_HOST_PASSWORD`, `DEFAULT_FROM_EMAIL`

- **Omniport OAuth (optional)**
	- `OMNIPORT_BASE_URL`, `OMNIPORT_CLIENT_ID`, `OMNIPORT_CLIENT_SECRET`, `OMNIPORT_REDIRECT_URI`

- **Media storage**
	- `USE_S3_MEDIA` = `True` or `False`
	- If `True`, also set: `AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_REGION_NAME`, `AWS_S3_CUSTOM_DOMAIN`.

> Never commit real `.env` files. They are already ignored in [.gitignore](.gitignore). Use the `*.env.example` files as safe templates.

### Root `.env` for Docker

See [.env.example](.env.example). This is read by Docker Compose and typically mirrors the DB and secret values in `backend/.env`:

- `DJANGO_SECRET_KEY`
- `DB_NAME`, `DB_USER`, `DB_PASSWORD`

---

## API Overview

For full details, use the interactive docs at `/api/docs/`. High-level summary of key endpoints:

- **Auth**
	- `POST /api/auth/register/` – register with email/password/full name (sends OTP).
	- `POST /api/auth/verify-email/` – verify OTP.
	- `POST /api/auth/login/` / `POST /api/auth/logout/`.
	- `GET /api/auth/me/` – current user profile.
	- Omniport OAuth 2.0 login (`/api/auth/omniport/login/`, `/api/auth/omniport/callback/`).

- **Events**
	- `GET /api/events/`, `POST /api/events/`.
	- `GET/PUT/PATCH/DELETE /api/events/<slug>/`.
	- `GET /api/events/<slug>/photos/` – event gallery (paginated).

- **Photos**
	- `GET /api/photos/` – global feed with rich filters & sorting.
	- `GET /api/photos/my-uploads/`, `/api/photos/my-favourites/`, `/api/photos/my-likes/`.
	- `POST /api/photos/` – single upload.
	- `POST /api/photos/batch-upload/` – multi-file upload.
	- `POST /api/photos/batch-operations/` – bulk delete/move/update.
	- `GET/PUT/PATCH/DELETE /api/photos/<id>/` – manage a single photo.
	- Download endpoints for original/watermarked images.

- **Engagement**
	- Likes: `POST` / `DELETE` on `/api/photos/<id>/like/`.
	- Favourites: `POST` / `DELETE` on `/api/photos/<id>/favourite/`.
	- Comments: list/create at `/api/photos/<id>/comments/`, edit/delete via `/api/photos/comments/<comment_id>/`.

- **Notifications**
	- `GET /api/notifications/` – list.
	- `POST /api/notifications/<id>/read/` – mark as read.

- **Photos of Me**
	- Upload reference selfie and fetch matched photos via dedicated endpoints.

---

## Docker Services Reference

From [docker-compose.yml](docker-compose.yml):

- `db` – Postgres 16 (`POSTGRES_DB`, `POSTGRES_USER`, `POSTGRES_PASSWORD`).
- `redis` – Redis 7 for Channels + Celery.
- `backend` – Django + DRF + Channels served by Daphne on port 8000.
- `celery-worker` – Celery worker for background tasks.
- `celery-beat` – Celery beat scheduler.
- `frontend` – Vite dev server on port 5173.

---

## Contributing / Development Notes

- Use feature branches and pull requests for changes.
- Keep secrets out of Git; rely on `.env` files locally and, in production, on your deployment platform's secret management.
- When adding new settings, update the relevant `*.env.example` and this README so new contributors have a clear path to configure their environment.

Happy hacking!


