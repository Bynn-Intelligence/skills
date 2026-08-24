---
name: bynn-document-fraud
description: >-
  Detect forged, tampered, or AI-generated documents with Bynn: submit an ID,
  passport, invoice, bank statement, or contract to POST /documents, then read the
  forensic verdict from GET /documents/{id}. Covers the async submit-and-poll
  contract, risk score fields, the status versus analysis_status distinction,
  file limits, and metadata that improves the analysis. Use when asked whether a
  document is genuine, altered, or machine-generated.
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# Document fraud detection

One submission runs the full forensic pipeline: forgery template matching, tampering and
manipulation detection, font and layout consistency, signature validation, deepfake and
AI-generation scoring, MRZ and barcode parsing, EXIF analysis, classification, and an
overall risk score.

This is **asynchronous**. Submitting returns a receipt, not a verdict.

Base: `https://api.bynn.com/v1`. Private key on both calls.

## 1. Submit

Multipart, which is what you want for anything of real size:

```bash
curl -X POST https://api.bynn.com/v1/documents \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>" \
  -F "file=@/path/to/document.pdf" \
  -F "reference_id=order-8123"
```

Or JSON with strict base64, no line breaks and no `data:` prefix:

```bash
curl -X POST https://api.bynn.com/v1/documents \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>" \
  -H "Content-Type: application/json" \
  -d '{ "document_base64_strict": "<...>", "reference_id": "order-8123" }'
```

Send `file` or `document_base64_strict`, not both.

Response:

```json
{ "submission_id": "document_...", "document_id": "...", "status": "received" }
```

`submission_id` is what you poll. Store it.

### Submit the original file, never a derivative

**Do not resize, crop, re-encode, re-compress, or otherwise process the document before
submitting it.** Send the bytes exactly as you received them.

Tampering detection, AI-generation scoring, and deepfake analysis all work on traces the
manipulation left in the file: compression and quantization artifacts, resampling
patterns, sensor noise, font and edge inconsistencies, and EXIF. Those traces live in the
exact bytes. Resizing resamples them away, re-encoding overwrites them with your own
encoder's artifacts, and stripping metadata removes evidence outright.

The failure mode is quiet and dangerous: a processed forgery comes back looking clean.

- Store the original upload and submit that, not a thumbnail or a normalized copy.
- Do not flatten a PDF to an image, and do not re-render it. Send the PDF.
- Do not run the file through an image optimizer, a screenshot, or a messaging app.
- If a file exceeds the size limit, reject or escalate it. Do not shrink it and submit
  anyway. A downscaled submission can return a false clean verdict.

### Limits

| Constraint | Value |
|---|---|
| Max size | 64 MB |
| Types | jpg, jpeg, png, pdf |

A `413` or `415` means the file broke one of these. Neither is retryable as-is.

### reference_id

Your own identifier for the document, used to index the forensic output. Keep personally
identifiable information out of it: use an internal id or order number, never a name,
email, or document number.

### characteristics

Optional metadata that sharpens the analysis and enriches the report. Two groups:

- `characteristics.document`: `document_type_string`, `issuing_country_code` (ISO 3166-1
  alpha-3), `document_side` (`front` or `back`), `source_channel` (`api`, `web`,
  `mobile`), `customer_case_id`, `customer_tenant_id`, `submission_time`.
- `characteristics.device`: `device_ip_address`, `country_code`, `city`, `postal_code`,
  and geolocation of the device that captured the file.

Send what you already have. Issuing country and document side in particular help the
template matching decide what the document should look like.

## 2. Get the verdict

Prefer the webhook. `document.analyzed` fires when the pipeline finishes and
`document.rejected` when it will not produce a verdict. See `bynn-webhooks`.

Poll only as a fallback:

```bash
curl https://api.bynn.com/v1/documents/<submission_id> \
  -H "Authorization: Bearer <YOUR_PRIVATE_KEY>"
```

Back off between attempts. A small image finishes quickly, a multi-page scanned PDF takes
considerably longer. Do not poll in a tight loop and do not hold a request thread open
waiting for the result.

Fields to read:

| Field | Meaning |
|---|---|
| `analysis_risk_status` | The verdict. This is what your decision logic should branch on. |
| `analysis_risk_score` | Numeric risk, for thresholding and triage queues. |
| `ai_generated_score` | Likelihood the document was produced by a generative model. |
| `tampering_results` | Per-detector findings backing the score. Use it to explain a decision to a reviewer. |
| `status` | Lifecycle of the submission itself. |
| `analysis_status` | Lifecycle of the analysis. |

## status versus analysis_status

This trips up most integrations. **A document that failed still reports
`analysis_status: pending`.** Pending does not mean "still working".

Check `status` to tell the two apart:

- `status` is normal and `analysis_status` is pending: analysis is genuinely running. Keep
  waiting.
- `status` is `error`: the submission failed. It will never complete. Surface it, and
  resubmit if the input was recoverable.

An integration that polls only `analysis_status` waits forever on a failed document.

## What a verdict is and is not

The score describes the **file**, not the person. A clean score means the artifact shows
no signs of forgery, tampering, or generation. It says nothing about whether the person
presenting it is its rightful holder. If you need that, run a session with liveness and
face matching. See `bynn-kyc-sessions`.

Treat the score as evidence for a decision, not as the decision. Pick thresholds
deliberately, route the middle band to human review, and log `tampering_results` so a
reviewer can see why.

## Over MCP

`submit_document`, then poll `get_document`. Same contract, same fields, no key handling.
See `bynn-mcp`.
