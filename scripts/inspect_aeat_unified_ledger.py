"""Generate the unified AEAT workbook from persisted fiscal records without modifying data."""

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from api.aeat_unified_ledger_service import (  # noqa: E402
    AeatUnifiedLedgerError,
    export_aeat_unified_ledger,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Genera EXPEDIDAS_INGRESOS + RECIBIDAS_GASTOS sin modificar datos."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--period", choices=("1T", "2T", "3T", "4T"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--force", action="store_true", help="Sobrescribe un XLSX existente.")
    return parser.parse_args(argv)


def load_components():
    from app import app
    from api.models import AccountingEntry, SupplierInvoice

    return app, AccountingEntry, SupplierInvoice


def main(argv=None):
    args = parse_args(argv)
    app, accounting_entry_model, supplier_invoice_model = load_components()

    try:
        with app.app_context():
            sales_entries = (
                accounting_entry_model.query.filter_by(
                    entry_type=accounting_entry_model.ENTRY_TYPE_SALE
                )
                .order_by(
                    accounting_entry_model.invoice_date.asc(),
                    accounting_entry_model.invoice_number.asc(),
                    accounting_entry_model.id.asc(),
                )
                .all()
            )
            supplier_invoices = (
                supplier_invoice_model.query.filter_by(
                    status=supplier_invoice_model.STATUS_REGISTERED
                )
                .order_by(supplier_invoice_model.id.asc())
                .all()
            )
            result = export_aeat_unified_ledger(
                sales_entries,
                supplier_invoices,
                year=args.year,
                period=args.period,
                output_path=args.output,
                overwrite=args.force,
            )
    except AeatUnifiedLedgerError as exc:
        print(f"No se pudo generar el libro AEAT conjunto: {exc}", file=sys.stderr)
        return 1
    except Exception as exc:
        print(f"No se pudo generar el libro AEAT conjunto: {exc}", file=sys.stderr)
        return 1

    print(f"Filas expedidas: {result.sales_row_count}")
    print(f"Facturas recibidas: {result.received_invoice_count}")
    print(f"Filas recibidas: {result.received_row_count}")
    print(f"Ruta del archivo: {result.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
