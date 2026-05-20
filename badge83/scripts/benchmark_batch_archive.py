from __future__ import annotations

import argparse
import io
import sys
import time
import zipfile
from pathlib import Path

from fastapi import FastAPI
from fastapi.testclient import TestClient


ROOT_DIR = Path(__file__).resolve().parents[1]
if str(ROOT_DIR) not in sys.path:
    sys.path.insert(0, str(ROOT_DIR))

from app.routes.badge_constructor import router as badge_constructor_router  # noqa: E402


def _build_client(db_path: Path) -> TestClient:
    """Construit un client FastAPI local pour mesurer le flux batch sans serveur externe."""
    import os

    os.environ["BADGE83_REGISTRY_DB"] = str(db_path)
    app = FastAPI()
    app.include_router(badge_constructor_router)
    return TestClient(app)


def _create_template(client: TestClient, row_count: int) -> str:
    """Crée un modèle minimal utilisable par l'émission groupée."""
    response = client.post(
        "/badge-constructor/templates",
        json={
            "name": f"Benchmark émission groupée {row_count} lignes",
            "text_overlays": [],
            "qr_code_placement": "bottom-right",
            "qr_code_size": 0.22,
        },
    )
    response.raise_for_status()
    return response.json()["id"]


def _build_csv(row_count: int) -> str:
    """Génère un CSV synthétique avec uniquement des lignes prêtes."""
    lines = ["nom,email,programme,reussi"]
    for index in range(1, row_count + 1):
        lines.append(f"Participant {row_count}-{index},participant{row_count}-{index}@example.org,Formation volume,oui")
    return "\n".join(lines) + "\n"


def _measure_archive(client: TestClient, template_id: str, row_count: int) -> dict:
    csv_content = _build_csv(row_count)
    started = time.perf_counter()
    response = client.post(
        f"/badge-constructor/templates/{template_id}/batch-issue/archive",
        files={"file": (f"participants-{row_count}.csv", csv_content, "text/csv")},
    )
    elapsed = time.perf_counter() - started
    response.raise_for_status()

    archive = zipfile.ZipFile(io.BytesIO(response.content))
    png_count = len([name for name in archive.namelist() if name.startswith("badges/") and name.endswith(".png")])
    return {
        "rows": row_count,
        "seconds": round(elapsed, 3),
        "zip_bytes": len(response.content),
        "png_count": png_count,
        "session_id": response.headers.get("X-Badge83-Session-Id"),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Benchmark local de génération ZIP pour l'émission groupée Badge83.")
    parser.add_argument("--rows", nargs="+", type=int, default=[50, 100, 300], help="Volumes de lignes à tester")
    parser.add_argument(
        "--db",
        type=Path,
        default=ROOT_DIR / "data" / "benchmark-batch-archive.sqlite3",
        help="Chemin de base SQLite temporaire utilisée pour le benchmark",
    )
    args = parser.parse_args()

    args.db.parent.mkdir(parents=True, exist_ok=True)
    if args.db.exists():
        args.db.unlink()

    client = _build_client(args.db)
    print("rows,seconds,zip_bytes,png_count,session_id")
    for row_count in args.rows:
        template_id = _create_template(client, row_count)
        result = _measure_archive(client, template_id, row_count)
        print(
            f"{result['rows']},{result['seconds']},{result['zip_bytes']},"
            f"{result['png_count']},{result['session_id']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())