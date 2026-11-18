# Learning log

Plain-English notes on what we built and why. Useful for interview prep.

## Phase 0–1: setup + health check

- **API**: the "waiter" between the frontend and the database. Keeps the business rules (no double bookings, deposit required) in one safe place the browser can't skip.
- **FastAPI vs Flask vs Django**: FastAPI sits in the middle. It's lighter than Django, does more for you than Flask, checks data for you, and writes the API docs automatically (`/docs`).
- **Endpoint**: one "menu item" the API serves, e.g. `GET /health`.
- **`/health`**: answers "is the server alive right now?" so monitoring tools can check it. (Not the same as tests.)
- **Tests**: check that code which used to work still works after changes. Run with `pytest -v`.
- **CI (GitHub Actions)**: re-runs the tests automatically on every push / pull request.
- **Monorepo**: backend and frontend in one repo. Simpler for a solo project, easy for recruiters to browse.

## Secrets and why `.env` is never committed

- Secrets (Stripe key, DB password) live in `.env`, which `.gitignore` blocks from Git.
- If a secret leaks, bots can use it within minutes:
  - Stripe secret key → see customer details, issue refunds, create charges on saved cards
  - DB password → read, change or delete all bookings and client contact details (a GDPR problem)
  - Cloud keys → run crypto-mining servers on your bill
  - Email API keys → send spam or phishing as your business
- Deleting the key later doesn't fix it: **Git history keeps it**. The fix is to **rotate** the key (revoke it and make a new one).
- Normal code being public is fine (open source works this way). Security comes from secrets + proper checks (login, permissions), not from hiding code.
- Stripe works with GitHub secret scanning, so leaked Stripe keys pushed to public repos get flagged.
