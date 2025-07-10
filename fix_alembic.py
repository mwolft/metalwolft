
from src.app import app, db

with app.app_context():
    db.session.execute("DELETE FROM alembic_version")
    db.session.commit()
    print("🔥 Eliminado alembic_version con éxito")
