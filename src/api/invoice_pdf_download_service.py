from dataclasses import dataclass
import os
import re


DOWNLOAD_PREFIX = "/api/download-invoice/"


class InvoicePdfDownloadError(Exception):
    """Base error for read-only invoice PDF downloads."""


class InvoicePdfDownloadUnavailable(InvoicePdfDownloadError):
    """The invoice does not reference an existing generated PDF."""


class InvoicePdfDownloadInvalidPath(InvoicePdfDownloadError):
    """The stored invoice PDF path is unsafe or outside the allowed shape."""


class InvoicePdfDownloadFileMissing(InvoicePdfDownloadError):
    """The stored invoice PDF path is valid but the physical file is missing."""


@dataclass(frozen=True)
class ResolvedInvoicePdfDownload:
    file_path: str
    filename: str
    download_name: str


def resolve_invoice_pdf_download(invoice, invoice_folder):
    raw_pdf_path = getattr(invoice, "pdf_path", None)
    if not raw_pdf_path:
        raise InvoicePdfDownloadUnavailable("Invoice PDF is not available.")

    filename = _extract_pdf_filename(str(raw_pdf_path))
    allowed_dir = _safe_allowed_dir(invoice_folder)
    file_path = os.path.realpath(os.path.join(allowed_dir, filename))

    try:
        common_path = os.path.commonpath([allowed_dir, file_path])
    except ValueError as exc:
        raise InvoicePdfDownloadInvalidPath("Invoice PDF path is outside the allowed directory.") from exc

    if common_path != allowed_dir:
        raise InvoicePdfDownloadInvalidPath("Invoice PDF path is outside the allowed directory.")

    if not os.path.isfile(file_path):
        raise InvoicePdfDownloadFileMissing("Invoice PDF file is missing.")

    return ResolvedInvoicePdfDownload(
        file_path=file_path,
        filename=filename,
        download_name=_download_name_for_invoice(invoice, filename),
    )


def _safe_allowed_dir(invoice_folder):
    if not invoice_folder:
        raise InvoicePdfDownloadInvalidPath("Invoice PDF folder is not configured.")
    return os.path.realpath(str(invoice_folder))


def _extract_pdf_filename(pdf_path):
    normalized_path = pdf_path.strip().replace("\\", "/")
    if normalized_path.startswith(DOWNLOAD_PREFIX):
        filename = normalized_path[len(DOWNLOAD_PREFIX):]
    elif "/" not in normalized_path:
        filename = normalized_path
    else:
        raise InvoicePdfDownloadInvalidPath("Invoice PDF path has an unsupported format.")

    if (
        not filename
        or filename in {".", ".."}
        or "?" in filename
        or "#" in filename
        or filename != os.path.basename(filename)
        or not filename.lower().endswith(".pdf")
    ):
        raise InvoicePdfDownloadInvalidPath("Invoice PDF filename is invalid.")

    return filename


def _download_name_for_invoice(invoice, filename):
    invoice_number = getattr(invoice, "invoice_number", None)
    if not invoice_number:
        return filename

    safe_invoice_number = re.sub(r"[^A-Za-z0-9._-]+", "_", str(invoice_number)).strip("._-")
    if not safe_invoice_number:
        return filename

    return f"factura_{safe_invoice_number}.pdf"
