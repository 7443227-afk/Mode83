// SPDX-License-Identifier: MIT
pragma solidity ^0.8.20;

/// @title Badge83Registry
/// @notice Registre universel minimal pour ancrer et revoquer uniquement l'empreinte opaque d'un credential Badge83.
/// @dev Le contrat ne stocke aucune donnee personnelle: ni assertion_id, ni nom, ni email, ni JSON, ni PNG.
contract Badge83Registry {
    struct CredentialStatus {
        bool anchored;
        bool revoked;
        uint64 anchoredAt;
        uint64 revokedAt;
        address anchoredBy;
        address revokedBy;
    }

    event CredentialAnchored(
        bytes32 indexed credentialHash,
        address indexed actor,
        uint64 anchoredAt
    );

    event CredentialRevoked(
        bytes32 indexed credentialHash,
        address indexed actor,
        uint64 revokedAt
    );

    event OperatorUpdated(address indexed operator, bool allowed);

    event OwnershipTransferred(
        address indexed previousOwner,
        address indexed newOwner
    );

    address public owner;
    mapping(address => bool) public operators;
    mapping(bytes32 => CredentialStatus) private credentials;

    modifier onlyOwner() {
        require(msg.sender == owner, "ONLY_OWNER");
        _;
    }

    modifier onlyOwnerOrOperator() {
        require(msg.sender == owner || operators[msg.sender], "NOT_AUTHORIZED");
        _;
    }

    constructor() {
        owner = msg.sender;
        emit OwnershipTransferred(address(0), msg.sender);
    }

    /// @notice Transfere l'administration du registre a une nouvelle adresse.
    /// @param newOwner Nouvelle adresse owner.
    function transferOwnership(address newOwner) external onlyOwner {
        require(newOwner != address(0), "INVALID_OWNER");
        address previousOwner = owner;
        owner = newOwner;
        emit OwnershipTransferred(previousOwner, newOwner);
    }

    /// @notice Autorise ou retire un operateur d'ancrage/revocation.
    /// @param operator Adresse a configurer.
    /// @param allowed True pour autoriser, false pour retirer.
    function setOperator(address operator, bool allowed) external onlyOwner {
        require(operator != address(0), "INVALID_OPERATOR");
        operators[operator] = allowed;
        emit OperatorUpdated(operator, allowed);
    }

    /// @notice Ancre un hash de credential deja calcule hors chaine par Badge83.
    /// @param credentialHash Empreinte SHA-256 convertie en bytes32.
    function anchor(bytes32 credentialHash) external onlyOwnerOrOperator {
        require(credentialHash != bytes32(0), "INVALID_HASH");
        CredentialStatus storage status = credentials[credentialHash];
        require(!status.anchored, "ALREADY_ANCHORED");

        uint64 anchoredAt = uint64(block.timestamp);
        status.anchored = true;
        status.anchoredAt = anchoredAt;
        status.anchoredBy = msg.sender;

        emit CredentialAnchored(credentialHash, msg.sender, anchoredAt);
    }

    /// @notice Revoque publiquement un hash deja ancre, sans publier la raison metier.
    /// @param credentialHash Empreinte SHA-256 convertie en bytes32.
    function revoke(bytes32 credentialHash) external onlyOwnerOrOperator {
        require(credentialHash != bytes32(0), "INVALID_HASH");
        CredentialStatus storage status = credentials[credentialHash];
        require(status.anchored, "NOT_ANCHORED");
        require(!status.revoked, "ALREADY_REVOKED");

        uint64 revokedAt = uint64(block.timestamp);
        status.revoked = true;
        status.revokedAt = revokedAt;
        status.revokedBy = msg.sender;

        emit CredentialRevoked(credentialHash, msg.sender, revokedAt);
    }

    /// @notice Retourne le statut complet d'un hash de credential.
    function getStatus(bytes32 credentialHash)
        external
        view
        returns (
            bool anchored,
            bool revoked,
            uint64 anchoredAt,
            uint64 revokedAt,
            address anchoredBy,
            address revokedBy
        )
    {
        CredentialStatus memory status = credentials[credentialHash];
        return (
            status.anchored,
            status.revoked,
            status.anchoredAt,
            status.revokedAt,
            status.anchoredBy,
            status.revokedBy
        );
    }

    /// @notice Indique si un hash est ancre et non revoque.
    function isValid(bytes32 credentialHash) external view returns (bool) {
        CredentialStatus memory status = credentials[credentialHash];
        return status.anchored && !status.revoked;
    }
}