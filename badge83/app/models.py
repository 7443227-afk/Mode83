from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal
from uuid import uuid4

from pydantic import BaseModel, EmailStr, model_validator


class Issuer(BaseModel):
    id: str
    name: str
    url: str


class BadgeClass(BaseModel):
    id: str
    name: str
    description: str
    issuer: Issuer


class Recipient(BaseModel):
    name: str | None = None
    email: EmailStr | None = None


class Assertion(BaseModel):
    id: str
    type: Literal["Assertion"]
    recipient: Recipient
    issuedOn: str
    badge: BadgeClass
    issuer: Issuer


class IssueRequest(BaseModel):
    name: str | None = None
    email: EmailStr | None = None

    @model_validator(mode="after")
    def validate_identity(self):
        if not self.name and not self.email:
            raise ValueError("Vous devez fournir au minimum un nom ou un email.")
        return self


class VerifyResponse(BaseModel):
    valid: bool
    message: str


def build_default_issuer() -> Issuer:
    return Issuer(
        id="https://mode83.example/issuers/main",
        name="MODE83",
        url="https://mode83.example",
    )


def build_default_badge_class(issuer: Issuer) -> BadgeClass:
    return BadgeClass(
        id="https://mode83.example/badges/badge-83",
        name="Badge 83",
        description="Badge pédagogique pour démontrer les digital credentials.",
        issuer=issuer,
    )


def build_assertion(request: IssueRequest) -> Assertion:
    issuer = build_default_issuer()
    badge_class = build_default_badge_class(issuer=issuer)
    return Assertion(
        id=f"urn:uuid:{uuid4()}",
        type="Assertion",
        recipient=Recipient(name=request.name, email=request.email),
        issuedOn=datetime.now(timezone.utc).isoformat(),
        badge=badge_class,
        issuer=issuer,
    )


def is_iso_datetime(value: str) -> bool:
    try:
        datetime.fromisoformat(value)
        return True
    except ValueError:
        return False
