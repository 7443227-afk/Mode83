# Rapport de validation — Projet A — Badge83 — 15/05/2026

Date de préparation : 13/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : synthèse de validation du Projet A et préparation de la remise finale

## 1. Objectif du Projet A

Le Projet A a pour objectif de mettre en place un outil MODE83 permettant d'émettre, remettre et vérifier des Open Badges.

Le périmètre attendu couvre principalement :

1. l'émission d'un badge pour un apprenant ;
2. la génération d'une assertion Open Badges au format JSON ;
3. la génération d'un badge PNG baked contenant les métadonnées Open Badges ;
4. la mise à disposition d'une page publique de vérification ;
5. l'ajout d'un QR code pour une vérification rapide ;
6. l'utilisation par un formateur ou opérateur sans modification manuelle des fichiers JSON ;
7. la conservation et la recherche des badges émis.

Le Projet A vise donc un MVP opérationnel Open Badges pour MODE83. Il ne couvre pas encore l'ancrage blockchain complet, qui relève du Projet B.

## 2. État général au 13/05/2026

Au 13/05/2026, Badge83 est dans un état fonctionnellement stable pour le périmètre Projet A.

État vérifié :

```text
Git : espace de travail propre
Tests automatisés : 27 passed in 1.06s
Validation fonctionnelle Projet A : concluante
Guide formateur : présent
```

Le parcours principal fonctionne de bout en bout :

```text
saisie apprenant → émission badge → assertion JSON → PNG baked → QR → page publique → vérification → registre local
```

Le projet peut être présenté comme livrable fonctionnel pour le Projet A. En revanche, il ne doit pas encore être considéré comme prêt pour une exposition production publique sans durcissement sécurité complémentaire.

## 3. Fonctionnalités livrées

### 3.1 Émission de badge

Badge83 permet d'émettre un badge depuis l'interface ou via API.

Une émission produit :

- une assertion JSON ;
- un PNG baked ;
- un lien de vérification publique ;
- une page QR ;
- une entrée dans le registre local.

### 3.2 Assertion Open Badges

Chaque badge reçoit une assertion compatible Open Badges 2.0.

Les assertions produites contiennent notamment :

- `@context` ;
- `type: Assertion` ;
- `id` / `url` ;
- `recipient` ;
- `badge` ;
- `issuer` ;
- `verification` ;
- `issuedOn` ;
- des métadonnées complémentaires utiles à l'interopérabilité.

L'identité email du titulaire est hachée dans le champ standard `recipient.identity`.

### 3.3 PNG baked

Badge83 génère un PNG baked, c'est-à-dire une image de badge contenant l'assertion Open Badges dans ses métadonnées.

Ce PNG peut :

- être ouvert comme une image classique ;
- être remis à l'apprenant comme preuve portable ;
- être inspecté pour extraire l'assertion ;
- être vérifié par le module de vérification Badge83.

### 3.4 QR code et vérification mobile

Un QR code visible est ajouté sur les badges PNG.

Il pointe vers une page de vérification de type :

```text
/verify/qr/{assertion_id}
```

Ce mécanisme permet une vérification rapide depuis smartphone.

### 3.5 Page publique de vérification

Chaque badge émis dispose d'une page publique de vérification :

```text
/verify/badge/{assertion_id}
```

Cette page affiche les informations principales du badge et son statut de vérification.

### 3.6 Registre local SQLite

Badge83 utilise un registre SQLite local comme index administratif.

Les fichiers JSON restent la source canonique des assertions Open Badges, tandis que SQLite sert à :

- lister les badges ;
- rechercher des badges ;
- faciliter la navigation opérateur ;
- relier les informations JSON, PNG et vérification.

### 3.7 Constructeur de badges

Le projet inclut un constructeur de badges permettant de gérer :

- des schémas de champs ;
- des modèles visuels ;
- une prévisualisation ;
- le placement du QR code ;
- des champs dynamiques ;
- l'émission depuis un modèle préparé.

Cette fonctionnalité dépasse le minimum attendu du Projet A et améliore l'utilisation par un opérateur non technique.

## 4. Stabilisation technique du 11/05/2026

Le 11/05/2026, le principal risque technique identifié concernait une erreur SQLite/threading sur les routes du constructeur.

Erreur observée :

```text
sqlite3.ProgrammingError: SQLite objects created in a thread can only be used in that same thread
```

Routes concernées :

```text
/badge-constructor/schemas
/badge-constructor/templates
```

Correction appliquée :

- connexion SQLite configurée avec `check_same_thread=False` ;
- ajout d'un `timeout=10` ;
- vérification des routes du constructeur ;
- inspection des logs après relance ;
- absence de régression observée.

Résultat :

```text
Erreur SQLite/threading corrigée
Tests automatisés OK
Routes constructeur OK
```

Référence documentaire :

```text
badge83/docs/rapport-travail-110526-stabilisation.md
```

## 5. Validation fonctionnelle du 12/05/2026

Le 12/05/2026, une validation fonctionnelle complète du Projet A a été réalisée.

Cinq scénarios ont été testés :

1. badge standard simple ;
2. badge émis depuis un modèle constructeur ;
3. vérification publique et page QR ;
4. vérification du PNG baked ;
5. registre local et recherche.

Les points suivants ont été contrôlés :

- création de l'assertion JSON ;
- création du PNG baked ;
- ouverture de la page publique ;
- ouverture de la page QR ;
- inspection ou extraction du PNG ;
- vérification par upload PNG ;
- présence et recherche dans le registre local.

Conclusion de cette validation :

```text
Validation fonctionnelle Projet A concluante
```

Référence documentaire :

```text
badge83/docs/test-report-projet-a-120526.md
```

## 6. Tests automatisés du 13/05/2026

Les tests automatisés ont été relancés le 13/05/2026.

Commande exécutée :

```bash
cd /home/ubuntu/projects/Mode83/badge83
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat :

```text
27 passed in 1.06s
```

Ce résultat confirme que l'état actuel reste stable après les travaux de stabilisation et de validation.

## 7. Documentation disponible

Les documents suivants constituent la base de remise Projet A :

### 7.1 Plan de travail de la semaine

```text
badge83/docs/plan-travail-semaine-110526.md
```

Ce document fixe la séquence de consolidation : stabilisation, validation Projet A, guide formateur, finitions UX, rapport final et décision Projet B.

### 7.2 Rapport de stabilisation

```text
badge83/docs/rapport-travail-110526-stabilisation.md
```

Ce rapport documente le diagnostic et la correction de l'erreur SQLite/threading.

### 7.3 Rapport de test Projet A

```text
badge83/docs/test-report-projet-a-120526.md
```

Ce rapport documente la validation fonctionnelle de bout en bout sur cinq scénarios.

### 7.4 Guide formateur

```text
badge83/docs/guide-formateur-mode83.md
```

Ce guide explique l'utilisation de Badge83 par un formateur ou opérateur non technique.

### 7.5 Audit architecture et sécurité

```text
badge83/docs/audit-architecture-security-120526.md
```

Cet audit montre que le projet est fonctionnel, mais qu'un durcissement sécurité est nécessaire avant exposition production.

## 8. Parcours de démonstration recommandé

Pour présenter le Projet A, le parcours de démonstration recommandé est le suivant :

1. ouvrir l'interface Badge83 ;
2. sélectionner un modèle de badge existant ;
3. renseigner les informations d'un apprenant ;
4. émettre le badge ;
5. afficher ou télécharger le PNG généré ;
6. ouvrir la page publique de vérification ;
7. ouvrir la page QR ;
8. vérifier le PNG via l'outil d'upload ;
9. retrouver le badge dans le registre local ;
10. effectuer une recherche par nom ou email.

Ce parcours démontre le cycle complet Open Badges : émission, preuve portable, vérification et registre.

## 9. Limites connues et risques résiduels

Le Projet A est fonctionnellement validé, mais plusieurs limites doivent rester visibles.

### 9.1 Sécurité P0/P1 avant production

Avant toute exposition production publique, les points suivants doivent être traités :

- ne pas utiliser de valeurs par défaut faibles comme `admin/admin` ;
- régénérer les secrets ;
- protéger les endpoints administrateur directement côté FastAPI ;
- ne pas dépendre uniquement de Nginx/auth_request pour la sécurité ;
- vérifier que `badge83.env` ne soit pas suivi dans Git ;
- limiter la taille des uploads ;
- protéger la vérification en ligne contre les risques SSRF ;
- protéger les chemins d'images contre les risques path traversal.

### 9.2 Données personnelles

L'email est haché dans le champ standard `recipient`, mais certaines métadonnées opérateur peuvent être conservées pour l'administration locale.

Une politique claire doit préciser :

- quelles données sont publiques ;
- quelles données restent réservées à l'administration ;
- quelles données sont intégrées dans le PNG baked ;
- quelles règles RGPD MODE83 doivent s'appliquer.

### 9.3 Architecture applicative

Le fichier `app/main.py` concentre encore plusieurs responsabilités.

À moyen terme, il serait préférable de séparer :

- les routes publiques ;
- les routes administrateur ;
- l'authentification et la sécurité ;
- les services métier ;
- les repositories d'accès aux données.

Cette limite n'empêche pas la validation du Projet A, mais elle doit être prise en compte pour la suite.

### 9.4 Statut production

Badge83 peut être présenté comme MVP ou outil interne fonctionnel. Il ne doit pas encore être présenté comme application production publique sans correction des points sécurité identifiés.

## 10. Actions restantes avant remise finale

Avant la remise finale, il est recommandé de :

1. réaliser quelques finitions UX opérateur ;
2. masquer les détails JSON derrière un bloc `détails techniques` ;
3. rendre le registre plus lisible ;
4. vérifier l'affichage mobile de la page QR ;
5. mettre à jour les éléments obsolètes du README ;
6. compléter le présent rapport avec les dernières vérifications ;
7. préparer le scénario de démonstration.

## 11. Décision recommandée pour le Projet B

Le Projet B concerne l'ancrage blockchain.

Recommandation :

```text
Ne pas démarrer le Projet B avant validation finale du Projet A et revue sécurité.
```

Justification :

- le Projet A est presque clôturé et doit d'abord être stabilisé comme livrable ;
- l'ancrage blockchain ajoutera de la complexité ;
- les points sécurité doivent être clarifiés avant d'ajouter une couche de confiance externe ;
- si le Projet B est retenu, il doit commencer par un cadrage technique séparé.

Premières règles pour un éventuel Projet B :

- ancrer uniquement un hash d'assertion ;
- ne jamais stocker de données personnelles on-chain ;
- définir un smart contract minimal ;
- choisir un réseau de test ;
- documenter la gestion des clés ;
- réaliser un proof of concept séparé du flux de production.

## 12. Conclusion

Badge83 répond aux objectifs principaux du Projet A comme MVP Open Badges MODE83.

Le projet permet aujourd'hui de :

- émettre des badges ;
- créer des assertions Open Badges ;
- générer des PNG baked ;
- ajouter une vérification par QR code ;
- vérifier les badges ;
- consulter un registre local ;
- utiliser des modèles visuels ;
- fournir un guide formateur.

État de synthèse :

```text
Projet A fonctionnellement validé
Tests automatisés OK
Documentation principale disponible
Démonstration possible
Production publique à différer avant corrections sécurité
```

Décision recommandée :

```text
Valider le Projet A comme livrable fonctionnel, terminer les finitions UX/documentation, puis décider séparément du démarrage Projet B.
```
