# Badge83 — plan de travail actualisé : registry blockchain universel et suite du développement

Date : 17/06/2026  
Projet : Badge83  
Objectif : stabiliser d'abord la base blockchain via le smart contract universel `Badge83Registry`, puis l'intégrer au backend Badge83, aux pages de vérification QR et aux optimisations de performance.

Statut au 17/06/2026 :

- [x] `Badge83Registry` ajouté, testé et fusionné dans `main` ;
- [x] intégration provider Python `Badge83Registry` présente dans `main` ;
- [x] helpers d'URL de vérification blockchain indépendante présents ;
- [x] liens de vérification blockchain affichés sur les pages publiques ;
- [x] première passe performance SQLite/QR réalisée : PRAGMA SQLite, suppression de l'initialisation répétée du schéma dans les dépendances FastAPI du constructeur, cache des polices dans `qr.py` ;
- [ ] QR `CHAIN` optionnel ;
- [ ] vérificateur blockchain indépendant statique.

---

## 1. Décision

Le projet contient déjà une branche d’ancrage EVM. Plutôt que de prolonger le modèle temporaire `Badge83AnchorV2`, il est recommandé de passer directement au contrat universel `Badge83Registry`.

Raisons :

1. éviter de figer un ABI et un modèle de statut temporaires ;
2. prendre en charge dès maintenant l’ancrage et la révocation des credentials ;
3. construire le futur QR `CHAIN` et le vérificateur indépendant autour de l’API finale ;
4. conserver le modèle de confidentialité : seul un `bytes32 credentialHash` opaque est publié on-chain ;
5. éviter de maintenir plusieurs nouveaux standards tant que la branche EVM n’est pas encore en production.

---

## 2. Architecture cible de la vérification blockchain

```text
Badge PNG
 ├─ QR VERIFY → Badge83 /verify/qr/<assertion_id>
 └─ QR CHAIN  → independent verifier → Badge83Registry.getStatus(hash)
```

Badge83 conserve la vérification complète :

- assertion locale ;
- enregistrement local de preuve ;
- enregistrement local de révocation ;
- statut EVM d’ancrage/révocation ;
- liens vers l’explorer.

Le vérificateur externe conserve une vérification autonome minimale :

- hash trouvé on-chain ou non ;
- hash révoqué ou non ;
- credential valide ou non ;
- timestamps ;
- adresses des acteurs ;
- chain id et adresse du contrat.

---

## 3. Contrat `Badge83Registry` v1

### 3.1 Scope v1

Le contrat doit être universel, mais minimal.

Fonctions :

```solidity
anchor(bytes32 credentialHash)
revoke(bytes32 credentialHash)
getStatus(bytes32 credentialHash)
isValid(bytes32 credentialHash)
setOperator(address operator, bool allowed)
transferOwnership(address newOwner)
```

État :

```solidity
struct CredentialStatus {
    bool anchored;
    bool revoked;
    uint64 anchoredAt;
    uint64 revokedAt;
    address anchoredBy;
    address revokedBy;
}
```

Événements :

```solidity
CredentialAnchored(bytes32 indexed credentialHash, address indexed actor, uint64 anchoredAt)
CredentialRevoked(bytes32 indexed credentialHash, address indexed actor, uint64 revokedAt)
OperatorUpdated(address indexed operator, bool allowed)
OwnershipTransferred(address indexed previousOwner, address indexed newOwner)
```

Access control:

- `owner` peut gérer les operators ;
- `owner` et les `operators` peuvent appeler `anchor` et `revoke` ;
- le `revoke` public est interdit afin qu’une adresse quelconque ne puisse pas révoquer des credentials tiers.

### 3.2 Hors périmètre v1

Ne pas ajouter dans la première version :

- proxy upgradeability;
- batch anchor/revoke;
- données personnelles ;
- `assertion_id`;
- email/name;
- JSON/PNG URI;
- revoke reason;
- issuer registry;
- EIP-712;
- fonctions payantes ;
- `AccessControl` OpenZeppelin complexe.

Si une nouvelle logique devient nécessaire, il sera préférable de déployer un contrat `Badge83RegistryV2` et de conserver localement dans Badge83 `chain_id`, `contract_address` et `contract_version`.

---

## 4. Premier livrable

Le premier point de merge doit rester isolé et sûr :

```text
formation/170626_newplan.md
badge83/blockchain/contracts/Badge83Registry.sol
badge83/blockchain/test/Badge83Registry.test.js
badge83/blockchain/scripts/deploy-registry.js
```

Le backend Badge83 ne change pas à cette étape.

Critère de validation :

```bash
cd badge83/blockchain
npm test
```

Tous les tests Hardhat doivent passer.

---

## 5. Plan de PR

### PR 1 — Universal contract

```text
feat(blockchain): add Badge83Registry contract
```

Contenu :

- `Badge83Registry.sol`;
- Hardhat tests;
- deploy script;
- ce plan de travail.

Merge dans `main` après succès de `npm test`.

### PR 2 — Python provider integration

```text
feat(blockchain): integrate Badge83Registry provider
```

Fichiers :

```text
badge83/app/proofs/anchoring_providers.py
badge83/app/config.py
badge83/tests/unit/test_anchoring_evm_provider.py
badge83/docs/blockchain-evm-anchoring.md
badge83/badge83.env.exemple
```

Critères :

- l’application fonctionne sans configuration EVM ;
- l’application ne plante pas sans `web3` lorsque EVM est désactivé ;
- le provider prend en charge `anchor`, `revoke`, `getStatus`, `isValid` ;
- le statut contient `anchored`, `revoked`, `valid`, timestamps et adresses des acteurs.

### PR 3 — Blockchain verification URL helpers

```text
feat(blockchain): add independent verification url helpers
```

Ajouter :

```python
credential_hash_to_bytes32_hex(...)
make_blockchain_verification_url(...)
```

URL-формат:

```text
https://verify.mode83.org/#/evm/<chainId>/<contractAddress>/<credentialHashBytes32>
```

### PR 4 — Public verification pages

```text
feat(blockchain): expose fallback verification link
```

Mettre à jour :

```text
badge83/templates/verify_qr.html
badge83/templates/verify_badge.html
```

Les pages doivent fonctionner :

- avec métadonnées blockchain ;
- sans métadonnées blockchain ;
- avec les anciens badges.

### PR 5 — Optional CHAIN QR

```text
feat(blockchain): add optional chain qr to baked badges
```

Ajouter le second QR uniquement derrière feature flag / configuration EVM complète.

Avant merge, une vérification visuelle manuelle du PNG est obligatoire.

### PR 6 — Independent verifier

```text
feat(verifier): add static blockchain status verifier
```

Mini-app séparée ou dépôt séparé lisant `getStatus` directement via RPC.

---

## 6. Retour au plan performance

Après le premier merge blockchain stable, il est recommandé de réaliser rapidement les optimisations performance suivantes :

1. [x] supprimer l’appel répété à `init_db_schema()` dans le `get_db()` du constructeur ;
2. [x] ajouter les PRAGMA SQLite `WAL`, `busy_timeout`, `synchronous=NORMAL` ;
3. [x] mettre en cache les polices dans `qr.py` ;
4. [ ] ajouter un debounce de preview ;
5. [ ] charger le PNG de fond une seule fois par batch.

Réalisation du 17/06/2026 :

- `badge83/app/database.py` applique désormais `journal_mode=WAL`, `busy_timeout=10000` et `synchronous=NORMAL` à chaque connexion SQLite ;
- `get_database_connection()` initialise le schéma une seule fois par chemin de base connu, au lieu de relancer `CREATE TABLE IF NOT EXISTS` à chaque requête du constructeur ;
- les dépendances FastAPI du constructeur dans `routes/badge_constructor/schemas.py` et `routes/badge_constructor/templates.py` utilisent `get_database_connection()` ;
- `badge83/app/qr.py` met en cache les polices de texte avec `lru_cache`, afin d'éviter de recharger les fichiers TTF pour chaque overlay ;
- couverture ajoutée dans `tests/unit/test_database.py` et `tests/unit/test_qr.py` ;
- validation : `186 passed, 22 warnings` avec `cd badge83 && .venv/bin/python -m pytest tests/unit`.

Ensuite, il sera possible de passer aux tâches SQLite read-model plus importantes :

- `/api/badges` depuis SQLite ;
- `/api/badges/search` depuis SQLite ;
- `badge_issuance_metadata` pour les numéros de certificat et la détection de doublons batch.

---

## 7. Règle de merge dans `main`

Ne pas attendre la fin de toute la roadmap. Fusionner par PR courts lorsqu’une couche est :

1. autonome ;
2. couverte par des tests ;
3. compatible avec le mode sans blockchain ;
4. accompagnée d’un rollback clair ;
5. indépendante d’une migration incomplète.

Le premier merge est recommandé après `Badge83Registry.sol + tests + deploy script`, car cela ne modifie pas le runtime backend Badge83.
