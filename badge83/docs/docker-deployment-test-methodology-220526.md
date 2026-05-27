# Badge83 — méthode d'installation, déploiement et tests Docker — 22/05/2026

## Objectif

Ce document décrit une méthode reproductible pour installer, déployer et tester
Badge83 avec Docker sur une nouvelle machine Linux.

Il ne documente pas un serveur réel. Les noms de domaine, chemins et secrets
utilisés ci-dessous sont des exemples à adapter à l'environnement cible.

Le scénario validé couvre :

- l'installation de Docker Engine et du plugin Docker Compose ;
- le déploiement de Badge83 depuis le dépôt Git ;
- la configuration d'un environnement production HTTPS avec Nginx ;
- la vérification des endpoints publics Open Badges ;
- la vérification de la persistance des données ;
- un test de redémarrage de la stack Docker.

## Architecture cible

Le modèle production retenu est :

```text
Internet
  -> Nginx HTTPS, conteneur Docker
  -> Badge83 FastAPI/Uvicorn, conteneur Docker
  -> runtime-data, dossier persistant sur l'hôte
```

Nginx assure :

- la terminaison HTTPS ;
- la redirection HTTP vers HTTPS ;
- l'exposition publique des routes Open Badges nécessaires à la vérification ;
- la protection des routes opérateur via `auth_request /auth/check`.

Badge83 conserve aussi ses protections applicatives côté FastAPI.

## Prérequis

Machine cible :

- Linux 64-bit, par exemple Ubuntu Server 24.04 LTS ;
- accès SSH administrateur ou utilisateur avec `sudo` ;
- Git installé ;
- ports `80` et `443` disponibles ;
- nom de domaine public pointant vers l'adresse IP de la machine ;
- certificat TLS existant ou possibilité d'en générer un ;
- accès sortant à Internet pour télécharger les images Docker et dépendances.

Exemples de placeholders utilisés dans ce document :

```text
badge83.example.com
~/projects/Mode83
```

## Installation de Docker sur Ubuntu

Vérifier l'état initial :

```bash
git --version
docker --version || echo "docker not installed"
docker compose version || echo "docker compose plugin not installed"
cat /etc/os-release | head
```

Installer les dépendances :

```bash
sudo apt update
sudo apt install -y ca-certificates curl gnupg
```

Ajouter le dépôt officiel Docker :

```bash
sudo install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg \
  | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
sudo chmod a+r /etc/apt/keyrings/docker.gpg

echo \
  "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu \
  $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
```

Installer Docker Engine et Compose :

```bash
sudo apt update
sudo apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin
```

Vérifier :

```bash
docker --version
docker compose version
sudo docker run --rm hello-world
```

Optionnel : permettre à l'utilisateur courant d'utiliser Docker sans `sudo` :

```bash
sudo usermod -aG docker "$USER"
```

Puis se déconnecter/reconnecter et vérifier :

```bash
docker ps
```

## Récupération du projet depuis Git

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/7443227-afk/Mode83.git
cd Mode83
```

Depuis le 22/05/2026, les fichiers Docker validés sont intégrés dans `main`.
Pour une installation sur une nouvelle machine, le déploiement doit donc se
faire depuis `main` :

```bash
git fetch --all
git switch main
git pull
```

Vérifier la présence des fichiers :

```bash
cd ~/projects/Mode83/badge83
ls -la Dockerfile docker-compose.yml docker-compose.prod.yml
ls -la .env.docker.example .env.production.example
ls -la docker/entrypoint.sh docker/setup.sh docker/nginx/templates
```

## Déploiement local ou démonstration HTTP

Ce mode sert à valider rapidement l'image Docker sans reverse proxy HTTPS.

```bash
cd ~/projects/Mode83/badge83
cp .env.docker.example .env
```

Adapter au minimum :

```env
BADGE83_BASE_URL=http://localhost:8000
BADGE83_AUTH_PASSWORD=change-me-password
BADGE83_AUTH_SECRET=change-me-auth-secret
BADGE83_SEARCH_PEPPER=change-me-search-pepper
```

Lancer :

```bash
docker compose up -d --build
```

Vérifier :

```bash
docker compose ps
curl http://localhost:8000/issuers/main
curl http://localhost:8000/badges/blockchain-foundations
```

Arrêter :

```bash
docker compose down
```

## Déploiement production HTTPS

### Préparer le fichier `.env`

Depuis `badge83/` :

```bash
cd ~/projects/Mode83/badge83
cp .env.production.example .env
```

Exemple de configuration :

```env
BADGE83_ENV=production
BADGE83_DOMAIN=badge83.example.com

BADGE83_HOST=0.0.0.0
BADGE83_PORT=8000
BADGE83_BASE_URL=https://badge83.example.com
BADGE83_REGISTRY_DB=/app/data/registry.db

BADGE83_AUTH_USERNAME=admin83
BADGE83_AUTH_PASSWORD=CHANGE_ME_STRONG_PASSWORD
BADGE83_AUTH_SECRET=CHANGE_ME_LONG_RANDOM_COOKIE_SECRET
BADGE83_SEARCH_PEPPER=CHANGE_ME_LONG_RANDOM_SEARCH_PEPPER

BADGE83_MAX_PNG_UPLOAD_BYTES=52428800
BADGE83_MAX_CSV_UPLOAD_BYTES=10485760
BADGE83_MAX_IMAGE_PIXELS=50000000
```

Générer les secrets :

```bash
openssl rand -hex 32
openssl rand -hex 32
```

Les valeurs obtenues peuvent être utilisées pour :

- `BADGE83_AUTH_SECRET` ;
- `BADGE83_SEARCH_PEPPER`.

Protéger le fichier :

```bash
chmod 600 .env
```

Vérifier sans afficher les secrets :

```bash
awk -F= '/BADGE83_AUTH_PASSWORD|BADGE83_AUTH_SECRET|BADGE83_SEARCH_PEPPER/ { print $1 " length=" length($2) }' .env
grep -E 'BADGE83_ENV|BADGE83_DOMAIN|BADGE83_BASE_URL|BADGE83_AUTH_USERNAME' .env
```

En production, les secrets faibles ou vides doivent être refusés par
l'application.

### Préparer les certificats TLS

Nginx attend les fichiers suivants :

```text
badge83/docker/nginx/certs/fullchain.pem
badge83/docker/nginx/certs/privkey.pem
```

Si un certificat Let's Encrypt existe déjà sur la machine :

```bash
cd ~/projects/Mode83/badge83
mkdir -p docker/nginx/certs
sudo cp -L /etc/letsencrypt/live/badge83.example.com/fullchain.pem docker/nginx/certs/fullchain.pem
sudo cp -L /etc/letsencrypt/live/badge83.example.com/privkey.pem docker/nginx/certs/privkey.pem
sudo chown "$USER:$USER" docker/nginx/certs/fullchain.pem docker/nginx/certs/privkey.pem
chmod 644 docker/nginx/certs/fullchain.pem
chmod 600 docker/nginx/certs/privkey.pem
```

Vérifier :

```bash
ls -la docker/nginx/certs
```

### Vérifier les ports

```bash
sudo ss -ltnp | grep -E ':80|:443' || true
```

Si un serveur Nginx ou Apache système occupe déjà ces ports, il faut l'arrêter
ou adapter l'architecture avant de démarrer la stack Docker.

### Lancer la stack production

```bash
cd ~/projects/Mode83/badge83
docker compose -f docker-compose.prod.yml up -d --build
```

Vérifier :

```bash
docker compose -f docker-compose.prod.yml ps
```

État attendu :

```text
badge83-badge83-1   Up ... (healthy)
badge83-nginx-1     Up ... 0.0.0.0:80->80/tcp, 0.0.0.0:443->443/tcp
```

En cas d'erreur :

```bash
docker compose -f docker-compose.prod.yml logs --tail=160 badge83
docker compose -f docker-compose.prod.yml logs --tail=160 nginx
```

## Méthode de test après déploiement

### 1. Vérifier les endpoints publics en GET

Certains endpoints FastAPI n'acceptent pas `HEAD`. Pour les tests automatisés,
utiliser donc `GET` plutôt que `curl -I`.

```bash
DOMAIN=badge83.example.com

for url in \
  "https://${DOMAIN}/issuers/main" \
  "https://${DOMAIN}/badges/blockchain-foundations" \
  "https://${DOMAIN}/assets/mode83-badge.png"
do
  code=$(curl -ksS -o /tmp/badge83_check_body -w "%{http_code}" "$url")
  size=$(wc -c < /tmp/badge83_check_body)
  printf "%s -> HTTP %s, %s bytes\n" "$url" "$code" "$size"
done
```

Résultat attendu : `HTTP 200` pour chaque URL.

### 2. Vérifier le contenu Issuer

```bash
curl -ksS "https://${DOMAIN}/issuers/main" | python3 -m json.tool | sed -n '1,60p'
```

Vérifier notamment :

- `id` ;
- `url` ;
- `image` ;
- `verification.startsWith`.

Ces valeurs doivent correspondre au domaine public configuré dans
`BADGE83_BASE_URL`.

### 3. Vérifier la redirection HTTP vers HTTPS

```bash
curl -sS -D - -o /dev/null "http://${DOMAIN}/issuers/main" | sed -n '1,12p'
```

Résultat attendu : `301` ou `308` avec un header `Location` vers HTTPS.

### 4. Vérifier l'interface opérateur

Ouvrir dans le navigateur :

```text
https://badge83.example.com/
```

Vérifier :

- l'affichage de la page de connexion si nécessaire ;
- l'authentification avec `BADGE83_AUTH_USERNAME` et `BADGE83_AUTH_PASSWORD` ;
- l'accès aux interfaces opérateur ;
- la création ou modification d'un modèle de badge ;
- l'émission d'un badge PNG baked.

### 5. Vérifier les données persistantes

Après émission d'un badge :

```bash
cd ~/projects/Mode83/badge83
ls -la runtime-data
ls -la runtime-data/issued | tail
ls -la runtime-data/baked | tail
ls -lh runtime-data/registry.db
```

Les fichiers attendus sont :

- assertions JSON dans `runtime-data/issued/` ;
- badges PNG dans `runtime-data/baked/` ;
- registre SQLite dans `runtime-data/registry.db`.

### 6. Test de redémarrage

```bash
cd ~/projects/Mode83/badge83
docker compose -f docker-compose.prod.yml restart
sleep 15
docker compose -f docker-compose.prod.yml ps
```

Puis vérifier un endpoint :

```bash
curl -ksS -o /tmp/badge83_after_restart -w "%{http_code}\n" \
  "https://${DOMAIN}/issuers/main"
```

Résultat attendu :

- conteneur Badge83 à nouveau `healthy` ;
- Nginx `Up` ;
- endpoint public en `HTTP 200` ;
- données toujours présentes dans `runtime-data/`.

## Résultats de validation observés

La procédure a été validée sur une machine distante de test, sans conserver dans
ce document son nom réel.

Résultats observés :

- installation Docker réussie ;
- récupération du projet depuis Git réussie ;
- validation initiale réalisée sur la branche Docker, puis intégration des
  fichiers Docker dans `main` pour simplifier les installations suivantes ;
- démarrage initial bloqué par des secrets production trop courts ;
- correction de `.env` avec des secrets aléatoires de 64 caractères ;
- démarrage de la stack production réussi ;
- conteneur `badge83` en état `healthy` ;
- conteneur `nginx` exposant `80` et `443` ;
- endpoints publics Open Badges en `HTTP 200` via `GET` ;
- redirection HTTP vers HTTPS active ;
- émission de badges PNG baked validée depuis l'interface ;
- présence des fichiers émis dans `runtime-data/issued/` et
  `runtime-data/baked/` ;
- présence du registre SQLite `runtime-data/registry.db` ;
- redémarrage de la stack réussi sans perte de données.

## Commandes d'exploitation courantes

Statut :

```bash
docker compose -f docker-compose.prod.yml ps
```

Logs application :

```bash
docker compose -f docker-compose.prod.yml logs -f badge83
```

Logs Nginx :

```bash
docker compose -f docker-compose.prod.yml logs -f nginx
```

Arrêt sans suppression des données :

```bash
docker compose -f docker-compose.prod.yml down
```

Redémarrage :

```bash
docker compose -f docker-compose.prod.yml restart
```

Mise à jour depuis Git :

```bash
cd ~/projects/Mode83
git pull
cd badge83
docker compose -f docker-compose.prod.yml up -d --build
```

## Sauvegarde minimale

À sauvegarder régulièrement :

```text
badge83/.env
badge83/runtime-data/
badge83/docker/nginx/certs/
```

Le dossier `runtime-data/` est prioritaire car il contient les badges émis et le
registre SQLite.

Exemple de sauvegarde horodatée depuis le dossier `badge83/` :

```bash
mkdir -p backups
BACKUP_DATE=$(date +%Y%m%d-%H%M%S)
tar -czf "backups/badge83-runtime-${BACKUP_DATE}.tar.gz" runtime-data
cp .env "backups/badge83-env-${BACKUP_DATE}.env"
tar -czf "backups/badge83-certs-${BACKUP_DATE}.tar.gz" docker/nginx/certs
```

Recommandations :

- conserver au moins une copie hors de la machine de production ;
- protéger les archives contenant `.env` ou `privkey.pem` ;
- tester périodiquement la restauration sur une machine séparée ;
- effectuer une sauvegarde avant toute mise à jour importante.

## Procédure de restauration

Cette procédure décrit une restauration simple sur une nouvelle machine ou après
réinstallation du serveur.

1. Réinstaller les prérequis système et Docker.

2. Récupérer le dépôt :

```bash
mkdir -p ~/projects
cd ~/projects
git clone https://github.com/7443227-afk/Mode83.git
cd Mode83
git switch main
cd badge83
```

3. Restaurer les fichiers sauvegardés :

```bash
tar -xzf /chemin/vers/badge83-runtime-YYYYMMDD-HHMMSS.tar.gz
cp /chemin/vers/badge83-env-YYYYMMDD-HHMMSS.env .env
tar -xzf /chemin/vers/badge83-certs-YYYYMMDD-HHMMSS.tar.gz
```

4. Vérifier les permissions sensibles :

```bash
chmod 600 .env
chmod 600 docker/nginx/certs/privkey.pem
chmod 644 docker/nginx/certs/fullchain.pem
```

5. Relancer la stack :

```bash
docker compose -f docker-compose.prod.yml up -d --build
docker compose -f docker-compose.prod.yml ps
```

6. Rejouer les tests de validation :

```bash
DOMAIN=badge83.example.com
curl -ksS -o /tmp/badge83_restore_issuer -w "%{http_code}\n" \
  "https://${DOMAIN}/issuers/main"
curl -ksS -o /tmp/badge83_restore_badge -w "%{http_code}\n" \
  "https://${DOMAIN}/badges/blockchain-foundations"
ls -lh runtime-data/registry.db
ls -la runtime-data/issued | tail
ls -la runtime-data/baked | tail
```

La restauration est considérée comme valide si :

- le conteneur `badge83` revient en état `healthy` ;
- Nginx expose toujours `80` et `443` ;
- les endpoints publics répondent en `HTTP 200` ;
- les badges et assertions précédemment émis sont présents ;
- l'interface opérateur reste accessible avec les identifiants restaurés.

## Supervision légère

Pour une exploitation simple, sans outil de monitoring dédié, les contrôles
suivants peuvent être exécutés régulièrement.

État des conteneurs :

```bash
docker compose -f docker-compose.prod.yml ps
```

Logs récents :

```bash
docker compose -f docker-compose.prod.yml logs --tail=80 badge83
docker compose -f docker-compose.prod.yml logs --tail=80 nginx
```

Smoke test HTTP :

```bash
DOMAIN=badge83.example.com
for url in \
  "https://${DOMAIN}/issuers/main" \
  "https://${DOMAIN}/badges/blockchain-foundations" \
  "https://${DOMAIN}/assets/mode83-badge.png" \
  "https://${DOMAIN}/verify/qr/"
do
  code=$(curl -ksS -o /tmp/badge83_monitor_body -w "%{http_code}" "$url")
  printf "%s -> HTTP %s\n" "$url" "$code"
done
```

Vérification de l'espace disque :

```bash
df -h .
du -sh runtime-data
```

Vérification de l'expiration du certificat :

```bash
openssl x509 -in docker/nginx/certs/fullchain.pem -noout -subject -issuer -dates
```

## Renouvellement des certificats TLS

Si les certificats proviennent de Let's Encrypt sur l'hôte, le renouvellement se
fait généralement hors des conteneurs, puis les nouveaux fichiers doivent être
recopiés dans `docker/nginx/certs/`.

Exemple après renouvellement côté hôte :

```bash
cd ~/projects/Mode83/badge83
sudo cp -L /etc/letsencrypt/live/badge83.example.com/fullchain.pem docker/nginx/certs/fullchain.pem
sudo cp -L /etc/letsencrypt/live/badge83.example.com/privkey.pem docker/nginx/certs/privkey.pem
sudo chown "$USER:$USER" docker/nginx/certs/fullchain.pem docker/nginx/certs/privkey.pem
chmod 644 docker/nginx/certs/fullchain.pem
chmod 600 docker/nginx/certs/privkey.pem
docker compose -f docker-compose.prod.yml restart nginx
```

Après redémarrage de Nginx, vérifier :

```bash
curl -sS -D - -o /dev/null "https://badge83.example.com/issuers/main" | sed -n '1,12p'
```

## Points de vigilance

- Ne jamais commiter `.env` ni les certificats privés.
- `BADGE83_BASE_URL` doit être correct avant toute émission réelle, car il est
  inscrit dans les badges et QR codes.
- Utiliser `GET` pour les smoke tests HTTP des endpoints publics ; `HEAD` peut
  retourner `405 Method Not Allowed` selon la route FastAPI.
- Vérifier que les ports `80` et `443` ne sont pas déjà occupés.
- Sauvegarder `runtime-data/` avant toute opération de migration ou remise à
  zéro.
