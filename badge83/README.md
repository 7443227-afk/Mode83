# Badge83 — Prototype Open Badges

## Description

Ce projet est un prototype backend minimal réalisé pour un contexte de stage en France.
Il montre de manière claire les bases des digital credentials / Open Badges avec FastAPI,
sans base de données et sans authentification.

## Fonctionnalités

- Émettre un badge (`POST /issue`) à partir de `name` et `email`.
- Vérifier un badge (`GET /verify/{id}`) à partir de son identifiant.
- Stockage des badges sous forme de fichiers JSON dans `data/issued/`.
