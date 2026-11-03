import io
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect
import test_google_ads_csv_import as cost_tests
from api.google_ads_purchase_service import (
    import_purchase_months, parse_purchase_csv, purchase_dashboard_data, save_manual_purchase,
)
from api.models import GoogleAdsPurchaseMonthly, db


HEADER = 'Mes,Campaña,Acción de conversión,Todas las conversiones,Valor de todas las conversiones'
PURCHASE = 'Compra (Evento de Google Analytics purchase)'


def report(*rows, end='31 de octubre de 2026'):
    return ('MetalWolft | Google Ads · Compras y valor mensual 2026\n'
            f'1 de enero de 2026 - {end}\n{HEADER}\n' + '\n'.join(rows) + '\n').encode()


JAN = f'enero de 2026,2 Merchant,{PURCHASE},"3,00","1.691,31"'
OCT = f'octubre de 2026,2 Merchant,{PURCHASE},"2,00","498,59"'
LOCAL = 'octubre de 2026,2 Merchant,Acciones locales: visitas al sitio web,"2,00","2,00"'


class GoogleAdsPurchaseImportTest(unittest.TestCase):
    setUp = cost_tests.GoogleAdsCsvImportTest.setUp
    tearDown = cost_tests.GoogleAdsCsvImportTest.tearDown

    def test_migration_is_additive_with_one_head(self):
        script = ScriptDirectory(str(Path(__file__).resolve().parents[1] / 'src' / 'migrations'))
        self.assertEqual(script.get_heads(), ['c8e4f0a2b6d9'])
        migration = script.get_revision('c8e4f0a2b6d9').module
        self.assertEqual(migration.down_revision, 'b7d3e9f1a2c4')
        engine = create_engine('sqlite:///:memory:')
        with engine.begin() as connection:
            operations = Operations(MigrationContext.configure(connection))
            original_op = migration.op
            try:
                migration.op = operations
                migration.upgrade()
                columns = {column['name'] for column in inspect(connection).get_columns('google_ads_purchase_monthly')}
                self.assertTrue({'year', 'month', 'conversions', 'value_eur', 'manual_conversions',
                                 'manual_value_eur', 'source_start', 'source_end'} <= columns)
                migration.downgrade()
                self.assertFalse(inspect(connection).has_table('google_ads_purchase_monthly'))
            finally:
                migration.op = original_op

    def test_csv_filters_action_and_keeps_missing_months_unknown(self):
        rows = parse_purchase_csv(report(JAN, LOCAL, OCT))
        self.assertEqual(len(rows), 2)
        self.assertEqual(sum((row.conversions for row in rows), Decimal('0')), Decimal('5.00'))
        self.assertEqual(rows[1].source_end, date(2026, 10, 31))
        for payload in (report(JAN, JAN), report(JAN.replace('2 Merchant', 'Otra')),
                        report(JAN.replace('"3,00"', '"-3,00"')),
                        report(OCT, end='15 de septiembre de 2026'),
                        report(JAN).replace(b'Camp', b'Wrong')):
            with self.subTest(payload=payload[:40]), self.assertRaises(ValueError):
                parse_purchase_csv(payload)

    def test_import_is_atomic_idempotent_and_manual_override_survives(self):
        rows = parse_purchase_csv(report(JAN, LOCAL, OCT))
        with self.app.app_context():
            self.assertEqual(import_purchase_months(db.session, rows, 'purchases.csv')['inserted'], 2)
            self.assertEqual(import_purchase_months(db.session, rows, 'purchases.csv')['unchanged'], 2)
            changed = parse_purchase_csv(report(JAN.replace('"3,00"', '"4,00"'), OCT))
            with self.assertRaises(ValueError):
                import_purchase_months(db.session, changed, 'new.csv')
            db.session.rollback()
            self.assertEqual(GoogleAdsPurchaseMonthly.query.filter_by(month=1).one().conversions,
                             Decimal('3.00'))
            save_manual_purchase(db.session, '2026-01', '5,25', '1900,00', editing=True)
            self.assertEqual(import_purchase_months(db.session, changed, 'new.csv',
                                                     replace_existing=True)['updated'], 1)
            row = GoogleAdsPurchaseMonthly.query.filter_by(month=1).one()
            self.assertEqual((row.conversions, row.manual_conversions),
                             (Decimal('4.00'), Decimal('5.25')))
            self.assertEqual(GoogleAdsPurchaseMonthly.query.count(), 2)

    def test_manual_month_and_comparable_ratios(self):
        with self.app.app_context():
            save_manual_purchase(db.session, '2026-01', '2,50', '100,00')
            row = GoogleAdsPurchaseMonthly.query.one()
            self.assertEqual((row.source_start, row.source_end),
                             (date(2026, 1, 1), date(2026, 1, 31)))
            ads = {'labels': ['2026-01'], 'costs': [25.0], 'future': [False],
                   'partial': [False], 'total': Decimal('25.00')}
            data = purchase_dashboard_data(db.session, ads)
            self.assertEqual((data['roas'], data['cost_per_purchase']),
                             (Decimal('4'), Decimal('10')))
            ads['labels'].append('2026-02')
            ads['costs'].append(10.0)
            ads['future'].append(False)
            ads['partial'].append(False)
            self.assertIsNone(purchase_dashboard_data(db.session, ads)['roas'])
            ads['future'][1] = True
            self.assertEqual(purchase_dashboard_data(db.session, ads)['roas'], Decimal('4'))

    def test_partial_period_and_zero_denominators(self):
        with self.app.app_context():
            import_purchase_months(db.session, parse_purchase_csv(report(OCT,
                end='15 de octubre de 2026')), 'partial.csv')
            ads = {'labels': ['2026-10'], 'costs': [10.0], 'future': [False],
                   'partial': [False], 'total': Decimal('10.00')}
            data = purchase_dashboard_data(db.session, ads)
            self.assertTrue(data['incomplete'][0])
            self.assertIsNone(data['roas'])
            self.assertIsNone(data['monthly_roas'][0])
            save_manual_purchase(db.session, '2026-11', '0', '0')
            ads = {'labels': ['2026-11'], 'costs': [0.0], 'future': [False],
                   'partial': [False], 'total': Decimal('0.00')}
            data = purchase_dashboard_data(db.session, ads)
            self.assertIsNone(data['roas'])
            self.assertIsNone(data['cost_per_purchase'])

    def test_admin_requires_auth_csrf_and_renders(self):
        self.assertEqual(self.client.get('/admin/ads-purchases').status_code, 401)
        self.assertEqual(self.client.post('/admin/ads-purchases-import').status_code, 401)
        page = self.client.get('/admin/ads-purchases', headers=self.auth)
        self.assertEqual(page.status_code, 200)
        self.assertEqual(self.client.post('/admin/ads-purchases', headers=self.auth,
                                         data={'month': '2026-01'}).status_code, 400)
        with self.client.session_transaction() as browser_session:
            token = browser_session['google_ads_purchase_csv_csrf'] if (
                'google_ads_purchase_csv_csrf' in browser_session) else None
        if token is None:
            self.client.get('/admin/ads-purchases-import', headers=self.auth)
            with self.client.session_transaction() as browser_session:
                token = browser_session['google_ads_purchase_csv_csrf']
        response = self.client.post('/admin/ads-purchases-import', headers=self.auth,
            data={'csrf_token': token, 'purchase_csv': (io.BytesIO(report(JAN, LOCAL, OCT)), 'p.csv')},
            content_type='multipart/form-data')
        self.assertEqual(response.status_code, 200)
        self.assertIn('2 meses nuevos', response.get_data(as_text=True))
        self.assertIn('2026-10', self.client.get('/admin/ads-purchases',
                                              headers=self.auth).get_data(as_text=True))

    def test_manual_edit_and_dashboard_keep_attribution_separate(self):
        from api.google_ads_csv_service import import_monthly_costs, parse_monthly_cost_csv
        with self.app.app_context():
            costs = (','.join(cost_tests.HEADERS) + '\n'
                     '2026-01,2026-01-01,2026-01-31,31,100.00,70.00,30.00,cost.csv,VERIFICADO\n')
            import_monthly_costs(db.session, parse_monthly_cost_csv(costs.encode()), 'cost.csv')
            import_purchase_months(db.session, parse_purchase_csv(report(JAN)), 'purchase.csv')
        page = self.client.get('/admin/?ads_period=year:2026', headers=self.auth)
        self.assertEqual(page.status_code, 200)
        self.assertIn('Compras atribuidas', page.get_data(as_text=True))
        self.assertIn('Sin datos comparables', page.get_data(as_text=True))
        page = self.client.get('/admin/ads-purchases?edit=2026-01', headers=self.auth)
        self.assertEqual(page.status_code, 200)
        with self.client.session_transaction() as browser_session:
            token = browser_session['google_ads_purchase_manual_csrf']
        response = self.client.post('/admin/ads-purchases', headers=self.auth, data={
            'csrf_token': token, 'action': 'edit', 'month': '2026-01',
            'conversions': '5,25', 'value_eur': '1800,00',
        })
        self.assertEqual(response.status_code, 302)
        with self.app.app_context():
            row = GoogleAdsPurchaseMonthly.query.one()
            self.assertEqual((row.conversions, row.manual_conversions),
                             (Decimal('3.00'), Decimal('5.25')))
        self.assertEqual(self.client.post('/admin/ads-purchases', headers=self.auth, data={
            'csrf_token': token, 'action': 'add', 'month': '2026-01',
            'conversions': '1', 'value_eur': '1',
        }).status_code, 400)


if __name__ == '__main__':
    unittest.main()
