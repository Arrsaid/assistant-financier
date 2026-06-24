# Frontend — notes pour les agents

Ceci est la SPA React d'Assistant Financier. Lis d'abord [../AGENTS.md](../AGENTS.md) — les règles universelles de construction y vivent. Ce fichier ajoute les conventions spécifiques au frontend.

## Stack

- **SPA React pure** (Vite + TypeScript, strict). **Pas Next.js** — ne suggère pas Next, SSR, server components, ou routage par fichiers.
- **Tailwind CSS** pour le style. Pas de CSS modules, styled-components, Emotion, ni fichiers `.module.css` pour le style des composants. Les tokens de thème globaux vivent dans `src/index.css`.
- **shadcn/ui** pour les primitives UI. Ajoute des composants avec `pnpm dlx shadcn@latest add <name>` — ne réécris pas à la main ce que shadcn fournit déjà.
- **React Router** pour le routage.
- **`@supabase/supabase-js`** pour l'auth (email uniquement — pas de connexion Google, pas de SSO).

## Gestionnaire de paquets

**`pnpm` uniquement.** N'utilise pas `npm install` ni `yarn add`. Le lockfile est `pnpm-lock.yaml`. Si tu vois apparaître `package-lock.json` ou `yarn.lock`, c'est un bug — supprime-le.

**Âge minimum de publication : 7 jours.** Configuré via `.npmrc` (`minimum-release-age=10080` minutes). pnpm refusera d'installer toute version de paquet publiée il y a moins de 7 jours. C'est une défense contre les attaques de typosquat / release compromise où une version malveillante d'un paquet populaire est mise en ligne puis retirée en quelques heures.

Si un paquet récent est réellement nécessaire (ex. correctif de sécurité urgent dans une dépendance déjà utilisée), surcharge par installation et justifie dans le message de commit — n'abaisse pas le seuil global.

## Politique de dépendances

Voir la politique universelle dans [../AGENTS.md](../AGENTS.md). Spécificités frontend :

- **HTTP :** utilise l'API native `fetch` via un client fin dans `src/lib/http.ts` et le singleton `api` dans `src/lib/api.ts`. **Pas d'axios, ky, got, superagent, redaxios.**
- **Dates :** utilise `Date` natif et `Intl.DateTimeFormat`. Pas de moment, dayjs, date-fns sauf réel besoin.
- **Utilitaires :** utilise les méthodes natives `Array` / `Object` / `Map`. Pas de lodash, ramda.
- **État :** `useState` / `useReducer` / `useContext` d'abord. Ne prends une lib d'état externe que quand la douleur est réelle.
- **Formulaires :** `<form>` natif + `FormData` d'abord.
- **Validation :** n'ajoute une lib de schéma que quand on a réellement besoin de validation runtime aux frontières.
- **Composants UI :** primitives shadcn via `pnpm dlx shadcn@latest add <name>`. Ne réécris pas à la main ce que shadcn fournit déjà.

Avant d'ajouter un paquet, vérifie :

1. Existe-t-il une API navigateur ou TS/JS native qui fait ça ?
2. shadcn/ui le couvre-t-il déjà ?
3. Est-il petit, bien maintenu, et vaut-il son coût de maintenance ?

Si oui à (3), ajoute-le — mais signale la décision dans le message de commit.

## Arborescence (à créer pendant le build)

```text
frontend/
├── src/
│   ├── components/        # Composants applicatifs. Primitives shadcn sous components/ui/
│   ├── lib/               # Helpers agnostiques du framework (http, api, auth, supabase, env)
│   ├── pages/             # Composants au niveau route
│   ├── App.tsx            # Router
│   ├── main.tsx
│   └── index.css          # Directives Tailwind + tokens de thème globaux
├── index.html
├── vite.config.ts
├── tsconfig.json
└── package.json
```

Garde les imports cohérents avec l'alias `@/*` (ex. `@/lib/api`, `@/components/ui/button`).

## Style de code (spécifique frontend)

- **TypeScript strict.** Pas de `any` sauf alternative inexistante ; préfère `unknown` et affine.
- **Fonctions et composants petits et composables** plutôt que des abstractions malignes. Trois lignes similaires > un générique prématuré.
- **Un composant = un fichier.** Les composants restent assez petits pour tenir sur un écran.
- **Classes Tailwind inline.** Pas de CSS modules, styled-components, Emotion, ni `.module.css` pour le style des composants. Les tokens globaux vivent dans `src/index.css`.

## Configuration

- Toutes les lectures d'env passent par un unique module `src/lib/env.ts` qui valide les variables requises au boot. Ne lis jamais `import.meta.env.X` directement dans les composants.
- Les variables d'env sont préfixées `VITE_` (convention Vite). Tout ce qui n'est pas préfixé n'est pas exposé au client.

## Intégration backend

- Parle à un backend Python séparé en JSON. L'URL vient de `VITE_API_BASE_URL`.
- Utilise toujours `api.get/post/put/patch/delete` depuis `@/lib/api` — il gère l'URL de base, le JSON, le bearer token Supabase, les timeouts, et les `ApiError` typées (dont le flag `isNetworkError` qui distingue CORS/réseau des erreurs HTTP).
- L'auth est Supabase email. Le bearer token est injecté automatiquement par le client `api` ; ne fais jamais transiter de token via les props des composants.

## Tests

**Pas de tests frontend.** N'écris pas de fichiers `*.test.ts` / `*.test.tsx` et n'introduis pas de test runner. On vérifie le frontend manuellement dans le navigateur, plus `pnpm tsc --noEmit` et `pnpm lint`. Si tu te surprends à vouloir vitest, Playwright ou Cypress — arrête. Ce n'est pas ce que fait ce projet. La justesse de la logique partagée vient de sa simplicité et de son typage, pas d'une suite de tests.

## Anti-patterns (rejetés)

- Lire `import.meta.env.X` directement hors de `lib/env.ts`.
- Importer une lib HTTP là où `fetch` suffirait.
- Mélanger des libs d'état client (Zustand + Jotai + Redux) sur un même projet.
- Annotations `any` pour faire taire le type-checker.
- Fichiers CSS maison / styled-components à côté de Tailwind.
- Réimplémenter à la main une primitive shadcn.
- Recourir à Next.js, SSR, ou tout framework exigeant un serveur Node devant la SPA.
