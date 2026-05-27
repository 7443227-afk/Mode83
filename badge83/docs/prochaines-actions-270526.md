# Badge83 — Prochaines actions après checkpoint du 27/05/2026

Date : 27/05/2026

## Contexte du checkpoint

Le checkpoint courant stabilise plusieurs axes importants du produit :

- documentation d'exploitation Docker : sauvegarde, restauration, supervision légère et renouvellement TLS ;
- amélioration ergonomique initiale du constructeur de badges ;
- traçabilité de l'émission groupée avec affichage de l'identifiant de session ;
- clarification des pages publiques de vérification QR et HostedBadge ;
- limitation de l'exposition des données personnelles sur les pages publiques.

Le fichier `badge83/data/registry.db` est considéré comme une donnée runtime. Il
n'est pas inclus dans ce checkpoint, même s'il existe encore dans l'historique Git.
Les données opérationnelles doivent être conservées via `runtime-data/` et les
procédures de sauvegarde documentées.

## Ordre de réalisation recommandé

### 1. Finaliser la documentation Docker et exploitation

Objectif : rendre l'installation et l'exploitation reproductibles pour un serveur
neuf.

Actions :

- relire la procédure complète de déploiement production ;
- ajouter une checklist `avant déploiement` ;
- distinguer clairement développement local, Docker local et Docker production ;
- confirmer que les fichiers `.env` d'exemple ne contiennent aucun secret réel ;
- valider les procédures sauvegarde/restauration sur une copie de test.

Critère de réussite : une nouvelle machine peut lancer Badge83 en suivant la
documentation sans accompagnement oral.

### 2. Terminer l'ergonomie du constructeur de badges

Objectif : permettre à un opérateur non technique de créer et réutiliser un modèle.

Actions :

- tester le flux complet création/modification/sauvegarde de modèle ;
- vérifier la cohérence entre aperçu et PNG final ;
- améliorer les messages d'erreur si une configuration visuelle est incomplète ;
- mettre à jour le guide opérateur du constructeur.

Critère de réussite : un modèle créé dans le constructeur peut servir en émission
individuelle puis groupée sans correction manuelle.

### 3. Consolider l'émission groupée CSV/Excel

Objectif : stabiliser l'usage formation réel avec cohorte, ZIP et historique.

Actions :

- rejouer les scénarios CSV et Excel ;
- vérifier lignes valides, lignes invalides et doublons ;
- confirmer l'affichage de `session_id` après génération du ZIP ;
- documenter la consultation de l'historique de session ;
- conserver le principe d'émission partielle contrôlée.

Critère de réussite : une cohorte peut être émise avec rapport compréhensible et
archive ZIP vérifiable.

### 4. Renforcer la vérification Open Badges

Objectif : rendre le résultat de vérification plus explicite pour un tiers.

Actions :

- créer un module léger `app/openbadges_checks.py` ;
- produire un rapport structuré `valid`, `errorCount`, `warningCount`, `messages` ;
- vérifier les champs de base Assertion, BadgeClass et Issuer ;
- contrôler la chaîne HostedBadge ;
- afficher les résultats principaux sur la page de vérification.

Critère de réussite : la page indique pourquoi un badge est considéré valide,
incomplet ou invalide.

### 5. Préparer une démonstration complète

Objectif : disposer d'un scénario produit de 10 à 15 minutes.

Scénario :

1. connexion opérateur ;
2. constructeur de badge ;
3. émission individuelle ;
4. vérification QR mobile ;
5. import CSV/Excel ;
6. génération ZIP ;
7. historique de session ;
8. endpoints publics Open Badges ;
9. sauvegarde/restauration Docker.

Critère de réussite : la démonstration montre une valeur utilisateur claire sans
dépendre d'explications techniques longues.

### 6. Reporter le prototype blockchain après stabilisation

Objectif : éviter de détourner l'effort produit avant la démo stable.

Le prototype d'ancrage blockchain reste prévu, mais uniquement après validation
des étapes précédentes. Il devra rester optionnel, désactivé par défaut et sans
donnée personnelle on-chain.
