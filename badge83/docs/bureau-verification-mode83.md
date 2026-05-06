# Bureau de vérification MODE83

## Objet du document

Cette note décrit la page **Bureau de vérification** mise en place dans Badge83 pour un usage administratif simple.

L’objectif est de proposer un écran clair, adapté à un personnel non technique, capable de :

- ouvrir un badge PNG ;
- vérifier rapidement sa validité ;
- visualiser les informations utiles ;
- voir si d’autres certificats sont liés au même profil.

---

## 1. Route et position dans l’interface

La page est accessible via :

- `/verify-desk`

Elle est reliée à la page principale :

- depuis le bandeau supérieur ;
- depuis le menu latéral.

Dans l’interface française, cette page est nommée :

- **Bureau de vérification**

---

## 2. Parcours utilisateur visé

Le parcours prévu est volontairement court.

### Étapes

1. l’utilisateur ouvre la page ;
2. il sélectionne un badge PNG ;
3. il voit un aperçu du badge chargé ;
4. il lance la vérification ;
5. l’application affiche le résultat ;
6. elle indique si le badge vient de MODE83 ou d’un autre organisme ;
7. elle propose une liste d’autres certificats liés lorsque c’est possible.

---

## 3. Informations affichées

Après vérification réussie, la page affiche :

- `Assertion ID`
- `Nom / prénom`
- `Email`
- `Badge`
- `Issuer`
- `Organisation émettrice`
- `Date de délivrance`

Les informations humaines doivent rester prioritaires dans l'interface : statut visuel, titulaire, email, badge, organisme émetteur et date. L'objectif est qu'un opérateur ou un recruteur comprenne immédiatement si le badge est exploitable, sans devoir lire l'assertion Open Badges brute.

Les détails techniques doivent être accessibles, mais ils ne doivent pas être affichés en premier niveau. La pratique retenue est d'utiliser un bouton ou panneau escamotable de type :

- **Afficher les détails techniques** ;
- **Vue avancée** ;
- **Assertion JSON brute**.

Ce panneau peut contenir l'assertion JSON extraite, les identifiants techniques, les URLs HostedBadge et les informations utiles à un expert. Il reste donc possible d'auditer la preuve technique, tout en conservant une page simple pour l'usage courant.

### Format de date

La date est affichée au format :

- `JJ/MM/AAAA`

Exemple :

- `20/04/2026`

---

## 4. Gestion de l’issuer

Le Bureau de vérification ne montre pas l’URL brute de l’émetteur comme information principale.

Pour simplifier la lecture, deux valeurs seulement sont affichées :

- `mode83`
- `autre organisme`

### Cas A — badge MODE83

Si le badge a été émis par MODE83, la page affiche :

- `Issuer : mode83`
- `Organisation émettrice : mode83`
- message : `Badge émis par mode83`

### Cas B — badge externe mais valide

Si le badge est valide mais n’a pas été émis par MODE83, la page affiche :

- `Issuer : autre organisme`
- `Organisation émettrice : autre organisme`
- message : `Badge valide, mais émis par un autre organisme`

Cette logique est utile pour éviter de rejeter un badge simplement parce qu’il est externe à l’organisation.

---

## 5. Certificats liés

Le bloc `Autres certificats liés` affiche, lorsque les données sont disponibles :

- l’identifiant du badge ;
- le nom ;
- l’email ;
- le nom du badge ;
- l’issuer ;
- la date de délivrance ;
- le type de correspondance (`email`, `name` ou les deux).

Cette liste repose sur les hash de recherche stockés localement.

---

## 6. Recherche par hash

Le rapprochement entre certificats repose sur les champs :

- `search.email_hash`
- `search.name_hash`

Ces valeurs sont calculées à l’émission et utilisées dans l’interface admin et dans le Bureau de vérification.

Pour les badges plus anciens :

- la recherche par email peut parfois être reconstruite via `recipient.identity` + `salt` ;
- la recherche par nom n’est pas garantie si le nom n’avait pas été stocké localement.

---

## 7. PNG baked — convention de nommage

Les badges émis en format PNG baked sont désormais téléchargés avec un nom lisible.

### Format utilisé

- `<numéro>_mode83_<jjmmaaa>.png`

### Exemple

- `37_mode83_200426.png`

### Intérêt

Cette convention facilite :

- le classement des fichiers ;
- l’identification rapide d’un badge MODE83 ;
- la lecture humaine de la date d’émission.

---

## 8. Cas d’erreur

Si le PNG ne contient pas un badge baked exploitable, la page :

- garde le flux utilisateur sur le Bureau de vérification ;
- affiche un message d’erreur lisible ;
- n’affiche pas de faux résultat.

Les erreurs techniques détaillées peuvent être conservées dans le panneau avancé, mais le message principal doit indiquer l'action suivante possible : choisir un autre PNG, vérifier que le fichier est bien un badge baked, ou contacter un administrateur.

---

## 9. Intérêt pour la démonstration

Le Bureau de vérification apporte une vraie valeur de démonstration car il permet de montrer :

- un usage concret ;
- une vérification compréhensible par un non spécialiste ;
- une distinction claire entre badge MODE83 et badge externe ;
- une recherche de certificats liés à un même profil.

Il constitue donc une interface adaptée à une présentation publique, à une démonstration encadrée ou à un usage de secrétariat.

---

## 10. Pistes de suite

Parmi les évolutions désormais pertinentes pour la suite du projet :

- ajout d’un QR code pointant vers une page de vérification publique ;
- enrichissement du rapport de vérification ;
- généralisation d'un panneau **détails techniques / vue avancée** pour masquer l'assertion JSON brute par défaut ;
- amélioration du rapprochement entre certificats ;
- réflexion sur une **base de données locale** pour stocker proprement :
  - les badges émis ;
  - les métadonnées administratives ;
  - les index de recherche ;
  - les relations entre badges, émissions et vérifications.

Une telle base pourrait simplifier les recherches, les exports, les statistiques et la gestion du registre à mesure que le volume de badges augmente.