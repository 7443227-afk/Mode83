# Plan de développement — Émission groupée CSV/XLSX — Badge83

Date de préparation : 13/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : cadrage d'une évolution permettant l'émission groupée de badges depuis un fichier CSV ou Excel

## 1. Objectif

L'objectif de cette évolution est de permettre à un opérateur MODE83 d'émettre plusieurs badges à partir d'un fichier contenant une liste de participants d'une formation.

Le cas d'usage typique est le suivant : une promotion ou un groupe a suivi une formation, a rendu les éléments attendus, puis certains participants sont reconnus comme ayant réussi. L'opérateur téléverse un fichier CSV ou Excel, Badge83 analyse les lignes, puis génère les badges uniquement pour les personnes éligibles.

Cette fonctionnalité doit transformer Badge83 d'un outil d'émission individuelle en outil réellement exploitable pour des groupes complets, tout en conservant la fiabilité du flux Open Badges existant.

## 2. Positionnement après Projet A

Cette fonctionnalité est pertinente, mais elle doit être traitée comme une évolution après validation du Projet A.

Décision recommandée :

```text
Ne pas intégrer l'émission groupée dans la clôture immédiate du Projet A.
La documenter comme une évolution prioritaire après validation fonctionnelle, documentation et revue sécurité du livrable principal.
```

Raison :

- le Projet A couvre déjà l'émission, le PNG baked, le QR, la vérification publique, le registre et le guide formateur ;
- l'émission groupée ajoute des risques spécifiques : erreurs de fichier, doublons, données personnelles, UX de confirmation ;
- cette évolution doit être développée avec une prévisualisation obligatoire et des tests dédiés ;
- elle ne doit pas retarder la remise du livrable Projet A.

## 3. Cas d'usage

Un opérateur dispose d'un fichier listant les apprenants d'une session.

Exemple :

| nom | email | programme | reussi | issue_date | certificate_number |
|---|---|---|---|---|---|
| Alice Martin | alice@example.org | Formation IA | oui | 2026-05-13 | IA-2026-001 |
| Karim Dupont | karim@example.org | Formation IA | oui | 2026-05-13 | IA-2026-002 |
| Paul Test | paul@example.org | Formation IA | non | 2026-05-13 | |

Badge83 doit :

1. lire le fichier ;
2. identifier les lignes éligibles ;
3. ignorer les personnes non admises ;
4. détecter les doublons ;
5. afficher une prévisualisation ;
6. attendre confirmation de l'opérateur ;
7. générer les badges uniquement pour les lignes valides ;
8. produire un rapport final.

## 4. Format attendu du fichier

### 4.1 Formats acceptés

Version MVP recommandée :

- `.csv` en priorité ;
- `.xlsx` dans une deuxième étape avec la dépendance `openpyxl`.

Le support CSV peut être réalisé avec la bibliothèque standard Python. Le support Excel nécessite une dépendance supplémentaire.

### 4.2 Colonnes minimales

Colonnes minimales recommandées :

| Colonne | Rôle | Obligatoire |
|---|---|---|
| `nom` ou `name` | nom complet du bénéficiaire | oui |
| `email` | email du bénéficiaire | oui |
| `programme` ou `program` | formation ou programme | oui |
| `reussi` ou `passed` | indique si la formation est validée | oui |

### 4.3 Colonnes optionnelles

Colonnes optionnelles utiles :

| Colonne | Utilisation |
|---|---|
| `issue_date` | date affichée ou utilisée dans le modèle |
| `certificate_number` | numéro de certificat fourni manuellement |
| `course_name` | intitulé de formation utilisé dans le template |
| `organisation` | organisation ou structure |
| `session` | session ou promotion |
| `formateur` | nom du formateur |

Les colonnes non réservées peuvent être copiées dans `field_values` afin d'être disponibles pour les textes dynamiques du modèle.

## 5. Règles métier

### 5.1 Réussite de la formation

Une ligne est éligible si la colonne `reussi` ou `passed` contient une valeur positive.

Valeurs positives proposées :

```text
oui, yes, true, 1, reussi, réussi, passed, valide, validé
```

Valeurs négatives proposées :

```text
non, no, false, 0, echoue, échoué, failed, absent
```

Si la valeur est ambiguë, la ligne doit être classée en erreur ou avertissement dans la prévisualisation.

### 5.2 Validation nom/email

Règles minimales :

- supprimer les espaces inutiles ;
- normaliser l'email en minuscules ;
- refuser une ligne sans nom ;
- refuser une ligne avec email vide ou invalide.

### 5.3 Déduplication

La fonctionnalité doit être idempotente : si le même fichier est importé deux fois, Badge83 ne doit pas générer deux fois les mêmes badges.

Clé de déduplication MVP :

```text
template_id + email normalisé
```

Ainsi, un même participant ne reçoit pas deux fois le même badge pour le même modèle ou programme.

### 5.4 Date et numéro de certificat

Si `issue_date` est fourni, il peut être utilisé dans les champs dynamiques du modèle.

Si `certificate_number` est fourni, Badge83 doit vérifier qu'il n'est pas déjà utilisé dans le contexte concerné.

Si `certificate_number` est absent, Badge83 peut utiliser la logique existante de génération automatique lorsque celle-ci est disponible pour le modèle.

## 6. Parcours opérateur recommandé

Le parcours doit éviter toute émission accidentelle.

Workflow recommandé :

```text
choisir un modèle → téléverser le fichier → analyser → prévisualiser → confirmer → émettre → afficher le rapport final
```

Étapes détaillées :

1. l'opérateur choisit un modèle de badge existant ;
2. il téléverse un fichier CSV ou XLSX ;
3. Badge83 analyse le fichier sans créer de badge ;
4. l'interface affiche un résumé : prêts, non admis, doublons, erreurs ;
5. l'opérateur confirme explicitement l'émission ;
6. Badge83 émet les badges pour les lignes valides ;
7. l'interface affiche un rapport final avec les liens utiles.

La prévisualisation doit être obligatoire.

## 7. Architecture proposée

### 7.1 Nouveau module métier

Créer un module dédié :

```text
badge83/app/batch_issuer.py
```

Responsabilités :

- parser les fichiers CSV/XLSX ;
- normaliser les noms de colonnes ;
- valider les lignes ;
- interpréter la réussite ;
- détecter les doublons ;
- préparer un rapport de prévisualisation ;
- exécuter l'émission réelle après confirmation.

Fonctions possibles :

```python
def parse_batch_file(file_bytes: bytes, filename: str) -> list[dict]:
    ...

def normalize_batch_row(row: dict) -> dict:
    ...

def is_passed(value: object) -> bool | None:
    ...

def preview_batch_issue(template_id: str, rows: list[dict]) -> dict:
    ...

def commit_batch_issue(template_id: str, rows: list[dict]) -> dict:
    ...
```

### 7.2 Routes API

Routes recommandées :

```text
POST /badge-constructor/templates/{template_id}/batch-issue/preview
POST /badge-constructor/templates/{template_id}/batch-issue
```

Le premier endpoint analyse sans créer de badge. Le second crée réellement les badges après confirmation.

### 7.3 Réutilisation du noyau existant

L'émission groupée doit réutiliser les fonctions existantes d'émission depuis template, notamment la logique qui crée déjà :

- assertion JSON ;
- PNG baked ;
- QR code ;
- entrée registre ;
- liens de vérification.

L'objectif n'est pas de créer un deuxième moteur d'émission, mais d'orchestrer plusieurs émissions unitaires de façon contrôlée.

## 8. Phases de réalisation

### Phase 1 — MVP CSV

Objectif : valider le besoin avec le minimum de complexité.

Contenu :

- support CSV ;
- colonnes minimales ;
- parsing et validation ;
- preview obligatoire ;
- déduplication par `template_id + email` ;
- émission réelle après confirmation ;
- rapport final simple.

Estimation :

```text
0,5 à 1 jour
```

### Phase 2 — Support Excel XLSX

Objectif : accepter les fichiers Excel utilisés par les opérateurs.

Contenu :

- ajout de `openpyxl` ;
- lecture du premier onglet ;
- gestion des cellules vides ;
- gestion des dates Excel ;
- tests dédiés `.xlsx`.

Estimation :

```text
1 à 2 jours avec CSV + XLSX
```

### Phase 3 — Interface opérateur améliorée

Objectif : rendre le parcours utilisable sans assistance technique.

Contenu :

- zone d'upload dans l'interface ;
- tableau de prévisualisation ;
- filtres par statut ;
- bouton de confirmation ;
- rapport final lisible ;
- messages d'erreur explicites.

Estimation :

```text
2 à 3 jours supplémentaires selon niveau UX
```

### Phase 4 — Exports et confort d'exploitation

Évolutions possibles :

- export CSV du rapport ;
- export ZIP des PNG créés ;
- historique des imports ;
- relance partielle des lignes en erreur ;
- téléchargement d'un modèle CSV exemple.

Ces éléments sont utiles, mais ne doivent pas bloquer le MVP.

## 9. Tests nécessaires

### Tests unitaires

- parsing CSV ;
- parsing XLSX ;
- normalisation `nom/name`, `programme/program`, `reussi/passed` ;
- interprétation des valeurs positives et négatives ;
- email invalide ;
- nom vide ;
- génération des `field_values` ;
- déduplication par template et email.

### Tests API

- preview avec fichier valide ;
- preview avec colonnes manquantes ;
- commit avec lignes prêtes ;
- commit avec lignes non admises ;
- commit avec doublons ;
- réimport du même fichier ;
- vérification que les JSON et PNG sont bien créés.

### Critère de réussite MVP

Avec un fichier de test de 10 lignes :

- 6 lignes réussies ;
- 2 lignes non réussies ;
- 1 ligne avec email invalide ;
- 1 ligne déjà émise ;

Badge83 doit produire :

- 5 nouveaux badges ;
- 2 lignes ignorées comme non admises ;
- 1 erreur email ;
- 1 doublon ignoré ;
- un rapport clair ;
- aucun doublon lors d'un second import du même fichier.

## 10. Risques et limites

### 10.1 Données personnelles

Les fichiers importés contiennent probablement des noms, emails et informations pédagogiques.

Mesures à prévoir :

- ne pas journaliser le contenu brut complet ;
- ne pas conserver le fichier original sans nécessité ;
- limiter l'accès à l'écran d'import ;
- documenter les règles RGPD applicables.

### 10.2 Données incorrectes

Les fichiers opérateur peuvent contenir :

- emails invalides ;
- lignes vides ;
- colonnes mal nommées ;
- valeurs ambiguës dans `reussi` ;
- doublons internes.

La prévisualisation doit rendre ces problèmes visibles avant émission.

### 10.3 Duplications

Sans idempotence, un même fichier pourrait produire plusieurs badges identiques.

La déduplication `template_id + email` est donc obligatoire dès le MVP.

### 10.4 Images dans Excel

L'extraction d'images depuis Excel est exclue du MVP.

Le modèle visuel doit être préparé dans le constructeur Badge83. Le fichier CSV/XLSX doit contenir les données, pas l'image de fond.

### 10.5 BadgeClass dynamique

Créer automatiquement un vrai `BadgeClass` Open Badges par programme est une évolution plus avancée.

Pour le MVP, le programme peut être représenté par un modèle existant et ses champs dynamiques.

## 11. Estimation globale

| Niveau | Contenu | Estimation | Risque |
|---|---|---:|---|
| MVP CSV | CSV, preview, commit, déduplication, rapport simple | 0,5 à 1 jour | Moyen |
| CSV + XLSX | Ajout Excel avec `openpyxl`, tests XLSX | 1 à 2 jours | Moyen |
| Version complète | UX avancée, exports, ZIP, historique | 3 à 5 jours | Moyen à élevé |

## 12. Décision recommandée

L'émission groupée CSV/XLSX est une évolution utile et cohérente avec l'exploitation réelle de Badge83.

Décision recommandée :

```text
Planifier cette fonctionnalité comme premier lot d'évolution après clôture du Projet A.
Commencer par un MVP CSV avec prévisualisation obligatoire, puis ajouter XLSX et UX avancée dans des phases séparées.
```

À ne pas inclure dans le MVP :

- ancrage blockchain ;
- envoi email automatique ;
- image de fond importée depuis Excel ;
- BadgeClass dynamique complet ;
- export ZIP obligatoire.

La bonne stratégie est de sécuriser d'abord le flux simple : importer, prévisualiser, confirmer, émettre, rapporter.
