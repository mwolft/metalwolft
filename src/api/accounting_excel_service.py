from dataclasses import dataclass
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
from pathlib import Path


SALES_SHEET_NAME = "Ingresos"
SALE_ENTRY_TYPE = "sale"
SUPPORTED_CURRENCY = "EUR"
HEADERS = [
    "Fecha factura",
    "Número factura",
    "Cliente",
    "NIF/CIF",
    "Base imponible",
    "IVA",
    "Total",
    "Moneda",
    "Método de pago",
    "Pedido",
    "Estado contable",
]
DATE_FORMAT = "DD/MM/YYYY"
MONEY_FORMAT = '#,##0.00'


class AccountingExcelExportError(Exception):
    """Base error for accounting Excel exports."""


class AccountingExcelValidationError(AccountingExcelExportError):
    """Raised when export input is not valid."""


class AccountingExcelWriteError(AccountingExcelExportError):
    """Raised when the export file cannot be written safely."""


@dataclass(frozen=True)
class AccountingExcelExportResult:
    output_path: str
    filename: str
    row_count: int
    generated_at: datetime
    file_size: int


def export_sales_accounting_entries(entries, *, output_path, overwrite=False):
    """Export sale AccountingEntry records to a deterministic XLSX workbook."""
    generated_at = datetime.now(timezone.utc)
    path = _validated_output_path(output_path)
    prepared_entries = _prepared_entries(entries)

    if path.exists() and not overwrite:
        raise AccountingExcelWriteError("El archivo de exportacion contable ya existe.")

    workbook = _build_workbook(prepared_entries)

    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(path)
    except OSError as exc:
        raise AccountingExcelWriteError("No se pudo escribir el Excel de ingresos.") from exc

    return AccountingExcelExportResult(
        output_path=str(path),
        filename=path.name,
        row_count=len(prepared_entries),
        generated_at=generated_at,
        file_size=path.stat().st_size,
    )


def _validated_output_path(output_path):
    if not output_path:
        raise AccountingExcelValidationError("La ruta de salida es obligatoria.")

    path = Path(output_path)
    if any(part == ".." for part in path.parts):
        raise AccountingExcelValidationError("La ruta de salida no es valida.")
    if path.suffix.lower() != ".xlsx":
        raise AccountingExcelValidationError("La exportacion debe tener extension .xlsx.")
    if not path.name or path.name == ".xlsx":
        raise AccountingExcelValidationError("El nombre del archivo de salida no es valido.")
    return path


def _prepared_entries(entries):
    if entries is None:
        raise AccountingExcelValidationError("Debe indicarse al menos un registro contable.")

    prepared = [_prepared_entry(entry) for entry in list(entries)]
    if not prepared:
        raise AccountingExcelValidationError("Debe indicarse al menos un registro contable.")

    return sorted(
        prepared,
        key=lambda entry: (
            entry["invoice_date"],
            entry["invoice_number"],
            entry["id"],
        ),
    )


def _prepared_entry(entry):
    entry_type = _required_text(getattr(entry, "entry_type", None), "entry_type")
    if entry_type != SALE_ENTRY_TYPE:
        raise AccountingExcelValidationError("Solo se pueden exportar registros contables de venta.")

    currency = _required_text(getattr(entry, "currency", None), "currency").upper()
    if currency != SUPPORTED_CURRENCY:
        raise AccountingExcelValidationError("Moneda no soportada para la exportacion contable.")

    return {
        "id": _entry_id(entry),
        "invoice_date": _invoice_date(getattr(entry, "invoice_date", None)),
        "invoice_number": _required_text(getattr(entry, "invoice_number", None), "invoice_number"),
        "customer_name": _required_text(getattr(entry, "customer_name", None), "customer_name"),
        "customer_tax_id": _optional_text(getattr(entry, "customer_tax_id", None)),
        "taxable_base": _money(getattr(entry, "taxable_base", None), "taxable_base"),
        "vat_amount": _money(getattr(entry, "vat_amount", None), "vat_amount"),
        "total_amount": _money(getattr(entry, "total_amount", None), "total_amount"),
        "currency": currency,
        "payment_provider": _optional_text(getattr(entry, "payment_provider", None)),
        "order_id": getattr(entry, "order_id", None),
        "status": _required_text(getattr(entry, "status", None), "status"),
    }


def _build_workbook(entries):
    from openpyxl import Workbook
    from openpyxl.styles import Font

    workbook = Workbook()
    worksheet = workbook.active
    worksheet.title = SALES_SHEET_NAME
    worksheet.append(HEADERS)

    for cell in worksheet[1]:
        cell.font = Font(bold=True)

    for entry in entries:
        worksheet.append([
            entry["invoice_date"],
            entry["invoice_number"],
            entry["customer_name"],
            entry["customer_tax_id"],
            entry["taxable_base"],
            entry["vat_amount"],
            entry["total_amount"],
            entry["currency"],
            entry["payment_provider"],
            entry["order_id"],
            entry["status"],
        ])

    worksheet.freeze_panes = "A2"
    worksheet.auto_filter.ref = worksheet.dimensions
    _apply_formats(worksheet)
    _apply_column_widths(worksheet)
    return workbook


def _apply_formats(worksheet):
    for row in worksheet.iter_rows(min_row=2, max_row=worksheet.max_row):
        row[0].number_format = DATE_FORMAT
        for cell in row[4:7]:
            cell.number_format = MONEY_FORMAT


def _apply_column_widths(worksheet):
    widths = {
        "A": 14,
        "B": 22,
        "C": 28,
        "D": 16,
        "E": 16,
        "F": 12,
        "G": 14,
        "H": 10,
        "I": 18,
        "J": 12,
        "K": 18,
    }
    for column, width in widths.items():
        worksheet.column_dimensions[column].width = width


def _entry_id(entry):
    entry_id = getattr(entry, "id", None)
    return int(entry_id or 0)


def _invoice_date(value):
    if isinstance(value, datetime):
        return value.date()
    if isinstance(value, date):
        return value
    if isinstance(value, str) and value:
        try:
            return datetime.fromisoformat(value).date()
        except ValueError as exc:
            raise AccountingExcelValidationError("Fecha de factura invalida.") from exc
    raise AccountingExcelValidationError("Fecha de factura obligatoria.")


def _money(value, field):
    try:
        amount = Decimal(str(value))
    except (InvalidOperation, ValueError) as exc:
        raise AccountingExcelValidationError(f"Importe no valido en {field}.") from exc
    if not amount.is_finite():
        raise AccountingExcelValidationError(f"Importe no valido en {field}.")
    return amount.quantize(Decimal("0.01"))


def _required_text(value, field):
    text = _optional_text(value)
    if not text:
        raise AccountingExcelValidationError(f"Campo obligatorio ausente: {field}.")
    return text


def _optional_text(value):
    if value is None:
        return None
    text = str(value).strip()
    return text or None
