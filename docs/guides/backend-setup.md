# Configuration du backend

Ce projet utilise un backend Python + FastAPI séparé car le serveur est responsable du travail IA et de traitement documentaire, pas seulement de CRUD web basique. Python offre le meilleur écosystème pour l'ingestion, le chunking, les embeddings, la recherche, l'évaluation et les workflows LLM. Garder cette logique derrière une API dédiée garde aussi le frontend focalisé sur l'expérience utilisateur, pendant que le backend détient l'accès aux données, l'orchestration et l'ancrage.

## Init (depuis un `backend/` vide)

```bash
cd backend
uv sync
uv add fastapi uvicorn pydantic pydantic-settings httpx structlog mistralai supabase pydantic-ai sqlalchemy alembic "psycopg[binary]" pgvector
uv add --dev pytest ruff
```

Les bibliothèques d'extraction de texte (pour transformer les URD en Markdown) seront ajoutées à l'étape d'ingestion — voir [../architecture.md](../architecture.md), section « Pipeline d'ingestion ». Les URD sont surtout du xHTML iXBRL (ESEF) et, pour de rares anciens exercices, du PDF : prévois un parser HTML/xHTML et un extracteur PDF. Choisis-les à ce moment-là selon la qualité d'extraction sur des URD réels.

## Migrations de base de données

Alembic détient les changements de schéma pour ce projet. Les modèles SQLAlchemy décrivent les tables de l'app, et les migrations Alembic appliquent ces changements à Supabase Postgres.

Initialise Alembic une fois depuis `backend/` :

```bash
uv run alembic init alembic
```

Configure `alembic/env.py` pour importer les métadonnées SQLAlchemy de l'app et lire l'URL de base directe depuis `app.config.settings`. Utilise la connexion base directe/session de Supabase, pas l'URL du transaction pooler, pour les migrations.

Crée une migration après avoir changé les modèles SQLAlchemy :

```bash
uv run alembic revision --autogenerate -m "add document tables"
```

Relis toujours la migration générée. Ajoute des opérations explicites pour les fonctionnalités Supabase/Postgres que l'autogenerate ne peut pas inférer de façon fiable :

- `create extension if not exists vector`
- colonnes `vector(1024)`
- colonnes `tsvector` générées (configuration `french`)
- index HNSW et GIN
- activation RLS et politiques

Applique les migrations :

```bash
uv run alembic upgrade head
```

## Lancer

```bash
cd backend
uv sync
uv run alembic upgrade head
uv run uvicorn app.main:app --reload
```

## Imports (`from app...`)

`backend/app` est installé comme paquet éditable par `uv sync`, donc les imports `from app...` fonctionnent depuis uvicorn, l'exécution Python directe, les tests, et les kernels Jupyter qui utilisent le venv backend.

Les sections `[build-system]` et `[tool.hatch.build.targets.wheel]` dans `backend/pyproject.toml` indiquent à uv comment installer le paquet local `app/`. Sans cette installation de paquet, les imports dépendent du répertoire de travail courant ou d'un `PYTHONPATH` configuré à la main, ce qui est fragile dans les notebooks et les boutons « run » des IDE.

Commande de serveur d'API préférée :

```bash
cd backend
uv run uvicorn app.main:app --reload
```

L'exécution directe de fichier marche aussi :

```bash
cd backend
uv run python app/main.py
```

Pour Jupyter, installe et sélectionne le kernel backend :

```bash
cd backend
uv run python -m ipykernel install --user --name assistant-financier-backend --display-name "Assistant Financier Backend"
```

Les notebooks peuvent alors importer les modules backend :

```python
from app.config import settings
```

## Données URD d'exemple

Depuis la racine du dépôt :

```bash
uv run data/download.py
```

Vérifie d'abord le schéma réel du dataset AMF avec `uv run data/download.py --discover` (voir [../../data/README.md](../../data/README.md)).
