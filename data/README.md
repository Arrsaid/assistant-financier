# Données

Les artefacts de données locaux pour le développement vivent ici.

- `downloads/` contient les fichiers sources bruts récupérés depuis info-financiere.fr (AMF), regroupés par année.
- Les contenus téléchargés sont gitignorés car le corpus peut devenir volumineux.
- Récupère un corpus d'exemple avec `uv run data/download.py`.
- Avant un téléchargement de masse, vérifie le schéma réel du dataset AMF avec `uv run data/download.py --discover` puis ajuste les constantes `FIELD_*` en haut du script si besoin.

## Source

Les **Documents d'Enregistrement Universel (URD)** des sociétés cotées sont publiés sur **info-financiere.fr**, la base publique de l'information réglementée de l'**AMF** (Autorité des marchés financiers). C'est l'équivalent français du dépôt SEC EDGAR : information réglementée, accessible publiquement.

L'URD est l'équivalent français du *10-K* américain : le rapport annuel réglementé d'un émetteur (présentation des activités, facteurs de risque, comptes, gouvernance).

## Particularité : PDF, pas HTML

Contrairement aux dépôts SEC (HTML structuré), les URD français sont distribués en **PDF** souvent volumineux (plusieurs centaines de pages, tableaux complexes). Le pipeline d'ingestion doit donc :

1. Télécharger le PDF de l'URD.
2. Extraire le texte en Markdown normalisé (en préservant titres, sections et tableaux autant que possible).
3. Découper (chunker), embedder, puis écrire dans Supabase.

## Échantillon prévu

Par défaut, le téléchargeur récupèrera les URD récents (exercices 2020–2025) pour un petit échantillon d'émetteurs du CAC 40 dans des dossiers par année sous `data/downloads/`, et écrira un `manifest.json` (émetteur, ISIN, exercice, URL source, chemin local).

Émetteurs d'exemple : LVMH, TotalEnergies, Sanofi, L'Oréal, Air Liquide.
