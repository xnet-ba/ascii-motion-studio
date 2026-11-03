# Architecture

## Components

### Frontend
React SPA served by Nginx. Communicates with backend via `/api/v1`. Uses `react-i18next` for internationalization.

### API
FastAPI application running on `127.0.0.1:8001`. Handles upload, job creation, project management and serves `/exports`.

### Worker
Separate Python process polling SQLite for pending jobs. Runs FFmpeg, Pillow and NumPy operations with configurable concurrency (`CONCURRENT_JOBS`).

### Storage
- SQLite for projects, jobs and metadata.
- Filesystem for uploads (`/var/lib/ascii-motion-studio/uploads`) and exports (`/var/lib/ascii-motion-studio/exports`).
- Temporary frame data in `/var/tmp/ascii-motion-studio/jobs`.

### Rendering pipeline
1. Upload validated by magic bytes and MIME type.
2. Job created in SQLite with status `pending`.
3. Worker picks up job, processes frames with Pillow/NumPy.
4. Output assembled with FFmpeg (video) or Pillow (image).
5. Job marked `completed` with output path.

## Security boundaries
- API token required for all mutations and sensitive reads.
- File paths sanitized to prevent traversal.
- External URL loading is not supported.
- FFmpeg invoked with argument lists (no shell).
