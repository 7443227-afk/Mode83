# Guide — modifier un modèle dans le constructeur de badges

## Objectif

Ce guide explique comment modifier un modèle de badge existant dans l'interface d'administration Badge83.

La modification d'un modèle permet de corriger ou d'adapter :

- le nom du modèle ;
- le schéma associé ;
- la position et la taille du QR code ;
- les textes affichés sur le PNG ;
- les textes dynamiques liés aux champs remplis lors de l'émission.

## Accéder au constructeur

1. Ouvrir l'interface d'administration Badge83.
2. Dans le menu de gauche, cliquer sur **Constructeur de badge**.
3. Vérifier que les blocs **Schémas disponibles** et **Modèles disponibles** sont chargés.

## Modifier un modèle existant

Dans le bloc **Modèles disponibles** :

1. repérer le modèle à modifier ;
2. cliquer sur **Modifier** ;
3. la zone de formulaire passe de **Nouveau modèle** à **Modifier le modèle** ;
4. le nom, le schéma, les paramètres QR et les textes du modèle sont chargés dans le formulaire ;
5. modifier les valeurs souhaitées ;
6. cliquer sur **Enregistrer les modifications**.

Après l'enregistrement :

- le modèle est mis à jour en base ;
- la liste des modèles est rechargée ;
- l'aperçu du modèle modifié est affiché.

Pour sortir du mode modification sans enregistrer, cliquer sur **Annuler** en haut du formulaire du modèle.

## Modifier un texte superposé

Lorsqu'un modèle est en cours de création ou de modification, les textes déjà ajoutés apparaissent dans la liste sous le bouton **Prévisualiser le brouillon**.

Pour modifier un texte :

1. cliquer sur **Modifier** à côté du texte concerné ;
2. les champs du texte sont rechargés dans le formulaire :
   - source du texte ;
   - texte fixe, si applicable ;
   - position X/Y ;
   - taille ;
   - couleur ;
3. ajuster les valeurs ;
4. cliquer sur **Mettre à jour ce texte**.

Pour annuler la modification du texte en cours, cliquer sur **Annuler** à côté du bouton de mise à jour du texte.

## Ajouter un nouveau texte

Si aucun texte n'est en cours de modification :

1. choisir une source dans **Source du texte** ;
2. saisir le texte fixe si la source est **Texte fixe** ;
3. définir la position, la taille et la couleur ;
4. cliquer sur **Ajouter ce texte au modèle**.

Le texte est ajouté à la liste des textes du modèle en préparation.

## Prévisualiser avant sauvegarde

Avant d'enregistrer un modèle ou une modification :

1. cliquer sur **Prévisualiser le brouillon** ;
2. vérifier le rendu PNG ;
3. ajuster les textes ou le QR code si nécessaire ;
4. enregistrer le modèle uniquement lorsque le rendu est correct.

La prévisualisation utilise des valeurs d'exemple pour les textes dynamiques, par exemple un nom, un email, un cours, un numéro de certificat et une date.

## Utiliser le modèle modifié pour émettre un badge

Après modification :

1. aller dans **Émission de badge** ;
2. choisir le modèle dans **Modèle de badge** ;
3. le mode passe en **PNG baked** ;
4. remplir le nom, l'email et les champs du modèle ;
5. cliquer sur **Émettre le badge**.

Le PNG généré utilise la dernière version enregistrée du modèle.

## Points d'attention

- Modifier un modèle affecte les prochains badges émis avec ce modèle.
- Les badges déjà émis ne sont pas régénérés automatiquement.
- Pour créer une variante sans toucher au modèle original, utiliser **Dupliquer**, puis modifier la copie.
- Après une modification importante, il est recommandé d'émettre un badge de test et de le vérifier via l'outil de vérification PNG.
