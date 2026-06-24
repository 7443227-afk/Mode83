# Badge83 — Open Badges MODE83

Badge83 est une application FastAPI légère pour émettre, gérer et vérifier des badges conformes au modèle **Open Badges 2.0**. Le projet cible les usages MODE83 : émission individuelle ou groupée, badges PNG baked, QR de vérification, registre local SQLite, preuves locales déterministes et ancrage blockchain optionnel.

## Fonctionnalités principales

- Émission d'assertions Open Badges 2.0 (`POST /issue`).
- Émission de badges PNG baked (`POST /issue-baked`) avec chunk `openbadges`.
- QR code visible sur les PNG, pointant vers une page publique de vérification mobile.
- Constructeur opérateur de modèles de badges : schémas, textes dynamiques, fond PNG, QR configurable, prévisualisation, modification et duplication.
- Émission depuis un modèle (`POST /badge-constructor/templates/{template_id}/issue-baked`).
- Émission groupée CSV/XLSX : prévisualisation, émission partielle contrôlée, archive ZIP, rapport CSV et historique SQLite.
- Bureau de vérification administrateur (`GET /verify-desk`) pour analyser un PNG et retrouver les informations utiles.
- Vérification publique par ID, QR, page humaine, assertion HostedBadge ou upload PNG.
- Registre SQLite local pour l'administration, la recherche, les preuves, les révocations, l'audit et l'ancrage.
- Preuve locale déterministe : canonicalisation, hash SHA-256, table `credential_proofs`.
- Révocation locale et révocation blockchain optionnelle.
- Ancrage blockchain optionnel via providers `mock` ou `evm` et contrats Hardhat dans `blockchain/`.
- Protection des routes opérateur par cookie applicative FastAPI, compatible avec Nginx `auth_request` en production.
- Politique RGPD par défaut : email complet non intégré dans l'assertion publique ni dans le PNG baked.

## Structure du projet

```text
badge83/
├── app/                         # Application FastAPI
│   ├── main.py                  # Routes principales, auth, API admin, HostedBadge
│   ├── issuer.py                # Émission d'assertions et PNG baked
│   ├── verifier.py              # Vérification JSON/PNG
│   ├── baker.py                 # Injection/extraction du chunk PNG openbadges
│   ├── database.py              # Registre SQLite et schéma local
│   ├── proofs/                  # Preuves, audit, révocation, ancrage
│   └── routes/badge_constructor # Constructeur et émission groupée
├── blockchain/                  # Smart contracts Hardhat optionnels
├── data/                        # Templates publics et assets de référence
├── docker/                      # Entrypoint, setup et Nginx production
├── docs/                        # Documentation finale maintenue
├── templates/                   # Pages HTML
├── tests/                       # Tests unitaires Python
├── docker-compose.yml           # Docker local
├── docker-compose.prod.yml      # Docker production avec Nginx
├── badge83.env.exemple          # Exemple de configuration shell
├── requirements.txt             # Dépendances applicatives
├── requirements-blockchain.txt  # Dépendances EVM optionnelles
└── badge83.sh                   # Script local de gestion serveur
```

Les dossiers et fichiers runtime (`data/issued/`, `data/baked/`, `data/registry.db`, `runtime-data/`, `.env`, `badge83.env`, certificats, logs) ne doivent pas être versionnés.

## Documentation maintenue

L'index complet est disponible dans [`docs/README.md`](docs/README.md).

Documents principaux :

- [`docs/guide-formateur-mode83.md`](docs/guide-formateur-mode83.md) — guide opérateur/formateur.
- [`docs/guide-edition-modele-constructeur.md`](docs/guide-edition-modele-constructeur.md) — constructeur de modèles.
- [`docs/guide-emission-groupee-csv.md`](docs/guide-emission-groupee-csv.md) — émission groupée CSV/XLSX.
- [`docs/bureau-verification-mode83.md`](docs/bureau-verification-mode83.md) — bureau de vérification.
- [`docs/technical-baking-verification.md`](docs/technical-baking-verification.md) — baking PNG et vérification Open Badges.
- [`docs/blockchain-anchoring.md`](docs/blockchain-anchoring.md) — preuves locales et modèle d'ancrage.
- [`docs/blockchain-evm-anchoring.md`](docs/blockchain-evm-anchoring.md) — ancrage EVM.
- [`docs/revocation-model.md`](docs/revocation-model.md) — révocation locale.
- [`docs/openbadges-validator-keys-reference.md`](docs/openbadges-validator-keys-reference.md) — référence de compatibilité Open Badges.

Les notes de formation, plans, rapports, brouillons et documents historiques sont conservés localement dans `formation/`, dossier ignoré par Git.

## Prérequis

- Python 3 avec `venv` et `pip`.
- Docker et Docker Compose pour l'exploitation conteneurisée.
- Node.js/npm uniquement pour les contrats dans `blockchain/`.

## Installation locale avec virtualenv

Depuis la racine de l'espace de travail `/home/ubuntu/projects/Mode83` :

```bash
python3 -m venv .venv
.venv/bin/pip install -r badge83/requirements.txt
```

Lancer ensuite l'application depuis `badge83/` :

```bash
cd badge83
cp badge83.env.exemple badge83.env
# éditer badge83.env avant une émission réelle
./badge83.sh start
./badge83.sh status
./badge83.sh logs
./badge83.sh stop
```

Le script `badge83.sh` charge `badge83/badge83.env` si le fichier existe, utilise le virtualenv de l'espace de travail et démarre Uvicorn.

Lancement manuel équivalent :

```bash
cd badge83
BADGE83_BASE_URL=http://127.0.0.1:8000 \
../.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

## Configuration essentielle

Variables principales :

```text
BADGE83_HOST=0.0.0.0
BADGE83_PORT=8000
BADGE83_BASE_URL=https://votre-domaine.example
BADGE83_REGISTRY_DB=/chemin/vers/registry.db
BADGE83_ENV=development|production
BADGE83_AUTH_USERNAME=admin83
BADGE83_AUTH_PASSWORD=<secret fort>
BADGE83_AUTH_SECRET=<secret fort>
BADGE83_SEARCH_PEPPER=<secret stable>
BADGE83_EMBED_ADMIN_RECIPIENT=false
BADGE83_MAX_PNG_UPLOAD_BYTES=52428800
BADGE83_MAX_CSV_UPLOAD_BYTES=10485760
BADGE83_MAX_IMAGE_PIXELS=50000000
```

`BADGE83_BASE_URL` est critique : cette URL est inscrite dans les assertions, les HostedBadges et les QR codes. Elle doit être définie avant toute émission réelle.

En production (`BADGE83_ENV=production` ou `prod`), l'application refuse les secrets faibles de développement.

## Docker

### Démonstration locale

Depuis `badge83/` :

```bash
cp .env.docker.example .env
# éditer .env si nécessaire
docker compose up -d --build
```

Application : `http://localhost:8000`.

Les données générées sont persistées dans `badge83/runtime-data/`, monté dans le conteneur en `/app/data`.

Commandes utiles :

```bash
docker compose ps
docker compose logs -f badge83
docker compose down
```

### Production HTTPS avec Nginx

Depuis `badge83/` :

```bash
cp .env.production.example .env
# éditer .env : domaine, BADGE83_BASE_URL, secrets forts
# placer les certificats dans docker/nginx/certs/fullchain.pem et privkey.pem
docker compose -f docker-compose.prod.yml up -d --build
```

Architecture recommandée :

```text
Internet -> Nginx HTTPS -> Badge83 FastAPI -> runtime-data
```

Le reverse proxy laisse publics les endpoints nécessaires à la vérification Open Badges et protège les routes opérateur via `auth_request`. Les routes sensibles restent également protégées côté FastAPI.

## Sécurité et confidentialité

- Ne jamais committer `.env`, `badge83.env`, `runtime-data/`, `data/issued/`, `data/baked/`, `data/registry.db`, certificats TLS, logs ou sauvegardes.
- Générer des valeurs fortes pour `BADGE83_AUTH_PASSWORD`, `BADGE83_AUTH_SECRET` et `BADGE83_SEARCH_PEPPER`.
- Sauvegarder hors Git `.env`/`badge83.env`, `runtime-data/` ou `data/registry.db`, les assertions et les PNG baked.
- Par défaut, l'email complet n'est pas inscrit dans l'assertion publique ni dans le PNG baked (`BADGE83_EMBED_ADMIN_RECIPIENT=false`).
- Le registre SQLite local peut contenir des données personnelles administratives : il doit être protégé et sauvegardé comme donnée sensible.
- Aucune donnée personnelle n'est envoyée on-chain par le provider EVM ; seul un hash opaque est transmis.

## Endpoints principaux

### Publics

| Endpoint | Rôle |
| --- | --- |
| `GET /issuers/main` | Profil public de l'émetteur MODE83. |
| `GET /badges/blockchain-foundations` | BadgeClass public. |
| `GET /assertions/{id}` | Assertion Open Badges hébergée. |
| `GET /assets/{asset}` | Assets publics. |
| `GET /verify/{id}` ou `GET /verify?badge_id=...` | Vérification JSON par identifiant. |
| `GET /verify/badge/{id}` | Page humaine de vérification. |
| `GET /verify/qr/{id}` | Page mobile publique pour QR. |
| `POST /verify-baked` | Vérification d'un PNG baked uploadé. |
| `POST /verify-online` | Vérification distante contrôlée d'une assertion publique. |

### Opérateur / administrateur

Ces routes nécessitent une session administrateur :

| Endpoint | Rôle |
| --- | --- |
| `GET /` | Console d'administration. |
| `POST /issue` | Émission JSON. |
| `POST /issue-baked` | Émission PNG baked. |
| `GET /verify-desk` | Bureau de vérification. |
| `GET /api/dashboard/stats` | Statistiques locales. |
| `GET /api/badges` / `GET /api/badges/search` | Consultation et recherche. |
| `GET/PUT/DELETE /api/badges/{id}` | Administration d'un badge. |
| `GET /api/badges/{id}/proof` | Preuve locale. |
| `POST /api/badges/{id}/revoke` | Révocation locale. |
| `POST /api/badges/{id}/anchor` | Ancrage optionnel. |
| `GET /api/badges/{id}/audit` | Journal d'audit. |
| `GET/POST/PUT/DELETE /badge-constructor/...` | Constructeur, modèles et émission groupée. |

## Open Badges implémenté

Badge83 produit des badges de type **HostedBadge** Open Badges 2.0 :

- `Issuer` public résolu via `/issuers/main`.
- `BadgeClass` public résolu via `/badges/blockchain-foundations`.
- `Assertion` publique résolue via `/assertions/{uuid}`.
- `recipient.identity` hashé au format `sha256$...`.
- `verification.type=HostedBadge` avec URL publique de l'assertion.
- Métadonnées utiles : `@language`, `expires`, `evidence`, `tags`, `alignment` selon les templates.

Les assertions JSON dans `data/issued/` restent la source canonique. Le registre SQLite est un index administratif et technique.

## PNG baked, QR et vérification

Le baking injecte l'assertion JSON dans un chunk PNG `tEXt` dont le mot-clé est `openbadges`. Le QR visible est ajouté séparément à l'image et pointe vers :

```text
<BADGE83_BASE_URL>/verify/qr/<assertion_id>
```

La vérification d'un PNG baked extrait le chunk `openbadges`. La vérification publique par QR s'appuie sur le registre local, la révocation et la preuve locale si disponibles.

## Preuves, révocation et blockchain

Chaque badge émis peut disposer d'une preuve locale :

```text
Assertion Open Badges -> payload canonique -> SHA-256 -> credential_proofs
```

États publics possibles : `matches`, `mismatch`, `missing`, `unavailable`.

L'ancrage blockchain est optionnel :

```text
BADGE83_ANCHORING_PROVIDER=mock|evm
```

Pour EVM :

```bash
pip install -r requirements-blockchain.txt
```

Puis configurer localement, sans committer de secrets :

```text
BADGE83_EVM_RPC_URL=
BADGE83_EVM_CHAIN_ID=
BADGE83_EVM_CONTRACT_ADDRESS=
BADGE83_EVM_CONTRACT_VERSION=registry
BADGE83_BLOCKCHAIN_VERIFY_BASE_URL=https://verify.mode83.org
BADGE83_EVM_PRIVATE_KEY=
BADGE83_EVM_NETWORK_LABEL=hardhat-local
BADGE83_EVM_EXPLORER_TX_URL_TEMPLATE=
BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS=120
```

Contrats :

```bash
cd badge83/blockchain
npm install
npm test
npm run deploy:registry:local
npm run deploy:registry:sepolia
```

## Tests

Depuis la racine de l'espace de travail :

```bash
.venv/bin/python -m pytest badge83/tests -q
```

Depuis `badge83/` avec le virtualenv activé :

```bash
pytest tests -q
```

Tests blockchain :

```bash
cd badge83/blockchain
npm test
```

## Attribution

Badge83 est un projet développé pour MODE83.

Conception fonctionnelle, développement logiciel, documentation technique et intégration : © 2026 Nikolay Semin. Tous droits réservés.

La réutilisation du code, de la documentation ou des éléments de conception doit conserver cette mention d'attribution, sauf autorisation écrite préalable.
