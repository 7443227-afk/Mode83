# Plan de conteneurisation Docker pour Badge83

## Objectif

L'objectif est de rendre Badge83 facilement installable sur une autre machine, avec une procédure courte de type :

```bash
git clone <depot>
cd Mode83/badge83
cp .env.docker.example .env
docker compose up -d --build
```

Le résultat attendu est une instance Badge83 immédiatement utilisable, sans création manuelle de virtualenv Python, sans installation locale des dépendances Python et avec une conservation fiable des données émises.

Le déploiement Docker doit permettre deux usages :

1. un mode local simple pour test ou démonstration ;
2. un mode production avec reverse proxy HTTP/HTTPS.

## Principes retenus

La conteneurisation doit rester simple et cohérente avec l'architecture actuelle du projet.

Badge83 est aujourd'hui une application FastAPI avec :

```text
badge83/app/          # code applicatif FastAPI
badge83/templates/    # templates HTML
badge83/data/         # templates JSON, assets, assertions, PNG baked, registre SQLite
badge83/requirements.txt
```

Le conteneur Docker doit embarquer :

- le code applicatif ;
- les templates HTML ;
- les assets de base ;
- les templates Open Badges ;
- les dépendances Python.

Les données produites par l'application doivent être persistantes :

- assertions JSON dans `data/issued/` ;
- badges PNG baked dans `data/baked/` ;
- base SQLite `data/registry.db`.

Ces données ne doivent pas disparaître lors d'une reconstruction d'image Docker.

## Séparation entre image et données persistantes

### Dans l'image Docker

L'image doit contenir les éléments nécessaires au démarrage initial :

```text
/app/app/
/app/templates/
/app/seed-data/issuer_template.json
/app/seed-data/badgeclass_template.json
/app/seed-data/badge.png
/app/seed-data/mode83-badge.png
/app/requirements.txt
```

### Dans un volume Docker

Les données vivantes doivent être stockées dans un volume :

```text
/app/data/issued/
/app/data/baked/
/app/data/registry.db
```

Le volume peut aussi contenir une copie des fichiers de base nécessaires :

```text
/app/data/issuer_template.json
/app/data/badgeclass_template.json
/app/data/badge.png
/app/data/mode83-badge.png
```

Pour cela, un script d'entrée (`entrypoint.sh`) doit copier les fichiers de démarrage depuis `/app/seed-data` vers `/app/data` lors du premier lancement, uniquement s'ils n'existent pas déjà.

Cette stratégie permet :

- de démarrer un conteneur neuf sans intervention manuelle ;
- de conserver les données entre deux mises à jour ;
- de modifier les templates dans le volume si nécessaire ;
- de migrer une instance vers une autre machine en copiant le volume.

## Fichiers à ajouter

Structure proposée :

```text
badge83/
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── docker-compose.prod.yml            # étape ultérieure
├── .env.docker.example
├── .env.production.example            # étape ultérieure
└── docker/
    ├── entrypoint.sh
    ├── Caddyfile                      # option production simple
    └── nginx/
        └── default.conf.template       # option production Nginx
```

Pour une première étape fonctionnelle, seuls les fichiers suivants sont indispensables :

```text
badge83/Dockerfile
badge83/.dockerignore
badge83/docker-compose.yml
badge83/.env.docker.example
badge83/docker/entrypoint.sh
```

## Dockerfile proposé

Le `Dockerfile` doit construire une image Python légère.

Exemple de structure :

```dockerfile
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends curl \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY templates /app/templates
COPY data /app/seed-data
COPY docker/entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh \
    && mkdir -p /app/data/issued /app/data/baked

EXPOSE 8000

ENTRYPOINT ["/entrypoint.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

Le choix de `WORKDIR /app` est important, car le code actuel calcule les chemins de données relativement au dossier parent de `app/`.

Avec cette disposition :

```text
/app/app/config.py
/app/data/
/app/templates/
```

les chemins attendus par Badge83 restent cohérents.

## Script `entrypoint.sh`

Le script d'entrée doit préparer l'environnement à chaque démarrage.

Rôles :

- créer les répertoires de données ;
- copier les fichiers de base si le volume est vide ;
- définir les valeurs par défaut utiles ;
- lancer la commande finale.

Exemple :

```bash
#!/usr/bin/env sh
set -eu

mkdir -p /app/data/issued /app/data/baked

for file in issuer_template.json badgeclass_template.json badge.png mode83-badge.png; do
  if [ ! -e "/app/data/$file" ] && [ -e "/app/seed-data/$file" ]; then
    cp "/app/seed-data/$file" "/app/data/$file"
  fi
done

export BADGE83_HOST="${BADGE83_HOST:-0.0.0.0}"
export BADGE83_PORT="${BADGE83_PORT:-8000}"
export BADGE83_REGISTRY_DB="${BADGE83_REGISTRY_DB:-/app/data/registry.db}"

exec "$@"
```

## `.dockerignore` proposé

Le fichier `.dockerignore` doit éviter d'intégrer dans l'image :

- secrets ;
- logs ;
- environnements virtuels ;
- caches ;
- données émises en production.

Exemple :

```dockerignore
.git
.pytest_cache
__pycache__
*.pyc
*.log
server.pid
server.log
badge83.env
.env
.venv

data/issued/*
data/baked/*
data/registry.db
```

Il ne faut pas exclure tout le dossier `data/`, car il contient les templates et images nécessaires au démarrage.

## Mode local simple avec Docker Compose

Le premier objectif est de pouvoir démarrer Badge83 localement avec un seul service.

Exemple de `docker-compose.yml` :

```yaml
services:
  badge83:
    build:
      context: .
      dockerfile: Dockerfile
    image: badge83:latest
    container_name: badge83
    restart: unless-stopped
    ports:
      - "8000:8000"
    env_file:
      - .env
    volumes:
      - badge83-data:/app/data

volumes:
  badge83-data:
```

Avec ce mode, l'application est disponible à l'adresse :

```text
http://localhost:8000
```

## Exemple de `.env.docker.example`

Fichier proposé :

```env
BADGE83_HOST=0.0.0.0
BADGE83_PORT=8000

# URL publique intégrée dans les badges émis.
# Pour un test local : http://localhost:8000
BADGE83_BASE_URL=http://localhost:8000

# Registre SQLite dans le volume Docker.
BADGE83_REGISTRY_DB=/app/data/registry.db

# Secrets à changer avant toute utilisation réelle.
BADGE83_SEARCH_PEPPER=change-me-search-pepper
BADGE83_AUTH_USERNAME=admin83
BADGE83_AUTH_PASSWORD=change-me-password
BADGE83_AUTH_SECRET=change-me-auth-secret
```

Sur une autre machine, l'utilisateur devra faire :

```bash
cp .env.docker.example .env
nano .env
docker compose up -d --build
```

## Mode production

Pour une installation publique, Badge83 doit être placé derrière un reverse proxy HTTP/HTTPS.

Deux stratégies sont possibles.

### Option A — reverse proxy externe à Docker

Le serveur hôte possède déjà Nginx, Caddy ou Traefik.

Dans ce cas, Docker expose Badge83 uniquement sur un port local, par exemple :

```yaml
ports:
  - "127.0.0.1:8000:8000"
```

Le reverse proxy de la machine hôte gère :

- HTTPS ;
- certificats ;
- redirection HTTP vers HTTPS ;
- protection des routes sensibles ;
- accès public aux endpoints Open Badges.

Avantages :

- plus simple si la machine possède déjà une configuration Nginx ;
- meilleure séparation entre application et exposition publique ;
- gestion des certificats déjà maîtrisée.

### Option B — reverse proxy dans Docker Compose

Le fichier `docker-compose.prod.yml` lance à la fois :

```text
caddy ou nginx -> badge83
```

Cette solution est plus portable : une nouvelle machine peut démarrer toute la stack avec une seule commande.

## Production avec Caddy

Caddy est intéressant car il peut gérer automatiquement les certificats Let's Encrypt.

Exemple de `docker-compose.prod.yml` :

```yaml
services:
  badge83:
    build:
      context: .
      dockerfile: Dockerfile
    restart: unless-stopped
    expose:
      - "8000"
    env_file:
      - .env
    volumes:
      - badge83-data:/app/data

  caddy:
    image: caddy:2.8-alpine
    restart: unless-stopped
    depends_on:
      - badge83
    ports:
      - "80:80"
      - "443:443"
    environment:
      BADGE83_DOMAIN: ${BADGE83_DOMAIN}
    volumes:
      - ./docker/Caddyfile:/etc/caddy/Caddyfile:ro
      - caddy-data:/data
      - caddy-config:/config

volumes:
  badge83-data:
  caddy-data:
  caddy-config:
```

Exemple de `docker/Caddyfile` :

```caddyfile
{$BADGE83_DOMAIN} {
    encode gzip
    reverse_proxy badge83:8000
}
```

Cette option est très simple, mais elle ne reproduit pas automatiquement la politique actuelle `auth_request` de Nginx. Si cette politique doit être conservée telle quelle, il faut préférer Nginx.

## Production avec Nginx

Nginx permet de reprendre plus fidèlement la configuration actuelle :

- protection de l'administration ;
- `auth_request` vers `/auth/check` ;
- redirection vers `/auth/login` ;
- endpoints Open Badges publics.

Routes à laisser publiques :

```text
/auth/login
/verify/qr/
/assertions/
/issuers/
/badges/
/assets/
```

Routes à protéger :

```text
/
/api/
/verify/badge/
/verify-desk
/issue
/issue-baked
/verify-baked
```

Extrait de logique Nginx attendue :

```nginx
auth_request /auth/check;
error_page 401 = /auth/login?next=$request_uri;
```

Les endpoints publics Open Badges ne doivent pas être protégés, car les validateurs externes doivent pouvoir résoudre :

```text
Assertion -> BadgeClass -> Issuer -> assets
```

## Migration des données vers une autre machine

Deux cas sont possibles.

### Cas 1 — nouvelle installation vide

La nouvelle machine démarre avec les templates et images de base.

Commande :

```bash
git clone <depot>
cd Mode83/badge83
cp .env.docker.example .env
docker compose up -d --build
```

Les dossiers `issued/`, `baked/` et la base SQLite seront créés automatiquement.

### Cas 2 — migration d'une instance existante

Il faut transférer :

```text
badge83/data/issued/
badge83/data/baked/
badge83/data/registry.db
```

Si un volume Docker nommé est utilisé, il faut soit :

- restaurer ces fichiers dans le volume ;
- utiliser un bind mount vers un dossier hôte ;
- exporter/importer le volume Docker.

Exemple avec bind mount :

```yaml
volumes:
  - ./runtime-data:/app/data
```

Dans ce cas, le dossier suivant peut être sauvegardé directement :

```text
badge83/runtime-data/
```

## Commandes de vérification après démarrage

Après lancement local :

```bash
curl http://localhost:8000/issuers/main
curl http://localhost:8000/badges/blockchain-foundations
curl http://localhost:8000/assets/mode83-badge.png --output /tmp/mode83-badge.png
```

Pour tester l'interface :

```text
http://localhost:8000
```

Pour tester l'émission d'un badge baked :

```bash
curl -X POST \
  -F "name=Alice Example" \
  -F "email=alice@example.org" \
  http://localhost:8000/issue-baked \
  --output badge.png
```

Pour tester la vérification :

```bash
curl -X POST \
  -F "badge=@badge.png" \
  "http://localhost:8000/verify-baked?deep=true"
```

## Points de vigilance

### URL publique

La variable la plus importante est :

```text
BADGE83_BASE_URL
```

Elle est intégrée dans les badges émis. Si elle est incorrecte, les assertions, QR codes et validateurs externes pointeront vers une mauvaise adresse.

Exemples :

```env
BADGE83_BASE_URL=http://localhost:8000
BADGE83_BASE_URL=https://mode83.example.com
```

### Secrets

Les valeurs suivantes doivent être changées en production :

```text
BADGE83_SEARCH_PEPPER
BADGE83_AUTH_PASSWORD
BADGE83_AUTH_SECRET
```

### Données Open Badges publiques

Même en production protégée, les endpoints suivants doivent rester accessibles sans authentification :

```text
/assertions/
/issuers/
/badges/
/assets/
```

Sinon, les validateurs externes ne pourront pas vérifier les badges HostedBadge.

### Registre SQLite

Le registre SQLite est un index local. Les fichiers JSON dans `data/issued/` restent la source canonique des assertions.

Au démarrage, Badge83 synchronise les assertions existantes dans le registre.

## Ordre de mise en œuvre recommandé

### Étape 1 — Docker local minimal

Créer :

```text
Dockerfile
.dockerignore
docker/entrypoint.sh
docker-compose.yml
.env.docker.example
```

Objectif : lancer Badge83 localement via :

```bash
docker compose up -d --build
```

### Étape 2 — documentation d'utilisation

Mettre à jour :

```text
README.md
docs/docker-deployment.md
```

avec :

- installation locale ;
- variables d'environnement ;
- volumes ;
- sauvegarde/restauration.

### Étape 3 — tests de fonctionnement

Vérifier :

- démarrage du conteneur ;
- accès à `/` ;
- accès aux endpoints Open Badges ;
- émission d'un badge ;
- vérification d'un PNG baked ;
- persistance après redémarrage du conteneur.

### Étape 4 — production avec reverse proxy

Ajouter ensuite :

```text
docker-compose.prod.yml
docker/Caddyfile
```

ou :

```text
docker/nginx/default.conf.template
```

selon le choix retenu.

### Étape 5 — migration d'une instance existante

Documenter la procédure pour transférer :

```text
data/issued/
data/baked/
data/registry.db
```

vers le volume Docker.

## Résultat attendu

À terme, une installation complète de Badge83 sur une nouvelle machine devrait se résumer à :

```bash
git clone <depot>
cd Mode83/badge83
cp .env.docker.example .env
nano .env
docker compose up -d --build
```

Pour une installation publique :

```bash
cp .env.production.example .env
nano .env
docker compose -f docker-compose.prod.yml up -d --build
```

Cette approche rend Badge83 plus portable, plus facile à tester et plus simple à déployer sur une autre machine.
