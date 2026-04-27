# Pile technique recommandée pour Mode83

Date : 2026-04-27

Ce document fixe la pile technique cible pour publier Mode83 de manière sûre, maintenable et compatible avec la nouvelle logique d’URL publique :

```text
BADGE83_BASE_URL=https://mode83.ddns.net
Backend interne = 127.0.0.1:8000
Issuer public = https://mode83.ddns.net/issuers/main
```

---

## 1. Architecture cible

```text
Internet
  |
  | 80/tcp, 443/tcp uniquement
  v
Nginx HTTPS / reverse proxy
  |
  | proxy_pass http://127.0.0.1:8000
  v
Mode83 backend FastAPI
  |
  v
SQLite maintenant / PostgreSQL plus tard

Développeur
  |
  | tunnel SSH ou VPN
  v
code-server / outils dev sur localhost
```

Principe clé : les ports applicatifs (`8000`, `8080`, `5000`) ne sont pas exposés directement à Internet.

---

## 2. Backend applicatif

Pile recommandée :

```text
Python 3.12+
FastAPI
Pydantic
Uvicorn
Gunicorn optionnel pour une phase production plus avancée
```

Mode83 utilise déjà FastAPI et Uvicorn. Il faut donc consolider l’existant plutôt que changer de plateforme.

Configuration d’exécution cible :

```env
BADGE83_HOST=127.0.0.1
BADGE83_PORT=8000
BADGE83_BASE_URL=https://mode83.ddns.net
```

Le backend écoute uniquement en local :

```text
127.0.0.1:8000
```

Il ne doit pas écouter sur :

```text
0.0.0.0:8000
```

---

## 3. URLs Open Badges

La nouvelle URL publique canonique est :

```text
https://mode83.ddns.net
```

Les nouveaux badges doivent contenir :

```text
issuer = https://mode83.ddns.net/issuers/main
badge  = https://mode83.ddns.net/badges/blockchain-foundations
id     = https://mode83.ddns.net/assertions/<uuid>
```

Le port interne `8000` ne doit jamais apparaître dans les nouveaux JSON publics.

---

## 4. Couche web publique

Pile recommandée :

```text
Nginx
Let’s Encrypt / Certbot
HTTPS only
Rate limiting
Security headers
```

Nginx est responsable de :

- TLS/HTTPS ;
- redirection `80 -> 443` ;
- reverse proxy vers `127.0.0.1:8000` ;
- limitation de débit ;
- logs HTTP ;
- en-têtes de sécurité.

---

## 5. Base de données

Phase actuelle :

```text
SQLite
```

Condition : sauvegardes régulières de `badge83/data/registry.db` et des dossiers `issued/` et `baked/`.

Phase ultérieure :

```text
PostgreSQL
```

À envisager lorsque le volume d’écritures, le nombre d’utilisateurs ou la concurrence augmentent.

---

## 6. Sécurité système

Pile recommandée :

```text
iptables/nftables
fail2ban
CrowdSec plus tard
SSH par clé uniquement
root login désactivé
```

Ports publics cibles :

```text
22/tcp  SSH, idéalement limité à une IP de confiance
80/tcp  HTTP redirect / Let’s Encrypt
443/tcp HTTPS
```

Ports privés :

```text
8000/tcp backend Mode83
8080/tcp code-server
5000/tcp validateur ou service test
```

---

## 7. Gestion firewall dans les scripts

Les scripts peuvent gérer temporairement les ports publics, mais cette fonction est désactivée par défaut.

Configuration :

```env
BADGE83_ENABLE_FIREWALL_MANAGEMENT=false
BADGE83_PUBLIC_HTTP_PORT=80
BADGE83_PUBLIC_HTTPS_PORT=443
```

Commandes prévues :

```bash
./badge83.sh firewall-open
./badge83.sh firewall-close
```

Si `BADGE83_ENABLE_FIREWALL_MANAGEMENT=true`, alors `start` peut ouvrir `80/443` et `stop` peut les fermer.

Important : le script ne doit pas ouvrir `8000` publiquement.

---

## 8. Accès développeur

Recommandation immédiate : tunnel SSH.

```bash
ssh -L 8080:127.0.0.1:8080 ubuntu@SERVER_IP
```

Option ultérieure :

```text
WireGuard ou Tailscale
```

Les outils de développement ne doivent pas être exposés publiquement.

---

## 9. Déploiement

Phase 1 :

```text
venv + badge83.env + badge83.sh + systemd
```

Phase 2 :

```text
Docker Compose
```

Docker Compose devient intéressant lorsque plusieurs services seront stabilisés : backend, PostgreSQL, worker, reverse proxy, validateur, etc.

---

## 10. Feuille de route

1. Fixer `BADGE83_BASE_URL=https://mode83.ddns.net`.
2. Faire écouter le backend sur `127.0.0.1:8000`.
3. Vérifier que les nouveaux badges ne contiennent plus `:8000`.
4. Ajouter ou maintenir la compatibilité locale avec les anciens issuer legacy.
5. Ajouter Nginx en reverse proxy HTTPS.
6. Ouvrir uniquement `80/443`.
7. Ajouter fail2ban et rate limiting Nginx.
8. Passer ensuite à systemd.

---

## 11. Critère de réussite

La pile est correctement mise en place lorsque :

```text
Mode83 répond sur 127.0.0.1:8000
Nginx répond sur https://mode83.ddns.net
Les nouveaux badges utilisent https://mode83.ddns.net/issuers/main
Le port 8000 n’est pas exposé publiquement
Les ports 80/443 sont contrôlés
Les services dev passent par tunnel SSH ou VPN
```
