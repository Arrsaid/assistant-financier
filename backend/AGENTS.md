# Backend — notes pour les agents

Ceci est le service FastAPI d'Assistant Financier. Lis d'abord [../AGENTS.md](../AGENTS.md) — les règles universelles de construction y vivent. Ce fichier ajoute les conventions spécifiques au backend.

## Stack

- Python 3.12+
- FastAPI + uvicorn
- Pydantic v2 + pydantic-settings
- `httpx` pour le HTTP sortant
- `pytest` pour les tests
- Client Python Supabase (DB + auth)
- Modèles SQLAlchemy + migrations Alembic pour les changements de schéma
- SDK Mistral pour le LLM & les embeddings
- Supabase `pgvector` pour la recherche sémantique et recherche plein texte Postgres pour le lexical. La recherche hybride exécute la requête vectorielle et la requête plein texte séparément, puis fusionne les listes classées en Python via Reciprocal Rank Fusion.
- `structlog` pour les logs
- `uv` pour la gestion des dépendances et du projet

## Politique de dépendances

Voir la politique universelle dans [../AGENTS.md](../AGENTS.md). Spécificités backend :

- **Préfère la stdlib :** `pathlib`, `datetime`, `uuid`, `enum`, `dataclasses`, `asyncio`, `collections`, `itertools`, `json`, `urllib`.
- **Non OK sans justification :** `python-dateutil`, `toolz`, `funcy`, `more-itertools`, micro-libs JSON/string, wrappers « ergonomiques » par-dessus les SDK déclarés.
- L'extraction de texte des URD (→ Markdown) est un cas légitime de dépendance. Les URD du flux AMF sont surtout du **xHTML iXBRL** (format ESEF) et, pour de rares anciens exercices, du **PDF** : prévois donc un parser HTML/xHTML éprouvé et un extracteur PDF, plutôt que de réécrire ces parsers. Voir [../data/README.md](../data/README.md).
- Les dépendances de dev (test/lint/build) ont une barre plus souple mais restent des outils répandus et à faible empreinte (`pytest`, `ruff`, `httpx`).

## Arborescence (à créer pendant le build)

```text
backend/
├── alembic/
│   ├── env.py           # importe les métadonnées de la base pour l'autogenerate
│   └── versions/        # fichiers de migration relus
├── alembic.ini
├── app/
│   ├── main.py          # point d'entrée FastAPI
│   ├── config.py        # config Pydantic — source de vérité unique de l'env
│   ├── api/             # routeurs FastAPI (chat, ingest, auth)
│   ├── auth/            # vérification du JWT Supabase + dépendance current user
│   ├── chat/            # orchestration du tour, conversion de messages AI SDK, streaming
│   ├── assistant/       # agent PydanticAI, deps, sorties, instructions
│   ├── retrieval/       # requêtes pgvector/plein texte, fusion RRF, lookup des passages sources
│   ├── grounding/       # validation des citations et vérification de l'ancrage des réponses
│   ├── database/        # modèles SQLAlchemy, wrapper client Supabase, helpers de requêtes typés
│   └── prompts/         # gabarits de prompt/instructions si non colocalisés avec assistant
├── ingest/              # scripts d'ingestion ponctuels (extraction xHTML/PDF→Markdown, chunking, embeddings, écritures Supabase)
├── tests/
└── pyproject.toml
```

## Style de code (spécifique backend)

- **Annotations de type sur les fonctions publiques et les éléments au niveau module.** N'annote pas chaque variable locale.
- **Async par défaut dans le code du chemin requête.** Ne lance pas d'I/O bloquante sur l'event loop. Tempfile + petites lectures de fichier synchrones sont OK (c'est rapide) ; les appels réseau doivent être async.
- **Utilise `async def` pour tous les handlers de route** et toute fonction de service faisant de l'I/O.
- **Valide seulement aux frontières.** L'entrée HTTP est validée par des modèles Pydantic. Les réponses d'API externes sont validées au parsing. Les appelants internes sont de confiance.

## Configuration

- `app.config.settings` est la source de vérité unique. Importe `settings` où nécessaire ; n'appelle jamais `os.getenv` dans le code applicatif, n'appelle jamais `load_dotenv`.
- Si un SDK tiers lit `os.environ` directement, ajoute le miroir dans `config.py` — n'éparpille pas de `setdefault` ailleurs.
- Échoue vite au démarrage quand des variables d'env requises manquent.

## Migrations de base de données

- Alembic est la source de vérité des changements de schéma. Ne modifie pas les tables de production manuellement dans le dashboard Supabase.
- Les modèles SQLAlchemy décrivent les tables et colonnes ordinaires. L'autogenerate Alembic crée des migrations candidates, mais chaque migration générée doit être relue avant application.
- Les fonctionnalités spécifiques Supabase/Postgres relèvent d'opérations de migration explicites : `create extension vector`, colonnes `tsvector` générées, index HNSW/GIN, activation RLS et politiques RLS.
- Alembic doit utiliser la connexion base directe/session, pas l'URL du transaction pooler Supabase.
- Lance les migrations depuis `backend/` avec `uv run alembic upgrade head`.

## Recherche plein texte en français

- Le corpus est en français. Configure la recherche plein texte Postgres avec la configuration `french` (`to_tsvector('french', ...)`, `plainto_tsquery('french', ...)`) pour bénéficier du stemming et des stop-words français.
- La colonne `tsvector` générée doit utiliser la même configuration `french` que les requêtes, sinon le classement sera incohérent.

## Tests

- **Préfère l'unitaire à l'intégration.** Mocke à la frontière du service.
- La suite rapide (`pytest -m "not integration"`) doit rester verte et ne toucher ni réseau ni base.
- Les tests d'intégration sont derrière `@pytest.mark.integration` et peuvent nécessiter des identifiants Mistral / Supabase réels.
- Les tests vivent à côté de ce qu'ils testent (`retrieval/retriever.py` → `tests/retrieval/test_retriever.py`).
- Couverture de test requise : logique d'ingestion, recherche, extraction de citations, application de l'ancrage.

## Anti-patterns (rejetés)

- `os.getenv` / `load_dotenv` dans les modules.
- Emballer les réponses FastAPI dans des classes d'enveloppe maison.
- Sur-attraper `Exception` juste pour logger et relancer ; laisse propager.
- État partagé via des globales au lieu de `app.state` FastAPI ou de l'injection de dépendances.
- Replis silencieux qui masquent de vraies erreurs de config.
- Mocker le LLM dans les tests unitaires sans tester aussi le contrat d'ancrage — le prompt est le produit.
