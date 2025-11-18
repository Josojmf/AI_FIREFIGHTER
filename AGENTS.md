# Repository Guidelines

## Project Structure & Module Organization
- `FO/` hosts the public Flask UI (`main.py`, Jinja templates, `static/` assets, seed data under `data/`).
- `API/` exposes the REST core via `api.py` (Flask + MongoDB); authentication tests live beside it in `test_chat.py`.
- `BO/` powers the admin back office; `app/__init__.py` creates the Flask app and `app.py` serves it through Waitress on port 8080.
- Infrastructure helpers (`docker-compose*.yml`, `nginx*.conf`, `logs/`, `shared/`) support local orchestration; environment defaults live in `.env*` files.

## Build, Test, and Development Commands
- `python -m venv .venv && .\.venv\Scripts\activate` prepares the workspace interpreter; install dependencies with `pip install -r requirements.txt` or the service-specific files in `FO/`, `API/`, and `BO/`.
- Run services individually with `python FO/main.py` (port 8000), `python API/api.py` (port 5000), and `python BO/app.py` (port 8080); ensure `.env` defines `API_BASE_URL` and Mongo credentials.
- Use `docker compose up --build` from the repo root for the full stack and nginx proxies; stop with `docker compose down` when finished.
- Execute `pytest` (or `pytest API/test_chat.py`) before pushing; append `--cov=API` to monitor coverage on API-heavy changes.
- Apply `black .`, `isort .`, `flake8`, and `mypy API BO FO` to format, lint, and type-check prior to committing.

## Coding Style & Naming Conventions
- Follow PEP 8: 4-space indentation, snake_case functions, and descriptive class names; keep helper modules under `shared/` when logic is reused across services.
- Keep Jinja block names snake_case and static asset filenames kebab-case (e.g. `static/js/modules/chat.js`, `static/css/modern-style.css`).
- Document new settings in `.env` and `.env.development`, mirroring the keys consumed by Flask configs.

## Testing Guidelines
- Write pytest suites alongside the code they verify; name files `test_<feature>.py` for discovery.
- Use Flask's test client for API and BO route checks, and patch Mongo calls with fixtures or test databases when possible.
- Aim for at least 80% coverage on new modules and note intentional gaps or TODOs in the PR description.

## Commit & Pull Request Guidelines
- Mirror existing history: concise, uppercase, imperative subjects (`INT CLUE ADDED`, `UPGRADED CD YML`); keep each commit focused.
- Each PR must explain the change, list the validation commands run, reference related issues (`Fixes #123`), and highlight new environment keys or migrations.
- Attach screenshots or `curl` samples for UI/API adjustments and confirm default admin credentials remain rotated when security changes ship.

## Environment & Security Tips
- Never commit secrets; load them through `.env` files and prefer `MONGO_URI` aggregation for production deployments.
- On first API boot a default admin (`admin/admin123`) is created - change it immediately and store the rotation securely.
- Run `setup-nginx.bat` before `start-with-nginx.bat` to scaffold logs and mime types; update your hosts file to route `onfire.local` domains when testing nginx.
test