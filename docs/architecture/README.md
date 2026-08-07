# MetalWolft Architecture Documents

This directory contains normative architecture documents for MetalWolft.

Before changing products, sales, orders, payments, manufacturing, delivery notes, invoices, invoice PDFs, accounting, VeriFactu or document email flows, read:

1. `BUSINESS_DOMAIN_ARCHITECTURE.md`
2. `INVOICE_DOMAIN_SPECIFICATION.md` when the change touches invoice, fiscal, PDF, accounting, VeriFactu or invoice email behavior
3. `VERIFACTU_RECORDS.md` when the change touches persisted VeriFactu records, future AEAT serialization, official fingerprints, QR or submission payloads

In `BUSINESS_DOMAIN_ARCHITECTURE.md`, review the Architectural Decision Log and the pending decisions section before implementing behavior.

The business domain document is the general authority. Specialized documents govern the internals of their own subdomain. If code and documentation disagree, do not assume the existing code is the intended business rule; document the contradiction and resolve it explicitly.
