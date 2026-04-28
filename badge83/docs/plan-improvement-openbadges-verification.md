# Projet de plan — amélioration de la vérification Open Badges dans Badge83

## Objectif

Améliorer la vérification Open Badges de Badge83 en s'inspirant des idées utiles de `openbadges-validator-core`, sans intégrer tout le validateur officiel dans l'application.

L'objectif est de conserver Badge83 comme un projet léger FastAPI d'émission et de vérification de badges, tout en ajoutant une couche locale de contrôle plus explicite : messages d'erreur, avertissements, vérification de la chaîne HostedBadge et contrôles de conformité de base.

## Principe général

Ne pas déplacer toute l'architecture de `openbadges-validator-core` dans Badge83.

À éviter :

- serveur Flask du validateur ;
- architecture Pydux / reducers / actions / tasks ;
- dépendances anciennes et potentiellement conflictuelles dans le runtime Badge83 ;
- pipeline JSON-LD complet ;
- remplacement du module actuel `app/baker.py`.

À reprendre :

- l'idée d'un rapport structuré `valid`, `errorCount`, `warningCount`, `messages` ;
- l'idée de checks unitaires nommés ;
- la séparation entre erreurs bloquantes et avertissements ;
- la vérification de la chaîne HostedBadge ;
- la vérification de `allowedOrigins` et `startsWith` côté issuer ;
- les contrôles simples de forme pour `Assertion`, `BadgeClass` et `Issuer` ;
- les tests de compatibilité avec un validateur externe en mode développement.

## Niveaux de vérification proposés

Badge83 peut gérer plusieurs niveaux de vérification, sans tout mélanger.

### 1. Vérification `basic`

Contrôle local minimal :

- le fichier JSON existe ;
- l'objet est de type `Assertion` ;
- les champs principaux sont présents.

### 2. Vérification `baked`

Contrôle d'un PNG baked :

- signature PNG valide ;
- présence d'un chunk `openbadges` ;
- extraction JSON possible ;
- objet extrait de type `Assertion`.

### 3. Vérification `hosted`

Contrôle de la chaîne hébergée :

```text
PNG baked
  -> embedded Assertion
  -> hosted Assertion
  -> BadgeClass
  -> Issuer
```

Vérifications :

- l'assertion intégrée correspond à l'assertion hébergée ;
- `assertion.badge` pointe vers le bon `BadgeClass` ;
- `BadgeClass.issuer` pointe vers le bon `Issuer` ;
- l'issuer autorise l'URL de l'assertion via sa politique de vérification.

### 4. Vérification `strict`

Contrôle optionnel en développement ou en CI avec `openbadges-validator-core` ou un validateur externe.

Ce niveau ne devrait pas être une dépendance obligatoire du runtime Badge83.

## Nouveau module proposé

Créer un module local :

```text
badge83/app/openbadges_checks.py
```

Ce module contiendrait des fonctions pures, simples à tester, sans dépendance lourde.

### Structure de check

Chaque check peut retourner un dictionnaire de ce type :

```json
{
  "name": "assertion_type",
  "ok": true,
  "success": true,
  "level": "ERROR",
  "messageLevel": "ERROR",
  "message": "Object type is Assertion."
}
```

Champs proposés :

| Champ | Description |
|---|---|
| `name` | Nom stable du check |
| `ok` / `success` | Résultat booléen |
| `level` / `messageLevel` | `ERROR`, `WARNING` ou `INFO` |
| `message` | Message lisible |
| autres champs | Détails de debug éventuels |

### Fonctions utilitaires

Fonctions utiles à prévoir :

```python
def make_check(name: str, ok: bool, message: str, level: str = "ERROR", **extra) -> dict: ...

def is_http_url(value: object) -> bool: ...

def is_iso_datetime_with_timezone(value: object) -> bool: ...

def is_sha256_identity(value: object) -> bool: ...

def summarize_checks(checks: list[dict]) -> dict: ...
```

La fonction `summarize_checks` produirait un rapport proche de celui de `openbadges-validator-core` :

```json
{
  "valid": true,
  "errorCount": 0,
  "warningCount": 1,
  "messages": [],
  "checks": []
}
```

## Checks proposés pour `Assertion`

Fonction proposée :

```python
def check_assertion(assertion: dict) -> list[dict]: ...
```

Contrôles :

- `@context == "https://w3id.org/openbadges/v2"` ;
- `type == "Assertion"` ;
- `id` est une URL HTTP/HTTPS ;
- `url` est absent ou cohérent avec `id` ;
- `badge` est une URL HTTP/HTTPS ;
- `issuer` est une URL HTTP/HTTPS ;
- `issuedOn` est une date ISO avec timezone ;
- `expires` est une date ISO avec timezone ;
- `expires > issuedOn` ;
- `recipient.type == "email"` ;
- `recipient.hashed == true` ;
- `recipient.identity` suit le format `sha256$` + 64 caractères hexadécimaux ;
- `verification.type == "HostedBadge"` ;
- `verification.url` est une URL HTTP/HTTPS.

## Checks proposés pour `BadgeClass`

Fonction proposée :

```python
def check_badgeclass(badgeclass: dict, expected_id: str | None = None) -> list[dict]: ...
```

Contrôles :

- `type == "BadgeClass"` ;
- `id` est une URL HTTP/HTTPS ;
- `id` correspond à `assertion.badge` si `expected_id` est fourni ;
- `name` est présent ;
- `description` est présent ;
- `image` est présent ;
- `criteria` est présent ;
- `issuer` est une URL HTTP/HTTPS.

## Checks proposés pour `Issuer`

Fonction proposée :

```python
def check_issuer(issuer: dict, expected_id: str | None = None) -> list[dict]: ...
```

Contrôles :

- `type` est `Issuer` ou `Profile` ;
- `id` est une URL HTTP/HTTPS ;
- `id` correspond à `BadgeClass.issuer` si `expected_id` est fourni ;
- `name` est présent ;
- `url` est une URL HTTP/HTTPS si présent ;
- `email` ressemble à un email si présent ;
- `verification.allowedOrigins` ou `verification.startsWith` est déclaré.

## Vérification `allowedOrigins` / `startsWith`

Fonction proposée :

```python
def check_hosted_verification_scope(assertion: dict, issuer: dict) -> list[dict]: ...
```

Contrôles :

- le host de `assertion.id` est autorisé par `issuer.verification.allowedOrigins` ;
- l'URL de `assertion.id` commence par au moins une valeur de `issuer.verification.startsWith`, si cette politique est déclarée.

Cette partie reprend l'idée de `hosted_id_in_verification_scope` de `openbadges-validator-core`, mais sous forme simple et locale.

## Vérification du hash destinataire

Fonction proposée :

```python
def verify_recipient_email(assertion: dict, email: str) -> dict: ...
```

Principe :

```text
sha256(normalized_email + salt) == recipient.identity
```

Cette fonction servirait surtout à l'administration ou à un bureau de vérification : un email saisi peut être comparé au hash sans exposer publiquement l'email dans l'assertion.

## Vérification image

Pour `BadgeClass.image`, reprendre l'idée de `tasks/images.py` du validateur officiel, mais simplement :

- l'image est une URL HTTP/HTTPS ;
- `GET` ou `HEAD` retourne `200` ;
- `Content-Type` commence par `image/png`, `image/svg+xml` ou un type image autorisé.

Cette vérification peut être intégrée au niveau `hosted` ou `deep`.

## Intégration dans `app/verifier.py`

### `verify_badge`

Après chargement de l'assertion JSON :

```python
checks = check_assertion(badge_data)
compliance = summarize_checks(checks)
```

Ajouter au retour :

```json
{
  "valid": true,
  "assertion": {},
  "summary": {},
  "compliance": {
    "valid": true,
    "errorCount": 0,
    "warningCount": 0,
    "messages": [],
    "checks": []
  }
}
```

Pour éviter de casser l'existant, le champ `compliance` doit être ajouté sans supprimer les champs actuels.

### `verify_baked_badge`

Après extraction de l'assertion depuis le PNG :

```python
checks = check_assertion(assertion)
compliance = summarize_checks(checks)
```

Ajouter le bloc `compliance` au résultat.

### `deep_verify_baked_badge`

Ajouter :

```python
all_checks = []
all_checks += check_assertion(embedded_assertion)
all_checks += check_assertion(hosted_assertion)
all_checks += check_badgeclass(badge_document, expected_id=hosted_assertion.get("badge"))
all_checks += check_issuer(issuer_document, expected_id=badge_document.get("issuer"))
all_checks += check_hosted_verification_scope(hosted_assertion, issuer_document)
compliance = summarize_checks(all_checks)
```

Puis retourner :

```json
{
  "deep": {
    "ok": true,
    "compliance": {}
  }
}
```

## API proposée

Deux possibilités :

### Option A — ajouter des paramètres

```text
GET /verify/{id}?level=basic
GET /verify/{id}?level=deep
POST /verify-baked?level=baked
POST /verify-baked?level=deep
```

### Option B — ajouter des endpoints dédiés

```text
GET /api/badges/{id}/compliance
POST /validate-baked
```

Pour limiter les risques, commencer par ajouter seulement le bloc `compliance` aux fonctions existantes, puis exposer des endpoints dédiés si nécessaire.

## Strict validation externe

Le validateur complet peut être utilisé en option, mais pas dans le runtime principal.

Approche recommandée :

```text
badge83/requirements.txt          # dépendances runtime Badge83
badge83/requirements-dev.txt      # dépendances dev/test éventuelles
openbadges-validator-core/        # outil externe séparé
```

Commandes futures possibles :

```bash
python -m app.validate_external --url https://mode83.ddns.net/assertions/<id>
python -m app.validate_external --png badge.png
```

Ce mode servirait :

- aux tests d'intégration ;
- à la CI ;
- aux vérifications manuelles avant mise en production ;
- pas au fonctionnement normal de l'application.

## Tests proposés

Créer :

```text
badge83/tests/unit/test_openbadges_checks.py
```

Tests recommandés :

1. une assertion valide passe tous les checks ;
2. une assertion sans `@context` échoue ;
3. une assertion avec `type` incorrect échoue ;
4. un mauvais hash recipient échoue ;
5. une date sans timezone échoue ;
6. `expires < issuedOn` échoue ou produit un warning ;
7. un issuer autorise l'URL d'assertion via `allowedOrigins` ;
8. un issuer refuse un domaine externe ;
9. `BadgeClass.id` correspond à `assertion.badge` ;
10. `Issuer.id` correspond à `BadgeClass.issuer`.

Tests de compatibilité optionnels :

```text
badge83/tests/integration/test_external_validator_compatibility.py
```

Objectifs :

- un PNG baked par Badge83 est lisible par un validateur externe ;
- un badge hébergé Badge83 passe une validation stricte en environnement configuré.

## Ordre de mise en œuvre

### Étape 1 — module local

Créer `app/openbadges_checks.py` avec :

- `make_check` ;
- `is_http_url` ;
- `is_iso_datetime_with_timezone` ;
- `is_sha256_identity` ;
- `check_assertion` ;
- `summarize_checks`.

### Étape 2 — intégration minimale

Brancher `check_assertion` dans :

- `verify_badge` ;
- `verify_baked_badge`.

Ajouter le bloc `compliance` aux réponses sans casser les champs existants.

### Étape 3 — vérification HostedBadge

Ajouter :

- `check_badgeclass` ;
- `check_issuer` ;
- `check_hosted_verification_scope`.

Les brancher dans `deep_verify_baked_badge`.

### Étape 4 — tests unitaires

Ajouter les tests de base pour tous les checks.

### Étape 5 — validation stricte externe optionnelle

Ajouter un outil dev/test qui appelle `openbadges-validator-core`, sans l'ajouter aux dépendances runtime principales.

## Résultat attendu

Badge83 conservera son architecture simple :

```text
FastAPI
issuer.py
baker.py
verifier.py
database.py
routes/
```

Mais il gagnera une couche de vérification plus claire :

```json
{
  "valid": true,
  "compliance": {
    "valid": true,
    "errorCount": 0,
    "warningCount": 0,
    "messages": [],
    "checks": []
  }
}
```

Ainsi, Badge83 bénéficiera des bonnes idées de `openbadges-validator-core` sans importer toute sa complexité.
