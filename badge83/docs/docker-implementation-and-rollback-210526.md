# Badge83 — plan de création Docker et procédure de rollback — 21/05/2026

## Objectif

Ajouter une couche Docker à Badge83 sans modifier le cœur applicatif FastAPI et
sans casser le lancement historique par virtualenv + `badge83.sh`.

La branche de travail est :

```bash
feature/docker-badge83
```

La branche de sauvegarde créée avant les changements Docker est :

```bash
backup/pre-docker-2026-05-21
```

Elle pointe sur le commit :

```text
140db32069895686295bdd367cd9448064aabb90
```

## Principe de compatibilité

Docker doit rester une couche d'exploitation optionnelle. Le projet existant
doit continuer à fonctionner avec :

```bash
cd /home/ubuntu/projects/Mode83/badge83
./badge83.sh start
./badge83.sh status
./badge83.sh stop
```

Aucun changement n'est prévu dans `app/config.py`, `app/main.py` ou la logique
métier pour la première version Docker. Dans le conteneur, la structure est
alignée avec les chemins déjà attendus par le code :

```text
/app/app/
/app/templates/
/app/data/
```

## Fichiers Docker ajoutés

```text
badge83/Dockerfile
badge83/.dockerignore
badge83/docker-compose.yml
badge83/docker-compose.prod.yml
badge83/.env.docker.example
badge83/.env.production.example
badge83/docker/entrypoint.sh
badge83/docker/setup.sh
badge83/docker/nginx/templates/default.conf.template
```

## Données persistantes

Les données vivantes ne doivent pas être intégrées à l'image Docker. Elles sont
stockées dans un bind mount lisible et sauvegardable :

```text
badge83/runtime-data:/app/data
```

Le script `docker/entrypoint.sh` crée les dossiers nécessaires et copie les
fichiers de démarrage depuis `/app/seed-data` vers `/app/data` uniquement s'ils
n'existent pas encore.

À préserver/sauvegarder :

```text
runtime-data/issued/
runtime-data/baked/
runtime-data/backgrounds/
runtime-data/registry.db
runtime-data/*.json
runtime-data/*.png
runtime-data/*.xlsx
runtime-data/*.csv
```

## Lancement Docker local

```bash
cd /home/ubuntu/projects/Mode83/badge83
cp .env.docker.example .env
docker compose up -d --build
```

Sur une machine disposant de Compose v1, utiliser :

```bash
docker-compose up -d --build
```

Vérification rapide :

```bash
curl http://localhost:8000/issuers/main
curl http://localhost:8000/badges/blockchain-foundations
```

Arrêt :

```bash
docker compose down
```

ou, avec Compose v1 :

```bash
docker-compose down
```

## Sécurité et équivalence avec le lancement actuel

Le conteneur `badge83` exécute le même code FastAPI que le lancement historique.
Les protections applicatives existantes restent donc actives :

- les routes opérateur déclarées avec `Depends(require_admin)` restent protégées
  par cookie côté FastAPI ;
- `/auth/login`, `/auth/check` et `/auth/logout` restent fournis par l'application ;
- les endpoints Open Badges publics restent accessibles sans authentification.

La couche reverse proxy retenue est Nginx, afin de garder une façade de sécurité
proche de l'existant, avec séparation explicite entre routes publiques et routes
opérateur protégées.

Routes publiques à conserver :

```text
/auth/login
/verify/qr/
/assertions/
/issuers/
/badges/
/assets/
```

Les autres routes passent par `auth_request /auth/check`, en plus des contrôles
déjà présents dans FastAPI.

## Lancement production HTTPS avec Nginx

La variante Nginx est celle à privilégier si l'on veut conserver une couche de
protection réseau proche de l'existant :

```bash
cd /home/ubuntu/projects/Mode83/badge83
./docker/setup.sh
docker-compose -f docker-compose.prod.yml up -d --build
```

La configuration Nginx :

- redirige HTTP vers HTTPS ;
- laisse publics les endpoints de vérification et Open Badges ;
- protège les autres routes via `auth_request /auth/check` ;
- garde FastAPI comme deuxième barrière applicative.

Le wizard `docker/setup.sh` permet :

- de saisir le domaine public ;
- de définir `BADGE83_BASE_URL` ;
- de choisir le login admin ;
- de saisir ou générer un mot de passe admin ;
- de générer `BADGE83_AUTH_SECRET` et `BADGE83_SEARCH_PEPPER` ;
- de préparer les certificats selon trois modes : existants, self-signed, ou
  tentative Let's Encrypt via certbot Docker standalone.

Avant toute émission réelle, vérifier impérativement :

- `BADGE83_DOMAIN` ;
- `BADGE83_BASE_URL` ;
- `BADGE83_AUTH_PASSWORD` ;
- `BADGE83_AUTH_SECRET` ;
- `BADGE83_SEARCH_PEPPER`.

## Plan de validation

1. Construire l'image Docker.
2. Démarrer le conteneur local.
3. Vérifier `/issuers/main`, `/badges/blockchain-foundations`, `/assets/mode83-badge.png`.
4. Vérifier l'accès à l'interface d'administration.
5. Émettre un badge PNG baked.
6. Vérifier que le JSON apparaît dans `runtime-data/issued/`.
7. Vérifier que le PNG apparaît dans `runtime-data/baked/`.
8. Redémarrer le conteneur et confirmer que les données restent présentes.
9. Vérifier que le lancement historique `badge83.sh` reste inchangé.

## Rollback Git

Pour abandonner les changements Docker et revenir au snapshot pré-Docker :

```bash
git switch backup/pre-docker-2026-05-21
```

Pour revenir sur `main` :

```bash
git switch main
```

Pour supprimer la branche de travail Docker si elle n'est plus utile :

```bash
git branch -D feature/docker-badge83
```

## Rollback Docker local

Arrêter la stack :

```bash
cd /home/ubuntu/projects/Mode83/badge83
docker compose down
```

Supprimer uniquement les conteneurs/images Docker générés, sans toucher aux
données :

```bash
docker compose down --rmi local
```

Les données restent dans :

```text
badge83/runtime-data/
```

Ne supprimer ce dossier que si une remise à zéro complète est voulue :

```bash
rm -rf runtime-data
```

## Points de vigilance

- `BADGE83_BASE_URL` est intégré dans les badges et QR codes. Une mauvaise
  valeur produit des badges pointant vers une mauvaise adresse.
- Les endpoints publics Open Badges (`/assertions/`, `/issuers/`, `/badges/`,
  `/assets/`, `/verify/qr/`) doivent rester accessibles publiquement en
  production.
- Les secrets de production ne doivent jamais être commités.
- Les données runtime doivent être sauvegardées séparément de l'image Docker.