from io import BytesIO
from types import SimpleNamespace as Obj

from openpyxl import load_workbook

from api.commercial_orders_export_service import build_workbook, safe_cell


def detail(id, product_id, quantity, unit_price, name=None, **kwargs):
    return Obj(id=id, product_id=product_id, quantity=quantity, precio_total=unit_price,
               product=Obj(nombre=name) if name else None, line_type="physical",
               alto=kwargs.get("alto"), ancho=kwargs.get("ancho"),
               color=kwargs.get("color"), anclaje=kwargs.get("anclaje"))


def order(id, details, total, discount=0, shipping=0, context=None, checkout=None):
    return Obj(id=id, order_date=None, order_status="pendiente", order_details=details,
               total_amount=total, discount_value=discount, shipping_cost=shipping,
               confirmed_order_context=context, checkout_session=checkout)


def workbook(orders):
    return load_workbook(BytesIO(build_workbook(orders).getvalue()), data_only=False)


def test_three_sheets_and_reconciliation_with_multiple_lines():
    context = Obj(source="web_checkout", payment_status="confirmed",
                  quote_snapshot={"lines": [{"product_id": 7, "product_name": "Nombre vendido"}]})
    wb = workbook([order(1, [detail(1, 7, 2, 12.50, "Nombre nuevo", alto=100, ancho=50,
                                    color="rojo", anclaje="obra"), detail(2, 8, 1, 20)],
                         45, discount=5, shipping=5, context=context)])
    assert wb.sheetnames == ["Pedidos", "Lineas", "Control"]
    row = list(wb["Pedidos"].values)[1]
    assert row[5:13] == (2, 45, 5, 5, 45, 45, 0, "Conciliado")
    line = list(wb["Lineas"].values)[1]
    assert line[3:5] == ("Nombre vendido", "Nombre nuevo")
    assert line[9:11] == (0.5, 1)
    assert "cliente" not in " ".join(str(cell) for cell in wb["Pedidos"][1]).lower()


def test_nulls_are_preserved_and_calculation_is_provisional():
    wb = workbook([order(2, [detail(3, 9, 1, 10)], 10, None, None)])
    row = list(wb["Pedidos"].values)[1]
    assert row[7:13] == (None, None, 10, 10, 0, "Provisional (nulos como 0)")
    assert dict(list(wb["Control"].values)[1:])["Con importes provisionales"] == 1
    assert dict(list(wb["Control"].values)[1:])["Sin evidencia suficiente de pago"] == 1


def test_mismatch_and_missing_historical_name_and_formula_safety():
    wb = workbook([order(3, [detail(4, 10, 1, 10, "=HYPERLINK(\"bad\")")], 10.02)])
    assert list(wb["Pedidos"].values)[1][-1] == "Descuadrado"
    line = list(wb["Lineas"].values)[1]
    assert line[3] is None
    assert line[4].startswith("'=HYPERLINK")
    assert wb["Lineas"]["E2"].data_type == "s"
    assert safe_cell(" \t+1").startswith("'")
