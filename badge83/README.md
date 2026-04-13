# Badge83 — Projet Open Badges

## Description

Ce projet est une implémentation légère d'Open Badges 2.0 avec FastAPI.
Il permet d'émettre et de vérifier des assertions conformes au modèle Open Badges en s'appuyant sur les objets principaux du standard : `Issuer`, `BadgeClass` et `Assertion`.

## Fonctionnalités

- Émettre une assertion Open Badge (`POST /issue`) à partir de `name` et `email`.
- Émettre un badge **baked** dans un PNG (`POST /issue-baked`) — l'assertion JSON est injectée dans l'image via un chunk `tEXt` conforme au standard Open Badges.
- Vérifier une assertion par ID (`GET /verify/{id}` ou `GET /verify?badge_id=...`).
- Vérifier un badge baked depuis un fichier PNG uploadé (`POST /verify-baked`) — extraction automatique de l'assertion depuis le chunk `openbadges`.
- **Endpoints publics HostedBadge** — Servir l'Issuer, le BadgeClass et les Assertions via des URLs HTTP publiques pour validation externe (ex. `validator.openbadges.org`).
- Stocker les assertions en JSON dans `data/issued/` et les PNG baked dans `data/baked/`.
- Fournir des fichiers MODE83 de référence pour `Issuer` et `BadgeClass` (via templates).
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
    │   ├── issuer_template.json      # Profil émetteur (placeholder ${BASE_URL})
    │   ├── badgeclass_template.json  # Définition badge (placeholder ${BASE_URL})
    │   ├── badge.png                 # Image de base pour le baking
    │   ├── issued/                   # Assertions JSON
    │   └── baked/                    # Badges PNG baked
    ├── templates/
    │   └── index.html
    ├── docs/
    │   ├── technical-baking-verification.md
    │   └── plan-hosted-verification.md
    ├── requirements.txt
    ├── .env.example
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
```

### Configuration de l'URL publique

Les badges émis contiennent des URLs publiques pointant vers le serveur. Définissez la variable d'environnement `BADGE83_BASE_URL` :

```bash
# Copier l'exemple et configurer l'URL du serveur
cp .env.example .env
# Éditer .env et mettre l'IP ou le domaine de votre serveur
```

### Démarrage du serveur

```bash
export BADGE83_BASE_URL=http://127.0.0.1:8000  # ou votre URL publique
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Si le port `8000` est déjà utilisé, choisissez un autre port :

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

## Utilisation

Une fois le serveur démarré, ouvrir dans le navigateur :

- `http://127.0.0.1:8000`

### Tests rapides d'API

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

### Endpoints publics (HostedBadge)

Ces endpoints sont utilisés par les validateurs externes pour résoudre les URLs contenues dans les badges :

| Endpoint | Description |
|----------|-------------|
| `GET /issuers/main` | Profil de l'émetteur (Issuer) |
| `GET /badges/blockchain-foundations` | Définition du badge (BadgeClass) |
| `GET /assertions/{uuid}` | Assertion individuelle |
| `GET /assets/{fichier}` | Assets statiques (images de badge, logo) |

```bash
# Exemple : récupérer le profil de l'émetteur
curl http://127.0.0.1:8000/issuers/main

# Exemple : récupérer une assertion par son ID
curl http://127.0.0.1:8000/assertions/<uuid>
```

## Structure Open Badges implémentée

Le projet utilise une structure minimale inspirée d'Open Badges 2.0 :

- `issuer_template.json` : profil de l'émetteur MODE83 (avec `${BASE_URL}` dynamique)
- `badgeclass_template.json` : définition du badge MODE83 (avec `${BASE_URL}` dynamique)
- `Assertion` : badge individuel remis à un apprenant, généré dans `data/issued/`

Lors de l'émission :
- un identifiant unique d'assertion est créé,
- l'email du destinataire est dérivé en identité hachée,
- l'assertion embarque les URLs publiques de l'`Issuer` et du `BadgeClass` (format HostedBadge).

Les champs de structure restent ceux attendus par le standard Open Badges 2.0, mais les contenus éditoriaux de cette implémentation MODE83 sont rédigés en français.

## Remarques

- Le projet fonctionne sans base de données : les badges sont stockés dans des fichiers JSON (`data/issued/`) et PNG baked (`data/baked/`).
- **Badge Baking** : l'assertion JSON est injectée dans le PNG via un chunk `tEXt` avec le mot-clé `openbadges`, conformément au standard Open Badges 2.0. Le PNG reste visuellement identique à l'original.
- Le chunk `openbadges` est unique : re-baker le même PNG ne duplique pas les données.
- La vérification d'un badge baked se fait en extrayant le chunk `openbadges` du PNG ; aucune connexion réseau n'est requise.
- **HostedBadge** : les assertions contiennent des URLs HTTP publiques (au lieu d'objets imbriqués) permettant la validation externe par des tiers comme `validator.openbadges.org`.

## Journal des modifications

Voir [`docs/CHANGELOG-130426.md`](docs/CHANGELOG-130426.md) pour les modifications du 13/04/26.

## Roadmap

| Étape | Statut | Description |
|-------|--------|-------------|
| Émission d'assertions JSON | ✅ Implémenté | `POST /issue` |
| Badge Baking PNG | ✅ Implémenté | `POST /issue-baked` avec chunk `tEXt openbadges` |
| Vérification par ID | ✅ Implémenté | `GET /verify/{id}` |
| Vérification PNG baked | ✅ Implémenté | `POST /verify-baked` |
| Interface web | ✅ Implémenté | Page unique avec formulaires d'émission et vérification |
| Endpoints hébergés (HostedBadge) | ✅ Implémenté | URLs publiques pour Issuer, BadgeClass et Assertions |
| Signature JWS (SignedBadge) | 🔲 Planifié | Chiffrer les assertions avec une clé privée, vérification par clé publique |
| Ancrage blockchain | 🔲 Planifié | Enregistrer les empreintes d'assertions sur une blockchain pour preuve d'immutabilité |
| Validation IMS officielle | 🔲 Planifié | Passer le badge par le validateur <https://validator.openbadges.org> |
