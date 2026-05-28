# Badge83 — Cadrage Projet B blockchain

Date : 28/05/2026  
Projet : Badge83 — Open Badges MODE83  
Objet : cadrage d'un PoC d'ancrage blockchain après stabilisation du Projet A

---

## 1. Positionnement

Le Projet B blockchain est une extension optionnelle de Badge83. Il ne doit pas
modifier le flux Projet A validé : émission Open Badges, PNG baked, vérification
publique, QR code, émission groupée, registre local et exploitation Docker.

Le PoC doit rester isolé, démontrable localement et désactivé par défaut.

## 2. Règles impératives

- Ne jamais stocker de donnée personnelle on-chain.
- Ne jamais publier de nom, email, contenu JSON complet ou détail de formation
  sur blockchain.
- Ancrer uniquement une empreinte cryptographique.
- Ne jamais commiter de clé privée, seed phrase, token RPC ou fichier `.env` réel.
- Garder l'intégration désactivée par défaut.
- Ne pas casser les endpoints publics Open Badges existants.
- Documenter clairement les limites du PoC.

## 3. Périmètre recommandé

Créer un espace séparé dans le dépôt :

```text
badge83/blockchain-poc/
```

Fonctions minimales :

1. définir un payload canonique sans donnée personnelle ;
2. calculer un hash SHA-256 stable ;
3. écrire un smart contract Solidity minimal ;
4. tester avec Hardhat en réseau local ;
5. ancrer le hash d'un badge ;
6. vérifier l'existence du hash ;
7. documenter le lancement et les limites.

## 4. Payload canonique

Le payload de hash doit être stable, minimal et non personnel. Exemple :

```json
{
  "project": "Badge83",
  "version": "1",
  "assertion_id": "<uuid>",
  "assertion_url": "https://<domaine>/assertions/<uuid>",
  "issued_on": "<date ISO 8601>",
  "badge_class": "https://<domaine>/badges/blockchain-foundations"
}
```

Le JSON doit être sérialisé de manière déterministe avant hash, par exemple avec
tri des clés et séparateurs normalisés.

## 5. Contrat minimal cible

```solidity
// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

contract Badge83AnchorRegistry {
    mapping(bytes32 => uint256) public anchoredAt;

    event BadgeAnchored(bytes32 indexed badgeHash, uint256 timestamp);

    function anchorBadge(bytes32 badgeHash) external {
        require(anchoredAt[badgeHash] == 0, "Badge already anchored");
        anchoredAt[badgeHash] = block.timestamp;
        emit BadgeAnchored(badgeHash, block.timestamp);
    }

    function isAnchored(bytes32 badgeHash) external view returns (bool) {
        return anchoredAt[badgeHash] != 0;
    }
}
```

## 6. Variables de configuration possibles

```text
BLOCKCHAIN_ANCHORING_ENABLED=false
BLOCKCHAIN_RPC_URL=
BLOCKCHAIN_CONTRACT_ADDRESS=
BLOCKCHAIN_PRIVATE_KEY=
```

Ces variables ne doivent pas être obligatoires pour lancer Badge83. Elles doivent
rester vides ou désactivées dans les exemples publics, sauf placeholders sans
secret réel.

## 7. Critères de réussite du PoC

- Un badge émis produit un hash stable et reproductible.
- Le hash peut être ancré sur une chaîne locale Hardhat.
- La vérification retourne correctement l'état ancré/non ancré.
- Aucun secret ni donnée personnelle n'est présent dans Git.
- Le Projet A reste utilisable sans dépendance blockchain.

## 8. Limites à annoncer

- Le PoC ne remplace pas la validation Open Badges.
- La blockchain prouve seulement l'existence d'un hash à un instant donné.
- La révocation, la gouvernance des clés et le coût réseau doivent être étudiés
  avant toute mise en production.
- Toute intégration testnet/mainnet doit faire l'objet d'une décision séparée.
