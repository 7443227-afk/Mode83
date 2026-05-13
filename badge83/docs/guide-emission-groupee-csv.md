# Guide technique — Émission groupée CSV — Badge83

Date : 13/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : flux d'émission groupée depuis un fichier CSV, avec interface opérateur et archive ZIP

## 1. Objectif

Cette fonctionnalité permet d'émettre plusieurs badges à partir d'un fichier CSV contenant une liste de participants.

Elle s'appuie sur les modèles existants du constructeur de badges. L'opérateur choisit donc d'abord un modèle, puis fournit un fichier CSV. Badge83 analyse les lignes, classe les participants et émet uniquement les badges correspondant aux lignes valides.

## 2. Périmètre de cette version

Cette première version couvre :

- l'import CSV ;
- la normalisation des colonnes principales ;
- la prévisualisation sans émission ;
- l'émission après confirmation depuis l'interface opérateur ;
- l'exclusion des personnes non admises ;
- la détection des lignes invalides ;
- la détection des doublons par modèle et email ;
- la correspondance des colonnes lisibles avec les champs du schéma ;
- la génération des assertions JSON et PNG baked via le moteur existant ;
- le téléchargement d'une archive ZIP contenant les PNG générés, le CSV source et un rapport d'émission.

Ne sont pas encore inclus :

- import Excel `.xlsx` ;
- envoi automatique par email ;
- création dynamique de BadgeClass par programme.

## 3. Format CSV attendu

Colonnes minimales :

| Colonne | Rôle | Obligatoire |
|---|---|---|
| `nom` ou `name` | nom complet du bénéficiaire | oui |
| `email` | email du bénéficiaire | oui |
| `programme` ou `program` | formation ou programme | recommandé |
| `reussi`, `réussi` ou `passed` | statut de réussite | oui |

Exemple :

```csv
nom,email,programme,reussi
Alice Martin,alice@example.org,Formation IA,oui
Karim Dupont,karim@example.org,Formation IA,oui
Paul Test,paul@example.org,Formation IA,non
```

Les colonnes supplémentaires sont copiées dans `field_values` afin d'être utilisables par les textes dynamiques du modèle.

Exemples de colonnes utiles :

```text
course_name, issue_date, certificate_number, organisation, session, formateur
```

### 3.1 Colonnes liées aux champs du schéma

Les modèles du constructeur peuvent être associés à un schéma contenant des champs dynamiques.

Pour éviter de demander aux opérateurs de manipuler des identifiants techniques internes, l'import groupé accepte les colonnes CSV basées sur le libellé lisible du champ.

Exemple : si le schéma contient un champ :

```json
{
  "id": "29b19e6e-524e-4f79-9c1d-dec3aa775dbe",
  "label": "Couriel",
  "required": true
}
```

Le CSV peut utiliser une colonne lisible :

```csv
nom,email,programme,reussi,couriel
Alice Martin,alice@example.org,Formation IA,oui,alice@example.org
```

Badge83 mappe automatiquement `couriel` vers l'identifiant technique du champ au moment de créer l'assertion.

Dans l'interface, après sélection du modèle, un bloc **Colonnes CSV attendues pour ce modèle** affiche les colonnes recommandées. Les colonnes techniques restent masquées dans une zone de détail et ne doivent pas être utilisées dans un fichier préparé manuellement.

### 3.2 Fichier CSV de test

Un fichier exemple est fourni :

```text
badge83/data/sample_batch_issue.csv
```

Il contient :

- deux lignes valides ;
- une ligne `non` pour tester l'exclusion pédagogique ;
- une ligne sans email pour tester l'erreur `Email invalide`.

## 4. Valeurs de réussite reconnues

Valeurs positives :

```text
oui, yes, true, 1, reussi, réussi, passed, valide, validé
```

Valeurs négatives :

```text
non, no, false, 0, echoue, échoué, failed, absent
```

Une valeur absente ou ambiguë classe la ligne en erreur.

## 5. Endpoints API

### 5.1 Prévisualisation

```text
POST /badge-constructor/templates/{template_id}/batch-issue/preview
```

Effet : analyse le fichier CSV sans créer de badge.

Exemple :

```bash
curl -X POST \
  -F "file=@participants.csv" \
  http://127.0.0.1:8000/badge-constructor/templates/<template_id>/batch-issue/preview
```

Réponse :

```json
{
  "template_id": "...",
  "total_rows": 3,
  "ready_rows": 2,
  "skipped_not_passed": 1,
  "skipped_duplicates": 0,
  "errors": 0,
  "rows": []
}
```

### 5.2 Émission réelle JSON

```text
POST /badge-constructor/templates/{template_id}/batch-issue
```

Effet : émet les badges pour les lignes classées `ready` et retourne un rapport JSON. Cet endpoint reste disponible pour intégration API.

Exemple :

```bash
curl -X POST \
  -F "file=@participants.csv" \
  http://127.0.0.1:8000/badge-constructor/templates/<template_id>/batch-issue
```

Réponse :

```json
{
  "template_id": "...",
  "created": 2,
  "skipped_not_passed": 1,
  "skipped_duplicates": 0,
  "errors": 0,
  "created_badges": [
    {
      "row_number": 2,
      "name": "Alice Martin",
      "email": "alice@example.org",
      "assertion_id": "...",
      "png_url": "/api/badges/.../png",
      "verification_url": "/verify/badge/...",
      "qr_url": "/verify/qr/..."
    }
  ]
}
```

### 5.3 Émission avec archive ZIP

```text
POST /badge-constructor/templates/{template_id}/batch-issue/archive
```

Effet : émet les badges pour les lignes `ready` et retourne une archive ZIP.

Exemple :

```bash
curl -X POST \
  -F "file=@participants.csv" \
  -o batch-issue.zip \
  http://127.0.0.1:8000/badge-constructor/templates/<template_id>/batch-issue/archive
```

Contenu de l'archive :

```text
source.csv
rapport_emission.csv
manifest.json
badges/*.png
```

Rôle des fichiers :

| Fichier | Rôle |
|---|---|
| `source.csv` | copie du CSV importé |
| `rapport_emission.csv` | rapport opérateur ligne par ligne |
| `manifest.json` | rapport technique complet |
| `badges/*.png` | PNG baked fraîchement générés |

Le fichier `rapport_emission.csv` reprend les colonnes du CSV source et ajoute :

```text
badge83_status, badge83_reason, badge83_png_filename, badge83_assertion_id, badge83_verification_url, badge83_qr_url
```

Exemple de statuts :

| `badge83_status` | Sens |
|---|---|
| `issued` | badge émis |
| `not_issued` | badge non émis |

Exemples de raisons courtes :

```text
Non admis, Duplicate, Email invalide, Erreur de validation
```

Dans l'interface opérateur, la génération groupée utilise ce flux ZIP : après confirmation, le navigateur télécharge automatiquement l'archive.


## 6. Règles de déduplication

La déduplication MVP repose sur :

```text
template_id + email normalisé
```

Si une assertion existante possède déjà le même modèle et le même email administrateur, la ligne est classée `duplicate`.

Cela permet de réimporter le même fichier sans générer plusieurs fois les mêmes badges.

## 7. Réutilisation du moteur existant

L'émission groupée ne crée pas un nouveau moteur de badge.

Pour chaque ligne valide, elle réutilise :

```text
issue_baked_badge_from_template(...)
```

Le comportement reste donc cohérent avec l'émission individuelle depuis modèle :

- assertion JSON ;
- PNG baked ;
- QR code ;
- registre local ;
- métadonnées `badge83_template` ;
- `field_values`.

## 8. Tests automatisés

Les tests couvrent :

- parsing CSV ;
- normalisation des colonnes ;
- valeurs de réussite ;
- lignes prêtes, non admises, invalides et doublons ;
- API preview ;
- API commit JSON ;
- API archive ZIP ;
- création des fichiers JSON et PNG ;
- présence du rapport `rapport_emission.csv` dans l'archive.

Commande :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat validé le 13/05/2026 :

```text
36 passed in 1.45s
```

## 9. Limites connues

Cette première version reste volontairement limitée.

Points à traiter dans une phase suivante :

1. ajouter le support Excel `.xlsx` ;
2. proposer le téléchargement automatique d'un modèle CSV depuis l'interface ;
3. prévoir l'envoi automatique par email ;
4. renforcer les limites d'upload avant exposition production.

## 10. Conclusion

Le flux d'émission groupée CSV constitue un premier lot fonctionnel pour traiter des groupes de formation.

La stratégie retenue est prudente :

```text
prévisualiser → confirmer → émettre → télécharger l'archive ZIP → rapporter
```

Elle permet d'ajouter une fonctionnalité utile sans modifier le format Open Badges ni dupliquer le moteur d'émission existant.
