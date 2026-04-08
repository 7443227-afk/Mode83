from __future__ import annotations

from fastapi import APIRouter

from app.models import Assertion, IssueRequest, build_assertion

router = APIRouter(tags=["issue"])


@router.post("/issue", response_model=Assertion)
def issue_badge(payload: IssueRequest):
    return build_assertion(request=payload)
