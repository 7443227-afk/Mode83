# Guide technique — Émission groupée CSV — Badge83

Date : 13/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : première version du flux d'émission groupée depuis un fichier CSV

## 1. Objectif

Cette fonctionnalité permet d'émettre plusieurs badges à partir d'un fichier CSV contenant une liste de participants.

Elle s'appuie sur les modèles existants du constructeur de badges. L'opérateur choisit donc d'abord un modèle, puis fournit un fichier CSV. Badge83 analyse les lignes, classe les participants et émet uniquement les badges correspondant aux lignes valides.

## 2. Périmètre de cette version

Cette première version couvre :

- l'import CSV ;
- la normalisation des colonnes principales ;
- la prévisualisation sans émission ;
- l'émission après confirmation API ;
- l'exclusion des personnes non admises ;
- la détection des lignes invalides ;
- la détection des doublons par modèle et email ;
- la génération des assertions JSON et PNG baked via le moteur existant.

Ne sont pas encore inclus :

- import Excel `.xlsx` ;
- interface opérateur complète ;
- export ZIP des PNG ;
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

### 5.2 Émission réelle

```text
POST /badge-constructor/templates/{template_id}/batch-issue
```

Effet : émet les badges pour les lignes classées `ready`.

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
- API commit ;
- création des fichiers JSON et PNG.

Commande :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat validé le 13/05/2026 :

```text
33 passed in 1.33s
```

## 9. Limites connues

Cette première version reste volontairement limitée.

Points à traiter dans une phase suivante :

1. ajouter l'interface opérateur dans la console web ;
2. ajouter le support Excel `.xlsx` ;
3. proposer un fichier CSV exemple téléchargeable ;
4. permettre l'export CSV du rapport ;
5. prévoir un export ZIP des PNG générés ;
6. renforcer les limites d'upload avant exposition production.

## 10. Conclusion

Le flux d'émission groupée CSV constitue un premier lot fonctionnel pour traiter des groupes de formation.

La stratégie retenue est prudente :

```text
prévisualiser → confirmer → émettre → rapporter
```

Elle permet d'ajouter une fonctionnalité utile sans modifier le format Open Badges ni dupliquer le moteur d'émission existant.
