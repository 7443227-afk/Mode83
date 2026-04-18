# Plan de travail — QR code de vérification sur badge

## Idée

Étudier la génération et l’apposition d’un **QR code sur le badge** afin de permettre une vérification rapide par le titulaire ou par un tiers, sans manipulation technique complexe.

Le principe est simple :

- le badge contient un QR code visible ;
- le QR code pointe vers une ressource de vérification ;
- l’utilisateur scanne le code avec un téléphone ou un lecteur standard ;
- la page ouverte permet de contrôler rapidement la validité du badge.

---

## Objectif produit

Réduire au maximum le nombre d’étapes nécessaires pour vérifier un badge.

Au lieu de :

- chercher l’ID du badge ;
- ouvrir manuellement l’outil de vérification ;
- coller une URL ou téléverser un fichier ;

on permet :

- un scan direct ;
- une ouverture immédiate de la page de vérification ;
- une lecture simple du résultat.

---

## Ce que peut contenir le QR code

### Option A — Assertion URL publique

Le QR code encode directement l’URL publique de l’assertion.

Exemple :

- `https://.../assertions/<uuid>`

Avantages :

- simple ;
- fidèle au modèle HostedBadge ;
- directement exploitable par des outils externes.

Limites :

- l’URL d’assertion n’est pas toujours la meilleure page pour un humain non technique.

### Option B — URL dédiée de vérification humaine

Le QR code pointe vers une page du projet pensée pour les humains.

Exemple :

- `https://.../verify/badge/<uuid>`

Cette page peut :

- afficher le nom du badge ;
- afficher son statut ;
- résumer l’issuer ;
- indiquer si le badge est valide, trouvé, cohérent et non modifié.

Avantages :

- meilleure UX ;
- plus clair pour un recruteur, un organisme ou le titulaire.

Limites :

- nécessite une page dédiée côté projet.

### Option C — URL d’entrée dans l’outil de vérification existant

Le QR code ouvre directement le centre de vérification avec un paramètre prérempli.

Exemple :

- `https://.../verify?badge_id=<uuid>`
- ou `https://.../verify?assertion_url=...`

Avantages :

- réutilise les routes et outils déjà présents ;
- peu coûteux à mettre en place.

Limites :

- moins élégant qu’une page dédiée ;
- dépend de l’ergonomie actuelle du centre de vérification.

---

## Cas d’usage visés

### 1. Vérification par le titulaire

Le porteur du badge scanne le QR pour accéder rapidement à la preuve publique de validité.

### 2. Vérification par un tiers

Un recruteur, un formateur, un employeur ou un auditeur scanne le code et obtient immédiatement la page de contrôle.

### 3. Vérification sur support imprimé ou image partagée

Même si le badge circule sous forme d’image ou d’impression, le QR peut conserver un point d’entrée clair vers la vérification officielle.

---

## Contraintes techniques

### 1. Placement graphique

Le QR code doit être ajouté sans dégrader le design du badge.

Questions à étudier :

- emplacement (coin, marge, zone dédiée) ;
- taille minimale lisible ;
- contraste suffisant ;
- compatibilité avec les variations de template.

### 2. Compatibilité avec le baking PNG

Il faut garantir que l’ajout du QR :

- ne casse pas la génération du PNG ;
- ne perturbe pas le mécanisme baked ;
- reste cohérent avec le contenu Open Badges embarqué.

### 3. URL publique stable

Le QR code doit idéalement pointer vers un domaine et une route stables.

Sinon :

- le badge reste visuellement valide ;
- mais le scan peut mener à un lien obsolète.

---

## Limites et précautions

### 1. Le QR ne remplace pas la vérification

Le QR code ne constitue pas une preuve cryptographique en soi.

Il ne fait que :

- faciliter l’accès à la vérification ;
- accélérer l’entrée dans le bon flux de contrôle.

### 2. Risque d’obsolescence des liens

Si le domaine ou la structure des routes change, les anciens QR peuvent devenir partiellement inutiles.

### 3. Risque de surcharge visuelle

Un QR trop grand ou mal placé peut diminuer la qualité perçue du badge.

---

## Recommandation MVP

Si cette idée est reprise plus tard, un MVP raisonnable serait :

1. générer un QR code vers une **URL publique de vérification dédiée** ;
2. ajouter le QR uniquement sur certains badges de test ;
3. conserver le baking PNG actuel sans changement de structure ;
4. tester la lisibilité sur mobile ;
5. tester la compatibilité avec les badges imprimés et partagés.

---

## Architecture possible

### Backend

- générer l’URL de vérification publique au moment de l’émission ;
- générer une image QR à partir de cette URL ;
- fusionner le QR dans le PNG final avant ou pendant la phase de baking, selon la pipeline retenue.

### Frontend / Verification page

Prévoir une page claire et courte, orientée humain, qui affiche :

- statut du badge ;
- nom du badge ;
- issuer ;
- date d’émission ;
- lien vers l’assertion ou les détails techniques si besoin.

---

## Questions ouvertes

1. le QR doit-il pointer vers l’assertion brute ou vers une page dédiée ;
2. faut-il afficher seulement “valide / invalide” ou un rapport détaillé ;
3. le QR doit-il être intégré à tous les badges ou seulement à certains modèles ;
4. à quel stade de la génération faut-il apposer le QR ;
5. comment garantir la stabilité des URLs dans le temps.

---

## Décision actuelle

Cette idée est conservée comme **piste produit UX / vérification rapide**.

Elle paraît très pertinente pour Badge83 car elle améliore fortement l’usage réel du badge, sans remettre en cause le modèle Open Badges existant.
