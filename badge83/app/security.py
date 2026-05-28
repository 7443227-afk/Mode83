from __future__ import annotations

import ipaddress
import socket
from urllib.parse import urlparse


class SSRFProtectionError(ValueError):
    """Erreur levée lorsqu'une URL distante vise une ressource non publique."""


MAX_REMOTE_JSON_BYTES = 1_048_576
MAX_REMOTE_REDIRECTS = 3


def _is_private_or_local_address(address: str) -> bool:
    """Indique si une adresse IP pointe vers une zone locale ou non publique."""
    ip = ipaddress.ip_address(address)
    return any(
        (
            ip.is_loopback,
            ip.is_private,
            ip.is_link_local,
            ip.is_multicast,
            ip.is_reserved,
            ip.is_unspecified,
        )
    )


def validate_public_http_url(url: str) -> str:
    """Valide qu'une URL HTTP(S) distante ne cible pas le réseau local.

    Badge83 récupère parfois des documents Open Badges hébergés par des tiers.
    Cette fonction réduit le risque SSRF en refusant les schémas non HTTP(S),
    localhost, les IP privées/locales et les noms DNS qui résolvent vers ces IP.
    """
    parsed = urlparse(str(url or "").strip())
    if parsed.scheme not in {"http", "https"} or not parsed.hostname:
        raise SSRFProtectionError("URL distante non autorisée")

    hostname = parsed.hostname.strip().lower().rstrip(".")
    if hostname in {"localhost", "localhost.localdomain"} or hostname.endswith(".localhost"):
        raise SSRFProtectionError("URL locale refusée")

    try:
        if _is_private_or_local_address(hostname):
            raise SSRFProtectionError("Adresse IP non publique refusée")
    except ValueError:
        pass

    try:
        resolved = socket.getaddrinfo(hostname, parsed.port, type=socket.SOCK_STREAM)
    except socket.gaierror as exc:
        raise SSRFProtectionError("Nom DNS distant non résolu") from exc

    for item in resolved:
        address = item[4][0]
        if _is_private_or_local_address(address):
            raise SSRFProtectionError("Résolution DNS vers une adresse non publique refusée")

    return parsed.geturl()