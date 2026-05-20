# Rapport de travail — Badge83 — Hardening sécurité — 18/05/2026

Date : 18/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : sécurisation des accès administrateur, configuration production, uploads et nettoyage FastAPI

## 1. Objectif de la journée

L'objectif de la journée était de consolider Badge83 après la validation fonctionnelle du Projet A, en traitant les risques prioritaires identifiés dans l'audit architecture/sécurité.

Le travail a porté principalement sur :

1. la protection des endpoints administrateur côté FastAPI ;
2. le refus des secrets faibles en environnement production ;
3. la correction du risque de path traversal sur les images de fond ;
4. l'ajout de limites configurables sur les uploads ;
5. le remplacement de l'ancien hook FastAPI `@app.on_event("startup")` par `lifespan`.

## 2. État initial

Au début de la journée, Badge83 était fonctionnel et les tests passaient :

```text
36 passed in 1.45s
```

Le projet disposait déjà du socle suivant :

- émission d'assertions Open Badges ;
- génération de PNG baked ;
- QR code de vérification ;
- registre SQLite local ;
- constructeur de badges ;
- émission groupée CSV avec preview/commit/archive.

Les risques restants concernaient surtout le durcissement avant exposition plus large.

## 3. Travaux réalisés

### 3.1 Protection des endpoints administrateur

Une dépendance `require_admin` a été ajoutée dans `app/main.py`.

Elle vérifie le cookie d'authentification Badge83 et refuse les appels non autorisés :

```python
def require_admin(request: Request) -> None:
    if not _is_auth_cookie_valid(request):
        raise HTTPException(status_code=401, detail="Authentication required")
```

Les routes administrateur sont désormais protégées côté application, même si le reverse proxy est mal configuré.

Routes concernées notamment :

- `/` ;
- `/issue` ;
- `/issue-baked` ;
- `/api/badges*` ;
- `/api/dashboard/stats` ;
- `/verify-desk` ;
- `/badge-constructor/*`.

Les routes publiques restent accessibles :

- `/verify/*` ;
- `/verify-baked` ;
- `/verify-online` ;
- `/issuers/*` ;
- `/badges/*` ;
- `/assertions/*` ;
- `/assets/*` ;
- `/auth/*`.

### 3.2 Production guard

Un mode production a été ajouté :

```text
BADGE83_ENV=production
```

ou :

```text
BADGE83_ENV=prod
```

En production, l'application refuse les valeurs faibles par défaut :

- `BADGE83_AUTH_PASSWORD=admin` ;
- `BADGE83_AUTH_SECRET=badge83-dev-auth-secret-change-me` ;
- `BADGE83_SEARCH_PEPPER=badge83-dev-search-pepper`.

Ce contrôle est exécuté au démarrage de l'application.

### 3.3 Sécurisation des images de fond

Le chargement des fonds de badge a été durci dans :

```text
badge83/app/routes/badge_constructor/templates.py
```

Le code n'accepte plus les chemins arbitraires. Les fonds autorisés sont :

1. le PNG par défaut si aucun fond n'est fourni ;
2. un `data:image/png;base64,...` valide ;
3. un nom de fichier situé dans le dossier autorisé :

```text
badge83/data/backgrounds/
```

Les tentatives de type `../...`, chemins absolus ou chemins avec séparateurs sont rejetées.

### 3.4 Upload safety configurable

Un module dédié a été ajouté :

```text
badge83/app/upload_limits.py
```

Il fournit :

- `read_upload_limited(...)` ;
- `ensure_image_pixels_within_limit(...)`.

Les limites sont configurables via variables d'environnement :

```text
BADGE83_MAX_PNG_UPLOAD_BYTES
BADGE83_MAX_CSV_UPLOAD_BYTES
BADGE83_MAX_IMAGE_PIXELS
```

Valeurs par défaut :

```text
PNG : 50 MB
CSV : 10 MB
Image : 50 mégapixels
```

Ces valeurs sont volontairement larges pour ne pas bloquer les usages réels déjà observés, notamment les grands PNG correspondant à des feuilles de présence ou documents hebdomadaires.

### 3.5 Migration FastAPI lifespan

L'ancien hook :

```python
@app.on_event("startup")
```

a été remplacé par un `lifespan` FastAPI moderne.

Cela supprime les avertissements de dépréciation affichés pendant les tests.

## 4. Tests ajoutés ou complétés

Nouveaux tests ou compléments :

- accès admin sans authentification ;
- maintien des routes publiques ;
- refus des secrets faibles en production ;
- override des limites d'upload ;
- rejet des CSV/PNG trop volumineux avec seuil de test volontairement bas ;
- rejet des chemins de fond invalides ;
- acceptation des fonds PNG en data URL ;
- tests unitaires du helper d'upload limité.

## 5. Résultat de validation

Commande exécutée :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat final :

```text
54 passed in 1.75s
```

Les avertissements FastAPI liés à `@app.on_event("startup")` ne sont plus présents.

## 6. Fichiers principaux modifiés ou ajoutés

Fichiers applicatifs :

- `badge83/app/main.py` ;
- `badge83/app/config.py` ;
- `badge83/app/upload_limits.py` ;
- `badge83/app/routes/badge_constructor/templates.py`.

Tests :

- `badge83/tests/unit/test_admin_auth.py` ;
- `badge83/tests/unit/test_upload_limits.py` ;
- `badge83/tests/unit/test_config.py` ;
- `badge83/tests/unit/test_badge_constructor_api.py`.

Documentation :

- `badge83/docs/plan-travail-semaine-180526.md` ;
- `badge83/docs/rapport-travail-180526-hardening-securite.md`.

## 7. Points restants

Les prochains sujets recommandés sont :

1. traiter le risque SSRF sur `verify-online` ;
2. clarifier la politique de données personnelles dans les assertions baked ;
3. documenter les variables d'environnement ajoutées dans README / fichier `.env.example` ;
4. envisager une CI minimale pour lancer automatiquement les tests.

## 8. Conclusion

La journée a permis de transformer Badge83 d'un MVP fonctionnel vers un outil interne plus robuste.

Les deux points P0 principaux de l'audit sont désormais traités :

- protection applicative des routes administrateur ;
- refus des secrets faibles en production.

Deux points P1 ont également été avancés :

- protection contre le path traversal ;
- limites d'upload configurables et adaptées aux grands PNG métier.

État final :

```text
Tests OK — 54 passed
Warnings FastAPI on_event supprimés
Hardening sécurité engagé
```