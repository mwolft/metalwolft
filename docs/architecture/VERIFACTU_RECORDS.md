# VeriFactu Records

This document defines the first persistence boundary for MetalWolft's future
VERI*FACTU integration.

## Scope

This phase creates an auditable, deterministic record of the fiscal content that
will later be serialized and transmitted to AEAT.

It does not implement:

- HTTP transmission to AEAT.
- XML official serialization.
- Certificate signing.
- Official VeriFactu fingerprint calculation.
- QR generation.
- Cancellation records.
- Retry automation.

## Domain Boundary

The current flow is:

```text
Issued Invoice
    -> immutable InvoiceSnapshot v1
    -> persisted VeriFactu registration record
    -> future official serialization
    -> future AEAT submission
    -> future AEAT response
```

`VeriFactuRecord` is not:

- the invoice;
- the invoice PDF;
- the accounting entry;
- the AEAT sales ledger Excel;
- a submission attempt.

Submission attempts continue to belong to `InvoiceFiscalSubmission`.

## Hashes

`Invoices.invoice_snapshot_hash` is an internal integrity hash. It proves that
the stored `invoice_snapshot` has not changed inside MetalWolft.

It is not the official VeriFactu fingerprint.

`VeriFactuRecord.record_payload_hash` is also internal. It proves that the
persisted VeriFactu record payload has not changed.

The official VeriFactu fingerprint remains `NULL` until it can be implemented
exactly according to the official specification with reliable vectors.

## System Identity

The constructor requires explicit system identity:

- `system_id`
- `software_name`
- `software_version`

These values are persisted inside the record payload. They must later come from
approved configuration, not from the browser.

## Idempotency

The registration record is unique by:

```text
(invoice_id, record_type)
```

For v1, only `record_type="alta"` is built.

Calling the constructor again for the same invoice and record type returns the
existing record and does not rebuild a different payload.

## Current Blockers For Real Transmission

P1 for transmission, not for persistence:

- official XML structure;
- official fingerprint algorithm and chaining;
- certificate/signature requirements;
- QR content requirements;
- registration and cancellation final schemas;
- AEAT response mapping.

Until those are closed, the system must not transmit this payload as if it were
the official AEAT message.
