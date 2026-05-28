# Guide — modifier un modèle dans le constructeur de badges

## Objectif

Ce guide explique comment modifier un modèle de badge existant dans l'interface d'administration Badge83.

La modification d'un modèle permet de corriger ou d'adapter :

- le nom du modèle ;
- le schéma associé ;
- le fond PNG du badge ;
- la position et la taille du QR code ;
- les textes affichés sur le PNG ;
- les textes dynamiques liés aux champs remplis lors de l'émission.

## Accéder au constructeur

1. Ouvrir l'interface d'administration Badge83.
2. Dans le menu de gauche, cliquer sur **Constructeur de badge**.
3. Vérifier que les blocs **Schémas disponibles** et **Modèles disponibles** sont chargés.

## Scénario complet recommandé

Pour valider qu'un modèle est utilisable par un opérateur non technique, suivre le flux complet ci-dessous :

1. créer ou vérifier un **schéma** avec les champs nécessaires à l'émission ;
2. créer un **modèle** associé à ce schéma ;
3. choisir le fond PNG du badge ou conserver le fond standard MODE83 ;
4. placer le QR code avec une marge suffisante pour le scan mobile ;
5. ajouter au moins un texte fixe ou dynamique ;
6. utiliser **Voir l'aperçu avant enregistrement** ;
7. ajuster les textes ou le QR code par glisser-déposer si nécessaire ;
8. relancer l'aperçu après chaque modification visuelle ;
9. enregistrer le modèle ;
10. utiliser le bloc **Modèle prêt à tester** pour émettre un badge individuel ;
11. vérifier le PNG baked obtenu ;
12. revenir au modèle si le rendu final doit être corrigé ;
13. tester ensuite l'émission groupée avec le modèle validé.

L'interface affiche un encadré **Conseil opérateur** rappelant que l'enregistrement est bloqué lorsque le dernier aperçu ne correspond plus aux réglages affichés. Ce comportement évite d'enregistrer un modèle dont le rendu final n'a pas été contrôlé.

## Modifier un modèle existant

Dans le bloc **Modèles disponibles** :

1. repérer le modèle à modifier ;
2. cliquer sur **Modifier** ;
3. la zone de formulaire passe de **Nouveau modèle** à **Modifier le modèle** ;
4. le nom, le schéma, les paramètres QR et les textes du modèle sont chargés dans le formulaire ;
5. modifier les valeurs souhaitées ;
6. cliquer sur **Voir l'aperçu avant enregistrement** après les dernières modifications ;
7. cliquer sur **Enregistrer** en haut du formulaire ou sur **Enregistrer les modifications** en bas du formulaire.

Après l'enregistrement :

- le modèle est mis à jour en base ;
- la liste des modèles est rechargée ;
- l'aperçu du modèle modifié est affiché.
- un bloc **Modèle prêt à tester** propose de basculer directement vers l'émission individuelle ou l'émission groupée avec ce modèle déjà sélectionné.

Pour sortir du mode modification sans enregistrer, cliquer sur **Annuler** en haut du formulaire du modèle.

## Choisir ou réinitialiser le fond PNG

Le constructeur permet d'associer un fond PNG à chaque modèle de badge.

Pour utiliser un fond personnalisé :

1. dans le formulaire du modèle, choisir un fichier dans **Fond PNG du badge** ;
2. vérifier le rendu avec **Voir l'aperçu avant enregistrement** ;
3. enregistrer le modèle.

Si aucun fichier n'est choisi, Badge83 utilise automatiquement le fond standard défini par le projet.

Lors de la modification d'un modèle existant :

- si aucun nouveau fichier n'est sélectionné, le fond déjà enregistré est conservé ;
- si un nouveau PNG est sélectionné, il remplace le fond précédent ;
- le bouton **Utiliser le fond standard** permet de supprimer le fond personnalisé et de revenir au badge standard.

Le fichier fourni doit être un PNG valide. Une vérification est effectuée côté interface et côté serveur afin d'éviter l'enregistrement d'un fichier non compatible.

## Modifier un texte superposé

Lorsqu'un modèle est en cours de création ou de modification, les textes déjà ajoutés apparaissent dans la liste sous le bouton **Voir l'aperçu avant enregistrement**.

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

## Positionner précisément les textes sur le badge

Le constructeur dispose d'une zone de prévisualisation agrandie et d'outils de précision pour placer les textes destinés à être intégrés dans le PNG final.

### Zoom de la prévisualisation

Dans le bloc **Aperçu du modèle**, le sélecteur **Zoom** permet de choisir :

- **Fit** : ajuste l'image à la largeur disponible ;
- **100%** ;
- **150%** ;
- **200%** ;
- **300%**.

Le zoom ne modifie pas les coordonnées enregistrées. Il sert uniquement à améliorer le confort de placement dans l'interface. Les positions restent calculées en pixels réels du PNG.

### Déplacement à la souris

Les textes ajoutés au modèle apparaissent sous forme de poignées visuelles sur le badge. L'opérateur peut les déplacer directement par glisser-déposer.

Lors du déplacement :

- les coordonnées X/Y sont mises à jour dans les champs du formulaire ;
- le texte sélectionné est mis en évidence ;
- le statut affiche la position courante du texte.

### Déplacement fin au pixel

Sous la prévisualisation, les boutons directionnels **↑ ↓ ← →** permettent d'ajuster le texte sélectionné :

- clic simple : déplacement de **1 pixel** ;
- `Shift` + clic : déplacement de **10 pixels**.

Cette fonction est recommandée pour finaliser l'alignement après un premier placement à la souris.

Le bouton central **Texte** recharge le texte actif dans le formulaire. Il sert de repère opérateur lorsque plusieurs textes sont présents sur le même badge.

## Ajouter un nouveau texte

Si aucun texte n'est en cours de modification :

1. choisir une source dans **Que doit afficher ce texte ?** ;
2. saisir le texte fixe si la source est **Texte fixe** ;
3. définir la position, la taille et la couleur ;
4. cliquer sur **Ajouter ce texte au modèle**.

Le texte est ajouté à la liste des textes du modèle en préparation.

## Prévisualiser avant sauvegarde

1. vérifier que le modèle possède un nom, un schéma et au moins un texte ;
2. cliquer sur **Voir l'aperçu avant enregistrement** ;
3. vérifier le rendu PNG ;
4. ajuster les textes ou le QR code si nécessaire ;
5. relancer l'aperçu si une valeur a été modifiée ;
6. enregistrer le modèle uniquement lorsque le rendu est correct.

La prévisualisation utilise des valeurs d'exemple pour les textes dynamiques, par exemple un nom, un email, un cours, un numéro de certificat et une date.

Depuis la dernière amélioration du constructeur, l'interface bloque l'enregistrement si le brouillon n'a pas été prévisualisé après les dernières modifications. Les changements suivants invalident l'aperçu et demandent une nouvelle prévisualisation : nom du modèle, schéma, fond PNG, source ou contenu d'un texte, position, taille, couleur, position du QR ou taille du QR.

Si une configuration est incomplète, le constructeur affiche un message lisible dans la zone de statut, par exemple : modèle sans schéma, aucun texte ajouté, texte fixe vide ou taille de QR hors limites.

Les libellés de positionnement utilisent volontairement un vocabulaire opérateur : **En bas à droite**, **En haut à gauche**, **En bas, centré**, etc. Les coordonnées X/Y restent disponibles dans le bloc de réglage précis pour les ajustements fins, mais elles ne sont pas nécessaires pour le flux standard.

## Dupliquer ou supprimer un modèle

Dans le bloc **Modèles disponibles**, chaque modèle propose plusieurs actions :

- **Aperçu** : affiche le rendu du modèle ;
- **Modifier** : charge le modèle dans le formulaire ;
- **Dupliquer** : crée une copie du modèle pour préparer une variante ;
- **Supprimer** : retire le modèle de la liste des modèles disponibles.

La suppression demande une confirmation avant exécution. Elle désactive le modèle dans la base afin qu'il ne soit plus proposé pour les nouvelles émissions. Les badges déjà émis ne sont pas régénérés ni supprimés.

## Positionner le QR code avec des marges de sécurité

Le constructeur permet de déplacer le QR code directement sur l'aperçu du badge. Cette liberté est utile pour adapter le rendu au modèle graphique, mais elle doit rester encadrée pour préserver la lisibilité au scan.

Règles opérateur recommandées :

1. garder une marge visuelle autour du QR code ;
2. éviter les zones contenant du texte important : nom, email, intitulé du badge, date ou numéro de certificat ;
3. ne pas placer le QR code trop près des bords du badge ;
4. vérifier systématiquement le rendu dans **Voir l'aperçu avant enregistrement** ;
5. émettre un badge de test après une modification importante du placement.

Règles techniques à conserver dans l'outil :

- le QR code doit rester entièrement dans les limites du PNG ;
- les coordonnées personnalisées doivent être bornées par rapport à la taille réelle de l'image ;
- une marge de sécurité par défaut doit être prévue pour éviter un placement accidentel sur une zone critique ;
- le scan du QR code doit être testé lorsque le modèle visuel change fortement.

Cette règle suit le principe retenu pour Badge83 : donner de la flexibilité à l'opérateur sans créer de risque de badge visuellement valide mais difficilement vérifiable.

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
- Après un déplacement manuel du QR code, vérifier aussi le scan depuis un téléphone afin de confirmer que la marge et le contraste restent suffisants.
