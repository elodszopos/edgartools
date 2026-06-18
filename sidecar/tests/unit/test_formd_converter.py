"""Unit (pure converter): edgar `FormD` -> `FormDData` carries every co-issuer (issuerList) and the
related-person role / middle-name / clarification fields -- the disease-C flattening fix for Form D.

Feeds edgar's committed Form D XML test data straight through the pure `form_d_data` converter --
no network, no fixture store. D.APFund.xml files a real co-issuer; D.1685REIT.xml is single-issuer.
"""

from __future__ import annotations

from pathlib import Path

import edgar
from edgar.offerings import FormD

from app.converters.forms.formd import form_d_data

# edgar is editable-installed; its committed Form D XML lives at <repo>/data (parent of the package).
_DATA = Path(edgar.__file__).resolve().parent.parent / "data"


def _wire(xml_name: str):
    offering_xml = (_DATA / xml_name).read_text()
    obj = FormD.from_xml(offering_xml)
    # co-issuers and related-person roles live only in the offering XML, so the converter re-parses it
    return form_d_data(obj, offering_xml)


def test_converter_carries_co_issuers() -> None:
    wire = _wire("D.APFund.xml")
    assert wire.primary_issuer is not None and wire.primary_issuer.cik == "0001958740"
    # the issuerList co-issuer is carried, never collapsed into the primary issuer
    assert len(wire.additional_issuers) == 1
    co = wire.additional_issuers[0]
    assert co.cik == "0001963203"
    assert co.entity_name == "AP Fund IV AL Vehicle, a series of Inference Technology Partners, LP"
    assert co.entity_type == "Limited Partnership"
    # related-person role + free-text clarification cross the converter (previously dropped)
    p0 = wire.related_persons[0]
    assert p0.relationships == ["Director"]
    assert p0.relationship_clarification == "Manager of the general partner of the Issuer"


def test_converter_single_issuer_has_empty_co_issuers() -> None:
    wire = _wire("D.1685REIT.xml")
    assert wire.additional_issuers == []
    # the role + (absent) middle name + (empty->null) clarification still cross for a single issuer
    p0 = wire.related_persons[0]
    assert p0.middle_name is None
    assert p0.relationships == ["Executive Officer"]
    assert p0.relationship_clarification is None
