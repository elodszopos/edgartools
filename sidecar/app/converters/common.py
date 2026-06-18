"""Converter helpers shared across form converters (no form-specific logic).

Lives below both `converters/filing.py` (envelope) and `converters/forms/*` so either can
import it without the cycle that a forms->filing import would create (filing imports the form
converters to register them in its dispatch table)."""

from __future__ import annotations

from edgar.attachments import Attachment

from app.models.common import DocumentRef
from app.serialize import to_int, to_str


def document_ref(attachment: Attachment) -> DocumentRef:
    return DocumentRef(
        sequence=attachment.sequence_number,
        document=to_str(attachment.document),
        description=to_str(attachment.description),
        document_type=to_str(attachment.document_type),
        size=to_int(attachment.size),
        ixbrl=bool(attachment.ixbrl),
        url=attachment.url if not attachment.empty else None,
    )
