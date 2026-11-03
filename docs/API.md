# API Documentation

Base URL: `https://go.kolektiv.pro/api/v1`

Authentication: Bearer token in `Authorization` header.

## Endpoints

### Health
`GET /health`

### System info
`GET /system/info`

### Upload
`POST /upload` — multipart/form-data, field `file`.

### Image conversion
`POST /image/convert`

Body fields:
- `input_path` (str)
- `width` (int, 10-240)
- `mode` (`grayscale`, `color`, `monochrome`)
- `palette` (`standard`, `dense`, `minimal`, `blocks`, `binary`, `custom`)
- `background` (`black`, `white`, `transparent`, `custom`)
- `contrast_adapt` (bool)
- `output_format` (`png`, `gif`, `svg`, `txt`, `html`)

### Video conversion
`POST /video/convert`

Additional fields:
- `output_format` (`gif`, `mp4`, `webm`)
- `fps` (int, 1-30)
- `max_duration` (int, seconds)

### Animation / Web export
`POST /animation/render` — always produces HTML.
`POST /export` — `export_type`: `html`.

### Jobs
`GET /jobs/{job_id}`
`GET /jobs/{job_id}/progress`
`GET /jobs?limit=100`

### Projects
`GET /projects`
`POST /projects`
`GET /projects/{project_id}`
`DELETE /projects/{project_id}`

### OpenAPI
Interactive docs are available at `/docs` and `/redoc`.
