# Plan de travail Badge83 — semaine du 18/05/2026

Date de préparation : 18/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : état du projet, priorités du jour et plan de travail hebdomadaire

## 1. État du projet au 18/05/2026

Badge83 est aujourd'hui dans un état solide pour un **MVP avancé / outil interne MODE83**.

État constaté le 18/05/2026 :

```text
Git : espace de travail propre
Dernier commit observé : 73d15b7 13/05
Serveur Badge83 : arrêté au moment du contrôle
URL de base configurée : https://mode83.ddns.net
Tests automatisés au début de journée : 36 passed in 1.45s
Tests automatisés après hardening sécurité : 54 passed in 1.75s
```

Le Projet A — Open Badges MODE83 — peut être considéré comme fonctionnellement validé pour un usage MVP : émission, assertion JSON, PNG baked, QR code, vérification, registre local et constructeur de badges sont en place.

Depuis les rapports de validation précédents, le projet a aussi progressé sur l'**émission groupée CSV** : le code contient désormais un module dédié `app/batch_issuer.py`, des endpoints de preview/commit/archive et des tests unitaires associés.

## 2. Fonctionnalités actuellement disponibles

### 2.1 Socle Open Badges

- émission d'assertions JSON Open Badges ;
- génération de PNG baked avec chunk `openbadges` ;
- QR code visible sur le badge ;
- vérification par ID, page publique, QR et upload PNG ;
- endpoints HostedBadge publics ;
- stockage JSON/PNG et index SQLite local ;
- registre de consultation/recherche.

### 2.2 Constructeur de badges

- création de schémas de champs ;
- création et modification de modèles visuels ;
- textes dynamiques ;
- placement configurable du QR code ;
- prévisualisation ;
- émission depuis un template.

### 2.3 Émission groupée CSV

Fonctionnalités observées :

- parsing CSV ;
- normalisation des colonnes ;
- interprétation des valeurs de réussite (`oui`, `yes`, `passed`, etc.) ;
- classification des lignes : `ready`, `not_passed`, `duplicate`, `error` ;
- détection des doublons par template + email ;
- endpoint de prévisualisation sans émission ;
- endpoint de commit ;
- endpoint d'archive ZIP avec PNG et rapport CSV ;
- tests dédiés dans `tests/unit/test_batch_issuer.py`.

Limite actuelle : le support XLSX est documenté, mais `app/batch_issuer.py` supporte encore uniquement CSV.

## 3. Risques prioritaires

Le projet est fonctionnel, mais il ne doit pas encore être considéré comme production-ready sans durcissement.

### P0 — Avant exposition publique production

1. ~~Protéger les endpoints administrateur directement côté FastAPI.~~ Réalisé le 18/05/2026.
2. ~~Refuser les valeurs par défaut faibles en mode production (`admin/admin`, secrets de développement, pepper de recherche par défaut).~~ Réalisé le 18/05/2026.
3. Vérifier que Uvicorn n'est pas exposé directement sans reverse proxy sécurisé.
4. ~~Ajouter des tests d'accès non authentifié aux endpoints sensibles.~~ Réalisé le 18/05/2026.

### P1 — Sécurité et confidentialité

1. ~~Corriger le risque de path traversal sur les images de fond de templates.~~ Réalisé le 18/05/2026.
2. ~~Ajouter des limites de taille sur les uploads PNG/CSV.~~ Réalisé le 18/05/2026 avec des limites configurables larges pour ne pas bloquer les grands PNG métier.
3. Réduire ou rendre configurable l'inclusion de `admin_recipient.email` dans les assertions baked.
4. Durcir la vérification en ligne contre les risques SSRF.
5. Documenter clairement les règles privacy/RGPD.

### P2 — Maintenabilité et exploitation

1. Découper progressivement `app/main.py` en routers/services.
2. Introduire une stratégie de migrations SQLite.
3. Ajouter une stratégie backup/cohérence JSON + SQLite + PNG.
4. Mettre en place une CI minimale : tests + lint + audit dépendances.
5. ~~Remplacer `@app.on_event("startup")` par le mécanisme FastAPI `lifespan`.~~ Réalisé le 18/05/2026.

## 3.1 Bilan des travaux réalisés le 18/05/2026

Les travaux du 18/05 ont permis de traiter plusieurs points importants de l'audit sécurité et de nettoyer la compatibilité FastAPI.

### Sécurité applicative P0

- ajout d'une dépendance `require_admin` dans `app/main.py` ;
- protection directe côté FastAPI des routes administrateur ;
- protection du routeur `/badge-constructor/*`, incluant émission groupée CSV et émission depuis template ;
- ajout de tests vérifiant que les routes admin refusent les appels sans cookie ;
- maintien de l'accès public aux routes de vérification et aux endpoints Open Badges.

### Configuration production P0

- ajout de `BADGE83_ENV=production` / `prod` ;
- refus du démarrage en production si les valeurs faibles par défaut sont utilisées :
  - `BADGE83_AUTH_PASSWORD=admin` ;
  - secret d'authentification de développement ;
  - pepper de recherche de développement ;
- ajout de tests de configuration associés.

### Durcissement P1

- sécurisation du chargement des images de fond du constructeur ;
- interdiction des chemins `../`, chemins absolus et chemins contenant des séparateurs ;
- introduction d'un dossier autorisé `data/backgrounds` pour les fonds nommés ;
- maintien du support `data:image/png;base64,...` ;
- ajout de tests contre le path traversal.

### Upload safety configurable

- ajout d'un module `app/upload_limits.py` ;
- ajout de limites configurables par environnement :
  - `BADGE83_MAX_PNG_UPLOAD_BYTES` ;
  - `BADGE83_MAX_CSV_UPLOAD_BYTES` ;
  - `BADGE83_MAX_IMAGE_PIXELS` ;
- choix de valeurs par défaut volontairement larges pour ne pas bloquer les grands PNG métier, notamment les feuilles de présence ou attestations hebdomadaires ;
- ajout de tests avec override de petits seuils pour vérifier le mécanisme sans pénaliser l'usage réel.

### Nettoyage FastAPI

- remplacement de `@app.on_event("startup")`, désormais déprécié, par un `lifespan` FastAPI ;
- suppression des warnings de tests liés à `on_event`.

### Résultat de validation

```text
54 passed in 1.75s
```

Les avertissements FastAPI liés à `on_event` ont disparu après migration vers `lifespan`.

## 4. Objectif principal de la semaine

**Transformer Badge83 d'un MVP fonctionnel en outil interne plus sûr, documenté et démontrable.**

Critères de réussite de la semaine :

1. les tests automatisés passent toujours ;
2. les endpoints admin critiques sont protégés côté FastAPI ;
3. les defaults dangereux sont refusés en mode production ;
4. les principaux risques upload/path traversal sont réduits ;
5. l'émission groupée CSV est validée par un scénario complet ;
6. la documentation reflète l'état réel du projet ;
7. une démonstration complète peut être faite en fin de semaine.

## 5. Plan pour aujourd'hui — lundi 18/05/2026

### Priorité 1 — Baseline technique

Commandes :

```bash
cd /home/ubuntu/projects/Mode83/badge83
./badge83.sh status
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat attendu : confirmer l'état actuel, avec tests en succès.

### Priorité 2 — Protection FastAPI des routes admin

Ajouter une dépendance d'autorisation applicative, par exemple :

```python
def require_admin(request: Request) -> None:
    if not _is_auth_cookie_valid(request):
        raise HTTPException(status_code=401, detail="Authentication required")
```

Routes à protéger en priorité :

- `/issue` ;
- `/issue-baked` ;
- `/api/badges*` ;
- `/badge-constructor/*` ;
- endpoints d'émission groupée.

Routes à conserver publiques :

- `/verify/*` ;
- `/verify/badge/*` ;
- `/verify/qr/*` ;
- `/issuers/*` ;
- `/badges/*` ;
- `/assertions/*` ;
- `/assets/*` ;
- `/auth/*`.

Critère de réussite : un appel non authentifié à une route admin reçoit `401`, tandis que les routes publiques de vérification restent accessibles.

### Priorité 3 — Production guard

Ajouter un comportement explicite pour `BADGE83_ENV=production` :

- refuser `BADGE83_AUTH_PASSWORD=admin` ;
- refuser le secret de développement ;
- refuser le pepper de recherche par défaut.

Critère de réussite : les tests de configuration couvrent le cas production avec defaults faibles.

### Priorité 4 — Tests sécurité minimaux

Ajouter ou compléter les tests suivants :

- endpoint admin sans cookie → `401` ;
- endpoint public de vérification toujours accessible ;
- configuration production refuse les secrets faibles.

### Priorité 5 — Documentation

Mettre à jour les documents de référence si des changements sont appliqués :

- README ;
- rapport de travail de la semaine ;
- documentation opérateur CSV si nécessaire.

## 6. Plan de la semaine

### Lundi 18/05 — Security baseline et planification

Objectif : sécuriser les accès admin et fixer la trajectoire de la semaine.

Actions :

1. confirmer l'état Git, serveur et tests ;
2. protéger les routes admin côté FastAPI ;
3. ajouter production guard ;
4. ajouter tests de sécurité de base ;
5. créer le présent plan hebdomadaire.

Livrable attendu :

```text
badge83/docs/plan-travail-semaine-180526.md
```

### Mardi 19/05 — Privacy, uploads et path traversal

Objectif : réduire les principaux risques P1.

Actions :

1. sécuriser le chargement des images de fond ;
2. ajouter des limites de taille pour PNG/background/CSV ;
3. ajouter des garde-fous Pillow (`MAX_IMAGE_PIXELS`, dimensions maximales) ;
4. décider du comportement de `admin_recipient` en production ;
5. ajouter tests path traversal et fichiers trop volumineux.

Livrable attendu : court rapport de hardening sécurité.

### Mercredi 20/05 — Stabilisation émission groupée CSV

Objectif : rendre l'émission groupée CSV démontrable par un opérateur.

Actions :

1. valider le flux complet : upload CSV → preview → commit → archive ZIP ;
2. tester le réimport du même fichier sans doublons ;
3. préparer un fichier CSV exemple ;
4. documenter le format attendu ;
5. compléter les tests API batch si nécessaire.

Livrable attendu : documentation opérateur CSV + exemple de fichier.

### Jeudi 21/05 — UX opérateur ou XLSX

Deux options selon le besoin prioritaire.

#### Option A — Priorité Excel

1. ajouter `openpyxl` ;
2. implémenter le parsing XLSX ;
3. ajouter tests XLSX ;
4. documenter les limites du support Excel.

#### Option B — Priorité démonstration / opérateur

1. améliorer l'affichage de preview batch ;
2. rendre les erreurs plus lisibles ;
3. masquer le JSON technique derrière une zone dédiée ;
4. améliorer le rapport final.

Recommandation : choisir l'option B si une démonstration utilisateur est prévue rapidement ; choisir l'option A si les opérateurs disposent principalement de fichiers Excel.

### Vendredi 22/05 — Validation finale et décision suite

Objectif : produire un état démontrable et décider de la suite.

Actions :

1. relancer toute la suite de tests ;
2. exécuter un parcours de démonstration complet ;
3. vérifier les logs ;
4. rédiger un rapport hebdomadaire ;
5. décider entre trois suites possibles :
   - continuer le hardening production ;
   - finaliser XLSX/UX batch ;
   - démarrer Projet B blockchain comme PoC séparé.

Livrable attendu :

```text
badge83/docs/rapport-travail-semaine-180526.md
```

## 7. Démonstration recommandée en fin de semaine

Parcours à montrer :

1. ouvrir l'interface Badge83 ;
2. émettre un badge individuel ;
3. télécharger le PNG baked ;
4. vérifier le QR code ;
5. vérifier le PNG par upload ;
6. consulter le registre ;
7. importer un CSV ;
8. afficher la preview ;
9. confirmer l'émission groupée ;
10. télécharger l'archive ZIP ;
11. relancer le même CSV pour prouver l'absence de doublons.

## 8. Décision recommandée

La priorité de la semaine doit rester :

```text
sécurité applicative → stabilisation batch CSV → documentation → démonstration
```

Il est préférable de ne pas démarrer l'intégration blockchain complète cette semaine. Si le Projet B doit commencer, il devrait être traité comme un PoC séparé, limité à :

- calcul d'un hash d'assertion ;
- smart contract minimal sur testnet ;
- stockage on-chain du hash uniquement ;
- aucune donnée personnelle on-chain.

## 9. Conclusion

Badge83 est fonctionnel et dispose désormais d'un socle plus riche que le Projet A initial, notamment grâce au constructeur de badges et à l'émission groupée CSV.

Le principal enjeu n'est plus d'ajouter rapidement de nouvelles fonctionnalités, mais de **sécuriser, documenter et fiabiliser** ce qui existe déjà afin de pouvoir présenter un outil MODE83 crédible, démontrable et exploitable en interne.