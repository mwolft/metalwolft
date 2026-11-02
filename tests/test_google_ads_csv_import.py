import base64
import io
import sys
import unittest
from datetime import date
from decimal import Decimal
from pathlib import Path

from flask import Flask
from alembic.migration import MigrationContext
from alembic.operations import Operations
from alembic.script import ScriptDirectory
from sqlalchemy import create_engine, inspect

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / 'src'))

from api import admin as admin_module
from api.google_ads_csv_service import HEADERS, ads_dashboard_data, import_monthly_costs, parse_monthly_cost_csv
from api.google_ads_manual_service import effective_monthly_costs, save_manual_cost
from api.models import GoogleAdsImportedMonthlyCost, GoogleAdsMonthlySpend, GoogleAdsMonthlySpendChange, Orders, db


def csv_data(*rows):
    return ('\n'.join([','.join(HEADERS), *rows]) + '\n').encode('utf-8')


JUNE = '2025-06,2025-06-06,2025-06-30,25,0.00,0.00,0.00,daily.csv,DERIVADO'
JULY = '2025-07,2025-07-01,2025-07-31,31,198.42,163.01,35.41,daily.csv,DERIVADO'
AUGUST = '2025-08,2025-08-01,2025-08-31,31,172.12,53.86,118.26,daily.csv,DERIVADO'
SEPTEMBER = '2025-09,2025-09-01,2025-09-30,30,11.28,3.20,8.08,daily.csv,DERIVADO'


class GoogleAdsCsvImportTest(unittest.TestCase):
    def setUp(self):
        self.original_credentials = admin_module.ADMIN_USER, admin_module.ADMIN_PW
        admin_module.ADMIN_USER, admin_module.ADMIN_PW = 'ads-admin', 'ads-secret'
        self.app = Flask(__name__, template_folder=str(ROOT / 'src' / 'templates'),
                         static_folder=str(ROOT / 'src' / 'static'))
        self.app.config.update(TESTING=True, SECRET_KEY='test', SQLALCHEMY_DATABASE_URI='sqlite:///:memory:',
                               SQLALCHEMY_TRACK_MODIFICATIONS=False)
        db.init_app(self.app)
        admin_module.setup_admin(self.app)
        with self.app.app_context():
            db.create_all()
            db.session.add(Orders(locator='ADSTEST', order_date=date(2025, 7, 15), total_amount=50))
            db.session.commit()
        credentials = base64.b64encode(b'ads-admin:ads-secret').decode()
        self.auth = {'Authorization': f'Basic {credentials}'}
        self.client = self.app.test_client()

    def tearDown(self):
        admin_module.ADMIN_USER, admin_module.ADMIN_PW = self.original_credentials
        with self.app.app_context():
            db.session.remove()
            db.drop_all()

    def test_parser_and_rejections(self):
        rows = parse_monthly_cost_csv(csv_data(JUNE, JULY, AUGUST))
        self.assertEqual(len(rows), 3)
        self.assertEqual(sum((row.cost_eur for row in rows), Decimal('0.00')), Decimal('370.54'))
        self.assertEqual(rows[0].source_start, date(2025, 6, 6))
        for payload in (
            b'bad,header\n', csv_data(JUNE, JUNE),
            csv_data(JULY.replace('198.42', '198.43')),
            csv_data(JUNE.replace(',25,', ',24,')),
            csv_data(JULY.replace('2025-07-31', '2025-08-01')),
            csv_data(JULY.replace('198.42', '-1.00')),
            csv_data(JULY.replace('2025-07', '2025-13', 1)),
        ):
            with self.subTest(payload=payload[:20]), self.assertRaises(ValueError):
                parse_monthly_cost_csv(payload)

    def test_cent_constraint_accepts_valid_decimal_split(self):
        with self.app.app_context():
            rows = parse_monthly_cost_csv(csv_data(SEPTEMBER))
            self.assertEqual(import_monthly_costs(db.session, rows, 'cost.csv')['inserted'], 1)
            self.assertEqual(GoogleAdsImportedMonthlyCost.query.one().cost_eur, Decimal('11.28'))

    def test_atomic_repeat_update_and_missing_month(self):
        rows = parse_monthly_cost_csv(csv_data(JUNE, JULY, AUGUST))
        with self.app.app_context():
            self.assertEqual(import_monthly_costs(db.session, rows, 'cost.csv')['inserted'], 3)
            self.assertEqual(import_monthly_costs(db.session, rows, 'cost.csv')['unchanged'], 3)
            changed = parse_monthly_cost_csv(csv_data(JUNE, JULY.replace('198.42,163.01', '199.42,164.01')))
            with self.assertRaises(ValueError):
                import_monthly_costs(db.session, changed, 'updated.csv')
            db.session.rollback()
            self.assertEqual(GoogleAdsImportedMonthlyCost.query.filter_by(month=7).one().cost_eur,
                             Decimal('198.42'))
            self.assertEqual(import_monthly_costs(db.session, changed, 'updated.csv',
                                                  replace_existing=True)['updated'], 1)
            self.assertEqual(GoogleAdsImportedMonthlyCost.query.filter_by(month=7).one().cost_eur,
                             Decimal('199.42'))
            self.assertEqual(GoogleAdsImportedMonthlyCost.query.count(), 3)
            self.assertEqual(GoogleAdsImportedMonthlyCost.query.filter_by(month=7).one().import_filename,
                             'updated.csv')
            with self.assertRaises(ValueError):
                import_monthly_costs(db.session,
                    parse_monthly_cost_csv(csv_data(JULY.replace('daily.csv', 'other.csv'))), 'other.csv',
                    replace_existing=True)

    def test_dashboard_separates_cost_orders_and_missing_months(self):
        with self.app.app_context():
            import_monthly_costs(db.session, parse_monthly_cost_csv(csv_data(JUNE, AUGUST)), 'cost.csv')
            data = ads_dashboard_data(db.session, 'all', [2025])
            self.assertEqual(data['total'], Decimal('172.12'))
            self.assertEqual(data['labels'], ['2025-06', '2025-07', '2025-08'])
            self.assertEqual(data['costs'], [0.0, None, 172.12])
            self.assertEqual(data['orders'][1], 1)
            self.assertEqual(data['sales'][1], 50.0)
            self.assertEqual(data['missing'], 1)
            self.assertTrue(data['partial'][0])
            year_data = ads_dashboard_data(db.session, 'year:2025', [2025])
            self.assertEqual(len(year_data['labels']), 12)
            self.assertEqual(year_data['missing'], 10)
            self.assertIsNone(year_data['costs'][0])
            with self.assertRaises(ValueError):
                ads_dashboard_data(db.session, 'invalid', [2025])

    def test_manual_cost_overrides_csv_without_inventing_components(self):
        with self.app.app_context():
            import_monthly_costs(db.session, parse_monthly_cost_csv(csv_data(JULY)), 'cost.csv')
            self.assertTrue(save_manual_cost(db.session, '2025-07', '200,50', editing=True))
            self.assertEqual(GoogleAdsImportedMonthlyCost.query.one().cost_eur, Decimal('198.42'))
            data = ads_dashboard_data(db.session, 'all', [2025])
            self.assertEqual(data['total'], Decimal('200.50'))
            self.assertEqual(data['product'], Decimal('0.00'))
            self.assertEqual(data['without'], Decimal('0.00'))
            self.assertEqual(data['unclassified'], Decimal('200.50'))
            self.assertEqual(data['costs'], [200.5])
            self.assertEqual(len(effective_monthly_costs(db.session)), 1)
            change = GoogleAdsMonthlySpendChange.query.one()
            self.assertEqual((change.old_amount, change.new_amount),
                             (Decimal('198.42'), Decimal('200.50')))
            self.assertTrue(save_manual_cost(db.session, '2025-07', '201.00', editing=True))
            self.assertEqual(GoogleAdsMonthlySpendChange.query.count(), 2)
            self.assertFalse(save_manual_cost(db.session, '2025-07', '201.00', editing=True))
            self.assertEqual(GoogleAdsMonthlySpendChange.query.count(), 2)
            with self.assertRaises(ValueError):
                save_manual_cost(db.session, '2025-07', '202.00')

    def test_manual_month_validation_and_new_month(self):
        for month, amount in [('2025-13', '1.00'), ('2025-01', '-1.00'),
                              ('2025-01', '1.001'), ('2025-01', 'nan')]:
            with self.subTest(month=month, amount=amount), self.app.app_context():
                with self.assertRaises(ValueError):
                    save_manual_cost(db.session, month, amount)
        with self.app.app_context():
            self.assertTrue(save_manual_cost(db.session, '2025-09', '0'))
            self.assertEqual(GoogleAdsMonthlySpend.query.one().amount, Decimal('0.00'))
            self.assertIsNone(GoogleAdsMonthlySpendChange.query.one().old_amount)

    def test_legacy_manual_values_remain_inactive_until_confirmed(self):
        with self.app.app_context():
            import_monthly_costs(db.session, parse_monthly_cost_csv(csv_data(JULY)), 'cost.csv')
            db.session.add(GoogleAdsMonthlySpend(year=2025, month=7, amount=Decimal('70.00')))
            db.session.add(GoogleAdsMonthlySpend(year=2025, month=9, amount=Decimal('20.00')))
            db.session.commit()
            data = ads_dashboard_data(db.session, 'all', [2025])
            self.assertEqual(data['total'], Decimal('198.42'))
            self.assertEqual(len(effective_monthly_costs(db.session)), 1)
        html = self.client.get('/admin/ads-monthly', headers=self.auth).get_data(as_text=True)
        self.assertIn('pendientes de confirmar', html)
        with self.app.app_context():
            save_manual_cost(db.session, '2025-07', '75.00', editing=True)
            self.assertEqual(GoogleAdsMonthlySpendChange.query.one().old_amount, Decimal('198.42'))
            self.assertEqual(ads_dashboard_data(db.session, 'all', [2025])['total'], Decimal('75.00'))
            save_manual_cost(db.session, '2025-09', '20.00', editing=True)
            self.assertEqual(ads_dashboard_data(db.session, 'all', [2025])['total'], Decimal('95.00'))

    def test_manual_admin_auth_csrf_edit_and_dashboard(self):
        self.assertEqual(self.client.get('/admin/ads-monthly').status_code, 401)
        response = self.client.get('/admin/ads-monthly', headers=self.auth)
        self.assertEqual(response.status_code, 200)
        with self.client.session_transaction() as browser_session:
            token = browser_session['google_ads_monthly_csrf']
        self.assertEqual(self.client.post('/admin/ads-monthly', headers=self.auth,
            data={'action': 'add', 'month': '2025-07', 'amount': '40.00'}).status_code, 400)
        response = self.client.post('/admin/ads-monthly', headers=self.auth,
            data={'csrf_token': token, 'action': 'add', 'month': '2025-07', 'amount': '40.00'})
        self.assertEqual(response.status_code, 302)
        self.assertEqual(self.client.post('/admin/ads-monthly', headers=self.auth,
            data={'csrf_token': token, 'action': 'add', 'month': '2025-07', 'amount': '40.00'}).status_code, 400)
        edit = self.client.get('/admin/ads-monthly?edit=2025-07', headers=self.auth)
        self.assertIn('40.00', edit.get_data(as_text=True))
        self.assertEqual(self.client.post('/admin/ads-monthly', headers=self.auth,
            data={'csrf_token': token, 'action': 'edit', 'month': '2025-07', 'amount': '41.50'}).status_code, 302)
        dashboard = self.client.get('/admin/?ads_period=year:2025', headers=self.auth)
        self.assertIn('41.50 €', dashboard.get_data(as_text=True))
        self.assertIn('Sin desglose (manual)', dashboard.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(GoogleAdsMonthlySpendChange.query.count(), 2)

    def test_admin_auth_csrf_and_import(self):
        self.assertEqual(self.client.get('/admin/ads-import').status_code, 401)
        self.assertEqual(self.client.post('/admin/ads-import', data={}).status_code, 401)
        response = self.client.get('/admin/ads-import', headers=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.client.post('/admin/ads-import', headers=self.auth,
            data={'cost_csv': (io.BytesIO(csv_data(JULY)), 'cost.csv')}).status_code, 400)
        with self.client.session_transaction() as browser_session:
            token = browser_session['google_ads_csv_csrf']
        response = self.client.post('/admin/ads-import', headers=self.auth, data={
            'csrf_token': token, 'cost_csv': (io.BytesIO(csv_data(JULY)), 'cost.csv')
        })
        self.assertEqual(response.status_code, 200)
        self.assertIn('1 meses nuevos', response.get_data(as_text=True))
        with self.app.app_context():
            self.assertEqual(GoogleAdsImportedMonthlyCost.query.count(), 1)
        invalid = csv_data(JUNE, JULY.replace('198.42', '198.43'))
        self.assertEqual(self.client.post('/admin/ads-import', headers=self.auth, data={
            'csrf_token': token, 'cost_csv': (io.BytesIO(invalid), 'invalid.csv')
        }).status_code, 400)
        with self.app.app_context():
            self.assertEqual(GoogleAdsImportedMonthlyCost.query.count(), 1)
        dashboard = self.client.get('/admin/', headers=self.auth).get_data(as_text=True)
        self.assertIn('Publicidad · Google Ads', dashboard)
        self.assertIn('198.42 €', dashboard)
        self.assertIn('admin_google_ads_monthly.js', dashboard)
        self.assertLess(dashboard.index('Evolución por producto'), dashboard.index('Publicidad · Google Ads'))
        self.assertLess(dashboard.index('Publicidad · Google Ads'), dashboard.index('Actividad reciente'))
        self.assertEqual(self.client.get('/admin/?ads_period=invalid', headers=self.auth).status_code, 400)

    def test_dashboard_is_available_before_ads_migration(self):
        with self.app.app_context():
            GoogleAdsImportedMonthlyCost.__table__.drop(db.engine)
        response = self.client.get('/admin/', headers=self.auth)
        self.assertEqual(response.status_code, 200)
        html = response.get_data(as_text=True)
        self.assertIn('estará disponible cuando se aplique su migración', html)
        self.assertNotIn('>Importar CSV</a>', html)
        self.assertEqual(self.client.get('/admin/ads-import', headers=self.auth).status_code, 503)
        self.assertEqual(self.client.post('/admin/ads-import', headers=self.auth,
            data={'cost_csv': (io.BytesIO(csv_data(JULY)), 'cost.csv')}).status_code, 503)

    def test_dashboard_keeps_csv_until_manual_history_migration(self):
        with self.app.app_context():
            import_monthly_costs(db.session, parse_monthly_cost_csv(csv_data(JULY)), 'cost.csv')
            GoogleAdsMonthlySpendChange.__table__.drop(db.engine)
        response = self.client.get('/admin/', headers=self.auth)
        self.assertEqual(response.status_code, 200)
        self.assertIn('198.42 €', response.get_data(as_text=True))
        self.assertNotIn('>Gestionar gastos</a>', response.get_data(as_text=True))
        self.assertEqual(self.client.get('/admin/ads-monthly', headers=self.auth).status_code, 503)

    def test_migration_constraints_on_isolated_database(self):
        script = ScriptDirectory(str(ROOT / 'src' / 'migrations'))
        self.assertEqual(script.get_heads(), ['b7d3e9f1a2c4'])
        migration = script.get_revision('a6f2c9e4d1b8').module
        engine = create_engine('sqlite:///:memory:')
        with engine.begin() as connection:
            operations = Operations(MigrationContext.configure(connection))
            original = migration.op
            try:
                migration.op = operations
                migration.upgrade()
                inspector = inspect(connection)
                self.assertIn('google_ads_imported_monthly_cost', inspector.get_table_names())
                self.assertIn(('year', 'month'), {
                    tuple(item['column_names']) for item in inspector.get_unique_constraints(
                        'google_ads_imported_monthly_cost')
                })
                migration.downgrade()
                self.assertNotIn('google_ads_imported_monthly_cost', inspect(connection).get_table_names())
            finally:
                migration.op = original

    def test_manual_history_migration_on_isolated_database(self):
        script = ScriptDirectory(str(ROOT / 'src' / 'migrations'))
        migration = script.get_revision('b7d3e9f1a2c4').module
        self.assertEqual(migration.down_revision, 'a6f2c9e4d1b8')
        engine = create_engine('sqlite:///:memory:')
        with engine.begin() as connection:
            operations = Operations(MigrationContext.configure(connection))
            original = migration.op
            try:
                migration.op = operations
                migration.upgrade()
                columns = {item['name'] for item in inspect(connection).get_columns('google_ads_monthly_spend_change')}
                self.assertTrue({'old_amount', 'new_amount', 'changed_at'} <= columns)
                migration.downgrade()
                self.assertNotIn('google_ads_monthly_spend_change', inspect(connection).get_table_names())
            finally:
                migration.op = original


if __name__ == '__main__':
    unittest.main()
