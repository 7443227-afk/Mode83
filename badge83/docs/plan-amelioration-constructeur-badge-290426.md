# Plan d'amélioration du constructeur de badges — 29/04/2026

## Objectif

Rendre le constructeur de badges plus orienté utilisateur, plus clair et utilisable par une personne non technique pour créer des modèles de badges personnalisés.

Le constructeur doit permettre de définir les informations à collecter, de les afficher visuellement sur le badge, puis de générer un badge final à partir des valeurs saisies.

## 1. Amélioration de l'expérience utilisateur

Réorganiser l'interface du constructeur en étapes simples :

1. choisir ou créer un schéma ;
2. ajouter les champs nécessaires ;
3. configurer le modèle visuel ;
4. positionner les textes et le QR code ;
5. prévisualiser le badge ;
6. enregistrer le modèle.

À prévoir :

- ajouter des textes d'aide en français sous les champs importants ;
- améliorer les états vides : aucun schéma, aucun modèle, aucun aperçu ;
- afficher des confirmations claires après création, modification ou suppression ;
- éviter les termes trop techniques dans l'interface utilisateur ;
- garder l'ensemble de l'interface en français.

## 2. Gestion de plusieurs champs dans un schéma

Le constructeur doit permettre d'ajouter plusieurs champs dans un même schéma depuis le frontend.

Types de champs à prévoir :

- texte ;
- email ;
- nombre ;
- date ;
- liste de choix ;
- texte long.

Fonctionnalités attendues :

- ajouter un champ ;
- modifier un champ ;
- supprimer un champ ;
- marquer un champ comme obligatoire ou optionnel ;
- définir une valeur par défaut ;
- définir l'ordre d'affichage des champs ;
- afficher la liste des champs déjà ajoutés dans le schéma.

## 3. Texte superposé lié aux champs remplis

Le modèle visuel doit permettre deux types de textes superposés :

1. texte statique ;
2. texte dynamique lié à un champ rempli par l'utilisateur.

Exemples de texte statique :

- `MODE83` ;
- `Attestation de formation` ;
- `Badge délivré par MODE83`.

Exemples de texte dynamique :

- nom du bénéficiaire ;
- date d'émission ;
- nom de la formation ;
- niveau obtenu ;
- mention ou commentaire.

Comportement attendu :

- lors de la prévisualisation, utiliser des valeurs d'exemple ;
- lors de l'émission réelle, remplacer les champs dynamiques par les valeurs saisies ;
- conserver les valeurs remplies dans l'assertion Open Badges ;
- permettre plusieurs textes dynamiques sur le même badge.

## 4. Prévisualisation plus réaliste

La prévisualisation doit montrer le rendu final le plus proche possible du badge généré.

À ajouter :

- formulaire de valeurs d'exemple pour les champs du schéma ;
- remplacement des placeholders techniques par les valeurs de test ;
- rafraîchissement de l'aperçu après modification du texte, de la position ou du QR code ;
- affichage clair des erreurs si le rendu PNG échoue.

Objectif : éviter les placeholders de type `[field_id]` dans l'aperçu utilisateur.

## 5. Émission d'un badge depuis un modèle

Ajouter un workflow complet :

1. choisir un modèle ;
2. remplir les champs définis par le schéma ;
3. générer le PNG final avec textes dynamiques et QR code ;
4. créer l'assertion Open Badges ;
5. baker l'assertion dans le PNG ;
6. enregistrer le badge généré.

Contraintes :

- garder la compatibilité avec l'émission actuelle simple nom/email ;
- ne pas casser la vérification existante ;
- conserver les métadonnées de recherche déjà utilisées ;
- documenter clairement les champs ajoutés dans l'assertion.

## 6. Documentation en français

Créer ou compléter une documentation utilisateur en français.

Sections à prévoir :

- présentation du constructeur ;
- différence entre schéma et modèle ;
- création d'un schéma ;
- ajout de plusieurs champs ;
- création d'un modèle visuel ;
- ajout de textes statiques ;
- ajout de textes dynamiques liés aux champs ;
- configuration du QR code ;
- prévisualisation ;
- émission d'un badge depuis un modèle ;
- limitations connues ;
- prochaines étapes.

Créer aussi une courte documentation technique pour les routes API :

- `/badge-constructor/schemas` ;
- `/badge-constructor/templates` ;
- endpoint d'aperçu PNG ;
- futur endpoint d'émission depuis un modèle.

## 7. Tests à prévoir

Tests fonctionnels :

- créer un schéma avec plusieurs champs ;
- supprimer un champ ;
- créer un modèle associé à un schéma ;
- ajouter plusieurs textes superposés ;
- utiliser un texte dynamique basé sur le nom ;
- utiliser un texte dynamique basé sur une date ;
- générer un aperçu PNG ;
- émettre un badge depuis un modèle ;
- vérifier le badge généré.

Tests de langue :

- vérifier que les messages utilisateur sont en français ;
- vérifier que la documentation est en français ;
- vérifier que les erreurs API visibles côté utilisateur sont en français.

## 8. Priorité proposée pour demain

1. Ajouter la gestion frontend de plusieurs champs dans un schéma.
2. Ajouter la sélection d'un champ comme source d'un texte superposé.
3. Modifier le rendu PNG pour remplacer les textes dynamiques par les valeurs saisies.
4. Ajouter un aperçu avec valeurs d'exemple.
5. Documenter le workflow utilisateur en français.

---

## 9. Avancement réalisé le 29/04/2026

Une première version fonctionnelle du workflow orienté opérateur a été ajoutée.

### Stabilisation préalable

Avant de poursuivre le constructeur, deux erreurs bloquantes ont été corrigées :

- restauration de `app/models.py` en fichier Python valide ;
- correction du re-baking PNG pour remplacer correctement l'ancien chunk `openbadges` au lieu de conserver l'ancienne assertion.

Les contrôles rapides sont maintenant verts :

```bash
/home/ubuntu/projects/Mode83/.venv/bin/python -m compileall app -q
/home/ubuntu/projects/Mode83/.venv/bin/python -m pytest tests -q
```

Résultat actuel : `17 passed`.

### Création et gestion de modèles

Le constructeur permet désormais :

- de créer un schéma avec des champs opérateur par défaut :
  - `Nom du cours` ;
  - `Numéro de certificat` ;
  - `Date d'émission` ;
- de créer un modèle visuel associé à un schéma ;
- de choisir le placement et la taille du QR code ;
- d'ajouter plusieurs textes superposés avant d'enregistrer le modèle ;
- de choisir pour chaque texte une source compréhensible par l'opérateur :
  - texte fixe ;
  - nom du participant ;
  - email du participant ;
  - nom du cours ;
  - numéro de certificat ;
  - date d'émission ;
- de définir la taille, la couleur et la position du texte ;
- d'utiliser des presets de position :
  - haut centre ;
  - centre ;
  - sous le nom ;
  - bas gauche ;
  - bas centre ;
  - bas droite ;
- de dupliquer un modèle existant pour créer rapidement une variante pour une autre formation.

### Prévisualisation du brouillon

Un endpoint de prévisualisation avant enregistrement a été ajouté :

```text
POST /badge-constructor/templates/preview-draft
```

Il génère un PNG temporaire à partir des paramètres saisis dans le formulaire, sans créer de modèle en base.

Les valeurs d'exemple utilisées dans l'aperçu sont :

```text
Nom : Alice Example
Email : alice@example.org
Cours : Blockchain Foundations
Numéro : BF-2026-001
Date : 2026-04-29
```

Objectif : permettre à l'opérateur de voir immédiatement le rendu d'un badge avant de sauvegarder le modèle.

### Émission depuis un modèle

Le workflow d'émission existant a été conservé. Le choix du modèle a été ajouté directement dans l'écran `Émission de badge`.

Comportement actuel :

1. l'opérateur choisit un modèle ;
2. le mode bascule automatiquement vers `PNG baked` ;
3. l'aperçu du modèle sélectionné s'affiche ;
4. les champs du schéma sont affichés ;
5. l'opérateur remplit les valeurs ;
6. le badge PNG baked est généré, téléchargé et enregistré.

Endpoint ajouté :

```text
POST /badge-constructor/templates/{template_id}/issue-baked
```

La charge attendue est de type :

```json
{
  "name": "Alice Example",
  "email": "alice@example.org",
  "field_values": {
    "course_name": "Blockchain Foundations",
    "certificate_number": "BF-2026-001",
    "issue_date": "2026-04-29"
  }
}
```

Le PNG final :

- rend les textes dynamiques avec les valeurs saisies ;
- ajoute le QR code selon le modèle ;
- bake l'assertion Open Badges dans le PNG ;
- sauvegarde le JSON dans `data/issued/` ;
- sauvegarde le PNG dans `data/baked/` ;
- synchronise le registre SQLite.

L'assertion conserve aussi :

```json
{
  "badge83_template": {
    "id": "...",
    "name": "...",
    "schema_id": "..."
  },
  "field_values": {
    "course_name": "...",
    "certificate_number": "..."
  }
}
```

### Tests ajoutés

Un test couvre maintenant l'émission baked depuis un modèle :

- génération du PNG ;
- sauvegarde du JSON ;
- extraction de l'assertion depuis le PNG ;
- conservation de `field_values` ;
- conservation des informations de modèle.

Fichier concerné :

```text
badge83/tests/unit/test_issuer.py
```

## 10. Points restant à améliorer

Les priorités suivantes restent ouvertes :

1. Rendre les presets de position adaptatifs à la taille réelle de l'image, au lieu d'utiliser des coordonnées fixes adaptées au badge de base.
2. Ajouter l'upload de l'image de fond directement dans le flux de création du modèle.
3. Ajouter l'édition d'un modèle existant depuis l'interface, pas seulement la création/duplication.
4. Ajouter un mode d'émission par lot CSV.
5. Ajouter une documentation utilisateur courte avec captures ou étapes numérotées.
6. Nettoyer progressivement le vocabulaire technique visible par l'opérateur.
