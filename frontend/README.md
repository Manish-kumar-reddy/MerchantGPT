# MerchantGPT frontend

Next.js 15 (App Router) + TypeScript + Tailwind CSS v4 client for the MerchantGPT API.

See the [project root README](../README.md) for full setup instructions, and [`../docs/`](../docs/) for architecture, API reference, and deployment docs.

## Local development

```bash
npm install
cp .env.example .env.local   # set NEXT_PUBLIC_API_URL to your backend URL
npm run dev
```

## Scripts

- `npm run dev` -- start the dev server (Turbopack)
- `npm run build` -- production build
- `npm run start` -- run a production build
- `npm run lint` -- ESLint
