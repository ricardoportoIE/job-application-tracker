from prometheus_client import Counter, Histogram

HTTP_REQUESTS_TOTAL = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    [
        "method",
        "path",
        "status_code",
    ],
)

HTTP_REQUEST_DURATION_SECONDS = Histogram(
    "http_request_duration_seconds",
    "HTTP request duration in seconds",
    [
        "method",
        "path",
    ],
)

DATABASE_HEALTH_FAILURES_TOTAL = Counter(
    "database_health_failures_total",
    "Total number of database health check failures",
    [
        "check",
    ],
)
