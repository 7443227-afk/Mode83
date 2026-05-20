# Plan de réalisation Docker pour Badge83 — 20/05/2026

## Objectif

Ce document précise le plan de réalisation Docker pour Badge83 avant implémentation.

L'objectif est de préparer Badge83 à un usage plus simple sur une autre machine ou en production, sans devoir recréer manuellement un environnement virtuel Python ni installer les dépendances une par une sur le serveur cible.

Le résultat attendu est une procédure de démarrage courte :

```bash
cd badge83
cp .env.docker.example .env
docker compose up -d --build
```

Pour un serveur public, l'objectif est également de préparer une variante avec HTTPS :

```bash
cd badge83
cp .env.production.example .env
docker compose -f docker-compose.prod.yml up -d --build
```

## Principe général

Badge83 reste une application FastAPI. La conteneurisation ne doit pas modifier la logique métier existante : émission de badges, vérification, baking PNG, constructeur de badges et émission groupée restent dans `app/`.

La réalisation Docker ajoute uniquement une couche d'exploitation autour de l'application.

Architecture cible :

```text
Internet
  ↓
Reverse proxy HTTPS : Caddy ou Nginx
  ↓
Conteneur Docker Badge83 : FastAPI / Uvicorn
  ↓
Données persistantes : runtime-data ou volume Docker
```

## Fichiers à ajouter lors de l'implémentation

La première réalisation Docker doit ajouter les fichiers suivants :

```text
badge83/
├── Dockerfile
├── .dockerignore
├── docker-compose.yml
├── docker-compose.prod.yml
├── .env.docker.example
├── .env.production.example
└── docker/
    ├── entrypoint.sh
    └── Caddyfile
```

Le fichier `docker-compose.yml` servira au lancement local ou de démonstration.

Le fichier `docker-compose.prod.yml` servira au lancement production avec un reverse proxy HTTPS.

## Séparation entre image Docker et données vivantes

Les données générées par Badge83 ne doivent pas être stockées uniquement dans le conteneur.

Les éléments suivants doivent être persistants :

```text
data/issued/       # assertions JSON émises
data/baked/        # badges PNG baked
data/registry.db   # registre SQLite local
```

La solution recommandée pour la première version est un bind mount simple :

```text
badge83/runtime-data:/app/data
```

Avantages :

- les données restent visibles directement dans le projet ;
- la sauvegarde est simple ;
- le transfert vers une autre machine est plus lisible ;
- il n'est pas nécessaire d'inspecter un volume Docker nommé.

Après lancement, les données de production seraient donc dans :

```text
badge83/runtime-data/issued/
badge83/runtime-data/baked/
badge83/runtime-data/registry.db
```

## Rôle du script d'entrée

Le fichier `docker/entrypoint.sh` devra préparer le conteneur au démarrage.

Ses responsabilités :

1. créer les dossiers de données s'ils n'existent pas ;
2. copier les fichiers de base depuis l'image vers `/app/data` lors du premier lancement ;
3. définir les valeurs par défaut utiles ;
4. lancer la commande Uvicorn finale.

Fichiers de base à copier au premier démarrage :

```text
issuer_template.json
badgeclass_template.json
badge.png
mode83-badge.png
```

Cette stratégie évite d'écraser les fichiers déjà présents dans `runtime-data` lors d'une mise à jour.

## Variables d'environnement principales

### Variables communes

```env
BADGE83_BASE_URL=http://localhost:8000
BADGE83_REGISTRY_DB=/app/data/registry.db
BADGE83_AUTH_USERNAME=admin83
BADGE83_AUTH_PASSWORD=change-me-password
BADGE83_AUTH_SECRET=change-me-auth-secret
BADGE83_SEARCH_PEPPER=change-me-search-pepper
```

### Variables production

```env
BADGE83_ENV=production
BADGE83_DOMAIN=badge83.example.com
BADGE83_BASE_URL=https://badge83.example.com
BADGE83_REGISTRY_DB=/app/data/registry.db

BADGE83_AUTH_USERNAME=admin83
BADGE83_AUTH_PASSWORD=CHANGE_TO_STRONG_PASSWORD
BADGE83_AUTH_SECRET=CHANGE_TO_LONG_RANDOM_SECRET
BADGE83_SEARCH_PEPPER=CHANGE_TO_LONG_RANDOM_PEPPER
```

En mode production, Badge83 refuse déjà de démarrer si les secrets faibles de développement sont conservés.

## Point critique : `BADGE83_BASE_URL`

La variable la plus importante est :

```text
BADGE83_BASE_URL
```

Elle est intégrée dans :

- les assertions Open Badges ;
- les URLs publiques `Issuer`, `BadgeClass` et `Assertion` ;
- les QR codes visibles dans les PNG baked ;
- les vérifications externes de type HostedBadge.

Exemples :

```env
BADGE83_BASE_URL=http://localhost:8000
BADGE83_BASE_URL=https://badge83.example.com
```

Une mauvaise valeur produit des badges qui pointent vers une adresse incorrecte.

## Lancement local prévu

Commandes attendues :

```bash
cd badge83
cp .env.docker.example .env
docker compose up -d --build
```

URL locale :

```text
http://localhost:8000
```

Vérifications rapides :

```bash
curl http://localhost:8000/issuers/main
curl http://localhost:8000/badges/blockchain-foundations
```

## Lancement production prévu

Commandes attendues :

```bash
cd badge83
cp .env.production.example .env
nano .env
docker compose -f docker-compose.prod.yml up -d --build
```

Dans ce mode, Caddy peut être utilisé comme reverse proxy HTTPS.

Schéma :

```text
Caddy :80/:443
  ↓
badge83:8000
```

Le service `badge83` ne doit pas nécessairement être exposé directement au public avec `ports`. Il peut être accessible uniquement par Caddy via le réseau Docker interne.

## Routes publiques à préserver

Même avec une protection de l'administration, les endpoints Open Badges doivent rester publics pour permettre la validation externe.

Routes à laisser publiques :

```text
/auth/login
/verify/qr/
/assertions/
/issuers/
/badges/
/assets/
```

Routes opérateur ou administration à protéger :

```text
/
/api/
/verify-desk
/issue
/issue-baked
/verify-baked
/badge-constructor/
```

L'application FastAPI possède déjà une protection par cookie sur les routes sensibles. Un reverse proxy peut ajouter une barrière supplémentaire.

## Sauvegarde et restauration

Avec la stratégie `runtime-data`, la sauvegarde minimale concerne :

```text
badge83/runtime-data/issued/
badge83/runtime-data/baked/
badge83/runtime-data/registry.db
```

Il est recommandé de sauvegarder tout le dossier :

```text
badge83/runtime-data/
```

Une restauration sur une nouvelle machine consiste à recopier ce dossier avant de relancer Docker Compose.

## Ordre de réalisation proposé

### Étape 1 — Docker local minimal

Créer :

```text
Dockerfile
.dockerignore
docker-compose.yml
.env.docker.example
docker/entrypoint.sh
```

Objectif : démarrer Badge83 localement via Docker et vérifier les endpoints publics.

### Étape 2 — Persistance des données

Valider que les assertions JSON, les PNG baked et `registry.db` restent présents après :

```bash
docker compose restart
docker compose down
docker compose up -d
```

### Étape 3 — Production HTTPS

Ajouter :

```text
docker-compose.prod.yml
docker/Caddyfile
.env.production.example
```

Objectif : préparer un lancement public avec HTTPS automatique.

### Étape 4 — Documentation utilisateur

Mettre à jour le README avec :

- démarrage local Docker ;
- démarrage production ;
- variables d'environnement ;
- sauvegarde/restauration ;
- points de vigilance sur `BADGE83_BASE_URL`.

### Étape 5 — Validation

Tests manuels à réaliser :

```bash
curl http://localhost:8000/issuers/main
curl http://localhost:8000/badges/blockchain-foundations
curl http://localhost:8000/assets/mode83-badge.png --output /tmp/mode83-badge.png
```

Puis vérifier dans l'interface :

1. connexion administrateur ;
2. émission d'un badge PNG baked ;
3. présence du JSON dans `runtime-data/issued` ;
4. présence du PNG dans `runtime-data/baked` ;
5. vérification via upload ;
6. vérification via QR/page publique.

## Risques identifiés

| Risque | Mesure prévue |
| --- | --- |
| Mauvais `BADGE83_BASE_URL` | Documenter et vérifier avant émission réelle |
| Perte de données lors d'une reconstruction | Utiliser `runtime-data:/app/data` |
| Secrets faibles en production | `BADGE83_ENV=production` et secrets obligatoires |
| Endpoints Open Badges protégés par erreur | Lister les routes publiques à préserver |
| Certificats HTTPS absents | Utiliser Caddy ou configurer Nginx/Let's Encrypt |

## Conclusion

La conteneurisation de Badge83 doit être réalisée comme une couche d'exploitation, sans modifier le cœur applicatif FastAPI.

La priorité est :

1. rendre le lancement reproductible ;
2. garantir la persistance des badges émis ;
3. préparer une exposition HTTPS propre ;
4. simplifier le transfert de l'application vers une autre machine.
