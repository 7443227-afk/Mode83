# Guide technique — Émission groupée CSV/XLSX — Badge83

Date : 13/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : flux d'émission groupée depuis un fichier CSV ou Excel `.xlsx`, avec interface opérateur et archive ZIP

Mise à jour du 18/05/2026 : clarification de la politique d'émission partielle contrôlée et du rapport JSON de commit.

Mise à jour du 19/05/2026 : ajout du support Excel `.xlsx`, conservation du support CSV, mise à jour de l'interface opérateur et des tests automatisés.

Mise à jour complémentaire du 19/05/2026 : génération d'un modèle Excel téléchargeable spécifique au modèle de badge sélectionné, afin d'aligner les colonnes du fichier sur les champs obligatoires du schéma associé.

Mise à jour du 27/05/2026 : l'interface opérateur affiche désormais l'identifiant de session d'émission groupée après la génération de l'archive ZIP, afin de faciliter le contrôle technique et la traçabilité.

Mise à jour du 28/05/2026 : le résumé de prévisualisation expose aussi des compteurs explicites `ready_count`, `not_passed_count`, `duplicate_count` et `error_count`, en complément des noms historiques `ready_rows`, `skipped_not_passed`, `skipped_duplicates` et `errors`.

## 1. Objectif

Cette fonctionnalité permet d'émettre plusieurs badges à partir d'un fichier CSV ou Excel `.xlsx` contenant une liste de participants.

Elle s'appuie sur les modèles existants du constructeur de badges. L'opérateur choisit donc d'abord un modèle, puis fournit un fichier CSV ou Excel. Badge83 analyse les lignes, classe les participants et émet uniquement les badges correspondant aux lignes valides.

## 2. Périmètre de cette version

Cette première version couvre :

- l'import CSV ;
- l'import Excel `.xlsx` ;
- la normalisation des colonnes principales ;
- la prévisualisation sans émission ;
- la politique d'émission partielle contrôlée ;
- l'émission après confirmation depuis l'interface opérateur ;
- l'exclusion des personnes non admises ;
- la détection des lignes invalides ;
- la détection des doublons par modèle et email ;
- la correspondance des colonnes lisibles avec les champs du schéma ;
- la génération d'un modèle Excel `.xlsx` adapté au schéma du modèle sélectionné ;
- la génération des assertions JSON et PNG baked via le moteur existant ;
- le téléchargement d'une archive ZIP contenant les PNG générés, le fichier source et un rapport d'émission ;
- l'affichage de l'identifiant de session d'émission groupée après génération de l'archive ZIP.

Ne sont pas encore inclus :

- import Excel historique `.xls` ;
- extraction d'images intégrées dans Excel ;
- envoi automatique par email ;
- création dynamique de BadgeClass par programme.

## 3. Formats d'import attendus

Formats acceptés :

| Format | Extension | Remarques |
|---|---|---|
| CSV | `.csv` | séparateurs virgule, point-virgule et tabulation détectés automatiquement |
| Excel | `.xlsx` | lu avec `openpyxl`, premier onglet actif, valeurs calculées si présentes |

Le format Excel historique `.xls` n'est pas supporté. Il faut convertir le fichier en `.xlsx` ou l'exporter en `.csv`.

Pour `.xlsx`, Badge83 utilise la première ligne non vide comme ligne d'en-tête et ignore les lignes entièrement vides.

## 3.1 Colonnes attendues

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

### 3.2 Colonnes liées aux champs du schéma

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

Le fichier d'import peut utiliser une colonne lisible :

```csv
nom,email,programme,reussi,couriel
Alice Martin,alice@example.org,Formation IA,oui,alice@example.org
```

Badge83 mappe automatiquement `couriel` vers l'identifiant technique du champ au moment de créer l'assertion.

Dans l'interface, après sélection du modèle, un bloc **Colonnes CSV attendues pour ce modèle** affiche les colonnes recommandées. Le libellé historique parle encore de CSV, mais les mêmes colonnes sont valables pour Excel `.xlsx`. Les colonnes techniques restent masquées dans une zone de détail et ne doivent pas être utilisées dans un fichier préparé manuellement.

### 3.3 Modèle Excel téléchargeable par schéma

L'interface d'émission groupée propose un bouton **Télécharger le modèle Excel**.

Le comportement dépend du choix de l'opérateur :

| Situation | Fichier téléchargé |
|---|---|
| Aucun modèle de badge sélectionné | modèle Excel générique avec `nom`, `email`, `reussi` |
| Modèle de badge sélectionné | modèle Excel généré dynamiquement avec les colonnes du schéma associé |

Le modèle spécifique contient :

- les colonnes minimales `nom`, `email`, `reussi` ;
- les champs du schéma associé, avec leurs libellés lisibles ;
- une ligne d'exemple ;
- un onglet `Instructions` ;
- une mise en évidence des colonnes obligatoires.

Exemple : si le modèle sélectionné est associé à un schéma contenant les champs obligatoires `Couriel` et `Nom du cours`, le fichier généré contient les en-têtes :

```text
nom, email, reussi, Couriel, Nom du cours
```

Cette génération évite le cas où l'opérateur télécharge un modèle générique, puis importe un fichier ne contenant pas les colonnes obligatoires attendues par le schéma. L'erreur du type :

```text
Champ obligatoire manquant : Couriel
```

doit donc être évitée lorsque le fichier est préparé depuis le modèle Excel téléchargé après sélection du modèle de badge.

### 3.4 Fichier CSV de test

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

## 4.1 Politique d'émission partielle contrôlée

Badge83 ne bloque pas l'intégralité d'un import si certaines lignes sont invalides.

La règle retenue est :

```text
prévisualiser toutes les lignes → classer les statuts → émettre uniquement les lignes prêtes → rapporter les autres lignes
```

Statuts internes :

| Statut | Signification | Émis lors du commit |
|---|---|---|
| `ready` | ligne valide et éligible | oui |
| `not_passed` | participant non admis | non |
| `duplicate` | badge déjà émis pour ce modèle et cet email | non |
| `error` | donnée manquante ou invalide | non |

Le résumé de prévisualisation expose aussi :

```json
{
  "issue_policy": "partial_valid_rows_only",
  "can_commit": true,
  "message": "L'émission peut être confirmée pour les lignes prêtes"
}
```

Si aucune ligne n'est prête, `can_commit` vaut `false` et le message devient :

```text
Aucune ligne prête à émettre
```

## 5. Endpoints API

### 5.1 Prévisualisation

```text
POST /badge-constructor/templates/{template_id}/batch-issue/preview
```

Effet : analyse le fichier CSV ou `.xlsx` sans créer de badge.

Exemple :

```bash
curl -X POST \
  -F "file=@participants.csv" \
  http://127.0.0.1:8000/badge-constructor/templates/<template_id>/batch-issue/preview
```

Exemple Excel :

```bash
curl -X POST \
  -F "file=@participants.xlsx" \
  http://127.0.0.1:8000/badge-constructor/templates/<template_id>/batch-issue/preview
```

Réponse :

```json
{
  "template_id": "...",
  "issue_policy": "partial_valid_rows_only",
  "total_rows": 3,
  "ready_count": 2,
  "not_passed_count": 1,
  "duplicate_count": 0,
  "error_count": 0,
  "ready_rows": 2,
  "skipped_not_passed": 1,
  "skipped_duplicates": 0,
  "errors": 0,
  "can_commit": true,
  "message": "L'émission peut être confirmée pour les lignes prêtes",
  "rows": []
}
```

### 5.1.1 Téléchargement du modèle Excel

Modèle générique historique :

```text
GET /badge-constructor/batch-issue/template.xlsx
```

Modèle Excel adapté à un modèle de badge et à son schéma :

```text
GET /badge-constructor/templates/{template_id}/batch-issue/template.xlsx
```

Exemple :

```bash
curl -L \
  -o modele-emission-groupee.xlsx \
  http://127.0.0.1:8000/badge-constructor/templates/<template_id>/batch-issue/template.xlsx
```

Ce second endpoint est celui utilisé par l'interface après sélection d'un modèle dans l'écran **Émission groupée**.

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

Le même endpoint accepte aussi `participants.xlsx`.

Réponse :

```json
{
  "template_id": "...",
  "issue_policy": "partial_valid_rows_only",
  "can_commit": true,
  "message": "Émission groupée terminée",
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
  ],
  "report_rows": [
    {
      "row_number": 2,
      "name": "Alice Martin",
      "email": "alice@example.org",
      "status": "issued",
      "reason": "",
      "assertion_id": "...",
      "verification_url": "/verify/badge/...",
      "qr_url": "/verify/qr/..."
    },
    {
      "row_number": 4,
      "name": "Paul Test",
      "email": "paul@example.org",
      "status": "not_issued",
      "source_status": "not_passed",
      "reason": "Non admis",
      "assertion_id": null,
      "verification_url": null,
      "qr_url": null
    }
  ]
}
```

Lorsque le fichier ne contient aucune ligne prête, l'endpoint répond toujours en succès technique mais sans émission :

```json
{
  "created": 0,
  "can_commit": false,
  "message": "Aucune ligne prête à émettre",
  "report_rows": []
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

Le même endpoint accepte aussi `participants.xlsx`.

Contenu de l'archive :

```text
source.csv ou source.xlsx
rapport_emission.csv
manifest.json
badges/*.png
```

Depuis le 18/05/2026, les PNG sont ajoutés au ZIP au fil de l'émission, sans conserver une liste intermédiaire de toutes les images générées. L'archive finale reste construite en mémoire avant envoi HTTP, mais la mémoire intermédiaire est réduite pour les imports de taille moyenne.

Rôle des fichiers :

| Fichier | Rôle |
|---|---|
| `source.csv` ou `source.xlsx` | copie du fichier importé |
| `rapport_emission.csv` | rapport opérateur ligne par ligne |
| `manifest.json` | rapport technique complet |
| `badges/*.png` | PNG baked fraîchement générés |

Le manifeste contient aussi l'identifiant de session d'import :

```json
{
  "session_id": "...",
  "archive_generation": {
    "mode": "streamed_png_entries"
  }
}
```

Le fichier `rapport_emission.csv` reprend les colonnes du fichier source, normalisées par Badge83, et ajoute :

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
- parsing Excel `.xlsx` ;
- refus explicite du format `.xls` ;
- normalisation des colonnes ;
- valeurs de réussite ;
- lignes prêtes, non admises, invalides et doublons ;
- API preview ;
- API de génération du modèle Excel spécifique à un schéma ;
- API commit JSON ;
- rapport JSON ligne par ligne du commit ;
- fichier sans aucune ligne prête ;
- API archive ZIP ;
- création des fichiers JSON et PNG ;
- présence du rapport `rapport_emission.csv` dans l'archive.

Commande :

```bash
cd /home/ubuntu/projects/Mode83/badge83
.venv/bin/python -m pytest -q
```

Résultat validé le 19/05/2026 après ajout du support Excel `.xlsx` :

```text
60 passed in 2.75s
```

Résultat ciblé validé le 19/05/2026 après génération du modèle Excel par schéma :

```text
25 passed in 2.14s
```

## 9. Limites connues

Cette première version reste volontairement limitée.

Points à traiter dans une phase suivante :

1. prévoir l'envoi automatique par email ;
2. mesurer les temps de traitement pour 50, 100 et 300 lignes avec CSV et XLSX ;
3. envisager un mode asynchrone si les volumes réels le justifient ;
4. éventuellement documenter une procédure de conversion `.xls` vers `.xlsx` pour les opérateurs.

## 9.1 Mesure de volume

Un test automatisé vérifie que la prévisualisation supporte un fichier synthétique de 300 lignes prêtes.

Pour mesurer manuellement la génération ZIP sur plusieurs volumes, un script de benchmark local est disponible :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python scripts/benchmark_batch_archive.py --rows 50 100 300
```

Le script affiche :

```text
rows,seconds,zip_bytes,png_count,session_id
```

Ce benchmark ne remplace pas les tests automatisés : il sert à documenter le comportement réel avant d'introduire, si nécessaire, une architecture asynchrone.

## 10. Conclusion

Le flux d'émission groupée CSV/XLSX constitue un lot fonctionnel pour traiter des groupes de formation à partir des formats réellement utilisés par les opérateurs.

La stratégie retenue est prudente :

```text
prévisualiser → confirmer → émettre → télécharger l'archive ZIP → rapporter
```

Elle permet d'ajouter une fonctionnalité utile sans modifier le format Open Badges ni dupliquer le moteur d'émission existant.
