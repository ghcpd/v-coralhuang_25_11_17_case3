Major fixes and features:

- Replaced hard-coded Redis/Celery setup with environment-driven configuration in `fixes/config.py`.
- Implemented safe DB access with SQLAlchemy, no raw SQL.
- Token parsing with strict validation and proper HTTP codes.
- Consistent JSON serialization and cache format.
- Redis wrapper with graceful degradation during failures.
- Celery configured with eager mode by default for testability.
- Added pytest suite covering happy path, missing token, redis failures, and Celery mode.

Limitations:
- In-memory SQLite used in tests; for production provide DATABASE_URL.
- No cloud uploads performed — simulated for safety.
