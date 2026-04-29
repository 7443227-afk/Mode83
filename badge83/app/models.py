from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, List, Literal, Optional
from uuid import uuid4

from pydantic import BaseModel, EmailStr, Field, field_validator, model_validator


class BadgeField(BaseModel):
    """Définition d'un champ individuel pour un schéma de badge."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    label: str
    field_type: Literal["text", "email", "number", "date", "select", "textarea"]
    required: bool = False
    default_value: Optional[str] = None
    options: Optional[List[str]] = None
    description: Optional[str] = None
    validation_pattern: Optional[str] = None
    min_length: Optional[int] = None
    max_length: Optional[int] = None
    min_value: Optional[float] = None
    max_value: Optional[float] = None
    position: int = 0

    @model_validator(mode="after")
    def validate_select_options(self):
        if self.field_type == "select" and not self.options:
            raise ValueError("Les champs de sélection doivent définir au moins une option.")
        return self


class BadgeSchema(BaseModel):
    """Schéma réutilisable définissant les champs attendus pour un badge."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    fields: List[BadgeField] = Field(default_factory=list)
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class TextOverlay(BaseModel):
    """Configuration d'un texte superposé sur le PNG du badge."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    content_type: Literal["static", "field"]
    static_text: Optional[str] = None
    field_id: Optional[str] = None
    font_family: str = "Arial"
    font_size: int = 16
    font_color: str = "#000000"
    font_style: List[Literal["bold", "italic", "underline"]] = Field(default_factory=list)
    text_align: Literal["left", "center", "right"] = "left"
    position_x: int = 0
    position_y: int = 0
    rotation: int = 0
    opacity: float = 1.0
    outline_width: int = 0
    outline_color: str = "#FFFFFF"

    @model_validator(mode="after")
    def validate_content_source(self):
        if self.content_type == "static" and not self.static_text:
            raise ValueError("Les textes statiques superposés doivent définir static_text.")
        if self.content_type == "field" and not self.field_id:
            raise ValueError("Les textes superposés liés à un champ doivent définir field_id.")
        return self

    @field_validator("opacity")
    @classmethod
    def validate_opacity(cls, value: float) -> float:
        if not 0 <= value <= 1:
            raise ValueError("L'opacité doit être comprise entre 0 et 1.")
        return value


class BadgeTemplate(BaseModel):
    """Modèle complet de badge combinant schéma, image et mise en page."""

    id: str = Field(default_factory=lambda: str(uuid4()))
    name: str
    description: Optional[str] = None
    schema_id: Optional[str] = None
    background_image: Optional[str] = None
    text_overlays: List[TextOverlay] = Field(default_factory=list)
    qr_code_placement: Literal[
        "top-left", "top-right", "bottom-left", "bottom-right", "center", "custom"
    ] = "bottom-right"
    qr_code_size: float = 0.22
    qr_code_offset_x: int = 0
    qr_code_offset_y: int = 0
    qr_code_foreground_color: str = "#000000"
    qr_code_background_color: str = "#FFFFFF"
    qr_code_error_correction: Literal["L", "M", "Q", "H"] = "M"
    qr_code_border: int = 2
    is_active: bool = True
    created_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    updated_at: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())

    @field_validator("qr_code_size")
    @classmethod
    def validate_qr_code_size(cls, value: float) -> float:
        if not 0.05 <= value <= 1.0:
            raise ValueError("La taille du QR code doit être comprise entre 0.05 et 1.0.")
        return value

    @field_validator("qr_code_border")
    @classmethod
    def validate_qr_code_border(cls, value: int) -> int:
        if value < 0:
            raise ValueError("La bordure du QR code ne peut pas être négative.")
        return value


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
    field_values: Dict[str, Any] = Field(default_factory=dict)


class IssueRequest(BaseModel):
    name: Optional[str] = None
    email: EmailStr | None = None
    issuer: Optional[Issuer] = None
    badge_class: Optional[BadgeClass] = None

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


def build_assertion(
    request: IssueRequest,
    issuer: Optional[Issuer] = None,
    badge_class: Optional[BadgeClass] = None,
) -> Assertion:
    issuer = issuer or request.issuer or build_default_issuer()
    badge_class = badge_class or request.badge_class or build_default_badge_class(issuer=issuer)
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
