// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Badge83AnchorV2
/// @notice Registre minimal pour ancrer et révoquer publiquement uniquement l'empreinte opaque d'un credential Badge83.
/// @dev Le contrat ne reçoit ni assertion_id, ni nom, ni email, ni raison de révocation, ni payload canonique.
contract Badge83AnchorV2 {
    event CredentialHashAnchored(
        bytes32 indexed credentialHash,
        address indexed anchoredBy,
        uint256 timestamp
    );

    event CredentialHashRevoked(
        bytes32 indexed credentialHash,
        address indexed revokedBy,
        uint256 timestamp
    );

    mapping(bytes32 => bool) public anchored;
    mapping(bytes32 => bool) public revoked;

    /// @notice Ancre un hash de credential déjà calculé hors chaîne par Badge83.
    /// @param credentialHash Empreinte SHA-256 convertie en bytes32.
    function anchor(bytes32 credentialHash) external {
        require(credentialHash != bytes32(0), "Hash invalide");
        require(!anchored[credentialHash], "Hash deja ancre");

        anchored[credentialHash] = true;
        emit CredentialHashAnchored(credentialHash, msg.sender, block.timestamp);
    }

    /// @notice Révoque publiquement un hash déjà ancré, sans publier la raison métier.
    /// @param credentialHash Empreinte SHA-256 convertie en bytes32.
    function revoke(bytes32 credentialHash) external {
        require(credentialHash != bytes32(0), "Hash invalide");
        require(anchored[credentialHash], "Hash non ancre");
        require(!revoked[credentialHash], "Hash deja revoque");

        revoked[credentialHash] = true;
        emit CredentialHashRevoked(credentialHash, msg.sender, block.timestamp);
    }

    function isAnchored(bytes32 credentialHash) external view returns (bool) {
        return anchored[credentialHash];
    }

    function isRevoked(bytes32 credentialHash) external view returns (bool) {
        return revoked[credentialHash];
    }

    function getStatus(bytes32 credentialHash) external view returns (bool isHashAnchored, bool isHashRevoked) {
        return (anchored[credentialHash], revoked[credentialHash]);
    }
}