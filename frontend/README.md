# Job Tracker Frontend

React and TypeScript MVP for the Job Application Tracker API.

## Features

- Registration and login
- Session-scoped JWT storage
- Pipeline summary, search, and status filters
- Company management
- Application creation, editing, and deletion
- Application event timeline
- Responsive layouts and accessible controls
- Request-ID propagation for support and log correlation

## Run locally

```bash
cp .env.example .env
npm ci
npm run dev
```

The default API is `http://localhost:8000/api/v1`. Override it with `VITE_API_BASE_URL`.

## Quality checks

```bash
npm run lint
npm run build
```

The frontend quality gate runs both commands on relevant pull requests and pushes to `main`.
