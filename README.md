# TFA Booking

A branded booking and payments platform for a real nail business ([tfa.nailsandbeauty](https://www.instagram.com/tfa.nailsandbeauty/)).

## Why I built it

I ran my bookings on Calendly and Square Appointments. Calendly had a smooth booking flow but no branding. Square had a customisable booking site, but setting availability was awkward. This project combines the best of both with Stripe deposits, in one system I control.

## Features

- [ ] Branded booking site (logo, colours, photos)
- [ ] Service list with duration, price and deposit
- [ ] Easy availability manager (weekly hours, breaks, days off)
- [ ] Slot generation from availability and existing bookings
- [ ] Stripe Checkout deposits confirmed by webhook
- [ ] Double-booking prevention at database level
- [ ] Email confirmations

## Tech stack

| Layer | Technology |
| --- | --- |
| Backend | Python, FastAPI |
| Frontend | React |
| Database | PostgreSQL |
| Payments | Stripe |
| CI | GitHub Actions |

## Project structure

```
tfa-booking/
├── backend/        FastAPI app and tests
├── frontend/       React app (Phase 2)
├── .github/        CI workflows
├── .env.example    Template for environment variables
└── README.md
```

## Running the backend locally

```bash
cp .env.example .env
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements-dev.txt
uvicorn app.main:app --reload
```

Then open http://localhost:8000/health or the interactive API docs at http://localhost:8000/docs.

## Running tests

```bash
cd backend
pytest -v
```

## Status

In development. See the feature checklist above.
