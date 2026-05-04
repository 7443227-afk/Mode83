# Tests du constructeur de badges — 04/05/2026

## Objectif

Ce document décrit les tests ajoutés pour sécuriser les évolutions récentes du constructeur de badges Badge83.

Les changements testés concernent principalement :

- la modification d'un modèle existant ;
- la prévisualisation d'un brouillon avec textes statiques et dynamiques ;
- la gestion d'erreur lorsqu'un modèle n'existe pas ;
- l'émission d'un PNG baked depuis un modèle modifié.

## Fichier de test concerné

Les tests sont regroupés dans :

```text
badge83/tests/unit/test_badge_constructor_api.py
```

Ce fichier utilise `FastAPI TestClient` avec le routeur du constructeur :

```python
from app.routes.badge_constructor import router as badge_constructor_router
```

Chaque test utilise une base SQLite temporaire via `BADGE83_REGISTRY_DB`, afin de ne pas modifier la base réelle du projet.

## Tests ajoutés

### 1. Modification d'un modèle existant

Test :

```text
test_update_badge_template_via_api_persists_changes
```

Ce test vérifie le scénario suivant :

1. création d'un schéma ;
2. création d'un modèle initial ;
3. modification du modèle via :

```text
PUT /badge-constructor/templates/{template_id}
```

4. relecture du modèle via :

```text
GET /badge-constructor/templates/{template_id}
```

5. vérification que les données modifiées sont bien persistées :
   - nom du modèle ;
   - schéma associé ;
   - placement du QR code ;
   - taille du QR code ;
   - texte superposé dynamique.

### 2. Prévisualisation d'un brouillon avec textes statiques et dynamiques

Test :

```text
test_preview_draft_returns_png_for_static_and_dynamic_overlays
```

Ce test vérifie que l'endpoint :

```text
POST /badge-constructor/templates/preview-draft
```

retourne bien un PNG valide lorsque le brouillon contient :

- un texte statique ;
- un texte dynamique lié à un champ (`course_name`) ;
- un QR code configuré.

Les vérifications principales sont :

- statut HTTP `200` ;
- en-tête `content-type: image/png` ;
- signature binaire PNG valide.

### 3. Erreur sur modification d'un modèle inexistant

Test :

```text
test_update_unknown_badge_template_returns_404
```

Ce test vérifie que la modification d'un modèle inexistant retourne une erreur contrôlée :

```text
PUT /badge-constructor/templates/unknown-template
```

Résultat attendu :

```text
HTTP 404 — Modèle introuvable
```

Ce test protège le comportement d'erreur de l'API.

### 4. Émission d'un PNG baked depuis un modèle modifié

Test :

```text
test_updated_badge_template_can_issue_baked_png
```

Ce test couvre un workflow plus complet :

1. création d'un schéma ;
2. création d'un modèle ;
3. modification du modèle via `PUT` ;
4. émission d'un PNG baked avec :

```text
POST /badge-constructor/templates/{template_id}/issue-baked
```

5. extraction de l'assertion depuis le PNG avec `unbake_badge` ;
6. vérification que l'assertion contient :
   - les informations du modèle modifié dans `badge83_template` ;
   - les valeurs saisies dans `field_values` ;
   - un identifiant public cohérent ;
7. vérification que le JSON et le PNG sont sauvegardés dans les répertoires isolés du test.

Ce test sécurise le flux principal :

```text
créer un modèle → le modifier → émettre un badge depuis ce modèle → vérifier le PNG baked
```

## Commandes de vérification

Exécuter uniquement les tests du constructeur :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests/unit/test_badge_constructor_api.py -q
```

Résultat attendu :

```text
4 passed
```

Exécuter toute la suite de tests :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat actuel :

```text
21 passed
```

## Limites actuelles

Ces tests couvrent principalement l'API et la génération PNG côté backend.

Ils ne remplacent pas une vérification manuelle dans le navigateur pour confirmer :

- le comportement du bouton `Modifier` dans la liste des modèles ;
- le chargement correct du formulaire ;
- l'édition visuelle d'un texte superposé ;
- l'affichage de l'aperçu dans l'interface ;
- le confort d'utilisation pour un opérateur non technique.

Une prochaine étape pourrait consister à ajouter des tests end-to-end d'interface avec un outil navigateur, mais ce n'est pas encore nécessaire pour le socle actuel.
