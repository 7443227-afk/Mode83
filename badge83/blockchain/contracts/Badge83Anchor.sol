// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Badge83Anchor
/// @notice Registre minimal pour ancrer uniquement l'empreinte opaque d'un credential Badge83.
/// @dev Le contrat ne reçoit ni nom, ni email, ni assertion JSON, ni payload canonique.
contract Badge83Anchor {
    event CredentialHashAnchored(
        bytes32 indexed credentialHash,
        address indexed anchoredBy,
        uint256 timestamp
    );

    mapping(bytes32 => bool) public anchored;

    /// @notice Ancre un hash de credential déjà calculé hors chaîne par Badge83.
    /// @param credentialHash Empreinte SHA-256 convertie en bytes32.
    function anchor(bytes32 credentialHash) external {
        require(credentialHash != bytes32(0), "Hash invalide");
        require(!anchored[credentialHash], "Hash deja ancre");

        anchored[credentialHash] = true;
        emit CredentialHashAnchored(credentialHash, msg.sender, block.timestamp);
    }
}