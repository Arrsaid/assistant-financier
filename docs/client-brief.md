# Brief client — Haussmann Recherche

## Le client

**Haussmann Recherche** est un cabinet indépendant de recherche actions d'environ 40 analystes. Il vend de la recherche actions approfondie à des clients institutionnels (hedge funds, sociétés de gestion, fonds de pension) sous abonnement annuel (50 k€ à 500 k€+ par client), plus de la recherche commandée sur mesure et des appels avec les analystes.

Il ne gère pas d'argent lui-même. Son produit, c'est la recherche et l'accès à ses analystes.

## Comment Haussmann gagne de l'argent

- Chaque analyste couvre une quinzaine de sociétés cotées dans un secteur précis (luxe, énergie, santé, banque, industrie, etc.)
- Ils produisent des notes de recherche écrites, des modèles financiers et des recommandations au niveau du titre
- Les clients gérants paient pour les notes et pour le droit d'appeler l'analyste avec leurs questions
- La réputation est tout — une seule mauvaise analyse entame la franchise

## Comment ils apportent de la valeur

- Leurs clients (gérants de portefeuille des fonds) n'ont pas la bande passante pour lire chaque URD, rapport semestriel, transcription de résultats et document sectoriel des sociétés où ils investissent
- Les analystes de Haussmann ont déjà fait cette lecture et l'ont transformée en synthèses actionnables
- La valeur, c'est la *condensation* : transformer des milliers de pages en une thèse d'une page sur laquelle le gérant peut agir

## Le problème

Chaque analyste de Haussmann passe environ **la moitié de chaque semaine** à faire de l'ingestion de documents sources — ouvrir des URD, parcourir les sections qui l'intéressent (facteurs de risque, rapport de gestion, segments d'activité), copier-coller des passages, comparer d'une année sur l'autre. Ce n'est qu'après ce travail d'ingestion qu'il peut produire la moindre analyse originale.

Ce travail d'ingestion est :

- Ennuyeux
- Nécessaire (on ne peut pas analyser ce qu'on n'a pas lu)
- Répétitif entre analystes (plusieurs analystes lisent le même URD de LVMH chaque année)
- Le plus gros frein unique à la production des analystes

Recruter plus d'analystes ne règle pas le problème — le goulet d'ingestion croît linéairement avec la couverture. Ils veulent supprimer le goulet.

## Ce qu'ils veulent

Un chatbot interne — appelons-le **Assistant Financier** — où n'importe quel analyste de Haussmann peut :

- Poser des questions en langage naturel sur n'importe quel document du corpus curé de Haussmann
- Obtenir une réponse sourcée qui cite le document précis et la page précise
- Faire suffisamment confiance à la réponse pour fonder une analyse en aval dessus
- L'utiliser depuis un navigateur, connecté avec son adresse email Haussmann
- Voir ses propres conversations passées

## Exemples de questions d'analystes

Le corpus d'exemple actuel contient les URD de LVMH, TotalEnergies, Sanofi, L'Oréal et Air Liquide sur les exercices 2020–2025. Le bot doit savoir traiter des questions comme celles-ci, avec réponses citées et passages sous-jacents :

1. Sur les URD 2020–2025 de LVMH, comment a évolué la répartition du chiffre d'affaires entre Mode & Maroquinerie, Vins & Spiritueux, Parfums & Cosmétiques, Montres & Joaillerie et Distribution sélective, et quelle division semble avoir le plus contribué à un éventuel changement de mix ?
2. Pour TotalEnergies, comment les filings décrivent-ils l'évolution des investissements (capex) entre les activités pétrole/gaz et les énergies bas-carbone (Integrated Power) de 2020 à 2025 ?
3. Comment Sanofi a-t-il décrit ses risques liés aux pertes de brevets, à la dépendance à certains produits clés et à son pipeline de R&D entre 2020 et 2025 ?
4. Sur les URD 2020–2025 de L'Oréal, qu'est-ce qui a changé dans la façon dont l'entreprise décrit la croissance du e-commerce, la Chine et les marchés émergents ?
5. Pour Air Liquide, comment ont évolué les tendances de chiffre d'affaires par zone géographique et par marché final (Grande Industrie, Industriel Marchand, Santé, Électronique) sur les URD disponibles ?
6. Parmi les cinq sociétés, lesquelles ont ajouté, retiré ou modifié de façon significative leur formulation des facteurs de risque liés au climat, à la réglementation, aux chaînes d'approvisionnement ou aux taux de change entre 2020 et 2025 ?
7. Pour LVMH et L'Oréal, que disent les filings sur la dépendance à la Chine et au tourisme international, et la formulation est-elle devenue plus ou moins prudente avec le temps ?
8. Compare les engagements et investissements liés à la décarbonation pour TotalEnergies, Air Liquide et Sanofi. Qu'impliquent les filings sur l'ampleur et le calendrier de ces investissements ?
9. Pour chaque société, résume les expositions géographiques de chiffre d'affaires les plus importantes divulguées dans le dernier URD, puis identifie tout changement d'une année sur l'autre qui pourrait compter pour un analyste.
10. Si un analyste demande si les filings prouvent que la stratégie de décarbonation a amélioré les marges de l'une de ces sociétés, quelles preuves existent dans le corpus, et où le bot doit-il refuser d'inférer au-delà des filings ?

## Ce que « confiance » veut dire ici

C'est un cabinet de recherche. Tout son métier, c'est d'avoir raison. Le bot doit :

- **Ne jamais inventer de faits.** Si la réponse n'est pas dans le corpus, il le dit.
- **Toujours citer.** Chaque affirmation renvoie au document source + page.
- **Montrer le passage sous-jacent** pour que l'analyste vérifie en un clic.

Une réponse fausse mais sûre d'elle est pire que pas de réponse. Les hallucinations tuent le produit.

## Contraintes

- Corpus : URD (Documents d'Enregistrement Universel) de sociétés du CAC 40, 2020–2025
- Source : info-financiere.fr / AMF (information réglementée publique)
- Utilisateurs : ~40 analystes de Haussmann, plus quelques associés
- Connexion : adresses email Haussmann (pas de SSO requis)
- Hébergement : doit tourner sur une empreinte cloud petite/moyenne ; Haussmann n'a pas d'équipe infra

## Hors périmètre (explicitement)

- Recommandations de trading ou sélections de titres
- Sources de données externes (pas d'actualités, pas de réseaux sociaux, pas de données alternatives)
- Toute analyse non ancrée dans le corpus
- Multi-tenant / multi-client. C'est interne à Haussmann uniquement.
- Facturation, offres, paywalls
- Application mobile

## Définition de « terminé »

Le groupe pilote (5 analystes seniors) l'essaie pendant une semaine et rapporte un gain d'au moins 3 heures par analyste par semaine. Si oui, Haussmann le déploie à tout le cabinet.
