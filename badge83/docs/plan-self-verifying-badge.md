# Plan de travail — Self-verifying badge

## Idée

Étudier un modèle dans lequel un **badge vérifie récursivement sa propre validité**, son identité et l’absence de modification, tout en restant compatible avec les principes et contraintes du standard **Open Badges**.

Autrement dit, le badge devrait pouvoir servir de support de preuve autonome pour répondre aux questions suivantes :

- suis-je bien le badge attendu ;
- ai-je été altéré depuis mon émission ;
- puis-je encore être résolu et vérifié selon le modèle Open Badges.

---

## Intuition fonctionnelle

Le concept vise à rapprocher le badge d’un objet “auto-vérifiable”, c’est-à-dire capable de fournir dans son propre contenu suffisamment d’indices ou de références pour :

1. retrouver son assertion ;
2. contrôler son identité ;
3. détecter une altération du contenu ;
4. confirmer la cohérence avec l’issuer et le BadgeClass ;
5. rester compatible avec un validateur Open Badges standard.

---

## Ce que cela signifie techniquement

### 1. Vérification de son identité

Le badge doit pouvoir démontrer qu’il correspond bien à une assertion donnée.

Cela peut passer par :

- un `id` d’assertion stable et résolvable ;
- une référence cohérente au `BadgeClass` ;
- une référence cohérente à l’`Issuer` ;
- un `recipient` vérifiable dans le cadre du modèle Open Badges.

### 2. Vérification de son intégrité

Le badge doit permettre de détecter une modification non autorisée.

Dans l’état actuel du modèle HostedBadge / baked PNG, cela peut être approché par :

- comparaison entre l’assertion embarquée et l’assertion publique résolue ;
- recalcul d’éléments déterministes attendus ;
- vérification qu’aucun champ critique n’a été modifié.

### 3. Vérification “récursive”

L’idée de récursivité doit être formulée avec prudence.

En pratique, cela ne veut pas dire une boucle infinie, mais plutôt :

- le badge contient une assertion ;
- cette assertion pointe vers des objets de référence ;
- le système revalide ces objets et la cohérence d’ensemble ;
- le badge confirme indirectement sa propre authenticité via cet aller-retour de vérification.

---

## Compatibilité avec Open Badges

### Compatible si

L’approche reste compatible si elle s’appuie sur les mécanismes standards, par exemple :

- `verification.type = HostedBadge` ou `SignedBadge` ;
- `id` public résolvable ;
- `BadgeClass` et `Issuer` accessibles ;
- format baked PNG valide ;
- structure JSON conforme au contexte Open Badges.

### Non compatible ou risqué si

L’approche devient fragile si elle introduit :

- une logique propriétaire non documentée ;
- des champs critiques non standards interprétés uniquement par Badge83 ;
- un mécanisme “auto-référent” qui casserait la lisibilité par les validateurs externes.

Conclusion :

➡️ le badge peut être **self-checking** ou **self-consistency-aware**, mais il ne faut pas rompre le modèle de vérification standard Open Badges.

---

## Scénarios de mise en œuvre

### Option A — HostedBadge + comparaison locale

Le PNG baked contient l’assertion embarquée. Lors de la vérification :

- on extrait l’assertion ;
- on recharge l’assertion distante via son `id` ;
- on compare les champs essentiels ;
- on signale toute divergence.

Avantages :

- simple à comprendre ;
- aligné avec l’architecture actuelle de Badge83 ;
- compatible avec les outils existants.

Limites :

- dépend d’un endpoint public résolvable ;
- l’intégrité est vérifiée par cohérence, pas par signature forte.

### Option B — SignedBadge / signature cryptographique

Le badge ou l’assertion porte une signature permettant de vérifier directement l’intégrité.

Avantages :

- beaucoup plus fort du point de vue sécurité ;
- plus proche d’une vraie auto-vérification d’intégrité.

Limites :

- plus complexe à mettre en œuvre ;
- nécessite gestion de clés, cycle de signature, compatibilité validator.

### Option C — Hash d’intégrité interne + contrôle externe

Le badge embarque ou référence un hash attendu de son assertion ou de certains champs critiques.

Avantages :

- plus simple qu’une vraie signature ;
- utile comme mécanisme complémentaire de détection.

Limites :

- moins robuste qu’une signature ;
- attention à ne pas créer une pseudo-sécurité non standard.

---

## Recommandation actuelle

Si cette idée est reprise plus tard, l’ordre raisonnable serait :

1. commencer par **HostedBadge + comparaison assertion embarquée / assertion distante** ;
2. documenter précisément les champs critiques à comparer ;
3. ajouter des tests d’intégrité sur les PNG baked ;
4. ensuite seulement étudier un vrai mode **SignedBadge**.

---

## Questions ouvertes

1. veut-on vérifier seulement l’intégrité du badge, ou aussi l’identité du porteur ;
2. quels champs doivent être considérés comme critiques ;
3. quelle différence accepte-t-on entre assertion embarquée et assertion distante ;
4. faut-il un mode strict ou un mode tolérant ;
5. faut-il viser à terme une signature cryptographique complète.

---

## Décision actuelle

Cette idée est conservée comme **piste de recherche et d’architecture**.

Elle semble compatible avec Badge83 si elle reste fondée sur les mécanismes standards Open Badges, sans dérive vers un format propriétaire opaque.
