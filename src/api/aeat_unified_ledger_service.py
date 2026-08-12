"""Compose the independent AEAT sales and received-expense ledgers into one XLSX."""

from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

from api.aeat_received_expense_ledger_service import (
    AeatReceivedExpenseLedgerError,
    prepare_aeat_received_expense_ledger_rows,
)
from api.aeat_received_expense_ledger_xlsx_service import (
    AeatReceivedExpenseLedgerWriteError,
    add_aeat_received_expense_ledger_worksheet,
    select_aeat_received_expense_ledger_rows,
)
from api.aeat_sales_ledger_service import (
    AeatSalesLedgerError,
    add_aeat_sales_ledger_worksheet,
    prepare_aeat_sales_ledger_rows,
    select_aeat_sales_ledger_rows,
)


class AeatUnifiedLedgerError(Exception):
    """Base error for unified AEAT workbook generation."""


class AeatUnifiedLedgerValidationError(AeatUnifiedLedgerError):
    """Raised when an operation cannot be represented in the requested workbook."""


class AeatUnifiedLedgerWriteError(AeatUnifiedLedgerError):
    """Raised when the unified workbook cannot be written safely."""


@dataclass(frozen=True)
class AeatUnifiedLedgerExportResult:
    output_path: str
    filename: str
    sales_row_count: int
    received_invoice_count: int
    received_row_count: int
    generated_at: datetime
    file_size: int


def generate_aeat_unified_ledger_workbook(sales_entries, supplier_invoices, *, year, period):
    """Build both AEAT sheets from their independent validated fiscal projections."""
    try:
        sales_rows = select_aeat_sales_ledger_rows(
            prepare_aeat_sales_ledger_rows(sales_entries, allow_empty=True),
            year=year,
            period=period,
        )
        received_rows = select_aeat_received_expense_ledger_rows(
            prepare_aeat_received_expense_ledger_rows(
                supplier_invoices,
                allow_empty=True,
            ),
            year=year,
            period=period,
        )
    except (AeatSalesLedgerError, AeatReceivedExpenseLedgerError, AeatReceivedExpenseLedgerWriteError) as exc:
        raise AeatUnifiedLedgerValidationError(str(exc)) from exc

    if not sales_rows and not received_rows:
        raise AeatUnifiedLedgerValidationError(
            "No hay operaciones para el ejercicio y periodo AEAT seleccionados."
        )

    from openpyxl import Workbook

    workbook = Workbook()
    workbook.remove(workbook.active)
    add_aeat_sales_ledger_worksheet(workbook, sales_rows)
    add_aeat_received_expense_ledger_worksheet(workbook, received_rows)
    return workbook, sales_rows, received_rows


def export_aeat_unified_ledger(
    sales_entries,
    supplier_invoices,
    *,
    year,
    period,
    output_path,
    overwrite=False,
):
    """Write a two-sheet AEAT workbook without changing either fiscal domain."""
    path = _validated_output_path(output_path)
    if path.exists() and not overwrite:
        raise AeatUnifiedLedgerWriteError("El archivo AEAT conjunto ya existe.")

    workbook, sales_rows, received_rows = generate_aeat_unified_ledger_workbook(
        sales_entries,
        supplier_invoices,
        year=year,
        period=period,
    )
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(path)
    except OSError as exc:
        raise AeatUnifiedLedgerWriteError("No se pudo escribir el libro AEAT conjunto.") from exc

    return AeatUnifiedLedgerExportResult(
        output_path=str(path),
        filename=path.name,
        sales_row_count=len(sales_rows),
        received_invoice_count=len({row["reception_number"] for row in received_rows}),
        received_row_count=len(received_rows),
        generated_at=datetime.now(timezone.utc),
        file_size=path.stat().st_size,
    )


def _validated_output_path(output_path):
    if not output_path:
        raise AeatUnifiedLedgerWriteError("La ruta de salida es obligatoria.")
    path = Path(output_path)
    if any(part == ".." for part in path.parts):
        raise AeatUnifiedLedgerWriteError("La ruta de salida no es valida.")
    if path.suffix.lower() != ".xlsx" or not path.stem:
        raise AeatUnifiedLedgerWriteError("La exportacion AEAT debe usar un archivo .xlsx valido.")
    return path
