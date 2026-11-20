"""Selective, fail-closed V1 import into the isolated Design V2 demo database."""

from __future__ import annotations

import hashlib
import os
import re
from pathlib import Path


REFERENCE_PATTERN = re.compile(r"DP-[A-F0-9]{10}")
SOURCE_ENV_KEYS = (
    "V1_READONLY_DATABASE_URL",
    "V1_EXPECTED_HOST",
    "V1_EXPECTED_PORT",
    "V1_EXPECTED_DATABASE",
    "V1_EXPECTED_USER",
    "V1_SOURCE_CUSTOMER_EMAIL",
)
REQUIRED_TABLES = (
    "design_requests", "design_request_items", "orders", "order_details",
    "products", "categories", "users",
)
RESULT_FIELDS = (
    "result_storage_key", "result_filename", "result_mime", "result_size", "result_sha256",
)


def normalize_references(references):
    normalized = [str(reference).strip().upper() for reference in references]
    if not normalized or len(normalized) > 10 or len(set(normalized)) != len(normalized):
        raise RuntimeError("Provide one to ten distinct DP references.")
    if any(not REFERENCE_PATTERN.fullmatch(reference) for reference in normalized):
        raise RuntimeError("Invalid DP reference format.")
    return tuple(normalized)


def source_configuration(environ):
    from sqlalchemy.engine import make_url

    if any(not environ.get(key) for key in SOURCE_ENV_KEYS):
        raise RuntimeError("Read-only source URL, independent Neon connection reference, and owner email are required.")
    raw = environ["V1_READONLY_DATABASE_URL"]
    url = make_url("postgresql://" + raw[len("postgres://"):] if raw.startswith("postgres://") else raw)
    expected_port = int(environ["V1_EXPECTED_PORT"])
    if (url.drivername not in {"postgresql", "postgresql+psycopg2"}
            or not url.host or not url.host.endswith(".neon.tech")
            or url.host != environ["V1_EXPECTED_HOST"]
            or (url.port or 5432) != expected_port or expected_port != 5432
            or url.database != environ["V1_EXPECTED_DATABASE"]
            or url.username != environ["V1_EXPECTED_USER"]
            or url.username in {"neondb_owner", "postgres", "gitpod"}
            or not url.password):
        raise RuntimeError("Source connection does not match the independent Neon reference or read-only role.")
    return url, environ["V1_SOURCE_CUSTOMER_EMAIL"].strip().lower()


def _assert_read_only(cursor, url):
    cursor.execute("SELECT current_database(), current_user, current_setting('transaction_read_only')")
    database, user, read_only = cursor.fetchone()
    if database != url.database or user != url.username or read_only != "on":
        raise RuntimeError("Source database, role, or transaction read-only state did not match.")
    cursor.execute("SELECT rolsuper, rolcreatedb, rolcreaterole, rolreplication, rolbypassrls FROM pg_roles WHERE rolname = current_user")
    role = cursor.fetchone()
    if role is None or any(role):
        raise RuntimeError("Source role has elevated privileges.")
    cursor.execute("SELECT has_database_privilege(current_user, current_database(), 'CREATE')")
    if cursor.fetchone()[0]:
        raise RuntimeError("Source role can create databases.")
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_namespace n
            WHERE n.nspname NOT IN ('information_schema', 'pg_catalog')
              AND n.nspname NOT LIKE 'pg_toast%'
              AND n.nspname NOT LIKE 'pg_temp%'
              AND has_schema_privilege(current_user, n.oid, 'CREATE')
        )
    """)
    if cursor.fetchone()[0]:
        raise RuntimeError("Source role can create schema objects.")
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind IN ('r', 'p')
              AND n.nspname NOT IN ('information_schema', 'pg_catalog')
              AND n.nspname NOT LIKE 'pg_toast%'
              AND n.nspname NOT LIKE 'pg_temp%'
              AND (has_table_privilege(current_user, c.oid, 'INSERT')
                OR has_table_privilege(current_user, c.oid, 'UPDATE')
                OR has_table_privilege(current_user, c.oid, 'DELETE')
                OR has_table_privilege(current_user, c.oid, 'TRUNCATE'))
        )
    """)
    if cursor.fetchone()[0]:
        raise RuntimeError("Source role has table write privileges.")
    cursor.execute("""
        SELECT EXISTS (
            SELECT 1 FROM pg_class c JOIN pg_namespace n ON n.oid = c.relnamespace
            WHERE c.relkind = 'S' AND n.nspname NOT LIKE 'pg_%'
              AND (has_sequence_privilege(current_user, c.oid, 'USAGE')
                OR has_sequence_privilege(current_user, c.oid, 'UPDATE'))
        )
    """)
    if cursor.fetchone()[0]:
        raise RuntimeError("Source role can advance or update sequences.")
    for table in REQUIRED_TABLES:
        cursor.execute("SELECT has_table_privilege(current_user, %s, 'SELECT')", (f"public.{table}",))
        if cursor.fetchone()[0] is not True:
            raise RuntimeError("Source role lacks required read access.")


def _dict_rows(cursor):
    names = [column[0] for column in cursor.description]
    return [dict(zip(names, row)) for row in cursor.fetchall()]


def read_source(url, owner_email, references):
    import psycopg2

    connection = psycopg2.connect(
        url.render_as_string(hide_password=False),
        connect_timeout=5,
        options="-c default_transaction_read_only=on -c statement_timeout=5000 -c lock_timeout=1000",
    )
    try:
        connection.set_session(readonly=True, autocommit=False)
        with connection.cursor() as cursor:
            _assert_read_only(cursor, url)
            cursor.execute("""
                SELECT r.reference, r.status, r.requested_at, r.paid_at, r.started_at,
                       r.delivered_at, r.cancelled_at, r.subtotal_gross, r.price_gross,
                       r.discount_amount, r.currency, r.lead_time_hours,
                       r.result_storage_key, r.result_filename, r.result_mime,
                       r.result_size, r.result_sha256,
                       o.order_date, o.total_amount, o.order_status,
                       (SELECT count(*) FROM design_request_items x WHERE x.design_request_id = r.id) AS item_count
                FROM design_requests r
                JOIN orders o ON o.id = r.order_id
                JOIN users u ON u.id = r.user_id
                WHERE r.reference = ANY(%s) AND lower(u.email) = %s
            """, (list(references), owner_email))
            requests = _dict_rows(cursor)
            if {row["reference"] for row in requests} != set(references):
                raise RuntimeError("A selected reference is missing, unpaid, or does not belong to the expected account.")
            cursor.execute("""
                SELECT r.reference, i.product_name, i.width_cm, i.height_cm,
                       d.quantity, d.line_type, d.alto, d.ancho, d.precio_total,
                       p.slug AS product_slug, p.nombre AS current_product_name,
                       p.precio AS current_price, p.precio_rebajado AS current_discounted_price,
                       p.published, p.available_for_sale, p.opening_type,
                       c.slug AS category_slug, c.nombre AS category_name
                FROM design_request_items i
                JOIN design_requests r ON r.id = i.design_request_id
                JOIN order_details d ON d.id = i.order_detail_id AND d.order_id = r.order_id
                JOIN products p ON p.id = i.product_id AND p.id = d.product_id
                JOIN categories c ON c.id = p.categoria_id
                WHERE r.reference = ANY(%s)
                ORDER BY r.reference, i.id
            """, (list(references),))
            items = _dict_rows(cursor)
            if {row["reference"] for row in items} != set(references):
                raise RuntimeError("A selected request has no complete design items.")
            connection.rollback()
            return requests, items
    finally:
        connection.close()


def validate_legacy_result(row, input_path):
    from api.design_result_service import has_complete_result_metadata

    metadata = {field: row[field] for field in RESULT_FIELDS}
    if row["status"] == "delivered":
        if not has_complete_result_metadata(type("Metadata", (), metadata)()):
            raise RuntimeError("Delivered V1 request has incomplete result metadata.")
        if input_path is None or not input_path.is_file():
            raise RuntimeError("A local copy of every delivered V1 result is required.")
        if input_path.stat().st_size != row["result_size"]:
            raise RuntimeError("Local result size does not match the V1 metadata.")
        if input_path.stat().st_size > 15 * 1024 * 1024:
            raise RuntimeError("Local V1 result exceeds the legacy file-size limit.")
        with input_path.open("rb") as handle:
            digest = hashlib.file_digest(handle, "sha256").hexdigest()
        if digest != row["result_sha256"].lower():
            raise RuntimeError("Local result SHA-256 does not match the V1 metadata.")
    elif any(value is not None for value in metadata.values()) or input_path is not None:
        raise RuntimeError("Unexpected result metadata or local file for a non-delivered request.")


def validate_source_rows(requests, items, files):
    allowed_statuses = {"pending", "in_progress", "delivered"}
    grouped = {row["reference"]: [] for row in requests}
    for item in items:
        grouped[item["reference"]].append(item)
    for row in requests:
        reference = row["reference"]
        if (row["status"] not in allowed_statuses or not row["paid_at"]
                or row["currency"] != "EUR" or not grouped[reference]
                or len(grouped[reference]) != row["item_count"]):
            raise RuntimeError("Only paid V1 requests with complete items can be imported.")
        for item in grouped[reference]:
            if (item["line_type"] != "design_service" or not item["product_name"]
                    or not item["product_slug"] or not item["category_slug"]
                    or not item["width_cm"] or not item["height_cm"]
                    or not item["quantity"] or item["quantity"] < 1):
                raise RuntimeError("A V1 design item is incomplete or not a design-service line.")
        validate_legacy_result(row, files.get(reference))
    return grouped


def resolve_input_files(references, mappings, input_dir):
    files = {}
    root = input_dir.resolve()
    for mapping in mappings:
        reference, separator, filename = mapping.partition("=")
        if not separator or reference not in references or reference in files or not filename:
            raise RuntimeError("Each --result must map one selected DP reference to one local filename.")
        candidate = root / filename
        path = candidate.resolve()
        if path.parent != root or not path.is_file() or candidate.is_symlink():
            raise RuntimeError("Result files must be regular files directly inside the private import-inputs directory.")
        files[reference] = path
    return files


def import_into_demo(app, db, access, requests, items, files, storage):
    from api.models import Categories, DesignRequest, DesignRequestItem, OrderDetails, Orders, Products, Users

    grouped = validate_source_rows(requests, items, files)
    staged_keys = []
    imported = 0
    with app.app_context():
        user = Users.query.filter_by(email=access["customer_email"]).one_or_none()
        if user is None:
            raise RuntimeError("Synthetic customer does not exist; run prepare first.")
        pending = []
        for row in requests:
            existing = DesignRequest.query.filter_by(reference=row["reference"]).one_or_none()
            if existing:
                if existing.user_id != user.id or existing.creation_key != f"v1-import-{row['reference']}":
                    raise RuntimeError("A selected reference already exists with different local ownership.")
                continue
            locator = "V1" + hashlib.sha256(row["reference"].encode()).hexdigest()[:8].upper()
            if Orders.query.filter_by(locator=locator).first():
                raise RuntimeError("Local demo order locator collision.")
            pending.append((row, locator))

        try:
            for row, locator in pending:
                if row["status"] == "delivered":
                    key = row["result_storage_key"]
                    storage.put_object(
                        storage_key=key,
                        content=files[row["reference"]].read_bytes(),
                        mime_type=row["result_mime"],
                    )
                    staged_keys.append(key)

                order = Orders(user_id=user.id, locator=locator, order_date=row["order_date"],
                               total_amount=row["total_amount"], order_status=row["order_status"])
                db.session.add(order)
                db.session.flush()
                request = DesignRequest(
                    reference=row["reference"], creation_key=f"v1-import-{row['reference']}",
                    user_id=user.id, order_id=order.id,
                    subtotal_gross=row["subtotal_gross"], price_gross=row["price_gross"],
                    discount_amount=row["discount_amount"], currency=row["currency"],
                    lead_time_hours=row["lead_time_hours"], status=row["status"],
                    requested_at=row["requested_at"], paid_at=row["paid_at"],
                    started_at=row["started_at"], delivered_at=row["delivered_at"],
                    cancelled_at=row["cancelled_at"],
                    **{field: row[field] for field in RESULT_FIELDS if row["status"] == "delivered"},
                )
                db.session.add(request)
                db.session.flush()
                for item in grouped[row["reference"]]:
                    category = Categories.query.filter_by(slug=item["category_slug"]).one_or_none()
                    if category is None:
                        category = Categories(nombre=item["category_name"], slug=item["category_slug"])
                        db.session.add(category)
                        db.session.flush()
                    product = Products.query.filter_by(slug=item["product_slug"]).one_or_none()
                    if product is None:
                        product = Products(
                            slug=item["product_slug"], nombre=item["current_product_name"],
                            descripcion="Producto de demostracion importado de V1.",
                            precio=item["current_price"], precio_rebajado=item["current_discounted_price"],
                            published=item["published"], available_for_sale=item["available_for_sale"],
                            opening_type=item["opening_type"], categoria_id=category.id,
                        )
                        db.session.add(product)
                        db.session.flush()
                    elif product.categoria_id != category.id:
                        raise RuntimeError("A catalog slug conflicts with an existing local category.")
                    detail = OrderDetails(
                        order_id=order.id, product_id=product.id, quantity=item["quantity"],
                        line_type="design_service", alto=item["alto"], ancho=item["ancho"],
                        precio_total=item["precio_total"], screw_option="not_applicable",
                        screw_supplement=0,
                    )
                    db.session.add(detail)
                    db.session.flush()
                    db.session.add(DesignRequestItem(
                        design_request_id=request.id, product_id=product.id,
                        product_name=item["product_name"], width_cm=item["width_cm"],
                        height_cm=item["height_cm"], order_detail_id=detail.id,
                    ))
                imported += 1
            db.session.commit()
        except Exception:
            db.session.rollback()
            for key in staged_keys:
                storage.delete_object(storage_key=key)
            raise
    return imported
