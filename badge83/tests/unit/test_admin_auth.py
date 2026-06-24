from __future__ import annotations

from fastapi.testclient import TestClient

from app.main import AUTH_COOKIE_NAME, _make_auth_cookie, app


def _client_admin() -> TestClient:
    client = TestClient(app)
    client.cookies.set(AUTH_COOKIE_NAME, _make_auth_cookie("admin"))
    return client


def test_admin_api_requires_authentication():
    client = TestClient(app)

    response = client.get("/api/badges")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_badge_constructor_requires_authentication():
    client = TestClient(app)

    response = client.get("/badge-constructor/templates")

    assert response.status_code == 401
    assert response.json()["detail"] == "Authentication required"


def test_public_verify_endpoint_remains_available():
    client = TestClient(app)

    response = client.get("/verify/non-existent-badge-id")

    assert response.status_code == 200
    assert response.json()["valid"] is False


def test_public_openbadges_endpoint_remains_available():
    client = TestClient(app)

    response = client.get("/issuers/main")

    assert response.status_code in {200, 404}
    assert response.status_code != 401


def test_admin_index_expose_le_bouton_ancrage_local():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="anchorLocalBtn"' in response.text
    assert "Demander un ancrage local" in response.text
    assert "/anchor" in response.text
    assert "provider: 'mock'" in response.text


def test_admin_index_expose_le_bouton_ancrage_blockchain_evm_distinct():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="anchorEvmBtn"' in response.text
    assert "Demander un ancrage blockchain réel" in response.text
    assert "Request real blockchain anchoring" in response.text
    assert "Запросить реальный blockchain-анкеринг" in response.text
    assert "requestRealEvmAnchoring" in response.text
    assert "provider: 'evm'" in response.text


def test_admin_index_expose_option_ancrage_local_apres_emission():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="issueAnchorLocal"' in response.text
    assert "Demander aussi un ancrage local mock après émission" in response.text
    assert "requestLocalMockAnchoring" in response.text
    assert "maybeAnchorIssuedBadge" in response.text


def test_admin_index_expose_option_ancrage_evm_apres_emission():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="issueAnchorEvm"' in response.text
    assert "Demander un ancrage blockchain réel après émission" in response.text
    assert "Request real blockchain anchoring after issuing" in response.text
    assert "Записать хеш в блокчейн после выдачи" in response.text
    assert "requestRealEvmAnchoring" in response.text
    assert "anchoring_results" in response.text


def test_admin_index_expose_audit_trail_dans_inspecteur():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert "Audit trail" in response.text
    assert "renderAuditAdminSummary" in response.text
    assert "/audit" in response.text


def test_admin_index_expose_resume_ancrage_apres_emission():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert "renderIssueAnchoringResultSummary" in response.text
    assert "Ancrage local mock" in response.text
    assert "Ancrage blockchain EVM" in response.text
    assert "non confirmé" in response.text



def test_admin_index_expose_actions_revocation_locale_et_evm():
    client = _client_admin()

    response = client.get("/")

    assert response.status_code == 200
    assert 'id="revokeLocalBtn"' in response.text
    assert 'id="revokeEvmBtn"' in response.text
    assert 'id="revokeAlsoEvm"' in response.text
    assert "Révoquer le badge" in response.text
    assert "Publier révocation EVM" in response.text
    assert "Revoke badge" in response.text
    assert "Отозвать badge" in response.text
    assert "requestLocalRevocation" in response.text
    assert "requestEvmRevocation" in response.text
    assert "/revoke/blockchain" in response.text
    assert "request_evm_revocation" in response.text
    assert "renderRevocationAdminSummary" in response.text
    assert "item.credential_status || item.revocation" in response.text



def test_api_badges_registry_uses_fast_listing_without_status_builders(tmp_path, monkeypatch):
    import json
    from app import main
    from app.database import sync_assertion_record

    issued_dir = tmp_path / "issued"
    baked_dir = tmp_path / "baked"
    issued_dir.mkdir()
    baked_dir.mkdir()
    assertion_id = "fast-registry-1"
    assertion = {
        "@context": "https://w3id.org/openbadges/v2",
        "id": f"https://tests.mode83.local/assertions/{assertion_id}",
        "type": "Assertion",
        "recipient": {"type": "email", "hashed": True, "identity": "sha256$abc"},
        "issuedOn": "2026-06-17T07:00:00+00:00",
        "verification": {"type": "HostedBadge"},
        "badge": "https://tests.mode83.local/badges/blockchain-foundations",
        "issuer": "https://tests.mode83.local/issuers/main",
        "admin_recipient": {"name": "Fast Registry", "email": "fast@example.test"},
    }
    (issued_dir / f"{assertion_id}.json").write_text(json.dumps(assertion), encoding="utf-8")
    monkeypatch.setattr(main, "ISSUED_DIR", issued_dir)
    monkeypatch.setattr(main, "BAKED_DIR", baked_dir)
    monkeypatch.setenv("BADGE83_REGISTRY_DB", str(tmp_path / "registry.db"))
    sync_assertion_record(
        assertion_id,
        {**assertion, "admin_recipient": {"name": "Fast Registry"}},
        private_recipient={"name": "Fast Registry", "email": "fast@example.test"},
    )

    def fail_status_builder(*args, **kwargs):
        raise AssertionError("status builder should not run for /api/badges list")

    monkeypatch.setattr(main, "_build_proof_status", fail_status_builder)
    monkeypatch.setattr(main, "_build_revocation_status", fail_status_builder)
    monkeypatch.setattr(main, "_build_anchoring_status", fail_status_builder)
    monkeypatch.setattr(main, "_build_blockchain_revocation_status", fail_status_builder)
    monkeypatch.setattr(main, "_build_audit_trail", fail_status_builder)

    client = _client_admin()
    response = client.get("/api/badges")

    assert response.status_code == 200
    item = response.json()["items"][0]
    assert item["assertion_id"] == assertion_id
    assert item["name"] == "Fast Registry"
    assert item["email"] == "fast@example.test"
    assert item["proof"] is None
    assert item["anchoring"] is None
    assert item["blockchain_revocation"] is None
