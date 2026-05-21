# Badge83 — Projet Open Badges

## Description

Ce projet est une implémentation légère d'Open Badges 2.0 avec FastAPI.
Il permet d'émettre et de vérifier des assertions conformes au modèle Open Badges en s'appuyant sur les objets principaux du standard : `Issuer`, `BadgeClass` et `Assertion`.

## Fonctionnalités

- Émettre une assertion Open Badge (`POST /issue`) à partir de `name` et `email`.
- Émettre un badge **baked** dans un PNG (`POST /issue-baked`) — l'assertion JSON est injectée dans l'image via un chunk `tEXt` conforme au standard Open Badges.
- Créer des modèles de badges via un **constructeur opérateur** : schémas de champs, textes dynamiques, QR configurable, preview de brouillon et duplication de modèles.
- Émettre un PNG baked depuis un modèle préparé (`POST /badge-constructor/templates/{template_id}/issue-baked`) avec valeurs dynamiques conservées dans l'assertion.
- Émettre des badges en groupe depuis un fichier CSV ou Excel `.xlsx` : preview obligatoire, émission partielle contrôlée, archive ZIP, rapport CSV et historisation SQLite des sessions.
- Ajouter automatiquement un **QR code visible** sur les badges PNG baked, pointant vers la page publique de vérification humaine.
- Enrichir les assertions avec des métadonnées minimales de conformité : `@language`, `expires` et `evidence`.
- Exposer un profil `Issuer` enrichi avec un bloc `verification` (`allowedOrigins`, `startsWith`).
- Exposer un `BadgeClass` enrichi avec `tags` et `alignment`.
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
    ├── badge83.env.exemple
    └── README.md
```

## Prérequis

- `python3`
- accès à `pip` / création de virtualenv (`python3 -m venv`)

## Environnement de travail standardisé

Le projet **Badge83** doit être utilisé via un environnement virtuel local `.venv` situé à la racine de l'espace de travail :

```text
/home/ubuntu/projects/Mode83/.venv
```

Ce virtualenv n'est pas réservé aux tests : il sert aussi au **lancement normal du projet**, à l'installation des dépendances, à l'exécution des scripts et au démarrage du serveur.

## Installation et lancement

Depuis `/home/ubuntu/projects/Mode83` :

```bash
python3 -m venv .venv
.venv/bin/pip install -r badge83/requirements.txt
```

Si vous préférez activer l'environnement :

```bash
source /home/ubuntu/projects/Mode83/.venv/bin/activate
pip install -r /home/ubuntu/projects/Mode83/badge83/requirements.txt
```

Toutes les commandes ci-dessous peuvent alors être lancées soit avec l'environnement activé, soit en appelant explicitement `.venv/bin/python`.

### Lancement avec Docker

Le lancement historique par virtualenv et `badge83.sh` reste supporté. Docker est une couche d'exploitation optionnelle pour faciliter les tests, démonstrations et déploiements.

Depuis `/home/ubuntu/projects/Mode83/badge83` :

```bash
cp .env.docker.example .env
docker compose up -d --build
```

Si la machine dispose de l'ancien binaire Compose v1 au lieu du plugin Compose v2, utilisez la forme équivalente :

```bash
docker-compose up -d --build
```

L'application est ensuite disponible sur :

```text
http://localhost:8000
```

Les données générées par le conteneur sont conservées dans :

```text
badge83/runtime-data/
```

Ce dossier est monté dans le conteneur en `/app/data` et contient notamment les assertions JSON, les PNG baked et `registry.db`.

Commandes utiles :

```bash
docker compose ps
docker compose logs -f badge83
docker compose down
```

Avec Compose v1 :

```bash
docker-compose ps
docker-compose logs -f badge83
docker-compose down
```

Vérifications rapides :

```bash
curl http://localhost:8000/issuers/main
curl http://localhost:8000/badges/blockchain-foundations
```

Pour une installation production sur une autre machine, le modèle recommandé est :

```text
Internet -> Nginx HTTPS -> Badge83 FastAPI -> runtime-data
```

Un assistant interactif permet de générer le fichier `.env`, les secrets et de préparer le certificat :

```bash
./docker/setup.sh
docker-compose -f docker-compose.prod.yml up -d --build
```

Le reverse proxy Nginx applique `auth_request` sur les routes opérateur et laisse publics les endpoints nécessaires à la vérification Open Badges.

Installation manuelle équivalente :

```bash
cp .env.production.example .env
# éditer .env : domaine, BADGE83_BASE_URL et secrets forts
# placer les certificats dans docker/nginx/certs/fullchain.pem et privkey.pem
docker-compose -f docker-compose.prod.yml up -d --build
```

Plan détaillé et rollback : [`docs/docker-implementation-and-rollback-210526.md`](docs/docker-implementation-and-rollback-210526.md).

### Configuration de l'URL publique

Les badges émis contiennent des URLs publiques pointant vers le serveur. Définissez la variable d'environnement `BADGE83_BASE_URL` :

```bash
# Copier l'exemple et configurer l'URL du serveur
cp badge83.env.exemple badge83.env
# Éditer badge83.env et mettre l'IP ou le domaine de votre serveur
```

### Démarrage du serveur

```bash
export BADGE83_BASE_URL=http://mode83.ddns.net  # ou votre URL publique
/home/ubuntu/projects/Mode83/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Script de gestion du serveur

Pour éviter d’oublier l’environnement, l’adresse et le port, utilisez le script fourni :

```bash
chmod +x badge83.sh
./badge83.sh start
./badge83.sh status
./badge83.sh logs
./badge83.sh stop
```

Le script charge automatiquement, si présent, le fichier de configuration :

```text
badge83/badge83.env
```

Exemple de paramètres actuellement utilisés :

```text
BADGE83_HOST=0.0.0.0
BADGE83_PORT=8000
BADGE83_PUBLIC_SCHEME=http
BADGE83_PUBLIC_HOST=mode83.ddns.net
BADGE83_PUBLIC_PORT=8000
BADGE83_REGISTRY_DB=/home/ubuntu/projects/Mode83/badge83/data/registry.db
```

Cela permet de corriger les QR codes pour l’environnement actuel (`:8000`) tout en gardant une configuration portable pour la production.

Par défaut, le script :

- utilise le virtualenv standardisé de l'espace de travail (`/home/ubuntu/projects/Mode83/.venv`) ;
- démarre `uvicorn` sur `0.0.0.0:8000` ;
- injecte `BADGE83_BASE_URL` avec une valeur par défaut configurable ;
- écrit le PID dans `server.pid` ;
- écrit les logs dans `server.log`.

Vous pouvez aussi définir un pepper de recherche stable pour les hash de recherche admin (`name` / `email`) :

```bash
export BADGE83_SEARCH_PEPPER="change-me-in-production"
./badge83.sh restart
```

Ce pepper est utilisé pour calculer des hash de recherche stables côté serveur, sans exposer les valeurs en clair dans l’interface admin.

### Sécurité et configuration production

Badge83 distingue l'environnement de développement et l'environnement production via :

```bash
export BADGE83_ENV=production
```

ou :

```bash
export BADGE83_ENV=prod
```

En mode production, l'application refuse de démarrer avec les valeurs faibles de développement pour :

- `BADGE83_AUTH_PASSWORD` ;
- `BADGE83_AUTH_SECRET` ;
- `BADGE83_SEARCH_PEPPER`.

Les uploads opérateur sont également bornés par des variables configurables :

```bash
export BADGE83_MAX_PNG_UPLOAD_BYTES=52428800
export BADGE83_MAX_CSV_UPLOAD_BYTES=10485760
export BADGE83_MAX_IMAGE_PIXELS=50000000
```

Valeurs par défaut : PNG 50 MB, CSV/XLSX 10 MB et images 50 mégapixels.

### Registre SQLite local

Le projet maintient désormais un registre SQLite local des assertions dans :

```text
badge83/data/registry.db
```

Ce registre est utilisé comme **index local** pour l’administration et la recherche, tandis que les fichiers JSON dans `badge83/data/issued/` restent la source canonique des assertions Open Badges.

Le comportement actuel est le suivant :

- au démarrage du serveur, les JSON existants de `data/issued/` sont importés/synchronisés dans SQLite ;
- lors d’une émission de badge (`/issue` ou `/issue-baked`), l’assertion est enregistrée en JSON puis synchronisée dans SQLite ;
- lors d’une modification/suppression via l’API admin, le registre SQLite est mis à jour aussi.

Vous pouvez surcharger le chemin de la base avec :

```bash
export BADGE83_REGISTRY_DB=/chemin/vers/registry.db
```

Vous pouvez surcharger l’hôte, le port et l’URL publique :

```bash
BADGE83_HOST=0.0.0.0 \
BADGE83_PORT=8010 \
BADGE83_BASE_URL=http://mode83.ddns.net:8010 \
./badge83.sh restart
```

Si le port `8000` est déjà utilisé, choisissez un autre port :

```bash
/home/ubuntu/projects/Mode83/.venv/bin/python -m uvicorn app.main:app --host 127.0.0.1 --port 8010 --reload
```

## Métadonnées Open Badges ajoutées

Les émissions générées par Badge83 incluent désormais un socle minimal de métadonnées supplémentaires pour améliorer l'interopérabilité et préparer les validations externes.

### Assertion

Les assertions générées via `/issue` et `/issue-baked` contiennent maintenant :

- `@language: "fr-FR"`
- `expires` : date d'expiration calculée par défaut à `issuedOn + 365 jours`
- `evidence` : tableau minimal contenant une preuve narrative locale
- `verification` : bloc HostedBadge pointant vers l'URL publique de l'assertion

Exemple simplifié :

```json
{
  "@context": "https://w3id.org/openbadges/v2",
  "@language": "fr-FR",
  "type": "Assertion",
  "issuedOn": "2026-04-24T12:00:00+00:00",
  "expires": "2027-04-24T12:00:00+00:00",
  "evidence": [
    {
      "type": "Evidence",
      "narrative": "Validation pédagogique du parcours MODE83 pour Alice Example."
    }
  ]
}
```

### Issuer

Le template `issuer_template.json` expose désormais :

- `@language: "fr-FR"`
- `verification.allowedOrigins`
- `verification.startsWith`

### BadgeClass

Le template `badgeclass_template.json` expose désormais :

- `@language: "fr-FR"`
- `tags`
- `alignment`

Ces ajouts restent volontairement minimaux afin de ne pas modifier le flux applicatif existant ni le baking PNG.

## Exécution des tests

Depuis la racine de l'espace de travail :

```bash
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest /home/ubuntu/projects/Mode83/badge83/tests -q
```

La suite couvre notamment le noyau d'émission/baking, la base SQLite locale et le constructeur de badges. Les tests du constructeur vérifient la création, la modification et l'émission depuis un modèle modifié.

Pour lancer uniquement les tests API du constructeur :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests/unit/test_badge_constructor_api.py -q
```

Documentation détaillée : [`docs/tests-constructeur-badge-040526.md`](docs/tests-constructeur-badge-040526.md).

Documents de validation Projet A :

- [`docs/rapport-travail-110526-stabilisation.md`](docs/rapport-travail-110526-stabilisation.md) — correction de l'erreur SQLite/threading ;
- [`docs/test-report-projet-a-120526.md`](docs/test-report-projet-a-120526.md) — validation fonctionnelle de bout en bout ;
- [`docs/guide-formateur-mode83.md`](docs/guide-formateur-mode83.md) — guide utilisateur pour formateur/opérateur ;
- [`docs/rapport-validation-projet-a-150526.md`](docs/rapport-validation-projet-a-150526.md) — synthèse de validation Projet A ;
- [`docs/audit-architecture-security-120526.md`](docs/audit-architecture-security-120526.md) — audit architecture, sécurité et exploitation.

Test spécifique de la couche base de données :

```bash
/home/ubuntu/projects/Mode83/.venv/bin/python /home/ubuntu/projects/Mode83/badge83/app/test_database.py
```

Ou, si le virtualenv est activé :

```bash
cd /home/ubuntu/projects/Mode83/badge83
pytest tests -q
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

### Constructeur de badges

Une vue `Constructeur de badge` permet de préparer des modèles réutilisables avant l'émission.

Le workflow actuel est le suivant :

1. créer un schéma de programme avec des champs opérateur ;
2. créer un modèle visuel associé ;
3. ajouter un ou plusieurs textes superposés ;
4. choisir pour chaque texte une source : texte fixe, nom du participant, email, cours, numéro, date ;
5. choisir une position rapide ou des coordonnées X/Y ;
6. prévisualiser le brouillon avant sauvegarde ;
7. enregistrer le modèle ;
8. utiliser ce modèle dans l'écran existant `Émission de badge`.

Lorsqu'un modèle est sélectionné dans l'écran d'émission, le mode passe en `PNG baked`, les champs du schéma sont affichés et les valeurs saisies sont utilisées pour générer le PNG final.

Endpoints principaux :

| Endpoint | Description |
|----------|-------------|
| `GET /badge-constructor/schemas` | Liste des schémas actifs |
| `POST /badge-constructor/schemas` | Création d'un schéma |
| `GET /badge-constructor/templates` | Liste des modèles actifs |
| `POST /badge-constructor/templates` | Création d'un modèle |
| `POST /badge-constructor/templates/preview-draft` | Aperçu PNG d'un brouillon non sauvegardé |
| `GET /badge-constructor/templates/{id}/preview` | Aperçu PNG d'un modèle sauvegardé |
| `PUT /badge-constructor/templates/{id}` | Modification d'un modèle existant |
| `POST /badge-constructor/templates/{id}/duplicate` | Duplication d'un modèle |
| `POST /badge-constructor/templates/{id}/issue-baked` | Émission d'un PNG baked à partir d'un modèle |

Les assertions émises depuis un modèle conservent les informations suivantes :

```json
{
  "badge83_template": {
    "id": "...",
    "name": "...",
    "schema_id": "..."
  },
  "field_values": {
    "course_name": "...",
    "certificate_number": "...",
    "issue_date": "..."
  }
}
```

Le constructeur permet aussi de modifier un modèle existant depuis l'interface : bouton `Modifier` dans la liste des modèles, édition du nom, du schéma, des paramètres QR et des textes superposés, puis sauvegarde via `PUT /badge-constructor/templates/{id}`. Chaque texte superposé peut également être modifié individuellement depuis la liste des textes du modèle.

Guide utilisateur détaillé : [`docs/guide-edition-modele-constructeur.md`](docs/guide-edition-modele-constructeur.md).

### Émission groupée CSV/XLSX

L'écran d'émission groupée permet à un opérateur d'émettre plusieurs badges depuis un fichier CSV ou Excel `.xlsx`, en réutilisant les modèles du constructeur.

Parcours recommandé :

1. sélectionner un modèle de badge existant ;
2. télécharger le modèle Excel adapté au schéma sélectionné ;
3. compléter les colonnes opérateur (`nom`, `email`, `reussi` et champs du schéma) ;
4. charger le fichier dans Badge83 ;
5. vérifier la prévisualisation ;
6. confirmer l'émission ;
7. télécharger l'archive ZIP contenant les PNG baked et le rapport d'émission.

La politique retenue est une **émission partielle contrôlée** : Badge83 analyse toutes les lignes, mais n'émet que les lignes prêtes. Les lignes non admises, en doublon ou en erreur sont conservées dans le rapport.

Statuts utilisés :

| Statut | Signification |
|--------|---------------|
| `ready` | ligne valide, émissible |
| `not_passed` | participant non admis |
| `duplicate` | badge déjà émis pour ce modèle et cet email |
| `error` | donnée manquante ou invalide |

Formats acceptés :

- `.csv` avec détection automatique des séparateurs courants ;
- `.xlsx` via `openpyxl` ;
- `.xls` n'est pas supporté.

Endpoints principaux :

| Endpoint | Description |
|----------|-------------|
| `GET /badge-constructor/batch-issue/template.xlsx` | Modèle Excel générique |
| `GET /badge-constructor/templates/{id}/batch-issue/template.xlsx` | Modèle Excel adapté au schéma sélectionné |
| `POST /badge-constructor/templates/{id}/batch-issue/preview` | Prévisualisation sans émission |
| `POST /badge-constructor/templates/{id}/batch-issue` | Émission groupée avec rapport JSON |
| `POST /badge-constructor/templates/{id}/batch-issue/archive` | Émission groupée avec archive ZIP |
| `GET /badge-constructor/batch-sessions` | Liste des sessions d'import |
| `GET /badge-constructor/batch-sessions/{session_id}` | Détail d'une session d'import |

L'archive ZIP contient notamment :

```text
source.csv ou source.xlsx
rapport_emission.csv
manifest.json
badges/*.png
```

Guide détaillé : [`docs/guide-emission-groupee-csv.md`](docs/guide-emission-groupee-csv.md).

### Bureau de vérification

Une page simplifiée dédiée à un usage administratif est disponible ici :

- `GET /verify-desk`

Cette page permet :

- de charger un badge PNG ;
- de lancer une vérification rapide ;
- d’afficher l’aperçu du badge ;
- de voir le nom, l’email, la date de délivrance et le statut de l’issuer ;
- de retrouver d’autres certificats liés si des hash de recherche sont disponibles.

Le comportement d’affichage de l’émetteur est volontairement simplifié :

- `mode83` si le badge appartient à l’organisation MODE83 ;
- `autre organisme` sinon.

### Nom des fichiers PNG baked

Les badges émis en PNG baked sont maintenant téléchargés avec un nom lisible de type :

```text
<numéro>_mode83_<jjmmaaa>.png
```

Exemple :

```text
37_mode83_200426.png
```

Réponse attendue pour un badge inexistant :

```json
{"valid": false, "badge": null}
```

### QR code sur les badges PNG

Les badges émis via `POST /issue-baked` embarquent maintenant un **QR code visible** dans l'image.

Le QR code :

- est ajouté visuellement sur le badge avant le baking Open Badges ;
- pointe vers une **page mobile de vérification** de type :

```text
<BADGE83_BASE_URL>/verify/qr/<assertion_id>
```

- permet un scan rapide depuis un smartphone ;
- affiche un statut de vérification très visuel avec codes couleur ;
- ne remplace pas l'assertion Open Badges, qui reste injectée séparément dans les métadonnées PNG.

Cette séparation garantit que :

- le QR sert de point d'entrée utilisateur vers une page mobile minimale ;
- le chunk `openbadges` continue d'assurer la compatibilité avec le flux baked / unbake standardisé.

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

Le projet implémente le modèle **HostedBadge** d'Open Badges 2.0 :

- `issuer_template.json` : profil public de l'émetteur MODE83 (avec `${BASE_URL}` dynamique)
- `badgeclass_template.json` : définition publique du badge MODE83 (avec `${BASE_URL}` dynamique)
- `Assertion` : badge individuel remis à un apprenant, stocké dans `data/issued/`

Lors de l'émission, Badge83 génère une assertion avec :
- `@context: https://w3id.org/openbadges/v2`
- `id` et `url` sous forme d'URL HTTP publique (`${BASE_URL}/assertions/<uuid>`)
- `verification.type: HostedBadge`
- `verification.url` pointant vers l'URL publique de l'assertion
- `badge` sous forme d'URL vers le `BadgeClass`
- `issuer` sous forme d'URL vers le profil `Issuer`
- `recipient.identity` haché au format `sha256$...`

Cette structure correspond au format effectivement produit par `app/issuer.py` et consommé par les validateurs Open Badges 2.0.

## Remarques

- Les assertions JSON stockées dans `data/issued/` restent la source canonique des badges. Le registre SQLite local sert d'index administratif pour la recherche, la consultation et la cohérence opérateur.
- **Badge Baking** : l'assertion JSON est injectée dans le PNG via un chunk `tEXt` avec le mot-clé `openbadges`, conformément au standard Open Badges 2.0. Le PNG reste visuellement identique à l'original.
- Le chunk `openbadges` est unique : re-baker le même PNG ne duplique pas les données.
- La vérification d'un badge baked se fait en extrayant le chunk `openbadges` du PNG ; aucune connexion réseau n'est requise.
- **HostedBadge** : les assertions contiennent des URLs HTTP publiques (au lieu d'objets imbriqués) permettant la validation externe par des tiers comme `validator.openbadges.org`.
- Le fichier `app/models.py` contient encore des modèles historiques plus anciens ; la structure réellement émise en production est celle implémentée dans `app/issuer.py`.
- Avant toute exposition production publique, appliquer les recommandations de sécurité documentées dans `docs/audit-architecture-security-120526.md`.
- Les routes administrateur sont protégées côté FastAPI ; les routes publiques de vérification et HostedBadge restent accessibles sans authentification.

## Journal des modifications

Voir [`docs/CHANGELOG-130426.md`](docs/CHANGELOG-130426.md) pour les modifications du 13/04/26.

## Roadmap

| Étape | Statut | Description |
|-------|--------|-------------|
| Émission d'assertions JSON | Implémenté | `POST /issue` |
| Badge Baking PNG | Implémenté | `POST /issue-baked` avec chunk `tEXt openbadges` |
| Vérification par ID | Implémenté | `GET /verify/{id}` |
| Vérification PNG baked | Implémenté | `POST /verify-baked` |
| Interface web | Implémenté | Page unique avec formulaires d'émission et vérification |
| Endpoints hébergés (HostedBadge) | Implémenté | URLs publiques pour Issuer, BadgeClass et Assertions |
| Signature JWS (SignedBadge) | 🔲 Planifié | Chiffrer les assertions avec une clé privée, vérification par clé publique |
| Ancrage blockchain | 🔲 Planifié | Enregistrer les empreintes d'assertions sur une blockchain pour preuve d'immutabilité |
| Base de données locale | Implémenté | Registre SQLite local pour index administratif, recherche et cohérence JSON/PNG |
| Validation avec `openbadges-validator-core` | Validé | Test de conformité réussi sur un badge MODE83 hébergé |
| Validation IMS officielle | 🔲 À poursuivre | Vérifications complémentaires sur l'infrastructure publique / HTTPS |
| Émission groupée CSV/XLSX | Implémenté | Preview, commit, archive ZIP, rapport et historisation SQLite |
