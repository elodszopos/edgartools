"""Service health: liveness, edgartools version, identity state."""

from __future__ import annotations

import os
from typing import Literal

from edgar.__about__ import __version__ as edgartools_version
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class Health(BaseModel):
    status: Literal["ok"]
    edgartools_version: str
    identity_set: bool


@router.get("/health")
def health() -> Health:
    # read the env directly: edgar.core.get_identity() prompts interactively when unset
    return Health(
        status="ok",
        edgartools_version=edgartools_version,
        identity_set=bool(os.environ.get("EDGAR_IDENTITY")),
    )
