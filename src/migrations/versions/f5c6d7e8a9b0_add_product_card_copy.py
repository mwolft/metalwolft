"""Add catalogue card copy and best-seller badge variant.

Revision ID: f5c6d7e8a9b0
Revises: e2f3a4b5c6d7
"""

from alembic import op
import sqlalchemy as sa


revision = "f5c6d7e8a9b0"
down_revision = "e2f3a4b5c6d7"
branch_labels = None
depends_on = None


CARD_COPY = {
    "reja-fija-albany": "Líneas horizontales · Estilo moderno",
    "reja-fija-luton": "Líneas diagonales · Diseño llamativo",
    "reja-fija-idaho": "Líneas horizontales · Acabado robusto",
    "reja-fija-dakota": "Diseño vertical · Sin bastidor",
    "reja-fija-essex": "Líneas verticales · Estilo clásico",
    "reja-fija-cortland": "Horizontales con detalles verticales",
    "reja-fija-erie": "Líneas horizontales · Refuerzo central",
    "reja-fija-genesee": "Horizontales · Refuerzos en las esquinas",
    "reja-fija-livingston": "Pletinas dobles horizontales",
    "reja-fija-virginia": "Líneas horizontales · Diseño sencillo",
    "reja-fija-maryland": "Líneas horizontales · Perfil cuadrado",
    "reja-fija-clasica-charleston": "Barrotes verticales · Detalles ornamentales",
    "reja-fija-ithaca": "Entramado diagonal en rombos",
    "reja-fija-orleans-clasica": "Diseño ornamental · Refuerzo central",
    "reja-fija-vermont": "Verticales con dos refuerzos horizontales",
    "reja-fija-pittsburgh": "Horizontales · Refuerzos en las esquinas",
    "reja-mascotas-ohio": "Separación reducida · Especial para mascotas",
    "reja-abatible-maryland-para-ventanas": "Apertura abatible · Diseño horizontal",
    "reja-abatible-cortland": "Apertura abatible · Diseño mixto",
    "reja-abatible-albany": "Apertura abatible · Líneas horizontales",
    "reja-abatible-essex": "Apertura abatible · Líneas verticales",
    "reja-puerta-albany": "Para puertas · Líneas horizontales",
    "reja-puerta-cortland": "Para puertas · Diseño reforzado",
    "reja-puerta-maryland": "Para puertas · Perfil cuadrado",
}


def upgrade():
    op.add_column("products", sa.Column("descripcion_card", sa.Text(), nullable=True))
    op.add_column(
        "products",
        sa.Column(
            "best_seller_badge_variant",
            sa.String(length=24),
            server_default="top_sales",
            nullable=False,
        ),
    )
    with op.batch_alter_table("products") as batch_op:
        batch_op.create_check_constraint(
            "ck_products_best_seller_badge_variant",
            "best_seller_badge_variant IN ('top_sales', 'most_sold')",
        )

    products = sa.table(
        "products",
        sa.column("slug", sa.String()),
        sa.column("descripcion_card", sa.Text()),
        sa.column("best_seller_badge_variant", sa.String()),
    )
    connection = op.get_bind()
    for slug, copy in CARD_COPY.items():
        connection.execute(
            products.update()
            .where(products.c.slug == slug)
            .values(descripcion_card=copy)
        )
    connection.execute(
        products.update()
        .where(products.c.slug == "reja-fija-albany")
        .values(best_seller_badge_variant="most_sold")
    )


def downgrade():
    with op.batch_alter_table("products") as batch_op:
        batch_op.drop_constraint("ck_products_best_seller_badge_variant", type_="check")
        batch_op.drop_column("best_seller_badge_variant")
        batch_op.drop_column("descripcion_card")
