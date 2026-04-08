# Badge83 — Prototype Open Badges

## Description

Ce projet est un prototype backend minimal réalisé pour un contexte de stage en France.
Il montre de manière claire les bases des digital credentials / Open Badges avec FastAPI,
sans base de données et sans authentification.

## Fonctionnalités

- Émettre un badge (`POST /issue`) à partir de `name` et `email`.
- Vérifier un badge (`GET /verify/{id}`) à partir de son identifiant.
- Stockage des badges sous forme de fichiers JSON dans `data/issued/`.

## Structure du projet

```text
mode83/
├── badge.sh                # script de démarrage rapide
└── badge83/
    ├── app/
    │   ├── main.py
    │   ├── issuer.py
    │   └── verifier.py
    ├── data/
    │   └── issued/
    ├── templates/
    ├── requirements.txt
    └── README.md
```

## Prérequis

- `python3`
- accès à `pip` / création de virtualenv (`python3 -m venv`)

## Installation et lancement

### Option 1 — lancement rapide avec `badge.sh`

Depuis la racine du dépôt `mode83` :

```bash
chmod +x badge.sh
./badge.sh
```

Le script :
- crée `badge83/.venv` si nécessaire,
- installe les dépendances depuis `requirements.txt`,
- démarre `uvicorn` sur `http://127.0.0.1:8000`.

Vous pouvez aussi personnaliser l'hôte et le port :

```bash
HOST=0.0.0.0 PORT=8010 ./badge.sh
```

### Option 2 — lancement manuel

Depuis `mode83/badge83` :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

## Utilisation

Une fois le serveur démarré, ouvrir dans le navigateur :

- `http://127.0.0.1:8000`

Tests rapides d'API :

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/verify/test-id
```

Réponse attendue pour un badge inexistant :

```json
{"valid": false, "badge": null}
```

## Remarques

- Le projet fonctionne sans base de données : les badges sont stockés dans des fichiers JSON.
- Un `HEAD /` retourne `405 Method Not Allowed`, ce qui est normal ici car la route `/` est définie en `GET` uniquement.
