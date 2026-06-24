# Configuration du frontend

Ce projet utilise une SPA Vite + React car le frontend est un outil interne qui a surtout besoin d'itération rapide, de flux applicatifs authentifiés et d'une connexion propre au backend FastAPI. On n'a pas besoin du rendu côté serveur, du SEO, ni du routage full-stack pour lesquels Next.js est optimisé.

## Init (depuis un `frontend/` vide)

```bash
cd frontend
pnpm create vite . --template react-ts
pnpm install
pnpm add react-router-dom @supabase/supabase-js
pnpm add -D tailwindcss @tailwindcss/vite
pnpm dlx shadcn@latest init
```

## Lancer

```bash
cd frontend
pnpm install
pnpm dev
```

## Vérifier

```bash
pnpm tsc --noEmit
pnpm lint
```
