# Frontend

The TFA booking site (React + Vite). Clients pick a treatment, extras and a time,
then pay their deposit on Stripe.

## Run it

```bash
cd frontend
cp .env.example .env    # first time only
npm install             # first time only (and when package.json changes)
npm run dev
```

Then open http://localhost:5173. The backend must be running on port 8000.
