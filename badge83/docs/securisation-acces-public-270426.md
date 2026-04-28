# Sécurisation de l’accès public Mode83 — 27/04/2026

## Objectif

Mettre en place une exposition publique contrôlée de Mode83 tout en limitant l’accès non authentifié aux seules informations strictement nécessaires à la vérification rapide par QR code.

## Architecture retenue

Le backend Mode83 n’est pas exposé directement sur Internet. Il écoute uniquement en local :

```text
127.0.0.1:8000
```

L’accès public passe par Nginx :

```text
Internet -> HTTPS 443 -> Nginx -> 127.0.0.1:8000
```

Le domaine public canonique est :

```text
https://mode83.ddns.net
```

L’émetteur canonique des nouveaux badges est :

```text
https://mode83.ddns.net/issuers/main
```

## Protection par mot de passe

Une authentification applicative via `auth_request` Nginx a été activée au niveau Nginx.

Sans authentification, les routes administratives, les API et les pages détaillées ne sont pas accessibles.

Les ressources publiques nécessaires à la validation externe Open Badges restent volontairement accessibles sans authentification.

Les réponses attendues sont :

```text
/                         -> 401 sans mot de passe
/api/badges               -> 401 sans mot de passe
/verify/badge/<id>        -> 401 sans mot de passe
```

## Exceptions publiques conservées

La page applicative laissée publique est la page mobile de vérification QR :

```text
/verify/qr/<id>
```

Cette page ne doit afficher que :

- le résultat global de vérification ;
- le fait que le badge soit ou non reconnu comme émis par MODE83 ;
- l’identifiant public de vérification.

Elle ne doit pas afficher publiquement :

- le nom du titulaire ;
- l’email du titulaire ;
- les détails complets du badge ;
- les liens directs vers JSON/PNG/API.

Le lien vers la page détaillée n’est affiché que si le badge est valide et reconnu comme MODE83. Cette page détaillée reste protégée par mot de passe.

Les endpoints Open Badges nécessaires au modèle `HostedBadge` sont également publics afin de permettre aux validateurs externes de résoudre la chaîne complète :

```text
/assertions/<id>              -> Assertion JSON-LD publique
/issuers/main                 -> profil Issuer JSON-LD public
/badges/blockchain-foundations -> BadgeClass JSON-LD public
/assets/<image>.png           -> image publique du badge / issuer
```

Ces routes ne donnent pas accès à l’interface d’administration ni aux API internes. Elles exposent uniquement les objets publics requis par le standard Open Badges.

## Certificat TLS

Le certificat Let’s Encrypt a été émis pour :

```text
mode83.ddns.net
```

Il est installé dans :

```text
/etc/letsencrypt/live/mode83.ddns.net/
```

Le renouvellement automatique est géré par `certbot.timer`.

## Services actifs

Les services attendus sont :

```text
nginx  -> active
mode83 -> active
```

Les ports attendus sont :

```text
22/tcp   SSH
80/tcp   redirection HTTP vers HTTPS
443/tcp  HTTPS public
8000/tcp backend local uniquement sur 127.0.0.1
8080/tcp code-server local uniquement sur 127.0.0.1
```

## Vérifications réalisées

Les contrôles suivants ont été effectués :

```text
/ sans authentification              -> 401
/ avec authentification              -> 200
/verify/qr/<id> sans authentification -> accessible, page minimale
/verify/badge/<id> sans authentification -> 401
/api/badges sans authentification    -> 401
/assertions/<id> sans authentification -> 200, `application/ld+json`
/issuers/main sans authentification    -> 200, `application/ld+json`
/badges/... sans authentification      -> 200, `application/ld+json`
/assets/... sans authentification      -> 200, `image/png`
```

La suite de tests Python a été exécutée avec succès :

```text
14 passed
```

## Points d’attention

Cette configuration privilégie la confidentialité de l’administration tout en conservant la compatibilité avec la validation externe Open Badges.

Point d’équilibre retenu :

- les ressources Open Badges publiques (`Assertion`, `Issuer`, `BadgeClass`, assets) sont accessibles sans authentification ;
- les pages détaillées, l’administration et les API de gestion restent protégées ;
- les données personnelles complètes ne doivent pas être rendues publiques dans les pages QR ou les vues non protégées.

Le 27/04/2026, la configuration Nginx a été ajustée pour désactiver `auth_request` sur `/assertions/`, `/issuers/`, `/badges/` et `/assets/`, car les validateurs externes recevaient auparavant la page HTML de connexion au lieu du JSON-LD Open Badges.

Le même jour, le profil `Issuer` a aussi été ajusté pour la compatibilité validator Open Badges :

- `verification.type` est explicitement défini à `VerificationObject` ;
- `verification.allowedOrigins` contient l’autorité seule (`mode83.ddns.net`) et non l’URL complète (`https://mode83.ddns.net`) ;
- `verification.startsWith` conserve l’URL complète attendue pour les assertions (`https://mode83.ddns.net/assertions/`).

Les réponses JSON-LD publiques déclarent aussi explicitement `charset=utf-8` dans leur `Content-Type` afin d’éviter qu’un client HTTP ancien ou un validateur ne décode les accents UTF-8 comme du Latin-1/Windows-1252 (`pédagogique` affiché en `pĂŠdagogique`).
