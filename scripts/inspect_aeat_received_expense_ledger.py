"""Create a standalone RECIBIDAS_GASTOS workbook without changing database data."""

import argparse
import sys
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


from api.aeat_received_expense_ledger_xlsx_service import (  # noqa: E402
    AeatReceivedExpenseLedgerWriteError,
    export_aeat_received_expense_ledger,
)


def parse_args(argv=None):
    parser = argparse.ArgumentParser(
        description="Genera RECIBIDAS_GASTOS desde snapshots registrados sin modificar datos."
    )
    parser.add_argument("--year", type=int, required=True)
    parser.add_argument("--period", choices=("1T", "2T", "3T", "4T"), required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--force", action="store_true", help="Sobrescribe un XLSX existente.")
    return parser.parse_args(argv)


def load_components():
    from app import app
    from api.models import SupplierInvoice

    return app, SupplierInvoice


def main(argv=None):
    args = parse_args(argv)
    app, supplier_invoice_model = load_components()

    try:
        with app.app_context():
            invoices = (
                supplier_invoice_model.query.filter_by(
                    status="registered",
                    snapshot_schema_version=2,
                )
                .order_by(supplier_invoice_model.id.asc())
                .all()
            )
            result = export_aeat_received_expense_ledger(
                invoices,
                year=args.year,
                period=args.period,
                output_path=args.output,
                overwrite=args.force,
            )
    except Exception as exc:
        print(f"No se pudo generar RECIBIDAS_GASTOS: {exc}", file=sys.stderr)
        return 1

    print(f"Facturas incluidas: {result.invoice_count}")
    print(f"Filas generadas: {result.row_count}")
    print(f"Ruta del archivo: {result.output_path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
