import pytest

from src.health_archive import AppointmentDocument, prepare_archive


def test_archive_payload_masks_patient_identifiers():
    parsed = {"text": "Jane Doe visit; member 123-45-6789"}
    result = prepare_archive(AppointmentDocument("Jane Doe", "pdf", "apt-42"), parsed)
    assert result == {"appointment_id": "apt-42", "status": "ready_for_archive", "text": "[PATIENT] visit; member [ID]"}


@pytest.mark.parametrize("parsed", [{}, {"text": ""}, {"text": "  \n "}, {"text": None}])
def test_archive_rejects_missing_or_empty_extraction(parsed):
    with pytest.raises(ValueError, match="produced no text"):
        prepare_archive(AppointmentDocument("", "pdf", "apt-42"), parsed)
