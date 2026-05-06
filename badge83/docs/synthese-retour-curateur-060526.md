# Synthèse — retour du curateur et ajustements Badge83 — 06/05/2026

## Contexte

Le curateur a validé l'axe de travail engagé sur Badge83 : stabiliser le noyau technique existant et consacrer du temps aux finitions d'interface pour transformer le prototype technique en outil réellement utilisable sur le terrain.

Le retour confirme que l'amélioration des interfaces opérateur, des pages de vérification et du constructeur de badges est pertinente pour le livrable de fin de stage.

## Points confirmés

### 1. Priorité à l'expérience utilisateur

Les pages de vérification ne doivent pas submerger l'utilisateur avec des informations techniques brutes.

Informations à afficher en priorité :

- statut visuel de validation ;
- titulaire du badge ;
- email ou identité affichable selon la politique de confidentialité ;
- nom du badge ;
- organisme émetteur ;
- date de délivrance ;
- action simple pour vérifier un autre badge ou accéder au lien public.

### 2. Détails techniques accessibles mais repliés

L'assertion JSON brute et les détails Open Badges avancés doivent rester disponibles pour un expert, mais derrière une action volontaire :

- **Afficher les détails techniques** ;
- **Vue avancée** ;
- **Assertion JSON brute**.

Cette séparation permet de satisfaire deux publics :

- opérateur, recruteur ou utilisateur final : compréhension rapide du résultat ;
- expert technique : accès possible à la preuve Open Badges et aux informations de diagnostic.

### 3. Positionnement libre du QR code à encadrer

La possibilité de déplacer le QR code dans le constructeur est utile, mais elle doit être accompagnée de règles de protection :

- marges de sécurité par défaut ;
- interdiction pratique de sortir le QR code des limites de l'image ;
- attention aux zones textuelles importantes ;
- vérification du rendu en prévisualisation ;
- test de scan après modification importante du modèle.

L'objectif est d'éviter qu'un opérateur place accidentellement le QR code sur un nom, une date, un intitulé de formation ou trop près d'un bord, ce qui pourrait nuire à la lisibilité lors du scan.

## Décision de méthode

Le noyau technique reste stable :

- format Open Badges conservé ;
- assertions JSON non modifiées sans nécessité ;
- logique de validation existante préservée ;
- baking PNG conservé ;
- endpoints publics HostedBadge conservés.

Le travail porte prioritairement sur l'enveloppe applicative : lisibilité, parcours opérateur, messages d'erreur, hiérarchie visuelle, masquage progressif des détails techniques et sécurisation ergonomique du constructeur.

## Documents mis à jour

- `badge83/docs/guide-edition-modele-constructeur.md` : ajout des règles de positionnement QR avec marges de sécurité.
- `badge83/docs/bureau-verification-mode83.md` : clarification du principe de vue avancée pour les détails techniques et le JSON brut.
- `badge83/docs/plan-amelioration-interfaces-operateur-060526.md` : intégration des recommandations du curateur dans les priorités UX.

## Prochaines actions recommandées

1. Ajouter dans l'interface un panneau replié **Afficher les détails techniques** sur les pages de vérification.
2. Étendre les messages de validation lisibles : succès, erreur, avertissement, information.
3. Ajouter des marges de sécurité visibles ou implicites autour du QR code dans le constructeur.
4. Vérifier manuellement le scan QR après déplacement personnalisé.
5. Continuer à documenter les finitions UX séparément des changements techniques du noyau.