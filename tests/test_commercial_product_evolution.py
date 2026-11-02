import unittest
from datetime import datetime, timezone
from sqlalchemy import event

from test_commercial_model_ranking import CommercialModelRankingTest
from api.commercial_analytics_service import product_evolution, ranked_physical_models, resolve_ranking_period
from api.models import OrderDetails, Orders, db


class CommercialProductEvolutionTest(unittest.TestCase):
    setUp = CommercialModelRankingTest.setUp
    tearDown = CommercialModelRankingTest.tearDown

    def test_monthly_aggregation_and_ranking_amount(self):
        with self.app.app_context():
            statements = []

            def record(connection, cursor, statement, parameters, context, executemany):
                statements.append(statement)

            event.listen(db.engine, 'before_cursor_execute', record)
            try:
                data = product_evolution(db.session, self.year, now=datetime(self.year, 7, 1, tzinfo=timezone.utc))
            finally:
                event.remove(db.engine, 'before_cursor_execute', record)
            self.assertEqual(len(statements), 2)
            self.assertEqual(data['selected'], [self.first_id, self.second_id])
            first = data['series'][self.first_id]
            second = data['series'][self.second_id]
            self.assertEqual(first['units'][1:3], [5, 1])
            self.assertEqual(first['orders'][1:3], [1, 1])
            self.assertEqual(first['amount'][1:3], [50.0, 10.0])
            self.assertEqual(second['units'][1], 1)
            self.assertEqual(second['amount'][1], 100.0)
            self.assertEqual(first['units'][3], 0)
            self.assertIsNone(first['units'][7])
            ranking = ranked_physical_models(db.session, resolve_ranking_period('year', [self.year],
                now=datetime(self.year, 7, 1, tzinfo=timezone.utc)))
            self.assertEqual(sum(value or 0 for value in first['amount']),
                             float(ranking['rows'][0]['amount']))
            self.assertEqual(product_evolution(db.session, self.year - 2, now=datetime(
                self.year, 7, 1, tzinfo=timezone.utc))['options'], [])

    def test_unit_price_rounding_and_requested_product(self):
        with self.app.app_context():
            order = Orders(locator='EVOLVE004', order_date=datetime(self.year, 5, 1, 12), total_amount=0)
            db.session.add(order)
            db.session.flush()
            db.session.add(OrderDetails(order_id=order.id, product_id=self.first_id, quantity=2,
                                        precio_total=10.005, line_type='physical'))
            db.session.commit()
            data = product_evolution(db.session, self.year, [self.first_id],
                                     now=datetime(self.year, 7, 1, tzinfo=timezone.utc))
            self.assertEqual(data['series'][self.first_id]['amount'][4], 20.02)
            ranking = ranked_physical_models(db.session, resolve_ranking_period(
                'year', [self.year], now=datetime(self.year, 7, 1, tzinfo=timezone.utc)))
            self.assertEqual(sum(value or 0 for value in data['series'][self.first_id]['amount']),
                             float(ranking['rows'][0]['amount']))

    def test_product_selection_auth_and_dashboard(self):
        with self.app.app_context():
            data = product_evolution(db.session, self.year, [self.second_id])
            self.assertEqual(data['selected'], [self.second_id])
            self.assertEqual(list(data['series']), [self.second_id])
            for ids in ([1, 2, 3, 4, 5, 6], [self.first_id, self.first_id], [-1]):
                with self.assertRaises(ValueError):
                    product_evolution(db.session, self.year, ids)
        self.assertEqual(self.client.get('/admin/product-evolution-data?year=' + str(self.year)).status_code, 401)
        response = self.client.get('/admin/product-evolution-data?year=' + str(self.year), headers=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json['selected']), 2)
        self.assertEqual(self.client.get('/admin/product-evolution-data?year=bad', headers=self.auth).status_code, 400)
        self.assertEqual(self.client.get('/admin/product-evolution-data?year=' + str(self.year)
            + '&product_id=1&product_id=1', headers=self.auth).status_code, 400)
        html = self.client.get('/admin/', headers=self.auth).get_data(as_text=True)
        self.assertLess(html.index('Configuraciones vendidas'), html.index('Evolución por producto'))
        self.assertLess(html.index('Evolución por producto'), html.index('Actividad reciente'))
        self.assertIn('admin_product_evolution.js', html)


if __name__ == '__main__':
    unittest.main()
