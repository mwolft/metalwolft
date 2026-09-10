import ast
import sys
import unittest
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
SRC_DIR = ROOT_DIR / "src"
ADMIN_PATH = SRC_DIR / "api" / "admin.py"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))


def source(path):
    return path.read_text(encoding="utf-8")


def module_ast(path):
    return ast.parse(source(path))


def class_node(class_name):
    for node in module_ast(ADMIN_PATH).body:
        if isinstance(node, ast.ClassDef) and node.name == class_name:
            return node
    raise AssertionError(f"{class_name} not found")


def class_source(class_name):
    return ast.get_source_segment(source(ADMIN_PATH), class_node(class_name))


def class_assignment_node(class_name, assignment_name):
    for statement in class_node(class_name).body:
        if not isinstance(statement, ast.Assign):
            continue
        for target in statement.targets:
            if isinstance(target, ast.Name) and target.id == assignment_name:
                return statement.value
    raise AssertionError(f"{assignment_name} not found in {class_name}")


def class_assignment_value(class_name, assignment_name):
    return ast.literal_eval(class_assignment_node(class_name, assignment_name))


def class_dict_keys(class_name, assignment_name):
    node = class_assignment_node(class_name, assignment_name)
    if not isinstance(node, ast.Dict):
        raise AssertionError(f"{assignment_name} is not a dict in {class_name}")
    return [
        key.value
        for key in node.keys
        if isinstance(key, ast.Constant) and isinstance(key.value, str)
    ]


def method_source(class_name, method_name):
    text = source(ADMIN_PATH)
    for statement in class_node(class_name).body:
        if isinstance(statement, ast.FunctionDef) and statement.name == method_name:
            return ast.get_source_segment(text, statement)
    raise AssertionError(f"{method_name} not found in {class_name}")


class FlaskAdminOrderViewInvoiceNumberTest(unittest.TestCase):
    def setUp(self):
        self.view_source = class_source("OrderAdminView")

    def test_invoice_number_is_not_part_of_order_admin_forms(self):
        form_columns = class_assignment_value("OrderAdminView", "form_columns")
        form_extra_fields = class_dict_keys("OrderAdminView", "form_extra_fields")

        self.assertNotIn("invoice_number", form_columns)
        self.assertNotIn("invoice_number", form_extra_fields)

    def test_invoice_number_is_not_inline_editable(self):
        editable_columns = class_assignment_value("OrderAdminView", "column_editable_list")

        self.assertNotIn("invoice_number", editable_columns)

    def test_invoice_number_remains_visible_and_searchable_as_read_only_data(self):
        column_list = class_assignment_value("OrderAdminView", "column_list")
        searchable_columns = class_assignment_value("OrderAdminView", "column_searchable_list")
        labels = class_assignment_value("OrderAdminView", "column_labels")

        self.assertIn("invoice_number", column_list)
        self.assertIn("invoice_number", searchable_columns)
        self.assertIn("invoice_number", labels)

    def test_order_admin_blocks_direct_creation_and_keeps_fiscal_sequence_out_of_the_view(self):
        self.assertIn("can_create = False", self.view_source)
        self.assertIn("can_delete = False", self.view_source)
        self.assertNotIn("def create_form", self.view_source)
        self.assertNotIn("Orders.generate_locator()", self.view_source)
        self.assertNotIn("Orders.generate_next_invoice_number()", self.view_source)

    def test_order_admin_view_does_not_create_invoices_or_consume_fiscal_sequence(self):
        self.assertNotIn("Invoices(", self.view_source)
        self.assertNotIn("InvoiceSequence", self.view_source)
        self.assertNotIn("acquire_next_invoice_number", self.view_source)
        self.assertNotIn("generate_next_invoice_number", self.view_source)

    def test_order_admin_exposes_only_operational_fields_for_editing(self):
        form_columns = class_assignment_value("OrderAdminView", "form_columns")
        editable_columns = class_assignment_value("OrderAdminView", "column_editable_list")

        for protected_field in (
            "user_id",
            "total_amount",
            "discount_code",
            "discount_value",
            "order_date",
            "locator",
        ):
            self.assertNotIn(protected_field, form_columns)
        self.assertEqual(editable_columns, [])

    def test_order_details_admin_blocks_direct_mutation_of_confirmed_lines(self):
        detail_source = class_source("OrderDetailsAdminView")

        self.assertIn("can_create = False", detail_source)
        self.assertIn("can_edit = False", detail_source)
        self.assertIn("can_delete = False", detail_source)

    def test_order_admin_view_exposes_details_for_contextual_invoice_action(self):
        self.assertIn("can_view_details = True", self.view_source)
        self.assertIn("'customer_phone_snapshot'", self.view_source)
        self.assertIn("'customer_phone_snapshot': 'Teléfono'", self.view_source)
        self.assertIn("'shipping_address_summary'", self.view_source)
        self.assertIn("'invoice_number': _format_order_invoice_detail", self.view_source)

    def test_order_admin_distinguishes_design_service_without_hiding_physical_fields(self):
        detail_source = class_source("OrderDetailsAdminView")
        self.assertIn("'order_type_label'", self.view_source)
        self.assertIn("'line_type_label'", detail_source)
        self.assertIn('"Diseño previo · {m.product.nombre}"', detail_source)
        self.assertIn('m.line_type == "design_service"', detail_source)
        self.assertIn("'anclaje'", detail_source)
        self.assertIn("'color'", detail_source)
        self.assertIn("'shipping_cost'", detail_source)

    def test_status_email_controls_are_grouped_and_transient(self):
        for field_name in (
            "send_sent_status_email",
            "include_receipt_guide_in_sent_email",
            "include_installation_guide_in_sent_email",
            "include_incident_form_in_sent_email",
            "send_delivered_status_email",
            "include_installation_guide_in_delivered_email",
            "include_maintenance_guide_in_delivered_email",
        ):
            self.assertIn(field_name, self.view_source)

        self.assertIn("Notificaciones del email de estado", self.view_source)
        self.assertIn('extra_css = ["/static/admin/order_sent_email_options.css"]', self.view_source)
        self.assertIn('extra_js = ["/static/admin/order_sent_email_options.js"]', self.view_source)
        on_model_change_source = method_source("OrderAdminView", "on_model_change")
        self.assertIn("is_real_status_transition", on_model_change_source)
        self.assertIn("status_history.has_changes()", on_model_change_source)
        self.assertIn("_admin_order_status_email_options", on_model_change_source)
        self.assertIn("model.__dict__.pop(field_name, None)", on_model_change_source)

    def test_sent_status_notification_assets_are_csp_safe_and_group_the_secondary_controls(self):
        script = (SRC_DIR / "static" / "admin" / "order_sent_email_options.js").read_text(encoding="utf-8")
        stylesheet = (SRC_DIR / "static" / "admin" / "order_sent_email_options.css").read_text(encoding="utf-8")

        self.assertIn("Incluir en este email:", script)
        self.assertIn("Estas opciones se incluyen dentro del email de pedido ", script)
        self.assertIn("entry.field.disabled = !enabled", script)
        self.assertIn("master.addEventListener(\"change\", syncSecondaryFields)", script)
        self.assertIn("container.hidden = container.dataset.orderStatus !== statusField.value", script)
        self.assertIn("include_maintenance_guide_in_delivered_email", script)
        self.assertNotIn("javascript:", script.lower())
        self.assertNotIn("onclick", script.lower())
        self.assertIn("margin: -6px 0 0 26px", stylesheet)
        self.assertIn("mw-order-status-email-options__nested--disabled", stylesheet)

    def test_pending_order_status_keeps_its_code_and_uses_received_label(self):
        self.assertIn("('pendiente', 'Recibido')", self.view_source)
        self.assertNotIn("('recibido',", self.view_source)


if __name__ == "__main__":
    unittest.main()
