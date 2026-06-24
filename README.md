# Assistant Financier

Un chatbot IA interne qui permet aux analystes d'interroger en langage naturel un corpus de documents de sociétés cotées françaises et d'obtenir des réponses sourcées et citables.

## Le client

**Haussmann Recherche** — cabinet fictif et indépendant de recherche actions, qui couvre le CAC 40. Ses analystes passent la moitié de leur semaine à lire des Documents d'Enregistrement Universel (URD) avant de pouvoir produire la moindre analyse originale. Assistant Financier absorbe ce travail d'ingestion pour qu'ils passent directement à l'analyse.

Brief complet : [docs/client-brief.md](docs/client-brief.md)

## Stack

| Couche             | Choix                                                          |
| ------------------ | -------------------------------------------------------------- |
| Backend            | Python + FastAPI                                               |
| Frontend           | Vite + React SPA + TypeScript                                  |
| Base de données    | Supabase Postgres (utilisateurs, conversations, documents, chunks) |
| Migrations         | Modèles SQLAlchemy + Alembic                                   |
| Recherche          | Supabase `pgvector` + recherche plein texte Postgres          |
| Authentification   | Supabase Auth (email uniquement)                              |
| Hébergement        | Railway                                                        |
| LLM + embeddings   | Mistral AI                                                     |

## Arborescence du dépôt

```text
assistant-financier/
├── AGENTS.md           # instructions pour les agents (à lire en premier)
├── README.md           # ce fichier
├── data/               # corpus local + script de téléchargement (contenus gitignorés)
├── docs/
│   └── client-brief.md # le one-pager client
├── backend/            # service FastAPI
└── frontend/           # SPA React (Vite)
```

## Prérequis

À installer avant de configurer `backend/` ou `frontend/` :

| Outil | Version | Sert à | Installation |
| ----- | ------- | ------ | ------------ |
| [Python](https://www.python.org/downloads/) | 3.12+ | Runtime backend | gestionnaire de paquets OS ou python.org |
| [uv](https://docs.astral.sh/uv/getting-started/installation/) | dernière | Dépendances backend + `data/download.py` | `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| [Node.js](https://nodejs.org/) | 20+ (LTS) | Outillage frontend | nodejs.org ou `nvm install --lts` |
| [pnpm](https://pnpm.io/installation) | dernière | Gestionnaire de paquets frontend | `corepack enable && corepack prepare pnpm@latest --activate` |

Il faut aussi des comptes/clés pour les services externes une fois l'application câblée. Commence par [docs/guides/supabase-setup.md](docs/guides/supabase-setup.md) (compte + projet), puis crée une [clé API Mistral](https://console.mistral.ai/) quand la couche LLM sera branchée.

## Lancer en local

À compléter pendant le build. Guides de configuration :

- [Supabase](docs/guides/supabase-setup.md) — compte, projet hébergé (dashboard ou CLI)
- [Backend](docs/guides/backend-setup.md)
- [Frontend](docs/guides/frontend-setup.md)

## Données URD d'exemple

Le corpus est le **Document d'Enregistrement Universel (URD)** des sociétés du CAC 40, publié sur **info-financiere.fr** (la base publique de l'information réglementée de l'AMF).

Par défaut, le téléchargeur prévu récupère les URD récents (exercices 2020–2025) pour un petit échantillon d'émetteurs (LVMH, TotalEnergies, Sanofi, L'Oréal, Air Liquide) dans des dossiers par année sous `data/downloads/`, et écrit un `manifest.json`.

Contrairement aux dépôts SEC (HTML structuré), les URD français sont distribués en **PDF** ; l'ingestion doit donc extraire le PDF en Markdown avant le chunking.

Les fichiers téléchargés sont gitignorés ; le dossier `data/` reste dans git pour le script et les notes.
