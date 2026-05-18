# Plan d'amélioration — Émission groupée Badge83 après retour curateur — 18/05/2026

Date : 18/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : plan de mise en œuvre des améliorations proposées par le curateur sur le module d'émission groupée

## 1. Contexte

Le retour du curateur valide l'intérêt fonctionnel de l'émission groupée CSV et identifie trois axes d'amélioration prioritaires pour transformer le prototype en outil opérateur plus robuste :

1. préciser le comportement en cas de données partiellement invalides dans un fichier volumineux ;
2. historiser les sessions d'émission groupée dans SQLite ;
3. anticiper les questions de performance lors de la génération des archives ZIP.

## 2. Décision de conception

Badge83 adopte une politique d'**émission partielle contrôlée** :

```text
Le fichier CSV est d'abord prévisualisé sans émission.
Les lignes sont classées par statut.
Après confirmation, seules les lignes prêtes sont émises.
Les lignes non admises, en doublon ou en erreur restent exclues et documentées dans le rapport.
```

Cette approche évite de bloquer une promotion complète à cause de quelques lignes incorrectes, tout en conservant une barrière de sécurité grâce à la prévisualisation obligatoire.

## 3. Lot 1 — Gestion fine des erreurs CSV

### Objectif

Rendre explicite et testable le comportement de Badge83 face aux fichiers mixtes contenant des lignes valides et invalides.

### Changements prévus

- exposer la politique d'émission dans le résumé de prévisualisation ;
- indiquer clairement si un commit est possible ;
- retourner un message lisible lorsqu'aucune ligne n'est prête ;
- ajouter un rapport JSON structuré dans la réponse de commit ;
- compléter les tests sur les fichiers partiellement invalides.

### Critères de réussite

- `preview` classe correctement les lignes `ready`, `not_passed`, `duplicate` et `error` ;
- `commit` émet uniquement les lignes `ready` ;
- un fichier sans ligne prête ne provoque pas d'émission accidentelle ;
- la réponse API explique le résultat à l'opérateur ;
- les tests automatisés passent.

## 4. Lot 2 — Historisation SQLite des sessions d'import

### Objectif

Créer une traçabilité de cohorte : un import CSV doit pouvoir être retrouvé comme une session liée aux badges émis et aux lignes ignorées.

### Schéma cible

Tables envisagées :

```text
batch_sessions
- id
- template_id
- session_label
- source_filename
- source_file_hash
- created_at
- status
- total_rows
- ready_count
- issued_count
- error_count
- duplicate_count
- not_passed_count

batch_session_items
- id
- session_id
- badge_id
- row_number
- recipient_name
- recipient_email_hash
- status
- error_message
- verification_url
- created_at
```

### Critères de réussite

- chaque émission groupée crée un `session_id` ;
- toutes les lignes du CSV sont rattachées à cette session ;
- les badges émis sont reliés à la session ;
- un administrateur peut consulter la liste des sessions et le détail d'une session.

## 5. Lot 3 — Performance et expérience utilisateur ZIP

### Objectif

Garantir un comportement acceptable lorsque le volume augmente.

### Approche progressive

1. mesurer les temps de traitement pour 50, 100 et 300 lignes ;
2. réduire la mémoire utilisée pendant la génération ZIP si nécessaire ;
3. améliorer le message opérateur pendant le traitement ;
4. envisager un mode asynchrone uniquement si les mesures le justifient.

### Critères de réussite

- les temps de traitement sont connus ;
- l'archive contient toujours les PNG, le rapport CSV, le manifeste et le fichier source ;
- le comportement est documenté ;
- l'asynchrone reste une évolution maîtrisée, non une complexité immédiate.

## 6. Ordre recommandé

```text
1. Clarifier et tester la politique d'émission partielle.
2. Ajouter l'historisation SQLite des sessions batch.
3. Ajouter les endpoints de consultation des sessions.
4. Mesurer puis optimiser la génération ZIP.
5. Mettre à jour le guide opérateur et le rapport hebdomadaire.
```

## 7. État de démarrage

Au début de cette amélioration, Badge83 possède déjà :

- un module `app/batch_issuer.py` ;
- une prévisualisation CSV ;
- un commit qui n'émet que les lignes `ready` ;
- une archive ZIP avec PNG, source CSV, rapport et manifeste ;
- des tests unitaires et API couvrant le flux principal.

Le premier travail consiste donc à formaliser ce comportement existant, puis à préparer l'historisation des sessions.