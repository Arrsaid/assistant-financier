# Données

Les artefacts de données locaux pour le développement vivent ici.

- `downloads/` contient les fichiers sources bruts récupérés depuis info-financiere.fr (AMF), regroupés par exercice.
- Les contenus téléchargés sont gitignorés car le corpus peut devenir volumineux (plusieurs centaines de Mo).
- Récupère un corpus d'exemple avec `uv run data/download.py`.
- Avant un téléchargement de masse, vérifie le schéma réel du dataset AMF avec `uv run data/download.py --discover` puis ajuste au besoin les constantes `FIELD_*`, `ISSUERS` et `TARGET_FISCAL_YEARS` en haut du script.

## Source

Les **Documents d'Enregistrement Universel (URD)** des sociétés cotées sont publiés sur **info-financiere.fr**, la base publique de l'information réglementée de l'**AMF** (Autorité des marchés financiers). C'est l'équivalent français du dépôt SEC EDGAR : information réglementée, accessible publiquement.

L'URD est l'équivalent français du *10-K* américain : le rapport annuel réglementé d'un émetteur (présentation des activités, facteurs de risque, comptes, gouvernance).

## Particularité : ESEF (xHTML iXBRL), pas PDF

Contrairement à une idée répandue, les URD de ce flux AMF ne sont **pas** distribués en PDF. Depuis l'exercice 2021, les émetteurs déposent leur rapport annuel au format réglementaire européen **ESEF** : une archive **ZIP** contenant un gros fichier **xHTML (iXBRL)** — du HTML avec des données financières balisées en XBRL. Seuls quelques anciens exercices (≈2020) existent encore en PDF.

C'est en fait une **bonne nouvelle** pour l'ingestion : le xHTML est du texte structuré (titres, sections, tableaux en balises), bien plus propre à extraire qu'un PDF mis en page.

`download.py` gère les deux cas :

1. Cherche les URD par **ISIN exact**, filtre les titres pour écarter avis « mise à disposition », amendements et brochures d'AG, et applique un seuil de taille minimale.
2. Suit l'URL directe en conservant la vraie extension ; pour un **ZIP ESEF**, dézippe et extrait le rapport xHTML (le plus volumineux de l'archive).
3. Regroupe par **exercice** (année de publication − 1) et déduplique.

Le pipeline d'ingestion backend prendra ensuite le relais :

1. Extraire le texte en Markdown normalisé (titres, sections, tableaux), depuis le xHTML iXBRL ou, pour les anciens, depuis le PDF.
2. Découper (chunker), embedder, puis écrire dans Supabase.

> Note : le xHTML iXBRL n'a pas de pagination fixe comme un PDF. Les citations devront s'ancrer sur la **section** (et un offset dans le document) plutôt que sur un numéro de page.

## Échantillon prévu

Par défaut, le téléchargeur récupère les URD des exercices 2020–2025 pour un petit échantillon d'émetteurs du CAC 40 dans des dossiers par exercice sous `data/downloads/`, et écrit un `manifest.json` (émetteur, ISIN, exercice, date de publication, titre, format source, URL source, chemin local).

Émetteurs d'exemple : LVMH, TotalEnergies, Sanofi, L'Oréal, Air Liquide.

La couverture réelle dépend de ce que chaque émetteur a effectivement déposé dans le flux AMF : certains exercices manquent (URD non encore déposé, ou déposé via un autre canal). Le `manifest.json` fait foi sur ce qui a été récupéré.
