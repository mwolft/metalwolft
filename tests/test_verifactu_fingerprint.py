import unittest
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
import sys


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from api.verifactu_fingerprint import (  # noqa: E402
    OfficialRegistrationData,
    VERIFACTU_FINGERPRINT_ALGORITHM,
    VERIFACTU_OFFICIAL_PAYLOAD_SCHEMA_VERSION,
    VERIFACTU_ORDINARY_INVOICE_TYPE_CODE,
    VeriFactuFingerprintError,
    VeriFactuSystemIdentity,
    build_official_registration_payload,
    build_registration_fingerprint_input,
    calculate_verifactu_fingerprint,
)


class VeriFactuFingerprintTest(unittest.TestCase):
    def official_example_data(self, *, previous_fingerprint=None):
        return OfficialRegistrationData(
            issuer_tax_id="89890001K",
            invoice_number="12345678/G33",
            issue_date=date(2024, 1, 1),
            invoice_type_code=VERIFACTU_ORDINARY_INVOICE_TYPE_CODE,
            tax_amount=Decimal("12.35"),
            total_amount=Decimal("123.45"),
            previous_fingerprint=previous_fingerprint,
            generation_timestamp=datetime(
                2024,
                1,
                1,
                19,
                20,
                30,
                tzinfo=timezone(timedelta(hours=1)),
            ),
        )

    def system_identity(self):
        return VeriFactuSystemIdentity(
            system_id="MW",
            system_name="MetalWolft",
            system_version="2026.7",
            installation_id="DEV-001",
            producer_name="MetalWolft S.L.",
            producer_tax_id="B00000000",
        )

    def test_official_registration_fingerprint_vector(self):
        fingerprint_input = build_registration_fingerprint_input(self.official_example_data())

        self.assertEqual(
            fingerprint_input.value,
            "IDEmisorFactura=89890001K&"
            "NumSerieFactura=12345678/G33&"
            "FechaExpedicionFactura=01-01-2024&"
            "TipoFactura=F1&"
            "CuotaTotal=12.35&"
            "ImporteTotal=123.45&"
            "Huella=&"
            "FechaHoraHusoGenRegistro=2024-01-01T19:20:30+01:00",
        )
        self.assertEqual(
            calculate_verifactu_fingerprint(fingerprint_input),
            "3C464DAF61ACB827C65FDA19F352A4E3BDC2C640E9E9FC4CC058073F38F12F60",
        )

    def test_previous_fingerprint_is_inserted_in_the_official_position(self):
        previous = "A" * 64
        fingerprint_input = build_registration_fingerprint_input(
            self.official_example_data(previous_fingerprint=previous)
        )

        self.assertIn(f"&Huella={previous}&FechaHoraHusoGenRegistro=", fingerprint_input.value)

    def test_official_payload_keeps_xml_out_of_scope(self):
        fingerprint_input = build_registration_fingerprint_input(self.official_example_data())
        fingerprint = calculate_verifactu_fingerprint(fingerprint_input)

        payload = build_official_registration_payload(
            self.official_example_data(),
            system=self.system_identity(),
            fingerprint_input=fingerprint_input,
            fingerprint=fingerprint,
            is_first_record=True,
        )

        self.assertEqual(payload["schema_version"], VERIFACTU_OFFICIAL_PAYLOAD_SCHEMA_VERSION)
        self.assertEqual(payload["RegistroAlta"]["IDFactura"]["IDEmisorFactura"], "89890001K")
        self.assertEqual(payload["RegistroAlta"]["TipoFactura"], "F1")
        self.assertEqual(payload["RegistroAlta"]["Encadenamiento"], {"PrimerRegistro": "S"})
        self.assertEqual(payload["RegistroAlta"]["TipoHuella"], VERIFACTU_FINGERPRINT_ALGORITHM)
        self.assertEqual(payload["RegistroAlta"]["Huella"], fingerprint)
        self.assertNotIn("xml", str(payload).lower())

    def test_rejects_timezone_missing_invalid_invoice_number_and_missing_required_data(self):
        with self.assertRaises(VeriFactuFingerprintError):
            build_registration_fingerprint_input(
                OfficialRegistrationData(
                    issuer_tax_id="89890001K",
                    invoice_number="12345678=G33",
                    issue_date=date(2024, 1, 1),
                    invoice_type_code="F1",
                    tax_amount=Decimal("12.35"),
                    total_amount=Decimal("123.45"),
                    previous_fingerprint=None,
                    generation_timestamp=datetime(2024, 1, 1, 19, 20, 30),
                )
            )


if __name__ == "__main__":
    unittest.main()
