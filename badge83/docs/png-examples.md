### Documentation - Analyse et Extraction des Métadonnées PNG

#### Objectif

Le script `png_parser.py` est conçu pour analyser des fichiers PNG et extraire des métadonnées, en particulier en se concentrant sur les données Open Badges. Ce document explique ce que fait ce script, comment il fonctionne, quels outils et technologies sont utilisés et comment il est implémenté.

#### Fonctionnalités

1. **Vérification de la Signature PNG**:
   - Le script commence par vérifier si le fichier possède la signature PNG (`PNG_SIGNATURE`).

2. **Analyse des Chunks**:
   - Le script lit le fichier PNG par morceaux (chunks), extrayant les informations suivantes pour chaque chunk :
     - `index`: La position du chunk dans le fichier.
     - `type`: Le type du chunk (par exemple, `tEXt`, `iTXt`, `IHDR`, `IDAT`, `IEND`).
     - `length`: La longueur des données du chunk.
     - `keyword`: Pour les chunks `tEXt` et `iTXt`, le mot-clé.
     - `text_preview`: Un aperçu du contenu texte.
     - `json_keys`: Si le contenu texte est un JSON, une liste des clés JSON.
     - `compression_flag`: Pour les chunks `iTXt`, le drapeau de compression.
     - `compression_method`: Pour les chunks `iTXt`, la méthode de compression.
     - `language`: Pour les chunks `iTXt`, la langue.
     - `translated_keyword`: Pour les chunks `iTXt`, le mot-clé traduit.

3. **Injections Open Badges**:
   - Le script cherche spécifiquement des chunks avec le mot-clé `openbadges` et enregistre leur contenu dans la liste `openbadges_injections`.

4. **Sortie**:
   - Le script génère un rapport JSON contenant toutes les informations extraites.

#### Problèmes Potentiels avec les Données Image

Au cours de l'implémentation actuelle, le script ne s'occupe pas d'extrait et d'inclure explicitement les données de l'image (par exemple, les données des pixels) dans le rapport. Il se concentre plutôt sur l'extraction des métadonnées et des données Open Badges.

#### Recommandations

1. **Inclure les Données de l'Image dans le Rapport**:
   - Pour afficher l'image, le code côté client attend que les données de l'image soient incluses dans le rapport. Nous devons modifier la fonction `inspect_png` pour extraire les données de l'image des chunks `IDAT` et les inclure dans le rapport.

2. **Mettre à Jour la Fonction `inspect_png`**:
   - Nous devons ajouter une étape dans la fonction `inspect_png` pour extraire les données de l'image des chunks `IDAT` et les inclure dans le rapport.

3. **Mettre à Jour le Code Côté Client**:
   - Assurez-vous que le code côté client traite et affiche correctement les données de l'image.

#### Fonction `inspect_png` Mise à Jour

Voici la fonction `inspect_png` mise à jour qui inclut les données de l'image dans le rapport :

```python
#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import struct
import sys
import zlib
import base64
from pathlib import Path
from typing import Any


PNG_SIGNATURE = b"\x89PNG\r\n\x1a\n"


def parse_itxt(data: bytes) -> dict[str, Any] | None:
    keyword_end = data.find(b"\x00")
    if keyword_end == -1:
        return None

    keyword = data[:keyword_end].decode("latin-1", errors="replace")
    rest = data[keyword_end + 1 :]
    if len(rest) < 2:
        return None

    compression_flag = rest[0]
    compression_method = rest[1]
    rest = rest[2:]

    language_end = rest.find(b"\x00")
    if language_end == -1:
        return None
    language = rest[:language_end].decode("latin-1", errors="replace")
    rest = rest[language_end + 1 :]

    translated_end = rest.find(b"\x00")
    if translated_end == -1:
        return None
    translated_keyword = rest[:translated_end].decode("utf-8", errors="replace")
    text_bytes = rest[translated_end + 1 :]

    if compression_flag == 1:
        if compression_method != 0:
            return None
        text_bytes = zlib.decompress(text_bytes)
    elif compression_flag != 0:
        return None

    return {
        "keyword": keyword,
        "compression_flag": compression_flag,
        "compression_method": compression_method,
        "language": language,
        "translated_keyword": translated_keyword,
        "text": text_bytes.decode("utf-8", errors="replace"),
    }


def try_parse_json(text: str) -> dict[str, Any] | list[Any] | None:
    try:
        return json.loads(text)
    except Exception:
        return None


def inspect_png(path: Path) -> dict[str, Any]:
    data = path.read_bytes()
    report: dict[str, Any] = {
        "file": path.name,
        "path": str(path),
        "size_bytes": len(data),
        "signature_ok": data[:8] == PNG_SIGNATURE,
        "chunk_count": 0,
        "chunk_summary": {},
        "chunks": [],
        "openbadges_injections": [],
        "image_data": ""  # Initialiser les données de l'image
    }

    pos = 8
    while pos + 8 <= len(data):
        length = struct.unpack(">I", data[pos : pos + 4])[0]
        chunk_type = data[pos + 4 : pos + 8].decode("latin-1", errors="replace")
        payload = data[pos + 8 : pos + 8 + length]
        chunk: dict[str, Any] = {
            "index": report["chunk_count"] + 1,
            "type": chunk_type,
            "length": length,
        }

        if chunk_type == "tEXt":
            nul_idx = payload.find(b"\x00")
            if nul_idx != -1:
                keyword = payload[:nul_idx].decode("latin-1", errors="replace")
                text = payload[nul_idx + 1 :].decode("utf-8", errors="replace")
                chunk["keyword"] = keyword
                chunk["text_preview"] = text[:160]
                parsed_json = try_parse_json(text)
                if parsed_json is not None:
                    chunk["json_keys"] = list(parsed_json.keys()) if isinstance(parsed_json, dict) else None
                if keyword == "openbadges":
                    report["openbadges_injections"].append(
                        {
                            "chunk_type": "tEXt",
                            "keyword": keyword,
                            "parsed_json": parsed_json,
                            "raw_text": text,
                        }
                    )

        elif chunk_type == "iTXt":
            parsed = parse_itxt(payload)
            if parsed is not None:
                chunk.update({k: v for k, v in parsed.items() if k != "text"})
                chunk["text_preview"] = parsed["text"][:160]
                parsed_json = try_parse_json(parsed["text"])
                if parsed_json is not None:
                    chunk["json_keys"] = list(parsed_json.keys()) if isinstance(parsed_json, dict) else None
                if parsed["keyword"] == "openbadges":
                    report["openbadges_injections"].append(
                        {
                            "chunk_type": "iTXt",
                            "keyword": parsed["keyword"],
                            "compression_flag": parsed["compression_flag"],
                            "parsed_json": parsed_json,
                            "raw_text": parsed["text"],
                        }
                    )

        elif chunk_type == "IDAT":
            report["image_data"] += base64.b64encode(payload).decode('utf-8')  # Encoder les données de l'image en Base64

        report["chunks"].append(chunk)
        report["chunk_count"] += 1
        report["chunk_summary"][chunk_type] = report["chunk_summary"].get(chunk_type, 0) + 1

        pos += 12 + length
        if chunk_type == "IEND":
            break

    return report


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Inspecte un PNG et produit un rapport de structure et de métadonnées Open Badges."
    )
    parser.add_argument("png_file", help="Chemin du fichier PNG à analyser")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="Affiche le JSON avec indentation",
    )
    args = parser.parse_args()

    path = Path(args.png_file)
    if not path.exists():
        print(f"Fichier introuvable : {path}", file=sys.stderr)
        return 1

    report = inspect_png(path)
    if args.pretty:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print(json.dumps(report, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```

#### Résumé

1. **Inclure les Données de l'Image dans le Rapport**:
   - La fonction `inspect_png` inclut maintenant les données de l'image (`IDAT` chunks) dans le rapport comme des données encodées en Base64.

2. **Mettre à Jour le Code Côté Client**:
   - Assurez-vous que le code côté client traite et affiche correctement les données de l'image.

Avec ces mises à jour, le serveur devrait maintenant inclure correctement les données de l'image dans la réponse, et le code côté client devrait être en mesure d'afficher l'image.