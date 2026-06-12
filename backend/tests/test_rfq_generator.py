from types import SimpleNamespace

from app.services.rfq_generator import RFQGenerator


def test_rfq_generator_includes_required_questions() -> None:
    draft = RFQGenerator().generate(
        SimpleNamespace(cas="64-17-5", primary_name="Ethanol"),
        SimpleNamespace(
            quantity="100 kg",
            required_grade="technical grade",
            destination_country="Poland",
            intended_use="lawful industrial cleaning validation",
        ),
        SimpleNamespace(name="Acme Chemicals"),
    )
    assert "CAS 64-17-5" in draft.subject
    assert "COA" in draft.body
    assert "SDS/MSDS" in draft.body
    assert "REACH" in draft.body
    assert "false declarations" in draft.body
