import unittest

from sqlalchemy import event

from test_commercial_model_ranking import CommercialModelRankingTest
from api.commercial_analytics_service import (
    commercial_indicators, configuration_distributions, resolve_ranking_period,
)
from api.models import OrderDetails, Orders, db


class CommercialConfigurationDistributionsTest(unittest.TestCase):
    setUp = CommercialModelRankingTest.setUp
    tearDown = CommercialModelRankingTest.tearDown

    def _add_lines(self):
        with self.app.app_context():
            order_id = db.session.query(Orders.id).filter_by(locator="RANK001").scalar()
            samples = [
                (2, "satinado_negro", "Sin obra: con agujeros interiores", 60, 100),
                (3, "forja_negro", "Sin obra: con agujeros frontales", 100, 100),
                (1, "negro", "Sin obra: con pletinas", 150, 200),
                (1, "marrón", "Con obra: con garras metálicas", 200, 150),
                (1, "otro_historico", "Otro histórico", -1, 80),
                (1, " ", "", 0, None),
                (1, "gris", None, 250, 300),
                (1, "blanco", "Sin obra: con pletinas", 100, 200),
                (1, "satinado_gris", "Sin obra: con agujeros frontales", float("inf"), 100),
            ]
            db.session.add_all([
                OrderDetails(order_id=order_id, product_id=self.first_id, quantity=quantity,
                             precio_total=10, line_type="physical", color=color, anclaje=anchor,
                             alto=height, ancho=width)
                for quantity, color, anchor, height, width in samples
            ])
            db.session.commit()

    def test_all_distributions_reconcile_and_preserve_codes(self):
        self._add_lines()
        with self.app.app_context():
            period = resolve_ranking_period("all", [self.year])
            statements = []

            def record(connection, cursor, statement, parameters, context, executemany):
                statements.append(statement)

            event.listen(db.engine, "before_cursor_execute", record)
            try:
                data = configuration_distributions(db.session, period)
            finally:
                event.remove(db.engine, "before_cursor_execute", record)
            self.assertEqual(len(statements), 6)
            self.assertEqual(data["total_units"], 23)
            self.assertEqual(data["total_units"], commercial_indicators(db.session, period)["physical_units"])
            for key in ("colors", "anchorages", "height", "width", "area"):
                self.assertEqual(sum(row["units"] for row in data[key]), 23, key)
            colors = {row["label"]: row["units"] for row in data["colors"]}
            self.assertEqual(colors["Satinado negro (satinado_negro)"], 2)
            self.assertEqual(colors["Forja negro (forja_negro)"], 3)
            self.assertEqual(colors["Negro (negro)"], 1)
            self.assertEqual(colors["otro_historico"], 1)
            self.assertEqual(colors["Sin dato"], 12)
            anchors = {row["label"]: row["units"] for row in data["anchorages"]}
            self.assertEqual(anchors["Sin obra: con agujeros interiores"], 2)
            self.assertEqual(anchors["Sin obra: con agujeros frontales"], 4)
            self.assertEqual({row["label"]: row["units"] for row in data["height"]}["60 a menos de 100 cm"], 2)
            self.assertEqual({row["label"]: row["units"] for row in data["height"]}["200 cm o más"], 2)
            areas = {row["label"]: row["units"] for row in data["area"]}
            self.assertEqual(areas["Menos de 1 m²"], 2)
            self.assertEqual(areas["1 a menos de 2 m²"], 3)
            self.assertEqual(areas["2 a menos de 3 m²"], 1)
            self.assertEqual(areas["3 m² o más"], 3)
            self.assertEqual(areas["Sin dato o anómalo"], 14)

    def test_periods_empty_state_and_admin_controls(self):
        self.assertEqual(self.client.get("/admin/").status_code, 401)
        with self.app.app_context():
            current = configuration_distributions(db.session, resolve_ranking_period("year", [self.year]))
            empty = configuration_distributions(db.session, resolve_ranking_period(
                f"year:{self.year - 2}", [self.year - 2]))
            self.assertEqual(current["total_units"], 11)
            self.assertEqual(empty["total_units"], 0)
            self.assertEqual(sum(row["units"] for row in empty["area"]), 0)
        response = self.client.get("/admin/", headers=self.auth)
        html = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertLess(html.index("Modelos más vendidos"), html.index("Configuraciones vendidas"))
        self.assertLess(html.index("Configuraciones vendidas"), html.index("Actividad reciente"))
        self.assertIn('id="config-period" name="config_period"', html)
        self.assertIn('data-measure="area" hidden', html)
        self.assertIn("admin_configurations.js", html)
        self.assertIn("11 rejas físicas en el periodo", html)
        self.assertIn("No hay rejas físicas registradas en este periodo.",
                      self.client.get("/admin/?config_period=previous_year", headers=self.auth)
                      .get_data(as_text=True))
        self.assertEqual(self.client.get("/admin/?config_period=invalid", headers=self.auth).status_code, 400)


if __name__ == "__main__":
    unittest.main()
