from __future__ import annotations

from fastapi import APIRouter

from app.models import Assertion, VerifyResponse, is_iso_datetime

router = APIRouter(tags=["verify"])
EXPECTED_ISSUER_ID = "https://mode83.example/issuers/main"


@router.post("/verify", response_model=VerifyResponse)
def verify_badge(assertion: Assertion):
    required_fields = [
        assertion.id,
        assertion.type,
        assertion.issuedOn,
        assertion.badge.id,
        assertion.issuer.id,
    ]
    if not all(required_fields):
        return VerifyResponse(valid=False, message="Le badge ne contient pas tous les champs obligatoires.")

    if not assertion.recipient.name and not assertion.recipient.email:
        return VerifyResponse(valid=False, message="Le destinataire doit contenir un nom ou un email.")

    if not is_iso_datetime(assertion.issuedOn):
        return VerifyResponse(valid=False, message="Le champ issuedOn doit être une date ISO 8601 valide.")

    if assertion.issuer.id != EXPECTED_ISSUER_ID:
        return VerifyResponse(valid=False, message="L'émetteur n'est pas reconnu par ce prototype.")

    return VerifyResponse(valid=True, message="Le badge est valide pour ce prototype Open Badges.")
