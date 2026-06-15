# Badge83 — Ancrage blockchain EVM local

Date : 15/06/2026  
Projet : Badge83  
Objet : procédure d'intégration locale Hardhat pour le provider d'ancrage EVM optionnel

---

## 1. Objectif

Cette page décrit le flux de test local permettant de valider l'ancrage EVM réel de Badge83 sur un nœud Hardhat local.

L'objectif est limité : vérifier que le provider `evm` peut publier uniquement le digest `bytes32` du badge, récupérer un `tx_hash` réel local et enregistrer le `block_number` dans SQLite.

Badge83 doit continuer à fonctionner sans blockchain. Cette procédure est donc optionnelle et ne doit pas modifier le runtime principal.

---

## 2. Règles de sécurité et de confidentialité

Le contrat `Badge83Anchor` ne reçoit qu'une seule donnée :

```text
bytes32 credentialHash
```

Cette valeur provient du hash local :

```text
sha256:<64 hex>
```

Le provider EVM convertit les 64 caractères hexadécimaux en `bytes32` avant l'appel au contrat.

Ne jamais envoyer on-chain :

- nom ;
- email ;
- assertion JSON ;
- PNG ;
- payload canonique ;
- `admin_recipient` ;
- `search` ;
- raison détaillée de révocation ;
- `assertion_id` dans cette version ;
- secret, seed phrase ou clé privée réelle.

Les clés privées affichées par Hardhat sont publiques et uniquement destinées au développement local. Elles ne doivent jamais être utilisées sur un réseau réel.

---

## 3. Prérequis

Depuis la racine de l'espace de travail :

```bash
cd /home/ubuntu/projects/Mode83
```

Installer les dépendances Python principales si nécessaire :

```bash
.venv/bin/pip install -r badge83/requirements.txt
```

Installer les dépendances blockchain Python uniquement pour cette intégration locale :

```bash
.venv/bin/pip install -r badge83/requirements-blockchain.txt
```

Installer les dépendances Node du sous-projet Hardhat si `node_modules/` n'existe pas :

```bash
cd badge83/blockchain
npm install
```

`requirements.txt` reste inchangé : `web3` n'est pas une dépendance obligatoire de Badge83.

---

## 4. Lancer le nœud Hardhat local

Dans un terminal dédié :

```bash
cd /home/ubuntu/projects/Mode83/badge83/blockchain
npx hardhat node --hostname 127.0.0.1
```

Le RPC local attendu est :

```text
http://127.0.0.1:8545
```

La chaîne Hardhat locale utilise généralement :

```text
chainId = 31337
```

---

## 5. Déployer le contrat localement

Dans un autre terminal :

```bash
cd /home/ubuntu/projects/Mode83/badge83/blockchain
npx hardhat run scripts/deploy.js --network localhost
```

Sortie attendue :

```text
Badge83Anchor deploye: 0x...
```

Conserver cette adresse uniquement dans l'environnement local, par exemple :

```bash
export BADGE83_EVM_CONTRACT_ADDRESS=0x...
```

---

## 6. Configurer Badge83 pour l'intégration locale

Exemple de configuration locale Hardhat :

```bash
export BADGE83_EVM_RPC_URL=http://127.0.0.1:8545
export BADGE83_EVM_CHAIN_ID=31337
export BADGE83_EVM_CONTRACT_ADDRESS=0x...
export BADGE83_EVM_PRIVATE_KEY=0x...
export BADGE83_EVM_NETWORK_LABEL=hardhat-local
export BADGE83_EVM_CONFIRMATION_TIMEOUT_SECONDS=120
```

Pour que l'API utilise EVM par défaut si le corps ne précise pas de provider :

```bash
export BADGE83_ANCHORING_PROVIDER=evm
```

Sinon, garder le comportement par défaut :

```bash
export BADGE83_ANCHORING_PROVIDER=mock
```

et appeler explicitement le provider EVM dans le corps API.

Ne pas écrire de clé privée réelle dans un fichier versionné. Utiliser un `.env` local non commité ou des variables d'environnement de session.

---

## 7. Tester via l'API Badge83

Démarrer Badge83 avec l'environnement configuré, puis émettre un badge normalement. Une preuve locale est créée automatiquement à l'émission.

Demander ensuite un ancrage EVM explicite :

```bash
curl -X POST "http://127.0.0.1:8000/api/badges/<assertion_id>/anchor" \
  -H "Content-Type: application/json" \
  --cookie "badge83_auth=<cookie_admin>" \
  -d '{"provider":"evm","actor":"admin","process":true}'
```

Réponse attendue :

```json
{
  "assertion_id": "...",
  "transaction": {
    "status": "anchored",
    "provider": "evm",
    "network": "hardhat-local",
    "tx_hash": "0x...",
    "block_number": 2,
    "error_message": null
  }
}
```

Vérifier l'historique d'ancrage :

```bash
curl "http://127.0.0.1:8000/api/badges/<assertion_id>/anchoring" \
  --cookie "badge83_auth=<cookie_admin>"
```

---

## 8. Test d'intégration Python local sans lancer l'UI

Pour valider le provider et la persistance SQLite sans passer par le navigateur, utiliser un script ponctuel non versionné ou une commande Python locale qui :

1. crée une assertion de test ;
2. calcule le hash via `HashService` ;
3. sauvegarde une `VerificationProof` dans une base SQLite temporaire ;
4. appelle `AnchoringService.demander_ancrage(..., provider="evm")` ;
5. traite la transaction ;
6. vérifie `status=anchored`, `tx_hash=0x...` et `block_number` non nul.

Exemple de résultat obtenu en intégration locale Hardhat :

```text
status = anchored
provider = evm
network = hardhat-local
tx_hash = 0x...
block_number = 2
```

---

## 9. Vérification blockchain publique du hash

Après un ancrage EVM confirmé, les pages publiques de vérification Badge83 affichent une vérification blockchain en lecture seule.

Cette vérification :

- utilise le dernier ancrage local dont `provider=evm` et `status=anchored` ;
- relit uniquement le `credential_hash` local ;
- convertit `sha256:<64 hex>` en `bytes32` ;
- appelle la fonction view `anchored(bytes32)` du contrat ;
- n'utilise pas `BADGE83_EVM_PRIVATE_KEY` ;
- ne publie aucune donnée personnelle et ne crée aucune transaction.

La configuration minimale de lecture est :

```text
BADGE83_EVM_RPC_URL
BADGE83_EVM_CONTRACT_ADDRESS
BADGE83_EVM_NETWORK_LABEL
```

Si `web3` ou la configuration RPC est absente, Badge83 continue de fonctionner. La page affiche alors un statut informatif, par exemple `Vérification blockchain non configurée` ou `Dépendance blockchain absente`.

Les pages concernées sont :

```text
GET /verify/badge/<assertion_id>
GET /verify/qr/<assertion_id>
```

Important : la page publique contient toujours l'`assertion_id` car c'est son identifiant de consultation Badge83, mais cet identifiant n'est pas envoyé au smart contract. Le contrat ne voit que le hash `bytes32`.

---

## 10. Vérifications de non-régression

Les tests unitaires Python doivent rester passants sans RPC réel obligatoire :

```bash
cd /home/ubuntu/projects/Mode83/badge83
../.venv/bin/python -m pytest tests/unit -q
```

Les tests Hardhat doivent rester passants :

```bash
cd /home/ubuntu/projects/Mode83/badge83/blockchain
npm test
```

Résultat de référence après intégration locale du 15/06/2026 :

```text
Python unit suite : 158 passed, 12 warnings
Hardhat tests : 6 passing
```

---

## 11. Dépannage

### `Configuration EVM incomplète.`

Vérifier :

```text
BADGE83_EVM_RPC_URL
BADGE83_EVM_CONTRACT_ADDRESS
BADGE83_EVM_PRIVATE_KEY
```

### `Dépendance optionnelle web3 non installée.`

Installer les dépendances optionnelles :

```bash
.venv/bin/pip install -r badge83/requirements-blockchain.txt
```

### `RPC EVM indisponible.`

Vérifier que le nœud Hardhat est lancé sur `127.0.0.1:8545`.

### Double ancrage refusé par le contrat

Le contrat refuse deux appels `anchor(bytes32)` avec le même hash. Pour refaire un test, utiliser une assertion différente ou redéployer le contrat sur un nœud Hardhat réinitialisé.

### Vérification blockchain publique non disponible

La vérification publique est read-only. Elle peut être indisponible même si Badge83 fonctionne correctement. Vérifier :

```text
BADGE83_EVM_RPC_URL
BADGE83_EVM_CONTRACT_ADDRESS
requirements-blockchain.txt installé si l'on veut activer web3
```

La clé privée n'est pas nécessaire pour cette vérification.

---

## 12. Limites actuelles

- pas encore de transaction testnet ;
- vérification blockchain publique limitée au dernier ancrage EVM local enregistré ;
- pas d'indexation externe des événements `CredentialHashAnchored`.