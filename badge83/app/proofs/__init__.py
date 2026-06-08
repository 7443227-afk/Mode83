"""Services de preuve locale pour les credentials Badge83.

Ce paquet prépare l'ancrage blockchain sans ajouter de dépendance blockchain
au flux d'émission existant.
"""

from app.proofs.canonical import CanonicalCredentialService
from app.proofs.hash_service import HashService
from app.proofs.models import VerificationProof

__all__ = ["CanonicalCredentialService", "HashService", "VerificationProof"]