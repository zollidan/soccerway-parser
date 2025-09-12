# Repository Guidelines

## Project Structure & Module Organization
- `main.py`: CLI entry point. Fetches Soccerway data, parses JSON, saves Excel. Toggle `TESTING` (True/False) inside this file.
- `pyproject.toml`: Python 3.13 project metadata and dependencies (`requests`, `selenium`, `pandas`, `openpyxl`).
- `example.json`, `h2h.json`: Local fixtures for test mode.
- `README.md`: Usage notes. `uv.lock`: dependency lock for `uv`.
- No `src/` or `tests/` directories yet; code lives at repo root.

## Build, Test, and Development Commands
- Create environment and install deps (uv): `uv sync`
- Run the app:
  - With uv: `uv run python main.py`
  - With system Python: `python main.py`
- Switch to live API: set `TESTING = False` in `main.py`.
- Output: Excel file `matches_YYYYMMDD_HHMMSS.xlsx` in repo root.

## Coding Style & Naming Conventions
- Python style: PEP 8, 4‑space indentation, max ~100 cols.
- Naming: `snake_case` for functions/vars, `UPPER_CASE` for constants (e.g., `BASE_URL`, `HEADERS`).
- Logging: use `logging` (already configured). Reserve `print()` for CLI prompts.
- Data fields: keep existing Russian column names and keys unchanged.

## Testing Guidelines
- Current state: no automated tests. Validate changes by running `main.py` in `TESTING=True` with `example.json`/`h2h.json` present, and inspecting the generated Excel.
- If adding tests, use `pytest`:
  - Location: `tests/` directory, files named `test_*.py`.
  - Prefer small fixtures derived from `example.json`.

## Commit & Pull Request Guidelines
- Commits: follow Conventional Commits (e.g., `feat:`, `fix:`, `refactor:`, `docs:`). Imperative mood, concise subject, details in body.
- PRs: include a clear description, rationale, run instructions, sample output (e.g., Excel filename), and linked issues. Screenshots of Excel preview are helpful.

## Security & Configuration Tips
- Do not commit secrets. No API keys required; requests use public endpoints and headers.
- Be respectful of site terms and rate limits when enabling live requests.

## Agent-Specific Instructions
- Prefer minimal diffs; do not rename columns or change file outputs without updating `README.md`.
- Keep behavior backward‑compatible; document any schema changes.
