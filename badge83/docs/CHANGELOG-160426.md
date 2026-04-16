# Journal des modifications — 16/04/26

## Résumé

Cette journée a été consacrée à l'audit de compatibilité entre **Badge83** et **openbadges-validator-core**, à la mise à jour de la documentation française, et à un premier renforcement du modèle d'identité destinataire avec l'ajout d'un **`salt`** dans les assertions.

---

## Changements applicatifs

### 1. Ajout du `salt` dans `recipient`

**Fichier** : `app/issuer.py`

- génération d'un `salt` aléatoire pour chaque assertion ;
- calcul de `recipient.identity` sur `email_normalisé + salt` ;
- ajout du champ `recipient.salt` dans les assertions JSON et les badges PNG baked.

### 2. Effet fonctionnel

- amélioration de la confidentialité des destinataires ;
- réduction de la corrélation entre plusieurs badges d'un même email ;
- compatibilité conservée avec `openbadges-validator-core` (`salt` étant un champ optionnel mais supporté).

---

## Documentation ajoutée ou mise à jour

### Documents mis à jour

- `README.md`
- `docs/technical-baking-verification.md`
- `docs/plan-hosted-verification.md`
- `docs/test-validation-2026-04-15.md`

### Nouveau document de référence

- `docs/openbadges-validator-keys-reference.md`

Ce document détaille :

- les clés vérifiées par `openbadges-validator-core` ;
- leur rôle ;
- leur présence ou non dans les objets produits par Badge83 ;
- une roadmap d'enrichissement du modèle Open Badges.

---

## Résultats d'audit documentés

### Compatibilité confirmée

- assertions HostedBadge conformes ;
- endpoints publics résolubles ;
- identité destinataire compatible (`sha256$...`) ;
- PNG baked compatible avec le mécanisme `unbake(...)` utilisé par le validator.

### Analyse PNG documentée

Structure observée sur un badge Badge83 validé :

1. `IHDR`
2. `IDAT`
3. `tEXt` avec keyword `openbadges`
4. `IEND`

---

## Prochaines étapes recommandées

1. Ajouter une politique `verification` au niveau `Issuer`
2. Passer en HTTPS avec domaine stable
3. Ajouter `expires`
4. Ajouter `evidence`, `tags`, `alignment`
5. Préparer `SignedBadge`