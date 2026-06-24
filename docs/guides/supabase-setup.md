# Configuration de Supabase

On utilise Supabase pour **Postgres** (utilisateurs, conversations, documents sources, chunks, embeddings et citations) et **Auth** (connexion par email uniquement). Il faut un projet Supabase hébergé avant de câbler `backend/` et `frontend/`.

## 1. Créer un compte

1. Va sur [supabase.com](https://supabase.com) et inscris-toi (GitHub ou email).
2. Confirme ton email si demandé.
3. Tu arrives sur le [dashboard](https://supabase.com/dashboard). Le tier gratuit suffit pour le développement local.

## 2. Créer un projet

1. Ouvre [New project](https://supabase.com/dashboard/new).
2. Choisis ton organisation (une org personnelle est créée automatiquement à la première inscription).
3. Définis un **nom de projet** (ex. `Assistant Financier`).
4. Choisis un **mot de passe de base de données** — garde-le en lieu sûr ; il sert à l'accès direct à la base et à `supabase link`.
5. Choisis une **région** proche de toi.
6. Clique sur **Create new project** et attends que le statut soit sain (~1–2 minutes).

## 3. Récupérer les identifiants

Tu as besoin de ces valeurs dans la config d'env du backend et du frontend (les noms exacts des variables vivront dans le module de config de chaque service une fois l'app construite).

| Valeur | Où la trouver | Utilisée par |
| ------ | ------------- | ------------ |
| **Project URL** | Dashboard → **Project Settings** → **API** → Project URL | Frontend + backend |
| **Clé anon (publique)** | Même page → clé `anon` `public` | Frontend (sûre pour le navigateur) |
| **Clé service_role (secrète)** | Même page → clé `service_role` `secret` | Backend uniquement — ne jamais exposer au navigateur |
| **Project ref** | URL du dashboard `supabase.com/dashboard/project/<ref>` ou `supabase projects list` | Commandes CLI |
| **Chaîne de connexion base directe** | Dashboard → **Project Settings** → **Database** → Connection string | Migrations Alembic et accès base backend |
| **Mot de passe de base** | Celui défini à la création du projet | Connexion Postgres directe |

Depuis la CLI, tu peux aussi afficher les clés d'API :

```bash
supabase projects api-keys --project-ref <ta-ref-projet>
```

Garde la clé `service_role` hors de git, des bundles client et des fichiers d'env frontend.

## 4. Paramètres d'auth (email uniquement)

Cette app utilise l'auth par email uniquement — pas de Google/SSO.

1. Dashboard → **Authentication** → **Providers**.
2. Laisse **Email** activé.
3. Pour le dev local, tu peux vouloir **Authentication** → **Email** → désactiver « Confirm email » pour que l'inscription marche sans accès à la boîte mail (à réactiver en production).

## 5. Gestion du schéma de base

Assistant Financier utilise Alembic depuis le backend Python pour gérer le schéma de base. Ne crée pas de tables de production manuellement dans le dashboard Supabase.

Les migrations Alembic créent et mettent à jour :

- l'extension `vector` pour `pgvector`
- les tables document source et chunk
- les colonnes d'embedding (`vector(1024)`)
- les colonnes de recherche plein texte générées (configuration `french`)
- les index HNSW et GIN
- les tables de conversation et de citation
- les politiques de row-level security

Utilise la chaîne de connexion base directe/session pour Alembic. N'utilise pas la chaîne de connexion du transaction pooler pour les migrations.

Depuis `backend/` :

```bash
uv run alembic upgrade head
```

Voir [Configuration du backend](backend-setup.md) pour le workflow Alembic.

## Étapes suivantes

- [Configuration du backend](backend-setup.md) — service Python + client Supabase
- [Configuration du frontend](frontend-setup.md) — app React + `@supabase/supabase-js`
