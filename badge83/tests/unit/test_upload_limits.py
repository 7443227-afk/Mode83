from __future__ import annotations

import asyncio

import pytest
from fastapi import UploadFile

from app.upload_limits import read_upload_limited


def test_read_upload_limited_rejects_content_over_limit(tmp_path):
    upload_path = tmp_path / "large.txt"
    upload_path.write_bytes(b"abcdefghijk")

    with upload_path.open("rb") as handle:
        upload = UploadFile(file=handle, filename="large.txt")
        with pytest.raises(Exception) as exc_info:
            asyncio.run(read_upload_limited(upload, 10, label="Test"))

    assert getattr(exc_info.value, "status_code", None) == 413
    assert getattr(exc_info.value, "detail", None) == "Test trop volumineux"


def test_read_upload_limited_accepts_content_at_limit(tmp_path):
    upload_path = tmp_path / "small.txt"
    upload_path.write_bytes(b"abcdefghij")

    with upload_path.open("rb") as handle:
        upload = UploadFile(file=handle, filename="small.txt")
        content = asyncio.run(read_upload_limited(upload, 10, label="Test"))

    assert content == b"abcdefghij"