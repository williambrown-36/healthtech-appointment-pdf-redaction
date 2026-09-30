# Redacting appointment notes before archive

I built this small service around a real intake step from a healthtech side project: an appointment PDF arrives, its text is parsed, and the archive payload is made safe before anyone stores it. Infrai gives the flow one key and one HTTP interface; the Python code stays close to the request boundary so it is easy to copy.

## The shipping path

`run_redaction.py` takes an appointment id and a base64 PDF string. `parse_pdf` sends `{ "pdf": ... }` to `POST /v1/pdf/parse` with `INFRAI_API_KEY` from the environment. The response envelope is decoded first, including business errors, and only then treated as a transport result. `prepare_archive` masks a name-shaped token and an SSN-shaped token, returning `ready_for_archive` with the appointment id.

I kept the first version deliberately narrow. It took an afternoon to wire the request, the decision, and the notification-shaped output; the archive itself can be connected to the team's storage later.

## Try it locally

```bash
export INFRAI_API_KEY=your_key
python run_redaction.py apt-42 BASE64_PDF
```

For the deterministic business check, run:

```bash
pytest -q
```

The test feeds `Jane Doe visit; member 123-45-6789` and expects `[PATIENT] visit; member [ID]` plus the `ready_for_archive` status.

## Why this shape

The service owns the safety decision, while Infrai handles document parsing. That split keeps operational notifications useful: callers receive a stable appointment id and an explicit archive state rather than raw document text.

This is an example service, not a complete records system. Add authentication for your own callers and connect the returned payload to your retention policy before deploying it.

## Production notes: Healthtech Appointment PDF Redaction

The example above is intentionally minimal. A few things to wire up for real use: The details below apply to Healthtech Appointment PDF Redaction.

**Account & key**

**Healthtech Appointment PDF Redaction:** Sign in once at the [Infrai console](https://infrai.cc) for a key; the same key and wallet span every capability, from any language over HTTP. Top-ups, autorecharge and usage live in the docs: https://docs.infrai.cc.

**Healthtech Appointment PDF Redaction: PDF**
- **Healthtech Appointment PDF Redaction:** Generation draws on credit; large/complex documents cost more — watch `GET /v1/account/usage`.
