# Badge83 — Projet Open Badges

## Description

Ce projet est une implémentation légère d'Open Badges 2.0 avec FastAPI.
Il permet d'émettre et de vérifier des assertions conformes au modèle Open Badges en s'appuyant sur les objets principaux du standard : `Issuer`, `BadgeClass` et `Assertion`.

## Fonctionnalités

- Émettre une assertion Open Badge (`POST /issue`) à partir de `name` et `email`.
- Émettre un badge **baked** dans un PNG (`POST /issue-baked`) — l'assertion JSON est injectée dans l'image via un chunk `tEXt` conforme au standard Open Badges.
- Vérifier une assertion par ID (`GET /verify/{id}` ou `GET /verify?badge_id=...`).
- Vérifier un badge baked depuis un fichier PNG uploadé (`POST /verify-baked`) — extraction automatique de l'assertion depuis le chunk `openbadges`.
- Stocker les assertions en JSON dans `data/issued/` et les PNG baked dans `data/baked/`.
- Fournir des fichiers MODE83 de référence pour `Issuer` et `BadgeClass`.
- Refuser les anciens badges JSON non conformes au format `Assertion` Open Badges 2.0.

## Structure du projet

```text
mode83/
└── badge83/
    ├── app/
    │   ├── main.py
    │   ├── issuer.py
    │   ├── verifier.py
    │   ├── baker.py          # Baking / unbaking PNG (tEXt chunk)
    │   └── models.py
    ├── data/
    │   ├── issuer.json
    │   ├── badgeclass.json
    │   ├── badge.png           # Image de base pour le baking
    │   ├── issued/             # Assertions JSON
    │   └── baked/              # Badges PNG baked
    ├── templates/
    │   └── index.html
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
# Vérification par ID
curl http://127.0.0.1:8000/verify/test-id
curl "http://127.0.0.1:8000/verify?badge_id=test-id"

# Émission d'un badge baked (télécharge un PNG)
curl -X POST -F "name=Alice" -F "email=alice@example.org" http://127.0.0.1:8000/issue-baked --output badge.png

# Vérification d'un badge baked (upload PNG)
curl -X POST -F "badge=@badge.png" http://127.0.0.1:8000/verify-baked
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

- Le projet fonctionne sans base de données : les badges sont stockés dans des fichiers JSON (`data/issued/`) et PNG baked (`data/baked/`).
- **Badge Baking** : l'assertion JSON est injectée dans le PNG via un chunk `tEXt` avec le mot-clé `openbadges`, conformément au standard Open Badges 2.0. Le PNG reste visuellement identique à l'original.
- Le chunk `openbadges` est unique : re-baker le même PNG ne duplique pas les données.
- La vérification d'un badge baked se fait en extrayant le chunk `openbadges` du PNG ; aucune connexion réseau n'est requise.

## Roadmap

| Étape | Statut | Description |
|-------|--------|-------------|
| Émission d'assertions JSON | ✅ Implémenté | `POST /issue` |
| Badge Baking PNG | ✅ Implémenté | `POST /issue-baked` avec chunk `tEXt openbadges` |
| Vérification par ID | ✅ Implémenté | `GET /verify/{id}` |
| Vérification PNG baked | ✅ Implémenté | `POST /verify-baked` |
| Interface web | ✅ Implémenté | Page unique avec formulaires d'émission et vérification |
| Endpoints hébergés (HostedBadge) | 🔲 Planifié | Servir les assertions, l'issuer et le BadgeClass via des URLs HTTP publiques pour validation externe |
| Signature JWS (SignedBadge) | 🔲 Planifié | Chiffrer les assertions avec une clé privée, vérification par clé publique |
| Ancrage blockchain | 🔲 Planifié | Enregistrer les empreintes d'assertions sur une blockchain pour preuve d'immutabilité |
| Validation IMS officielle | 🔲 Planifié | Passer le badge par le validateur <https://validator.openbadges.org> |
