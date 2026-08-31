from app.core.config import settings

if settings.test_database_url is None:
    raise RuntimeError("TEST_DATABASE_URL must be configured before running tests")

if settings.test_database_url == settings.database_url:
    raise RuntimeError("TEST_DATABASE_URL must be different from DATABASE_URL")

if not settings.test_database_url.endswith("/jobtracker_test"):
    raise RuntimeError("Tests must run against the jobtracker_test database")

settings.database_url = settings.test_database_url
