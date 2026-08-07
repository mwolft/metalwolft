# Repository Instructions

Before modifying any code or documentation related to products, sales, orders, payments, manufacturing, delivery notes, invoices, invoice PDFs, accounting, VeriFactu or document email flows, read:

- `docs/architecture/BUSINESS_DOMAIN_ARCHITECTURE.md`
- `docs/architecture/INVOICE_DOMAIN_SPECIFICATION.md` when the task touches invoices, fiscal snapshots, invoice numbering, invoice PDFs, accounting, VeriFactu or invoice email

When reading the business domain document, check both the Architectural Decision Log and the pending decisions section before implementing behavior.

These documents are normative. If the implementation contradicts them, do not treat the current code as automatically correct. Document the contradiction and resolve the architecture decision explicitly before changing business behavior.
