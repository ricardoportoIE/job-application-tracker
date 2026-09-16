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

## Run with the complete application

From the repository root:

```bash
docker compose up --build
```

Open `http://localhost:5173`. Nginx serves the production build and proxies
`/api` requests to the backend over the private Compose network.

## Run the development server

```bash
cp .env.example .env
npm ci
npm run dev
```

Vite proxies the default `/api/v1` URL to the backend on port `8000`. Override
it with `VITE_API_BASE_URL` when the API is hosted elsewhere.

## Quality checks

```bash
npm run lint
npm run build
```

The frontend quality gate runs both commands on relevant pull requests and pushes to `main`.
