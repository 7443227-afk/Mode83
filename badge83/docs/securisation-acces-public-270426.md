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

Une authentification HTTP Basic a été activée au niveau Nginx.

Sans authentification, les routes administratives, les API, les pages détaillées et les ressources Open Badges ne sont pas accessibles.

Les réponses attendues sont :

```text
/                         -> 401 sans mot de passe
/api/badges               -> 401 sans mot de passe
/verify/badge/<id>        -> 401 sans mot de passe
/issuers/main             -> 401 sans mot de passe
/badges/...               -> 401 sans mot de passe
/assertions/...           -> 401 sans mot de passe
/assets/...               -> 401 sans mot de passe
```

## Exception publique conservée

La seule page applicative laissée publique est la page mobile de vérification QR :

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
/issuers/main sans authentification  -> 401
/issuers/main avec authentification  -> 200
```

La suite de tests Python a été exécutée avec succès :

```text
14 passed
```

## Points d’attention

Cette configuration privilégie la confidentialité. En contrepartie, les validateurs externes Open Badges ne peuvent plus résoudre librement les ressources JSON publiques sans authentification. Pour une phase de démonstration ou de validation externe, il faudra décider si certaines ressources Open Badges doivent redevenir publiques temporairement ou si la vérification doit rester strictement interne.
