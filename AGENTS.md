# Instructions pour les agents

Ce fichier est la source de vérité pour tout agent de code (Claude Code, Cursor, Codex, etc.) travaillant dans ce dépôt. À lire avant de toucher au code.

## Stack

- **Backend :** Python + FastAPI
- **Frontend :** Vite + React SPA + TypeScript
- **Base de données :** Supabase Postgres (utilisateurs, conversations, documents sources, chunks)
- **Migrations :** modèles SQLAlchemy + Alembic, pilotés depuis le backend
- **Recherche (retrieval) :** Supabase `pgvector` + recherche plein texte Postgres
- **Authentification :** Supabase Auth
- **Hébergement :** Railway (un service backend + un service frontend)
- **LLM + embeddings :** Mistral AI

La stack est verrouillée sauf changement explicite. Ne propose pas d'alternatives sans raison déclarée.

## Arborescence du dépôt

```text
assistant-financier/
├── AGENTS.md           # ce fichier
├── README.md
├── data/               # corpus local + script de téléchargement (contenus gitignorés)
├── docs/               # specs, briefs, notes de conception
├── backend/            # service FastAPI (voir backend/AGENTS.md)
└── frontend/           # SPA React (voir frontend/AGENTS.md)
```

## Politique de dépendances

**Par défaut : écris-le toi-même. Ne prends une bibliothèque que si l'alternative serait non triviale, source d'erreurs, ou la réinvention d'un standard.** Chaque dépendance est un passif — taille du bundle, risque de chaîne d'approvisionnement, travail de mise à jour futur.

Dépendances acceptables :

- Ce qui est réellement difficile à faire correctement (clients HTTP, serveurs ASGI, drivers SQL, parsers, SDK de LLM, ORM, migrations, SDK d'auth, extraction de texte xHTML/PDF).
- La stack déclarée (FastAPI, React, Vite, clients Supabase, SDK Mistral, etc.).

Non acceptable :

- Bibliothèques utilitaires qui emballent 5 à 20 lignes de stdlib ou d'API de plateforme.
- Frameworks là où une fonction suffirait.
- Couches « API plus jolie » par-dessus une dépendance déjà présente.

Avant d'ajouter une dépendance runtime, réponds dans le message de commit :

1. Que fait-elle exactement qu'on ne peut pas écrire en moins de 30 lignes de code clair ?
2. À quelle fréquence est-elle utilisée ?
3. Quelle est son empreinte de maintenance / de dépendances transitives ?

Les spécificités par stack vivent dans `backend/AGENTS.md` et `frontend/AGENTS.md`.

## Configuration

Un unique module de configuration est la source de vérité de l'environnement par service (`backend/app/config.py`, `frontend/lib/env.ts`). N'appelle pas `os.getenv` / ne lis pas `process.env` directement dans le code applicatif. N'appelle `load_dotenv` nulle part. Si un SDK tiers lit des variables d'environnement directement, reflète-les dans le module de config — n'éparpille pas de `setdefault` ailleurs.

Échoue vite au démarrage si une config requise manque. Pas de repli silencieux qui masque une vraie erreur de configuration.

## Langue

Le corpus produit et la plupart des questions utilisateurs sont en **français** (Documents d'Enregistrement Universel du CAC 40). Garde le code, les identifiants, les commentaires et la doc en français, et suppose un contenu français de bout en bout : texte français dans les chunks, requêtes en français, réponses en français, et recherche plein texte configurée pour le dictionnaire français.

## Style de code (universel)

- **Fonctions petites et évidentes.** Une fonction de 15 lignes aux noms clairs vaut mieux qu'une abstraction à trois classes.
- **Pas d'abstraction prématurée.** Trois lignes similaires valent mieux qu'une classe de base mal nommée. On extrait quand il y a un troisième appelant, pas un hypothétique.
- **Pas de gestion d'erreur pour des cas impossibles.** Fais confiance aux appelants internes et aux garanties du framework. Valide seulement aux frontières : entrées HTTP, API externes, écritures en base, parsing non fiable.
- **Pas de couches de rétrocompatibilité** sauf demande explicite.
- **Pas de feature flags** ajoutés par anticipation.
- **Commentaires :** expliquent le *pourquoi* quand il n'est pas évident, jamais le *quoi*. Supprime les TODO obsolètes.
- **Garde les fichiers ciblés.** Préfère les petits modules.
