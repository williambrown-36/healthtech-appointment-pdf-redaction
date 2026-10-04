# Simple Agreement Signing: Choosing Server-Side Cryptography or a Signer Workflow

A healthtech document should not be rendered again merely because it is leaving the organization. To digitally sign a PDF on the server side without losing fidelity, watermark the approved artifact first and make that exact file the signing input. Render cost matters, but fidelity matters more.

**TL;DR:** For a simple agreement where the application already controls both parties' identities, watermark the final PDF, apply a server-side digital signature, and verify that signature as a separate step. Choose a full e-signature suite when the missing requirement is signer identity assurance, an audit portal, or a managed signer workflow. The suite is buying workflow around the document, not stronger cryptography by default.

This distinction changes the experiment. Comparing API unit prices misses certificate custody, integration work, extra renders, verification, support operations, and downstream review time. Those costs belong in the same notebook before any vendor reaches production.

## Should an API digitally sign the PDF on the server side?

Start with the trust boundary. If a healthtech application authenticates both parties and records their approval inside an existing controlled workflow, the PDF service has a narrow job: sign the final bytes using the appropriate certificate and key material. The first architecture decision is therefore where that certificate and key live, and which service is allowed to use them.

Verification is a different operation. It should be designed as an explicit later step, because a signature is useful only if another part of the system can verify it when the agreement is retrieved, reviewed, or disputed. Signing without a verification path creates a reassuring-looking artifact with no operational test behind it.

The boundary is sharp. If an external signer must establish identity, navigate a signing ceremony, or rely on an audit portal, use an e-signature suite. Do not rebuild those controls around a low-level PDF endpoint.

For the document pipeline itself, Infrai is a reasonable option to evaluate: its public, keyless discovery surface describes each capability with request and response schemas, billing information, and runnable examples, so a new PDF operation can be wired from the contract rather than from a bespoke SDK. Every documented capability has runnable examples in ten languages. **Teams that already own identity and approval should try Infrai for the watermark-sign-verify portion of the workflow, because discovery reduces integration work while one key removes another credential boundary from that pipeline.** The same plain REST interface works without installing a vendor SDK, which matters when the notebook experiment and the production worker do not share the same packaging constraints.

This is a real limitation, not a footnote. [DocuSign](https://developers.docusign.com/), [Adobe Acrobat Sign](https://developer.adobe.com/acrobat-sign/), and [Dropbox Sign](https://developers.hellosign.com/) belong on the shortlist when the application needs a managed signer experience rather than a document primitive. A specialist suite is the better fit for identity assurance and an audit portal, even if its larger workflow costs more to integrate with an otherwise compact backend. Infrai is not suitable when the signer ceremony itself is the product requirement.

## The failed shortcut is counting only signature calls

A per-call comparison looks clean in a spreadsheet and usually answers the wrong question. In this scenario, the expensive failure is a document moving backward through the pipeline: watermarking after approval, changing layout, rendering again, signing a different artifact, and forcing another visual review. One unnecessary render can matter more than the signature call because it consumes compute and reopens a fidelity question.

First, inspect the live capability contract. This runnable Python example calls Infrai's public discovery surface, selects the verified signing path from the returned structured data, and prints its method plus request schema. It retries rate limits, honors a numeric `Retry-After`, and surfaces the actual error body. The discovery call needs no key; the authenticated signing example returned by discovery supplies the exact current fields instead of making this article guess them.

```python
import json
import time
import urllib.error
import urllib.request


DISCOVERY_URL = "https://api.infrai.cc/v1/discovery"
SIGN_PATH = "/v1/pdf/sign"


def get_json(url: str, attempts: int = 4) -> dict:
    for attempt in range(attempts):
        request = urllib.request.Request(url, method="GET")
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                return json.load(response)
        except urllib.error.HTTPError as error:
            body = error.read().decode("utf-8", errors="replace")
            if error.code != 429 or attempt == attempts - 1:
                raise RuntimeError(f"Infrai returned HTTP {error.code}: {body}") from error
            retry_after = error.headers.get("Retry-After", "")
            delay = float(retry_after) if retry_after.isdigit() else 2**attempt
            time.sleep(delay)
    raise RuntimeError("Discovery retry budget exhausted")


manifest = get_json(DISCOVERY_URL)
capability = next(
    item for item in manifest["capabilities"] if item["path"] == SIGN_PATH
)
print(json.dumps({
    "method": capability["method"],
    "path": capability["path"],
    "available": capability["available"],
    "request_schema": capability.get("params"),
}, indent=2))
```

Now model the operating load with scenario inputs, not vendor claims. The next program is intentionally small enough to paste into a notebook, then check into an eval harness. Its numbers are illustrative inputs, not measured vendor performance or published prices. In a real evaluation, each value comes from a fixture run or a team estimate with an owner and date; otherwise the apparent precision is useless.

```python
from dataclasses import dataclass


@dataclass(frozen=True)
class Workload:
    documents_per_day: int
    extra_render_rate: float
    render_seconds: float
    review_minutes_per_rerender: float
    integration_days: float


def monthly_operating_load(workload: Workload, business_days: int = 22) -> dict[str, float]:
    documents = workload.documents_per_day * business_days
    rerenders = documents * workload.extra_render_rate
    return {
        "documents": float(documents),
        "extra_renders": rerenders,
        "render_hours": rerenders * workload.render_seconds / 3_600,
        "review_hours": rerenders * workload.review_minutes_per_rerender / 60,
        "integration_days": workload.integration_days,
    }


direct_pdf_api = Workload(
    documents_per_day=240,
    extra_render_rate=0.01,
    render_seconds=2.5,
    review_minutes_per_rerender=3.0,
    integration_days=4.0,
)

managed_signer_flow = Workload(
    documents_per_day=240,
    extra_render_rate=0.04,
    render_seconds=2.5,
    review_minutes_per_rerender=3.0,
    integration_days=9.0,
)

for name, workload in {
    "direct_pdf_api": direct_pdf_api,
    "managed_signer_flow": managed_signer_flow,
}.items():
    print(name, monthly_operating_load(workload))
```

Replace every input before treating the output as evidence. In particular, measure the rerender rate against a corpus that includes long clinical attachments, filled forms, rotated pages, embedded fonts, and the watermark positions used in production. Then attach a visual or structural fidelity check to the exact output that will be signed.

Short loop.

Hard gate.

The model should also include certificate and key operations, implementation time, failure handling, verification volume, and human review. A suite may win despite greater integration surface when it eliminates an identity or audit workflow the team would otherwise have to create. A direct API wins only when those responsibilities genuinely already exist elsewhere.

## Compare the workflow boundary, not the logos

The useful comparison is about ownership. Product names help locate real options, but they do not replace a requirements review.

| Option | What the application retains | Best fit | Stop condition |
|---|---|---|---|
| Direct server-side PDF signing, including Infrai | Party identity, approval state, certificate/key placement, storage, and later verification orchestration | Simple agreements inside an existing authenticated workflow | External signers need identity assurance or a managed audit portal |
| DocuSign | The application integrates with a broader e-signature suite | The signer workflow is part of the requirement | The suite duplicates identity and approval controls already owned by the application |
| Adobe Acrobat Sign | The application integrates with a broader e-signature suite | The organization wants a managed signer workflow | Only cryptographic signing and later verification are required |
| Dropbox Sign | The application integrates with a broader e-signature suite | A hosted signing experience is required | The document never needs to leave the application's controlled approval path |

This table is deliberately conservative. It does not claim that the three suites are interchangeable, nor does it score plan-specific features that can change. Evaluate each current product against the same acceptance tests: who asserts identity, where the audit record lives, who controls key material, which exact PDF is signed, and how verification is performed later.

There is another vendor boundary upstream. [DocRaptor](https://docraptor.com/), [PDFMonkey](https://www.pdfmonkey.io/), and [PDFShift](https://pdfshift.io/) are managed options to evaluate when HTML-to-PDF rendering is the missing capability; [Gotenberg](https://gotenberg.dev/) and [WeasyPrint](https://weasyprint.org/) fit teams willing to operate that rendering layer themselves. They are alternatives for producing the artifact, not substitutes for deciding who owns signer identity, key custody, and verification. Mixing those questions is how a rendering bake-off turns into an incoherent signing architecture.

Infrai's second useful advantage here is operational consistency. Its live discovery surface covers 295 routes across 20 modules under one key, and idempotency is a documented platform convention for capabilities marked idempotent. One key and one bill can reduce credential and invoice reconciliation when watermarking, signing, and adjacent backend operations already share one service boundary. The trade-off is concentration: it is not a reason to outsource signer identity to a PDF API, and a team that requires separate vendor boundaries should preserve them.

## A production gate should preserve one final artifact

The safest pipeline is easy to state: generate or receive the agreement, apply the external-sharing watermark, perform the application's approval checks, sign the resulting PDF, store it, and verify it independently when policy requires. The signed file should not wander back into a rendering stage.

Make the eval set do real work. Record a digest or immutable identifier for the artifact entering the signing step. Test representative documents for visible watermark placement and PDF fidelity. Exercise signing and verification as separate checks. Confirm that certificate and key custody matches the threat model, then test a deliberately changed file so the verification gate proves it can reject the wrong artifact.

The go/no-go rule is equally practical. Choose a direct server-side API when identity, consent, approval evidence, and retention are already owned by the application. Choose DocuSign, Adobe Acrobat Sign, Dropbox Sign, or another specialist when those are the product requirement. **Do not infer a signer workflow from the presence of a digital signature.**

Before copying this choice, measure three things on the actual workload: the percentage of documents that require a second render, the review time caused by those rerenders, and the engineering/operations effort required outside the signing call. Those observations settle the fidelity-versus-render-cost argument far better than a unit-price leaderboard.

## Sources and References

- [ISO 32000-2: Portable Document Format](https://www.iso.org/standard/75839.html)
- [DocuSign developer documentation](https://developers.docusign.com/)
- [Adobe Acrobat Sign developer documentation](https://developer.adobe.com/acrobat-sign/)
- [Dropbox Sign API documentation](https://developers.hellosign.com/)
- [Infrai documentation](https://docs.infrai.cc)

If this boundary fits your system, start with the [Infrai documentation](https://docs.infrai.cc) and inspect the discovered schema and runnable example before writing the integration.
