"""Service health: liveness, edgartools version, identity state."""

from __future__ import annotations

import os
from typing import Literal

from edgar.__about__ import __version__ as edgartools_version
from fastapi import APIRouter

from app.models.common import WireModel

router = APIRouter()


class Health(WireModel):
    status: Literal["ok"]
    edgartools_version: str
    identity_set: bool


@router.get("/health")
def health() -> Health:
    # read the env directly: edgar.core.get_identity() prompts interactively when unset.
    # identity_set is false only if boot semantics change (load_settings aborts without
    # an identity today) - kept as belt-and-suspenders for monitoring
    return Health(
        status="ok",
        edgartools_version=edgartools_version,
        identity_set=bool(os.environ.get("EDGAR_IDENTITY")),
    )
