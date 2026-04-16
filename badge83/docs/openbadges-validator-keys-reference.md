# Référence des clés vérifiées par `openbadges-validator-core`

## Objectif

Ce document recense les principales **clés JSON** que `openbadges-validator-core` vérifie dans les objets Open Badges 2.0, à partir des règles définies dans :

- `openbadges-validator-core/openbadges/verifier/tasks/validation.py`

Il compare ensuite ces attentes avec les objets réellement produits par **Badge83** :

- `Assertion` émise dans `data/issued/*.json`
- `BadgeClass` servie via `badgeclass_template.json`
- `Issuer` servi via `issuer_template.json`

> Périmètre : cette référence se concentre sur les objets utilisés actuellement par Badge83 (`Assertion`, `IdentityObject`, `VerificationObjectAssertion`, `BadgeClass`, `Criteria`, `Issuer/Profile`, `Image`) et mentionne aussi les propriétés génériques ajoutées par le validateur aux objets primaires.

---

## 1. Vue d'ensemble des objets vérifiés

Dans le flux Badge83 actuel, le validateur manipule principalement les objets suivants :

| Objet Open Badges | Rôle dans Badge83 |
|-------------------|-------------------|
| `Assertion` | Badge individuel remis à l'apprenant |
| `IdentityObject` | Bloc `recipient` dans l'assertion |
| `VerificationObjectAssertion` | Bloc `verification` dans l'assertion |
| `BadgeClass` | Définition publique du badge |
| `Criteria` | Critères d'obtention du badge |
| `Issuer` / `Profile` | Profil public de l'émetteur |
| `Image` | Ressource image du badge / de l'émetteur |

Le validateur ajoute aussi, pour les objets primaires (`Assertion`, `BadgeClass`, `Issuer`, `Profile`, `Endorsement`), des vérifications génériques sur :

- `@language`
- `version`
- `related`
- `endorsement`

---

## 2. Clés vérifiées pour une `Assertion`

Source : `ClassValidators(OBClasses.Assertion)`.

| Clé | Statut validator | Type attendu | Rôle | Présence dans Badge83 |
|-----|------------------|--------------|------|------------------------|
| `id` | obligatoire | IRI | Identifiant de l'assertion | ✅ oui |
| `type` | obligatoire | RDF type contenant `Assertion` | Type de l'objet | ✅ oui |
| `recipient` | obligatoire | ID / objet `IdentityObject` | Destinataire du badge | ✅ oui |
| `badge` | obligatoire | ID / URL / objet `BadgeClass` | Référence du badge | ✅ oui |
| `verification` | obligatoire | ID / objet `VerificationObjectAssertion` | Mode de vérification | ✅ oui |
| `issuedOn` | obligatoire | datetime | Date d'émission | ✅ oui |
| `expires` | optionnelle | datetime | Date d'expiration | ❌ non |
| `image` | optionnelle | ID | Image spécifique à l'assertion | ❌ non |
| `narrative` | optionnelle | markdown text | Texte additionnel | ❌ non |
| `evidence` | optionnelle | ID ou liste d'ID | Preuves associées | ❌ non |
| `@language` | optionnelle | language tag | Langue par défaut | ❌ non |
| `version` | optionnelle | texte ou nombre | Version Open Badges | ❌ non |
| `related` | optionnelle | ID ou liste d'ID | Ressources liées | ❌ non |
| `endorsement` | optionnelle | ID ou liste d'ID | Endorsements | ❌ non |

### Lecture

Badge83 produit aujourd'hui une assertion **minimale mais conforme** au validateur : toutes les clés obligatoires sont présentes.

### Clés réellement émises par Badge83 dans l'assertion

Badge83 ajoute aussi une clé :

| Clé | Vérifiée explicitement par le validator ? | Remarque |
|-----|-------------------------------------------|----------|
| `url` | non explicitement dans `ClassValidators(Assertion)` | utile dans le modèle HostedBadge ; acceptée, mais non exigée |

---

## 3. Clés vérifiées pour `recipient` (`IdentityObject`)

Source : `ClassValidators(OBClasses.IdentityObject)`.

| Clé | Statut validator | Type attendu | Rôle | Présence dans Badge83 |
|-----|------------------|--------------|------|------------------------|
| `type` | obligatoire | RDF type parmi `id`, `email`, `url`, `telephone` | Type d'identifiant du destinataire | ✅ oui (`email`) |
| `identity` | obligatoire | chaîne, avec contraintes si `hashed=true` | Valeur d'identité ou hash | ✅ oui |
| `hashed` | obligatoire | booléen | Indique si `identity` est haché | ✅ oui |
| `salt` | optionnelle | texte | Sel cryptographique | ✅ oui |

### Règles additionnelles vérifiées

Le validateur applique aussi une logique métier :

- si `hashed = true`, `identity` doit ressembler à un hash connu (`sha256$...` ou `md5$...`) ;
- si `hashed = false` et `type = email`, `identity` doit ressembler à un email ;
- le couple `hashed` / `identity` doit être cohérent.

### Comparaison avec Badge83

Badge83 est conforme :

- `type = email`
- `hashed = true`
- `identity = sha256$...`

Badge83 utilise désormais `salt`, ce qui améliore la confidentialité tout en restant conforme au validator.

---

## 4. Clés vérifiées pour `verification` de l'assertion

Source : `ClassValidators(OBClasses.VerificationObjectAssertion)`.

| Clé | Statut validator | Type attendu | Rôle | Présence dans Badge83 |
|-----|------------------|--------------|------|------------------------|
| `type` | obligatoire | valeur contenant `HostedBadge` ou `SignedBadge` | Type de vérification | ✅ oui (`HostedBadge`) |
| `creator` | optionnelle | ID d'une clé publique | Utilisé pour `SignedBadge` | ❌ non |

### Remarque importante

Badge83 ajoute également :

| Clé | Vérifiée explicitement par le validator ? | Remarque |
|-----|-------------------------------------------|----------|
| `url` | non explicitement dans `VerificationObjectAssertion` | utile dans le modèle hosted de Badge83 ; tolérée par le validateur |

Pour Badge83, l'absence de `creator` est normale car le mode utilisé est **HostedBadge**, pas **SignedBadge**.

---

## 5. Clés vérifiées pour un `BadgeClass`

Source : `ClassValidators(OBClasses.BadgeClass)`.

| Clé | Statut validator | Type attendu | Rôle | Présence dans Badge83 |
|-----|------------------|--------------|------|------------------------|
| `id` | obligatoire | IRI | Identifiant du badge | ✅ oui |
| `type` | obligatoire | RDF type contenant `BadgeClass` | Type de l'objet | ✅ oui |
| `issuer` | obligatoire | ID / URL / objet `Profile` | Référence émetteur | ✅ oui |
| `name` | obligatoire | texte | Nom du badge | ✅ oui |
| `description` | obligatoire | texte | Description du badge | ✅ oui |
| `image` | optionnelle au niveau propriété, mais soumise à validation image | ID / URL / data URI | Image représentative du badge | ✅ oui |
| `criteria` | obligatoire | ID / objet `Criteria` | Conditions d'obtention | ✅ oui |
| `alignment` | optionnelle | ID ou liste d'ID | Alignements pédagogiques | ❌ non |
| `tags` | optionnelle | texte ou liste | Mots-clés | ❌ non |
| `@language` | optionnelle | language tag | Langue par défaut | ❌ non |
| `version` | optionnelle | texte ou nombre | Version | ❌ non |
| `related` | optionnelle | ID ou liste d'ID | Ressources liées | ❌ non |
| `endorsement` | optionnelle | ID ou liste d'ID | Endorsements | ❌ non |

### Comparaison avec Badge83

Le `BadgeClass` de Badge83 couvre l'ensemble des propriétés obligatoires attendues :

- `id`
- `type`
- `issuer`
- `name`
- `description`
- `image`
- `criteria`

Badge83 n'utilise pas encore `alignment`, `tags`, `related`, `endorsement` ni `version`.

---

## 6. Clés vérifiées pour `criteria`

Source : `ClassValidators(OBClasses.Criteria)`.

| Clé | Statut validator | Type attendu | Rôle | Présence dans Badge83 |
|-----|------------------|--------------|------|------------------------|
| `type` | optionnelle | RDF type (`Criteria`) | Type de l'objet criteria | ❌ non |
| `id` | optionnelle | IRI | URL des critères | ❌ non |
| `narrative` | optionnelle, mais requise dans certains cas de nœud embarqué | markdown text | Description des critères | ✅ oui |

### Règle métier complémentaire

Le validateur accepte un objet `criteria` embarqué sans `id` **à condition** qu'il contienne un `narrative`.

### Comparaison avec Badge83

Badge83 fournit :

```json
"criteria": {
  "narrative": "..."
}
```

Ce choix est conforme à la logique du validator.

---

## 7. Clés vérifiées pour l’`Issuer` / `Profile`

Source : `ClassValidators(OBClasses.Profile or OBClasses.Issuer)`.

| Clé | Statut validator | Type attendu | Rôle | Présence dans Badge83 |
|-----|------------------|--------------|------|------------------------|
| `id` | obligatoire | IRI | Identifiant public de l'émetteur | ✅ oui |
| `type` | obligatoire | RDF type contenant `Issuer` ou `Profile` | Type de l'objet | ✅ oui |
| `name` | obligatoire | texte | Nom de l'émetteur | ✅ oui |
| `description` | optionnelle | texte | Description du profil | ✅ oui |
| `image` | optionnelle | ID / URL / data URI | Image du profil | ✅ oui |
| `url` | obligatoire | URL | URL publique de l'émetteur | ✅ oui |
| `email` | obligatoire | email | Contact de l'émetteur | ✅ oui |
| `telephone` | optionnelle | téléphone | Contact téléphonique | ❌ non |
| `publicKey` | optionnelle | ID | Clé publique pour signature | ❌ non |
| `verification` | optionnelle | ID / objet `VerificationObjectIssuer` | Politique de vérification hosted | ❌ non |
| `@language` | optionnelle | language tag | Langue par défaut | ❌ non |
| `version` | optionnelle | texte ou nombre | Version | ❌ non |
| `related` | optionnelle | ID ou liste d'ID | Ressources liées | ❌ non |
| `endorsement` | optionnelle | ID ou liste d'ID | Endorsements | ❌ non |

### Comparaison avec Badge83

L’`Issuer` de Badge83 respecte toutes les exigences obligatoires.

L'absence de `verification` côté issuer n'empêche pas la validation : le validateur sait appliquer une politique par défaut dérivée du domaine HTTP de l'issuer.

---

## 8. Clés vérifiées pour un objet `Image`

Source : `ClassValidators(OBClasses.Image)` et `tasks/images.py`.

| Clé | Statut validator | Type attendu | Rôle | Présence dans Badge83 |
|-----|------------------|--------------|------|------------------------|
| `type` | optionnelle | RDF type | Type de l'objet image | n/a (Badge83 utilise une URL simple) |
| `id` | obligatoire si objet image | data URI ou URL | Identifiant de la ressource image | n/a |
| `caption` | optionnelle | texte | Légende | n/a |
| `author` | optionnelle | IRI | Auteur de l'image | n/a |

### Remarque

Badge83 utilise simplement une **URL d'image** dans `BadgeClass.image` et `Issuer.image` :

```json
"image": "${BASE_URL}/assets/mode83-badge.png"
```

Le validateur accepte ce format.

En plus des clés, il vérifie que la ressource image est récupérable et qu'elle correspond à un type accepté (`image/png` ou `image/svg+xml`).

---

## 9. Synthèse : clés réellement produites par Badge83

### Assertion Badge83

```json
[
  "@context",
  "id",
  "type",
  "url",
  "recipient",
  "issuedOn",
  "verification",
  "badge",
  "issuer"
]
```

### Recipient Badge83

```json
[
  "type",
  "hashed",
  "salt",
  "identity"
]
```

### Verification Badge83

```json
[
  "type",
  "url"
]
```

### BadgeClass Badge83

```json
[
  "@context",
  "id",
  "type",
  "name",
  "description",
  "image",
  "criteria",
  "issuer"
]
```

### Criteria Badge83

```json
[
  "narrative"
]
```

### Issuer Badge83

```json
[
  "@context",
  "id",
  "type",
  "name",
  "url",
  "email",
  "description",
  "image"
]
```

---

## 10. Écarts entre la surface complète du validator et Badge83

### Clés obligatoires couvertes par Badge83

Badge83 couvre toutes les clés obligatoires nécessaires pour le scénario HostedBadge actuel :

- `Assertion.id`
- `Assertion.type`
- `Assertion.recipient`
- `Assertion.badge`
- `Assertion.verification`
- `Assertion.issuedOn`
- `IdentityObject.type`
- `IdentityObject.identity`
- `IdentityObject.hashed`
- `VerificationObjectAssertion.type`
- `BadgeClass.id`
- `BadgeClass.type`
- `BadgeClass.issuer`
- `BadgeClass.name`
- `BadgeClass.description`
- `BadgeClass.criteria`
- `Issuer.id`
- `Issuer.type`
- `Issuer.name`
- `Issuer.url`
- `Issuer.email`

### Clés optionnelles non utilisées par Badge83

Badge83 n'utilise pas encore, entre autres :

- `expires`
- `image` au niveau assertion
- `narrative` au niveau assertion
- `evidence`
- `alignment`
- `tags`
- `telephone`
- `publicKey`
- `verification` au niveau issuer
- `@language`
- `version`
- `related`
- `endorsement`
- `creator` pour `SignedBadge`

### Clés ajoutées par Badge83 mais non exigées explicitement

Badge83 ajoute des propriétés utiles au modèle hébergé, mais non listées comme obligatoires dans les règles du validator :

- `Assertion.url`
- `VerificationObjectAssertion.url`

Ces clés sont cohérentes avec le fonctionnement HostedBadge et ne posent pas de problème au validateur.

---

## 11. Conclusion

`openbadges-validator-core` vérifie une surface fonctionnelle assez large de la spécification Open Badges 2.0, incluant de nombreuses propriétés optionnelles destinées à des cas avancés : signatures, alignements, endorsements, related resources, politiques de vérification d'issuer, etc.

Badge83 n'implémente aujourd'hui qu'un **sous-ensemble ciblé**, mais ce sous-ensemble couvre bien les propriétés **obligatoires et suffisantes** pour un badge Open Badges 2.0 de type **HostedBadge**.

En résumé :

- **oui**, Badge83 ne produit pas toutes les clés que le validateur sait contrôler ;
- **mais** il produit bien toutes les clés indispensables à son scénario actuel ;
- les écarts restants correspondent surtout à des fonctionnalités avancées non encore implémentées, et non à des non-conformités.

---

## 12. Roadmap recommandée pour Badge83

### Priorité 1 — robustesse HostedBadge

1. **`verification` côté issuer**
   - ajouter `allowedOrigins` et/ou `startsWith`
   - intérêt : expliciter la politique de vérification hosted au lieu de dépendre du comportement par défaut du validator.

2. **HTTPS + domaine stable**
   - intérêt : améliorer la résolvabilité publique et éviter les warnings/limitations liés aux URLs temporaires.

3. **`expires` dans l'assertion**
   - intérêt : gérer les badges temporaires ou renouvelables.

### Priorité 2 — enrichissement pédagogique

4. **`evidence`**
   - intérêt : lier des preuves d'évaluation ou de réalisation.

5. **`tags`**
   - intérêt : faciliter l'indexation et la recherche des badges.

6. **`alignment`**
   - intérêt : relier le badge à des référentiels de compétences ou objectifs pédagogiques.

### Priorité 3 — interopérabilité avancée

7. **`@language`**
   - intérêt : meilleure gestion multilingue.

8. **`related`**
   - intérêt : relier badges, ressources ou variantes.

9. **`endorsement`**
   - intérêt : permettre des validations tierces du badge ou de l'émetteur.

### Priorité 4 — signature

10. **`publicKey` sur l'issuer + `creator` dans `verification`**
    - intérêt : ouvrir la voie au mode `SignedBadge`.