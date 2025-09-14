"""
In this file, you can add as many commands as you want using the @app.cli.command decorator
Flask commands are useful to run cronjobs or tasks outside of the API but still in integration 
with your database, for example: Import the price of bitcoin every night at 12am
"""
import click
from api.models import db, Users, Orders

def setup_commands(app):
    """Register Flask CLI commands."""

    @app.cli.command("insert-test-users")
    @click.argument("count")
    def insert_test_users(count):
        """Create test users. Example: flask insert-test-users 5"""
        print("Creating test users")
        for x in range(1, int(count) + 1):
            user = Users()
            user.email = f"test_user{x}@test.com"
            user.password = "123456"
            user.is_active = True
            db.session.add(user)
            db.session.commit()
            print("User:", user.email, "created.")
        print("All test users created")

    @app.cli.command("update-users")
    def update_users_from_orders():
        """
        Rellena datos de usuarios (nombre, direcciones, CIF) desde sus pedidos más recientes.
        """
        users = db.session.query(Users).join(Orders).distinct().all()
        updated_count = 0

        for user in users:
            latest_order = (
                db.session.query(Orders)
                .filter(Orders.user_id == user.id)
                .order_by(Orders.order_date.desc())
                .first()
            )
            if not latest_order or not latest_order.order_details:
                continue

            d0 = latest_order.order_details[0]
            changed = False

            if not user.firstname and d0.firstname:
                user.firstname = d0.firstname; changed = True
            if not user.lastname and d0.lastname:
                user.lastname = d0.lastname; changed = True
            if not user.shipping_address and d0.shipping_address:
                user.shipping_address = d0.shipping_address; changed = True
            if not user.shipping_city and d0.shipping_city:
                user.shipping_city = d0.shipping_city; changed = True
            if not user.shipping_postal_code and d0.shipping_postal_code:
                user.shipping_postal_code = d0.shipping_postal_code; changed = True
            if not user.billing_address and d0.billing_address:
                user.billing_address = d0.billing_address; changed = True
            if not user.billing_city and d0.billing_city:
                user.billing_city = d0.billing_city; changed = True
            if not user.billing_postal_code and d0.billing_postal_code:
                user.billing_postal_code = d0.billing_postal_code; changed = True
            if not user.CIF and d0.CIF:
                user.CIF = d0.CIF; changed = True

            if changed:
                updated_count += 1
                click.echo(f"Actualizado: {user.email}")

        db.session.commit()
        click.echo(f"✅ Usuarios actualizados: {updated_count}")
