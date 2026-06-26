"""U58 converter: edgar.effect.Effect -> EffectData, explicit field-by-field."""

from __future__ import annotations

from edgar.effect import Effect

from app.cik import pad_cik
from app.models.forms.effect import EffectData
from app.serialize import to_str


def effect_data(obj: Effect) -> EffectData:
    cik = to_str(obj.cik)
    return EffectData(
        form="EFFECT",
        cik=pad_cik(cik) if cik else None,
        submission_type=to_str(obj.submission_type),
        is_live=bool(obj.is_live),
        schema_version=to_str(obj.schema_version),
        effective_date=to_str(obj.effective_date),
        entity=to_str(obj.entity),
        source_submission_type=to_str(obj.source_submission_type) or None,
        source_accession_no=to_str(obj.source_accession_no),
        source_file_number=to_str(obj.effectiveness_data.file_number),
    )
