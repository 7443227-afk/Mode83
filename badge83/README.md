# Badge83 — Projet Open Badges

## Description

Ce projet est une implémentation légère d'Open Badges 2.0 avec FastAPI.
Il permet d'émettre et de vérifier des assertions conformes au modèle Open Badges en s'appuyant sur les objets principaux du standard : `Issuer`, `BadgeClass` et `Assertion`.

## Fonctionnalités

- Émettre une assertion Open Badge (`POST /issue`) à partir de `name` et `email`.
- Vérifier une assertion (`GET /verify/{id}`) à partir de son identifiant.
- Stocker les assertions en JSON dans `data/issued/`.
- Fournir des fichiers MODE83 de référence pour `Issuer` et `BadgeClass`.
- Refuser les anciens badges JSON non conformes au format `Assertion` Open Badges 2.0.

## Structure du projet

```text
mode83/
└── badge83/
    ├── app/
    │   ├── main.py
    │   ├── issuer.py
    │   └── verifier.py
    ├── data/
    │   ├── issuer.json
    │   ├── badgeclass.json
    │   └── issued/
    ├── templates/
    ├── requirements.txt
    └── README.md
```

## Prérequis

- `python3`
- accès à `pip` / création de virtualenv (`python3 -m venv`)

## Installation et lancement

Depuis `mode83/badge83` :

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Si le port `8000` est déjà utilisé, choisissez un autre port :

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

## Utilisation

Une fois le serveur démarré, ouvrir dans le navigateur :

- `http://127.0.0.1:8000`

Tests rapides d'API :

```bash
curl http://127.0.0.1:8000/
curl http://127.0.0.1:8000/verify/test-id
curl "http://127.0.0.1:8000/verify?badge_id=test-id"
```

Réponse attendue pour un badge inexistant :

```json
{"valid": false, "badge": null}
```

## Structure Open Badges implémentée

Le projet utilise une structure minimale inspirée d'Open Badges 2.0 :

- `issuer.json` : profil de l'émetteur MODE83
- `badgeclass.json` : définition du badge MODE83
- `Assertion` : badge individuel remis à un apprenant, généré dans `data/issued/`

Lors de l'émission :
- un identifiant unique d'assertion est créé,
- l'email du destinataire est dérivé en identité hachée,
- l'assertion embarque les informations `Issuer` et `BadgeClass`.

Les champs de structure restent ceux attendus par le standard Open Badges 2.0, mais les contenus éditoriaux de cette implémentation MODE83 sont rédigés en français.

## Remarques

- Le projet fonctionne sans base de données : les badges sont stockés dans des fichiers JSON.
- Cette version constitue une base de travail vers la conformité Open Badges 2.0, mais n'implémente pas encore la signature/baking PNG ni la validation officielle complète.
