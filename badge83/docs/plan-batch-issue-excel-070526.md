# Plan de travail — Émission groupée de badges depuis Excel/CSV — 07/05/2026

## 1. Contexte

Badge83 permet déjà d'émettre un badge individuellement depuis l'interface d'administration ou depuis un modèle visuel du constructeur.

Le besoin étudié ici est d'ajouter une fonctionnalité d'**émission groupée** : un opérateur téléverse un fichier Excel ou CSV contenant une liste de participants, Badge83 analyse les lignes, ignore les personnes non admises ou déjà traitées, puis génère automatiquement les badges pour les nouveaux bénéficiaires.

Cette fonctionnalité transformerait Badge83 d'un outil de génération unitaire en outil réellement exploitable pour des promotions ou des sessions de formation complètes.

## 2. Objectif fonctionnel

Permettre à un opérateur de fournir un fichier structuré contenant :

- les informations des bénéficiaires ;
- les champs pédagogiques ou administratifs du badge ;
- l'indication de réussite de la formation ;
- éventuellement la date ou le numéro de certificat.

À partir de ce fichier, Badge83 doit :

1. identifier la formation ou le programme ;
2. vérifier quelles lignes sont éligibles à l'émission ;
3. ignorer les lignes non réussies ;
4. ignorer les personnes déjà badgeées pour le même programme ;
5. générer les numéros de certificat manquants ;
6. générer les dates d'émission manquantes ;
7. émettre les assertions Open Badges et les PNG baked ;
8. produire un rapport lisible de l'opération.

## 3. Positionnement par rapport au noyau actuel

La première version doit rester prudente et respecter la stratégie actuelle du projet :

- ne pas modifier inutilement le format Open Badges ;
- ne pas casser les routes de vérification existantes ;
- réutiliser le constructeur de badges et les templates visuels ;
- conserver les détails techniques disponibles, mais rendre le parcours opérateur simple.

La fonctionnalité doit donc être construite comme une couche d'orchestration au-dessus des mécanismes existants, notamment :

- `issue_baked_badge_from_template(...)` dans `badge83/app/issuer.py` ;
- les schémas `badge_schemas` ;
- les modèles `badge_templates` ;
- les champs `field_values` sauvegardés dans l'assertion ;
- les métadonnées `badge83_template` ;
- l'autogénération actuelle des numéros de certificat côté constructeur.

## 4. Format attendu du fichier

### 4.1 Formats acceptés

Version MVP :

- `.csv` ;
- `.xlsx` avec la dépendance `openpyxl`.

Le CSV peut être supporté avec la bibliothèque standard Python. Le XLSX nécessite l'ajout de :

```text
openpyxl
```

dans `badge83/requirements.txt`.

### 4.2 Colonnes minimales

Le fichier doit contenir au minimum :

| Colonne | Rôle | Obligatoire |
|---|---|---|
| `name` ou `nom` | nom complet du bénéficiaire | oui |
| `email` | email du bénéficiaire | oui |
| `programme` ou `program` | programme / formation / promotion | oui |
| `reussi` | indique si la personne a réussi | oui |

### 4.3 Colonnes optionnelles utiles

| Colonne | Exemple | Utilisation |
|---|---|---|
| `organisation` | MODE83 | champ dynamique du modèle |
| `adresse` | Toulon | champ dynamique du modèle |
| `course_name` | Blockchain Foundations | champ dynamique du modèle |
| `certificate_number` | BF-2026-001 | numéro manuel si fourni |
| `issue_date` | 2026-05-07 | date d'émission si fournie |

Toutes les colonnes non réservées peuvent être copiées dans `field_values` afin d'être utilisées par les textes dynamiques du modèle.

## 5. Règles métier

### 5.1 Interprétation de `reussi`

Une ligne est éligible si la valeur de `reussi` correspond à une valeur positive.

Valeurs positives proposées :

```text
oui, yes, true, 1, reussi, réussi, passed, validé, valide
```

Valeurs négatives proposées :

```text
non, no, false, 0, échoué, echec, failed, absent, vide
```

Si la valeur est ambiguë, la ligne doit être placée en erreur ou en avertissement dans le rapport de prévisualisation.

### 5.2 Nom et email

Le nom et l'email restent les deux champs administratifs minimaux.

Règles :

- trim des espaces ;
- email normalisé en minuscules ;
- ligne en erreur si email invalide ;
- ligne en erreur si nom vide.

### 5.3 Date d'émission

Si `issue_date` est fourni, l'utiliser dans `field_values`.

Si `issue_date` est absent, générer la date du jour.

Remarque : dans le noyau actuel, `issuedOn` est généré automatiquement par `issue_baked_badge_from_template(...)`. Le champ `issue_date` est donc d'abord un champ visuel/opérateur. Une évolution ultérieure pourrait permettre de contrôler explicitement `issuedOn`.

### 5.4 Numéro de certificat

Si `certificate_number` est fourni :

- vérifier qu'il n'existe pas déjà pour le template ;
- sinon, marquer la ligne comme doublon ou erreur selon la stratégie choisie.

Si `certificate_number` est absent :

- utiliser la logique existante de génération automatique ;
- conserver le préfixe et le padding si des numéros existent déjà.

### 5.5 Déduplication

Le comportement demandé est : si le même fichier est fourni à nouveau pour la même formation, les badges déjà émis doivent être ignorés et seuls les nouveaux bénéficiaires doivent être créés.

Clé de déduplication MVP :

```text
template_id + normalized_email
```

Processus :

1. parcourir les assertions existantes dans `data/issued` ou dans le registre SQLite ;
2. lire `badge83_template.id` ;
3. lire `admin_recipient.email` ;
4. si le couple existe déjà, ignorer la ligne ;
5. sinon, émettre le badge.

Une version future pourra utiliser une clé plus riche :

```text
programme_slug + normalized_email + badgeclass_version
```

## 6. Image de fond dans Excel

Le besoin mentionne la possibilité d'une cellule avec une image pour la base du badge.

Pour le MVP, ce point doit être exclu.

Raisons :

- les images embarquées dans Excel sont plus complexes à extraire proprement ;
- la relation entre image et ligne n'est pas toujours évidente ;
- Badge83 possède déjà un mécanisme de `background_image` dans les templates ;
- il est plus fiable de choisir ou préparer le modèle visuel dans le constructeur avant l'import.

Décision MVP :

- l'Excel/CSV contient les données ;
- le modèle visuel est choisi dans Badge83 ;
- l'image de fond reste gérée par le constructeur.

Évolution possible : ajouter un onglet `_badge83_config` dans le fichier avec une référence au template ou à une image encodée.

## 7. Architecture proposée

### 7.1 Nouveau module métier

Créer :

```text
badge83/app/batch_issuer.py
```

Responsabilités :

- parser CSV/XLSX ;
- normaliser les noms de colonnes ;
- identifier les lignes éligibles ;
- détecter les erreurs ;
- détecter les doublons ;
- préparer un rapport de preview ;
- exécuter l'émission réelle en mode commit.

Fonctions envisagées :

```python
def parse_batch_file(file_bytes: bytes, filename: str) -> list[dict]:
    ...

def normalize_batch_row(row: dict) -> dict:
    ...

def is_passed(value: object) -> bool | None:
    ...

def find_existing_badge_for_template(template_id: str, email: str) -> dict | None:
    ...

def preview_batch_issue(template: dict, rows: list[dict]) -> dict:
    ...

def commit_batch_issue(template: dict, rows: list[dict]) -> dict:
    ...
```

### 7.2 Routes API

Créer un router dédié ou ajouter au routeur du constructeur.

Option recommandée MVP :

```text
POST /badge-constructor/templates/{template_id}/batch-issue/preview
POST /badge-constructor/templates/{template_id}/batch-issue
```

Le fichier est envoyé en `multipart/form-data`.

Le `preview` ne crée aucun badge.

Le `commit` crée effectivement les badges pour les lignes valides et non dupliquées.

### 7.3 Résultat de preview

Exemple :

```json
{
  "template_id": "...",
  "total_rows": 25,
  "eligible_rows": 18,
  "skipped_not_passed": 4,
  "skipped_duplicates": 2,
  "errors": 1,
  "rows": [
    {
      "row_number": 2,
      "status": "ready",
      "name": "Alice Example",
      "email": "alice@example.org",
      "field_values": {
        "programme": "Blockchain Foundations",
        "organisation": "MODE83"
      }
    }
  ]
}
```

### 7.4 Résultat de commit

Exemple :

```json
{
  "created": 18,
  "skipped_not_passed": 4,
  "skipped_duplicates": 2,
  "errors": 1,
  "created_badges": [
    {
      "name": "Alice Example",
      "email": "alice@example.org",
      "assertion_id": "...",
      "certificate_number": "BF-2026-001",
      "png_url": "/api/badges/.../png",
      "verification_url": "/verify/badge/...",
      "qr_url": "/verify/qr/..."
    }
  ]
}
```

## 8. Interface opérateur

Ajouter une zone dans le centre d'administration, probablement dans `Émission de badge` ou dans `Constructeur de badge`.

Parcours recommandé :

1. choisir un modèle existant ;
2. téléverser un fichier CSV/XLSX ;
3. cliquer sur `Analyser le fichier` ;
4. afficher un résumé avant émission ;
5. afficher les lignes prêtes, ignorées ou en erreur ;
6. cliquer sur `Émettre les badges` ;
7. afficher le rapport final.

Éléments UX importants :

- ne pas émettre immédiatement après upload ;
- toujours passer par une prévisualisation ;
- afficher clairement les doublons ;
- afficher clairement les personnes non admises ;
- conserver un détail technique téléchargeable pour diagnostic.

## 9. BadgeClass dynamique par programme

Le besoin évoque la génération d'un nouveau classe de badges à partir du fichier.

Il faut distinguer deux niveaux.

### 9.1 Niveau MVP

Dans le MVP, le “classe de badges” peut être représenté par le couple :

```text
schema + template
```

Cela suffit pour l'usage opérateur : chaque programme a ses champs, son modèle visuel, ses numéros et son historique.

### 9.2 Niveau Open Badges complet

Dans une évolution ultérieure, il serait plus conforme Open Badges de créer un vrai `BadgeClass` par programme :

```text
/badges/{programme_slug}
```

Chaque assertion devrait alors référencer :

```json
"badge": "https://mode83.ddns.net/badges/blockchain-foundations-2026"
```

Cette évolution nécessite :

- une table ou un stockage des BadgeClass dynamiques ;
- une route publique `/badges/{slug}` ;
- l'adaptation de `issue_baked_badge_from_template(...)` pour recevoir le BadgeClass ciblé ;
- des tests de vérification HostedBadge complets.

Décision recommandée : reporter cette partie après le MVP.

## 10. Phases de réalisation

### Phase 1 — Préparation technique

- Ajouter `openpyxl` aux dépendances.
- Créer `app/batch_issuer.py`.
- Écrire les fonctions de parsing CSV/XLSX.
- Normaliser les colonnes.
- Ajouter les tests unitaires de parsing.

### Phase 2 — Preview sans émission

- Ajouter endpoint `batch-issue/preview`.
- Vérifier les colonnes obligatoires.
- Classer les lignes : `ready`, `not_passed`, `duplicate`, `error`.
- Retourner un rapport JSON.

### Phase 3 — Commit réel

- Ajouter endpoint `batch-issue`.
- Réutiliser `issue_baked_badge_from_template(...)`.
- Générer `certificate_number` si absent.
- Générer `issue_date` si absent.
- Ignorer les doublons.
- Retourner les liens des badges créés.

### Phase 4 — Interface opérateur

- Ajouter upload CSV/XLSX dans `templates/index.html`.
- Ajouter prévisualisation lisible.
- Ajouter bouton de confirmation.
- Afficher rapport final.

### Phase 5 — Export et documentation

- Prévoir l'export ZIP des PNG créés.
- Prévoir l'export CSV du rapport.
- Documenter le format du fichier attendu.
- Ajouter un exemple de fichier CSV.

## 11. Tests nécessaires

### Tests unitaires

- parsing CSV ;
- parsing XLSX ;
- normalisation de colonnes `nom/name`, `programme/program` ;
- interprétation de `reussi` ;
- détection email invalide ;
- génération de `field_values` ;
- déduplication par `template_id + email`.

### Tests API

- preview avec fichier valide ;
- preview avec colonnes manquantes ;
- commit avec lignes prêtes ;
- commit avec doublons ;
- commit répété du même fichier ;
- vérification que les PNG et JSON sont créés.

### Critère de réussite MVP

Avec un fichier de 10 lignes :

- 6 lignes `reussi = oui` ;
- 2 lignes `reussi = non` ;
- 1 ligne email invalide ;
- 1 ligne déjà émise ;

Badge83 doit produire :

- 5 nouveaux badges ;
- 2 lignes ignorées car non réussies ;
- 1 erreur email ;
- 1 doublon ignoré ;
- un rapport clair ;
- `pytest` complet en succès.

Une seconde importation du même fichier doit produire :

- 0 nouveau badge ;
- toutes les lignes déjà émises classées comme doublons ;
- aucune régression du registre.

## 12. Risques et points d'attention

- **Données personnelles** : le fichier contient probablement noms, emails et informations administratives ; limiter les logs bruts.
- **Idempotence** : l'import doit pouvoir être relancé sans créer de doublons.
- **Validation email** : éviter d'émettre un badge inutilisable.
- **Colonnes variables** : prévoir une normalisation mais éviter trop de magie.
- **Images Excel** : à exclure du MVP pour éviter une complexité disproportionnée.
- **BadgeClass dynamique** : utile mais à traiter séparément pour ne pas fragiliser le noyau Open Badges actuel.
- **Gros fichiers** : pour les premières versions, limiter le nombre de lignes ou afficher un avertissement.

## 13. Décision recommandée

La fonctionnalité est pertinente et cohérente avec l'objectif de rendre Badge83 exploitable sur le terrain.

Recommandation : commencer par un MVP prudent :

1. import CSV/XLSX ;
2. preview obligatoire ;
3. émission par template existant ;
4. déduplication par template + email ;
5. rapport détaillé ;
6. tests automatisés.

Les extensions suivantes doivent rester séparées :

- BadgeClass dynamique par programme ;
- extraction d'image depuis Excel ;
- export ZIP ;
- envoi email automatique.
