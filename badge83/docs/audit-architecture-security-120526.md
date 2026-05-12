# Audit Badge83 — architecture, sécurité, qualité et exploitation

Date : 12/05/2026  
Projet audité : `badge83`  
Périmètre principal : application FastAPI, émission/vérification Open Badges, baking PNG, registre SQLite, constructeur de badges, configuration et tests.

## 1. Synthèse exécutive

Badge83 est un projet FastAPI fonctionnel qui implémente un flux Open Badges 2.0 de type HostedBadge : émission d'assertions JSON, génération de PNG baked, QR code de vérification, endpoints publics et interface d'administration. Le projet est cohérent pour un **MVP avancé / prototype opérationnel**, avec une base de tests existante et une documentation abondante.

En revanche, il n'est pas encore prêt pour une exposition production sans durcissement. Les principaux risques concernent :

- la présence de secrets dans le dépôt ;
- des valeurs par défaut faibles (`admin/admin`, secrets de développement) ;
- l'absence d'autorisation FastAPI intégrée sur les endpoints d'administration ;
- le stockage et l'exposition de données personnelles en clair dans les assertions et PNG ;
- des risques SSRF, path traversal et déni de service via uploads non limités ;
- une architecture encore trop centralisée dans `app/main.py`.

Tests exécutés pendant l'audit :

```bash
cd badge83 && ../.venv/bin/python -m pytest tests -q
```

Résultat :

```text
27 passed in 1.18s
```

## 2. Vue d'ensemble technique

### Stack

- Backend : FastAPI `0.115.12`
- ASGI : Uvicorn `0.34.0`
- Templates : Jinja2
- Validation : Pydantic / `email-validator`
- Images : Pillow, qrcode
- HTTP client : httpx
- Stockage : fichiers JSON/PNG + SQLite local
- Tests : pytest

### Modules principaux

| Fichier | Rôle |
|---|---|
| `app/main.py` | Application FastAPI, pages HTML, auth cookie, endpoints publics, endpoints admin, vérification en ligne |
| `app/issuer.py` | Émission d'assertions Open Badges, métadonnées, baking PNG, QR |
| `app/verifier.py` | Vérification JSON/PNG baked, vérification HostedBadge approfondie |
| `app/baker.py` | Injection/extraction du chunk PNG `openbadges` |
| `app/database.py` | SQLite : registre d'assertions et tables du constructeur |
| `app/qr.py` | Génération QR et overlays texte/image |
| `app/routes/badge_constructor/*` | API du constructeur de badges |
| `app/config.py` | Configuration via variables d'environnement |
| `badge83.sh` | Script de démarrage/arrêt/status/firewall |

## 3. Points forts

### 3.1 Flux métier complet

Le projet couvre un parcours complet :

1. émission d'une assertion Open Badges ;
2. sauvegarde JSON ;
3. génération PNG baked ;
4. ajout d'un QR visible ;
5. vérification par ID, PNG uploadé ou page QR ;
6. endpoints HostedBadge publics.

C'est un bon socle fonctionnel.

### 3.2 Séparation partielle des responsabilités

Les fonctions critiques ne sont pas toutes dans les routes :

- baking dans `baker.py` ;
- émission dans `issuer.py` ;
- vérification dans `verifier.py` ;
- QR et composition visuelle dans `qr.py` ;
- persistance SQLite dans `database.py`.

Cette séparation facilite déjà les tests unitaires.

### 3.3 Tests existants

La suite `pytest` passe avec 27 tests. Elle couvre notamment :

- baking/unbaking ;
- issuer ;
- QR ;
- configuration ;
- base SQLite ;
- API du constructeur.

### 3.4 Versions de dépendances fixées

`requirements.txt` utilise des versions exactes, ce qui améliore la reproductibilité.

### 3.5 Prise en compte partielle de la confidentialité

Le champ Open Badges `recipient.identity` est hashé avec salt. C'est une bonne pratique pour ne pas exposer directement l'email dans le champ standard.

## 4. Architecture et maintenabilité

### 4.1 Problème principal : `app/main.py` est trop volumineux

`app/main.py` contient environ 850 lignes et mélange :

- création FastAPI ;
- auth cookie ;
- pages HTML ;
- endpoints publics Open Badges ;
- endpoints admin ;
- téléchargement de fichiers ;
- recherche ;
- logique de dashboard ;
- vérification online ;
- helpers métier.

Impact :

- plus difficile à tester finement ;
- plus difficile à sécuriser par groupes d'endpoints ;
- risque accru de régression ;
- limites public/admin moins visibles.

Recommandation : découper en routers et services :

```text
app/
  main.py                    # création app + middleware + include_router
  security.py                # auth cookie, dependencies, policies
  services/
    badge_service.py
    verification_service.py
    dashboard_service.py
  repositories/
    assertion_repository.py
    template_repository.py
  routes/
    public_openbadges.py      # /issuers, /badges, /assertions, /assets
    public_verify.py          # /verify/qr, /verify/badge si public
    admin_badges.py           # /api/badges*
    issue.py                  # /issue, /issue-baked
    auth.py                   # /auth/*
    badge_constructor/
```

### 4.2 Modèles historiques dans `models.py`

Le README indique que `app/models.py` contient encore des modèles plus anciens, tandis que la structure réellement émise est dans `app/issuer.py`.

Risque : confusion entre modèles Open Badges imbriqués historiques et HostedBadge actuel basé sur URLs.

Recommandation :

- séparer les modèles actifs des modèles legacy ;
- documenter explicitement ce qui est utilisé en production ;
- supprimer ou déplacer les modèles obsolètes dans `legacy_models.py` si non nécessaires.

### 4.3 Couche base de données très procédurale

`database.py` fonctionne mais mélange :

- création de schéma ;
- registre assertions ;
- constructeur de badges ;
- sérialisation JSON ;
- accès SQLite direct.

Recommandation : introduire progressivement des repositories :

- `AssertionRepository` ;
- `BadgeSchemaRepository` ;
- `BadgeTemplateRepository`.

### 4.4 Absence de migrations

Les tables SQLite sont créées par `CREATE TABLE IF NOT EXISTS`, mais il n'y a pas de versionnement de schéma.

Risque : une évolution de colonne ou d'index en production devient fragile.

Recommandation : ajouter une table `schema_migrations` minimale ou utiliser Alembic si le projet grandit.

## 5. Sécurité

## 5.1 Synthèse des risques

| Priorité | Risque | Gravité | Fichiers concernés |
|---|---:|---:|---|
| P0 | Secrets présents dans le dépôt | Critique | `badge83/badge83.env` |
| P0 | Valeurs par défaut faibles | Critique | `app/config.py`, `badge83.sh` |
| P0 | Admin API non protégée côté FastAPI | Critique | `app/main.py`, `routes/badge_constructor/*` |
| P1 | PII en clair dans assertions et PNG | Élevée | `app/issuer.py`, `data/issued/*`, baked PNG |
| P1 | SSRF via `verify-online` | Élevée | `app/main.py`, `app/verifier.py` |
| P1 | Uploads sans limite de taille | Élevée | `app/main.py`, `templates.py` |
| P1 | Path traversal potentiel pour background image | Élevée | `routes/badge_constructor/templates.py` |
| P2 | CORS wildcard | Moyenne | `app/main.py` |
| P2 | Exceptions trop verbeuses | Moyenne | plusieurs routes |

### 5.2 Secrets dans le dépôt

La recherche a identifié `badge83/badge83.env` avec :

```text
BADGE83_AUTH_PASSWORD=...
BADGE83_AUTH_SECRET=...
```

Même si ce sont des secrets de test, ils doivent être considérés comme compromis dès lors qu'ils ont été versionnés.

Actions recommandées :

1. supprimer `badge83/badge83.env` du dépôt ;
2. ajouter `badge83/badge83.env` explicitement à `.gitignore` ;
3. régénérer tous les secrets ;
4. si le dépôt est public ou partagé, purger l'historique Git avec prudence ou invalider définitivement les secrets exposés.

### 5.3 Defaults dangereux

Dans `app/config.py` :

```python
DEFAULT_AUTH_USERNAME = "admin"
DEFAULT_AUTH_PASSWORD = "admin"
DEFAULT_AUTH_SECRET = "badge83-dev-auth-secret-change-me"
DEFAULT_SEARCH_PEPPER = "badge83-dev-search-pepper"
```

Dans `badge83.sh`, les mêmes valeurs existent.

Risque : démarrage accidentel en production avec mots de passe faibles.

Recommandation :

- en production, refuser le démarrage si `BADGE83_AUTH_PASSWORD`, `BADGE83_AUTH_SECRET` ou `BADGE83_SEARCH_PEPPER` sont absents ou égaux aux defaults ;
- introduire `BADGE83_ENV=production` ;
- générer des secrets longs aléatoires.

### 5.4 Authentification dépendante de Nginx uniquement

Le code contient `/auth/login` et `/auth/check` pour Nginx `auth_request`, mais les endpoints admin FastAPI eux-mêmes n'appliquent pas de dépendance d'autorisation.

Exemples sensibles :

- `POST /issue`
- `POST /issue-baked`
- `GET /api/badges`
- `GET /api/badges/search`
- `PUT /api/badges/{assertion_id}`
- `DELETE /api/badges/{assertion_id}`
- `/badge-constructor/*`

Si Uvicorn écoute sur `0.0.0.0` ou si le reverse proxy est mal configuré, ces endpoints peuvent devenir directement accessibles.

Recommandation P0 : ajouter une dépendance FastAPI de protection côté applicatif, par exemple :

```python
def require_admin(request: Request) -> None:
    if not _is_auth_cookie_valid(request):
        raise HTTPException(status_code=401, detail="Authentication required")
```

Puis l'appliquer à tous les routers admin. Garder Nginx comme défense supplémentaire, pas comme seule barrière.

### 5.5 Données personnelles dans `admin_recipient`

`issuer.py` ajoute :

```python
"admin_recipient": {
  "name": ...,
  "email": ...
}
```

Ce bloc est stocké dans :

- JSON sous `data/issued/` ;
- SQLite ;
- PNG baked via chunk `openbadges`.

Cela annule partiellement l'intérêt du recipient hashé : toute personne possédant le PNG baked peut extraire l'assertion et lire le nom/email.

Recommandations :

- distinguer assertion publique et métadonnées internes ;
- ne pas injecter `admin_recipient.email` dans le PNG public ;
- stocker les données admin uniquement en base locale protégée ;
- éventuellement garder un nom affichable si nécessaire, mais documenter clairement ce choix RGPD/privacy ;
- ajouter une option de minimisation : `BADGE83_EMBED_ADMIN_RECIPIENT=false`.

### 5.6 SSRF via `verify-online`

`POST /verify-online` accepte une `assertion_url` puis récupère des URLs via httpx. `deep_verify_baked_badge` peut aussi suivre les URLs contenues dans un PNG uploadé.

Risque : un utilisateur peut forcer le serveur à requêter :

- services internes ;
- metadata cloud ;
- localhost ;
- réseaux privés ;
- endpoints lents ou volumineux.

Recommandations :

- autoriser uniquement `https://` ;
- bloquer localhost, `127.0.0.0/8`, `10.0.0.0/8`, `172.16.0.0/12`, `192.168.0.0/16`, IPv6 local/link-local ;
- limiter redirects ;
- limiter taille de réponse ;
- ajouter allowlist optionnelle de domaines ;
- journaliser les refus.

### 5.7 Uploads sans limite

Les endpoints lisent les fichiers entièrement en mémoire :

```python
png_data = await badge.read()
content = await file.read()
```

Risque : DoS mémoire, stockage SQLite excessif via background base64, traitement Pillow coûteux.

Recommandations :

- limiter la taille via reverse proxy et côté FastAPI ;
- refuser les images > 2-5 MB selon besoin ;
- vérifier dimensions PNG avec Pillow avant traitement ;
- protéger contre decompression bombs : `PIL.Image.MAX_IMAGE_PIXELS` ;
- éviter de stocker de gros base64 en SQLite ; préférer un dossier contrôlé + nom généré.

### 5.8 Path traversal potentiel dans `_load_template_background`

Dans `routes/badge_constructor/templates.py` :

```python
content = BADGE_PNG.parent.joinpath(background_image).read_bytes()
```

Si `background_image` est contrôlable et n'est pas un `data:` URL, une valeur comme `../...` pourrait lire un fichier hors du dossier attendu.

Recommandation :

- interdire les chemins arbitraires ;
- stocker seulement des IDs/noms générés ;
- résoudre le chemin et vérifier qu'il reste sous un dossier autorisé :

```python
base = (BADGE_PNG.parent / "backgrounds").resolve()
candidate = (base / safe_name).resolve()
if not candidate.is_relative_to(base):
    raise HTTPException(status_code=400, detail="Invalid background path")
```

### 5.9 CORS wildcard

`allow_origins=["*"]` est configuré pour permettre aux validateurs externes de récupérer les ressources publiques. Le risque est limité car `allow_methods=["GET"]`, mais si des endpoints admin GET retournent de la donnée sensible et que l'auth repose sur cookies/proxy, cela peut faciliter l'exfiltration dans certains scénarios.

Recommandations :

- appliquer CORS uniquement aux endpoints publics Open Badges ;
- séparer sous-applications ou routers public/admin ;
- désactiver credentials CORS pour les endpoints admin.

## 6. Données, conformité et Open Badges

### 6.1 HostedBadge cohérent

Les assertions produites contiennent :

- `@context` ;
- `type: Assertion` ;
- `id`/`url` public ;
- `verification.type: HostedBadge` ;
- `badge` URL ;
- `issuer` URL ;
- recipient hashé.

C'est cohérent avec Open Badges 2.0 HostedBadge.

### 6.2 Points à améliorer

- Plusieurs anciennes assertions dans `data/issued` utilisent des URLs historiques HTTP, ports internes ou IP locale.
- Les templates `issuer_template.json` et `badgeclass_template.json` sont statiques : le paramètre `issuer_id`/`badge_slug` est ignoré.
- Il n'y a pas de signature cryptographique JWS/SignedBadge.
- La vérification locale accepte surtout l'existence et la structure minimale, pas une validation complète normative.

Recommandations :

- normaliser les anciennes assertions ou les marquer legacy ;
- retourner 404 si `issuer_id` ou `badge_slug` n'est pas reconnu ;
- ajouter une validation JSON-LD/Open Badges plus stricte ;
- planifier SignedBadge si l'intégrité forte devient un besoin.

## 7. Fiabilité et exploitation

### 7.1 Stockage fichiers + SQLite

Le design actuel utilise :

- JSON comme source canonique ;
- SQLite comme index admin ;
- PNG baked comme artefacts.

C'est simple, mais il faut gérer :

- atomicité JSON + SQLite + PNG ;
- concurrence d'écriture ;
- sauvegardes ;
- nettoyage des artefacts orphelins ;
- migrations.

Recommandations :

- écrire les fichiers de façon atomique (`tempfile` puis rename) ;
- définir une stratégie backup ;
- ajouter un job de cohérence JSON/SQLite/PNG ;
- centraliser les opérations dans un service transactionnel.

### 7.2 Script `badge83.sh`

Points positifs :

- script pratique pour start/stop/status/logs ;
- avertissement si host n'est pas localhost ;
- gestion optionnelle firewall.

Limites :

- chemins hardcodés `/home/ubuntu/projects/Mode83/...` ;
- defaults faibles ;
- pas de mode systemd/supervisor ;
- logs dans un fichier local sans rotation.

Recommandations :

- rendre `PROJECT_DIR` relatif au script ;
- ajouter checks production ;
- utiliser systemd, Docker ou supervisor ;
- ajouter rotation logs.

## 8. Qualité du code

### Points positifs

- Code globalement lisible.
- Type hints présents.
- Fonctions métier testables.
- Pydantic utilisé pour plusieurs payloads.
- SQL paramétré : faible risque d'injection SQL.

### Points à améliorer

- Beaucoup de `except Exception as e` exposent potentiellement des détails internes dans `detail=str(e)`.
- Duplications de dépendance DB `get_db()`.
- Mélange sync/async : plusieurs opérations fichiers/SQLite/Pillow bloquantes dans endpoints async.
- Pas de politique centralisée de validation des IDs.
- Pas de dépendance de sécurité standardisée par router.

## 9. Tests

### État actuel

Les tests passent : `27 passed`.

Couverture fonctionnelle observée :

- baking/unbaking ;
- issuer ;
- configuration ;
- QR ;
- database ;
- constructeur de badges.

### Tests à ajouter en priorité

| Priorité | Test recommandé |
|---|---|
| P0 | accès non authentifié aux endpoints admin refusé |
| P0 | production config refuse `admin/admin` et secrets par défaut |
| P1 | SSRF : localhost/private IP refusés dans `verify-online` |
| P1 | path traversal refusé pour `background_image` |
| P1 | uploads trop gros refusés |
| P1 | PNG decompression bomb refusé |
| P2 | anciennes assertions legacy gérées explicitement |
| P2 | cohérence JSON/SQLite/PNG après update/delete |

## 10. Roadmap recommandée

### P0 — À faire avant toute exposition production

1. Supprimer `badge83/badge83.env` du dépôt et régénérer les secrets.
2. Refuser les defaults `admin/admin` et secrets de dev en production.
3. Protéger les endpoints admin directement dans FastAPI.
4. S'assurer que Uvicorn écoute seulement `127.0.0.1` derrière Nginx, sauf architecture explicitement sécurisée.
5. Ajouter tests d'accès non authentifié.

### P1 — Sécurité et privacy

1. Corriger SSRF dans `verify-online` et deep verification.
2. Corriger path traversal pour background images.
3. Ajouter limites upload/taille/dimensions PNG.
4. Séparer données publiques et données admin privées.
5. Retirer ou rendre optionnel `admin_recipient.email` dans les assertions baked.

### P2 — Architecture et exploitation

1. Découper `main.py` en routers/services/repositories.
2. Introduire migrations SQLite.
3. Écritures atomiques et stratégie backup.
4. Logs structurés et rotation.
5. CI : lint + tests + audit dépendances.

### P3 — Conformité et confiance

1. Validation Open Badges plus stricte.
2. SignedBadge/JWS si besoin d'intégrité forte.
3. Normalisation/migration des anciennes assertions.
4. Documentation privacy/RGPD.

## 11. Verdict

Badge83 est un projet utile et déjà fonctionnel, avec une bonne base pour un outil interne de génération et vérification de badges. L'architecture actuelle convient à un MVP, mais doit être durcie avant une utilisation production publique.

La priorité absolue est la sécurité opérationnelle : secrets, authentification des endpoints admin, réduction des données personnelles exposées et protection contre SSRF/uploads/path traversal. Une fois ces points corrigés, le projet pourra évoluer vers une architecture plus maintenable avec routers/services/repositories et une exploitation plus robuste.
