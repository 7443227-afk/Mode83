# Plan de travail — Amélioration des interfaces opérateur Badge83 — 06/05/2026

## Objectif général

Améliorer le confort d'utilisation de Badge83 pour un opérateur non technique, en réduisant la visibilité des détails techniques au profit d'informations directement exploitables : titulaire du badge, email, statut, actions rapides, résultat de vérification et parcours guidé.

Le but n'est pas de modifier le modèle Open Badges ni la logique de validation, mais de rendre l'interface plus lisible, plus sûre et plus rapide pour les usages quotidiens.

À la suite du retour du curateur du 06/05/2026, deux règles UX sont confirmées comme structurantes :

- conserver un accès aux preuves techniques, mais masquer l'assertion JSON brute derrière une action explicite de type **détails techniques** ou **vue avancée** ;
- encadrer le positionnement libre du QR code par des marges de sécurité et des limites par défaut, afin d'éviter qu'il soit placé sur un texte important ou trop près des bords.

## Interfaces concernées

- `badge83/templates/index.html` : centre de contrôle administrateur.
- `badge83/templates/verify_desk.html` : bureau de vérification par PNG.
- `badge83/templates/verify_badge.html` : page publique de vérification complète.
- `badge83/templates/verify_qr.html` : page mobile après scan QR.
- `badge83/templates/auth_login.html` : connexion.
- `badge83/templates/index_legacy.html` : interface ancienne, à conserver comme point de retour.

## Scénarios opérateur à privilégier

1. Rechercher rapidement un badge déjà émis.
2. Identifier immédiatement le titulaire, son email, le badge et son statut.
3. Émettre un nouveau badge avec le minimum d'ambiguïté.
4. Utiliser un modèle visuel sans manipuler de JSON.
5. Vérifier un PNG et comprendre le résultat sans lire de réponse API brute.
6. Accéder aux détails techniques uniquement si nécessaire.

## Priorité 1 — Rendre le registre plus humain

### Actions prévues

- Remplacer les colonnes trop techniques ou mixtes par des intitulés cohérents en français.
- Mettre en avant :
  - nom du titulaire ;
  - email ;
  - nom du badge ;
  - date de délivrance ;
  - état JSON / PNG ;
  - disponibilité du lien public.
- Conserver l'identifiant UUID, mais en information secondaire.
- Ajouter des filtres rapides :
  - aujourd'hui ;
  - cette semaine ;
  - PNG uniquement ;
  - liens publics actifs ;
  - enregistrements incomplets.

### Critère de réussite

Un opérateur doit pouvoir retrouver un badge sans avoir à ouvrir l'inspecteur JSON.

## Priorité 2 — Améliorer le parcours d'émission

### Actions prévues

- Transformer progressivement le formulaire d'émission en parcours guidé :
  1. choix du modèle ;
  2. saisie du titulaire ;
  3. champs complémentaires ;
  4. prévisualisation ;
  5. émission ;
  6. résultat et actions rapides.
- Ajouter une carte de résultat après émission avec :
  - nom ;
  - email ;
  - badge ;
  - date ;
  - bouton de téléchargement PNG ;
  - lien de vérification ;
  - lien QR ;
  - action « émettre un autre badge similaire ».
- Ajouter une validation plus visible de l'email.
- Préremplir automatiquement les valeurs simples lorsque c'est possible : date du jour, modèle récemment utilisé.

### Critère de réussite

L'opérateur sait clairement si le badge a été émis, où le télécharger et comment le vérifier.

## Priorité 3 — Remplacer les sorties JSON par des messages lisibles

### Actions prévues

- Ajouter des notifications visuelles de type toast ou alerte :
  - succès ;
  - erreur ;
  - avertissement ;
  - information.
- Conserver le JSON technique dans un panneau « détails techniques » ou « mode expert ».
- Sur les pages de vérification, afficher d'abord un statut visuel et un résumé humain : valide / invalide, titulaire, email, badge, émetteur, date.
- Placer l'assertion JSON brute, les URLs techniques et les identifiants longs dans un panneau escamotable intitulé « détails techniques » ou « vue avancée ».
- Normaliser les messages d'erreur :
  - PNG non valide ;
  - badge introuvable ;
  - assertion inaccessible ;
  - émetteur externe ;
  - données incomplètes.

### Critère de réussite

Une erreur doit indiquer à l'opérateur quoi faire ensuite.

## Priorité 4 — Séparer mode opérateur et mode expert

### Actions prévues

- Ajouter un mode d'affichage simplifié pour les usages courants.
- Masquer par défaut :
  - éditeur JSON ;
  - sortie système brute ;
  - détails techniques des assertions.
- Garder un bouton « Afficher les détails techniques » pour l'administrateur.

### Critère de réussite

L'interface quotidienne ne doit pas exposer de fonctions dangereuses ou trop techniques sans intention explicite.

## Priorité 5 — Améliorer le bureau de vérification

### Actions prévues

- Ajouter une zone drag-and-drop pour déposer un PNG.
- Mettre en avant le résultat : valide, invalide, émetteur externe.
- Afficher en priorité :
  - titulaire ;
  - email ;
  - badge ;
  - émetteur ;
  - date.
- Ajouter un bouton « vérifier un autre badge ».
- Prévoir une petite historique de session des dernières vérifications.

### Critère de réussite

Le bureau de vérification doit pouvoir être utilisé par une personne de secrétariat sans connaissance Open Badges.

## Priorité 6 — Consolider la page QR mobile

### Actions prévues

- Conserver l'affichage humain récemment ajouté : nom et email du titulaire.
- Ajouter si disponible :
  - nom du badge ;
  - date de délivrance ;
  - émetteur ;
  - état de confiance.
- Déplacer les identifiants techniques dans une zone secondaire.
- Prévoir, si des informations Open Badges avancées doivent être exposées, un bloc replié par défaut plutôt qu'un affichage JSON immédiat.
- Prévoir une stratégie d'affichage public de l'email : complet, masqué ou caché selon le niveau de confidentialité attendu.

### Critère de réussite

Après scan QR, la première information visible doit répondre à la question : « ce badge appartient-il à cette personne ? ».

## Priorité 7 — Améliorer le constructeur de modèles

### Actions prévues

- Conserver le déplacement drag-and-drop du texte et du QR code.
- Ajouter progressivement :
  - grille de positionnement ;
  - boutons d'alignement ;
  - verrouillage du QR ;
  - marges de sécurité par défaut autour du QR ;
  - contrôle visuel si le QR recouvre une zone textuelle importante ;
  - liste des calques ;
  - annuler/rétablir ;
  - zoom du preview.
- Clarifier la différence entre schéma de données et modèle visuel.

### Règles de sécurité QR à appliquer

- Le QR code doit rester dans les limites de l'image, même en mode personnalisé.
- Une marge minimale par défaut doit être conservée par rapport aux bords.
- L'opérateur doit être encouragé à éviter les zones contenant le nom, l'email, le titre du badge ou la date.
- La prévisualisation doit rester obligatoire avant sauvegarde d'un modèle modifié.
- Un test de scan réel doit être recommandé après tout changement important de modèle graphique.

### Critère de réussite

Un modèle doit pouvoir être ajusté sans calculer manuellement des coordonnées X/Y.

## Priorité 8 — Mémoriser les préférences opérateur

### Actions prévues

- Sauvegarder dans `localStorage` :
  - langue ;
  - dernier onglet ;
  - filtres actifs ;
  - dernier modèle utilisé ;
  - mode d'émission préféré.

### Critère de réussite

L'opérateur retrouve son environnement après un rafraîchissement ou une reconnexion.

## Planning proposé pour demain

### Matin

1. Harmoniser les libellés du registre.
2. Ajouter l'affichage direct du titulaire et de l'email dans la liste principale.
3. Préparer une première version de notifications lisibles.

### Après-midi

1. Améliorer la carte de résultat après émission.
2. Ajouter la mémorisation du dernier onglet et de la langue.
3. Revoir la page QR mobile pour afficher badge, émetteur et date si disponibles.
4. Documenter les changements réalisés.

## Points d'attention

- Ne pas modifier le format Open Badges sans nécessité.
- Ne pas supprimer l'accès aux détails techniques : seulement les rendre moins visibles par défaut.
- Vérifier l'impact sur mobile et tablette.
- Faire attention à l'affichage public des données personnelles, notamment l'email.

## Livrables attendus

- Interface principale plus lisible pour un opérateur.
- Documentation mise à jour.
- Liste claire des améliorations restantes.
- Validation manuelle des parcours : recherche, émission, vérification PNG, vérification QR.