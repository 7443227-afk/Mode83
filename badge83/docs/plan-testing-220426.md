# Plan de Test Badge83 — 22 Avril 2026

## 1. Vue d'ensemble

Ce document décrit le plan de test complet pour l'application Badge83, une implémentation Open Badges 2.0 basée sur FastAPI. L'objectif est de garantir la qualité, la fiabilité et la conformité aux standards de tous les composants de l'application.

## 2. Architecture de l'application

### 2.1. Modules principaux

- `issuer.py` : Gestion de la création et de l'émission des badges
- `verifier.py` : Vérification des badges émis
- `baker.py` : Baking et unbaking des images PNG avec assertions Open Badges
- `qr.py` : Génération et superposition des codes QR sur les badges
- `main.py` : Application FastAPI avec les routes API

### 2.2. Fonctionnalités clés

- Émission de badges (assertions JSON)
- Création de badges bakés (PNG avec assertions intégrées)
- Vérification de badges par ID et par téléchargement de PNG baké
- Génération de codes QR et superposition sur les badges
- API REST complète pour toutes les fonctionnalités

## 3. Plan de test détaillé

### 3.1. Tests unitaires

#### 3.1.1. Module d'émission de badges

**Fonction `issue_badge` :**
- Test avec des noms et emails valides
- Test avec des caractères spéciaux dans les noms
- Test avec des emails mal formés
- Vérification de la génération d'UUID unique
- Validation de la structure JSON de l'assertion

**Fonction `issue_baked_badge` :**
- Test avec PNG par défaut
- Test avec téléchargement de PNG personnalisé
- Test avec différents formats d'image
- Vérification de la sauvegarde correcte des fichiers
- Validation de l'intégration des métadonnées

**Fonctions utilitaires :**
- Test de `_make_recipient_hash` avec divers emails
- Test de `normalize_email` et `normalize_name`
- Test de `make_search_hash` et `make_search_metadata`
- Test de `make_admin_recipient_metadata`

#### 3.1.2. Module de vérification

**Fonction `verify_badge` :**
- Test avec un badge valide existant
- Test avec un ID de badge inexistant
- Test avec des assertions mal formées
- Vérification du résumé généré

**Fonction `verify_baked_badge` :**
- Test avec PNG baké valide
- Test avec PNG non baké
- Test avec PNG corrompu
- Test avec assertions invalides

#### 3.1.3. Module de baking

**Fonctions `bake_badge` et `unbake_badge` :**
- Test de baking avec assertion valide
- Test d'unbaking avec PNG baké correct
- Test avec PNG non conforme
- Vérification de l'intégrité des données extraites

#### 3.1.4. Module QR

**Fonction `make_verification_qr_url` :**
- Test avec différentes configurations d'URL de base
- Test avec différents ID d'assertion

**Fonction `overlay_qr_on_badge` :**
- Test avec différents formats d'image
- Test avec images de différentes tailles
- Vérification du positionnement du QR code
- Test du placement personnalisé `placement="custom"` avec coordonnées `offset_x` / `offset_y`
- Test de limitation aux bords lorsque les coordonnées dépassent les dimensions du badge
- Vérification que le PNG généré reste lisible et conserve les dimensions du PNG source
- Vérification que l'image est effectivement modifiée dans la zone attendue du QR code

### 3.2. Tests d'API

#### 3.2.1. Routes d'émission

**Route `/issue` :**
- Test d'émission de badge standard
- Test de validation des paramètres
- Test de gestion des erreurs

**Route `/issue-baked` :**
- Test d'émission de badge baké
- Test avec et sans image téléchargée
- Test de téléchargement de fichier

#### 3.2.2. Routes de vérification

**Route `/verify/{badge_id}` :**
- Test de vérification d'un badge par ID
- Test avec ID invalide
- Test de format de réponse

**Route `/verify-baked` :**
- Test de vérification par téléchargement de PNG
- Test avec différents types de fichiers
- Test de gestion d'erreurs

#### 3.2.3. Routes d'administration

**Routes de tableau de bord :**
- Test d'accès aux badges émis
- Test de recherche par métadonnées
- Test de pagination

#### 3.2.4. Routes publiques HostedBadge

**Routes d'assertion, BadgeClass et Issuer :**
- Test d'accès aux ressources publiques
- Test de conformité JSON-LD
- Test de résolution des URLs

### 3.3. Tests d'intégration

#### 3.3.1. Workflow complet

**Processus d'émission à vérification :**
- Test du workflow complet : création → vérification
- Test de la cohérence des données entre émission et vérification
- Test de la persistance des données

**Processus de baking/unbaking :**
- Test du cycle complet de baking et unbaking
- Vérification de la conservation des données
- Test de compatibilité avec différents formats

**Processus QR :**
- Test de génération QR → superposition → vérification mobile
- Test de l'expérience utilisateur mobile
- Test de la redirection vers page de vérification complète
- Test de cohérence entre les coordonnées définies dans l'interface de construction et le rendu backend du PNG final
- Test manuel complémentaire du glisser-déposer QR dans le navigateur, car ce comportement relève de l'interface frontend

#### 3.3.2. Validation des données

**Conformité Open Badges :**
- Test de conformité des assertions émises
- Test de validation avec openbadges-validator-core
- Test de compatibilité avec différents validateurs

**Intégrité des badges bakés :**
- Test d'extraction d'assertions bakées
- Test de vérification de l'intégrité des données
- Test de compatibilité avec outils externes

### 3.4. Tests de cas limites

#### 3.4.1. Données invalides

**Entrées mal formées :**
- Test avec noms et emails invalides
- Test avec données corrompues
- Test avec fichiers manquants

**Erreurs système :**
- Test avec espace disque insuffisant
- Test avec permissions insuffisantes
- Test avec dépendances manquantes

#### 3.4.2. Compatibilité

**Navigateurs :**
- Test avec différents navigateurs (Chrome, Firefox, Safari)
- Test avec différentes versions de navigateurs
- Test de compatibilité mobile

**Images :**
- Test avec différents formats d'image (PNG, JPEG)
- Test avec différentes résolutions
- Test avec images animées

## 4. Environnement de test

### 4.1. Configuration requise

- Python 3.8+
- Virtualenv avec dépendances installées
- Accès aux répertoires de données (`data/issued`, `data/baked`)
- Serveur FastAPI en cours d'exécution

### 4.2. Données de test

- Jeux de données pour différents scénarios
- Images PNG de test
- Assertions JSON de référence
- Badges bakés pour tests de vérification

## 5. Outils de test

### 5.1. Framework de test

- `pytest` pour les tests unitaires et d'intégration
- `FastAPI TestClient` pour les tests d'API
- `coverage.py` pour le rapport de couverture
- `Pillow` pour créer et comparer des PNG de test en mémoire

### 5.2. Rapports

- Rapport de couverture du code
- Rapport de réussite/échec des tests
- Logs détaillés pour le débogage

## 6. Critères d'acceptation

### 6.1. Succès

- Tous les tests unitaires passent avec un taux de couverture > 90%
- Toutes les routes API répondent correctement
- Tous les workflows fonctionnels sont validés
- Aucune erreur critique détectée

### 6.2. Échec

- Tests unitaires en échec > 5%
- Routes API non fonctionnelles
- Erreurs de validation Open Badges
- Problèmes de compatibilité identifiés

## 7. Fréquence des tests

### 7.1. Tests automatiques

- À chaque commit (CI/CD)
- Avant chaque déploiement
- Rapport quotidien d'exécution
- Après toute modification du rendu PNG ou du positionnement QR

### 7.2. Tests manuels

- Avant chaque release majeure
- Après chaque modification d'architecture
- À la demande pour les tests d'acceptation

## 8. Maintenance du plan

Ce plan de test sera mis à jour :
- Lors de l'ajout de nouvelles fonctionnalités
- Suite aux retours d'expérience de test
- Pour intégrer de nouveaux cas de test identifiés
- Pour adapter les outils et méthodes de test

---
*Document créé le 22 Avril 2026 pour le projet Badge83*