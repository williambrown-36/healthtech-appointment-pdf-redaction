import json
import sys

from src.health_archive import AppointmentDocument, parse_pdf, prepare_archive


def main() -> None:
    if len(sys.argv) != 3:
        raise SystemExit("usage: python run_redaction.py APPOINTMENT_ID PDF_BASE64")
    appointment_id, pdf = sys.argv[1:]
    parsed = parse_pdf(pdf)
    result = prepare_archive(AppointmentDocument("", pdf, appointment_id), parsed)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()

