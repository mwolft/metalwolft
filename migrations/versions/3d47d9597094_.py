"""empty message

Revision ID: 3d47d9597094
Revises: 
Create Date: 2024-08-20 18:05:39.306797

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '3d47d9597094'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('equipments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('ingredients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=200), nullable=False),
    sa.Column('kcal', sa.Integer(), nullable=False),
    sa.Column('proteins', sa.Integer(), nullable=False),
    sa.Column('carbohydrates', sa.Integer(), nullable=False),
    sa.Column('fats', sa.Integer(), nullable=False),
    sa.Column('sugar', sa.Integer(), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('muscles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('users',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('password', sa.String(length=100), nullable=False),
    sa.Column('alias', sa.String(length=10), nullable=True),
    sa.Column('firstname', sa.String(length=30), nullable=True),
    sa.Column('lastname', sa.String(length=30), nullable=True),
    sa.Column('gender', sa.Enum('Male', 'Female', name='gender'), nullable=True),
    sa.Column('phone', sa.Integer(), nullable=True),
    sa.Column('email', sa.String(length=50), nullable=False),
    sa.Column('birth', sa.Date(), nullable=True),
    sa.Column('height', sa.Integer(), nullable=True),
    sa.Column('weight', sa.Integer(), nullable=True),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('rol', sa.Enum('user', 'admin', 'trainer', name='rol'), nullable=True),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('alias'),
    sa.UniqueConstraint('email')
    )
    op.create_table('recipes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ingredient_id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=100), nullable=True),
    sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('rutines',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('template_prompts',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('body_prompt', sa.Text(), nullable=False),
    sa.Column('suggest', sa.Text(), nullable=True),
    sa.Column('prompt_type', sa.Enum('nutrition', 'exercise', name='prompt_type'), nullable=True),
    sa.Column('date', sa.DateTime(), nullable=True),
    sa.Column('author_id', sa.Integer(), nullable=False),
    sa.Column('is_active', sa.Boolean(), nullable=True),
    sa.Column('title', sa.String(length=60), nullable=True),
    sa.Column('description', sa.String(length=60), nullable=True),
    sa.ForeignKeyConstraint(['author_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('body_prompt')
    )
    op.create_table('user_ingredients',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('ingredient_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['ingredient_id'], ['ingredients.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exercises',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('name', sa.String(length=50), nullable=False),
    sa.Column('description', sa.Text(), nullable=True),
    sa.Column('rutine_id', sa.Integer(), nullable=True),
    sa.ForeignKeyConstraint(['rutine_id'], ['rutines.id'], ),
    sa.PrimaryKeyConstraint('id'),
    sa.UniqueConstraint('name')
    )
    op.create_table('user_recipes',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('recipe_id', sa.Integer(), nullable=False),
    sa.Column('user_id', sa.Integer(), nullable=False),
    sa.Column('prompt', sa.Text(), nullable=True),
    sa.ForeignKeyConstraint(['recipe_id'], ['recipes.id'], ),
    sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exercise_equipments',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('excercise_id', sa.Integer(), nullable=False),
    sa.Column('equipment_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['equipment_id'], ['equipments.id'], ),
    sa.ForeignKeyConstraint(['excercise_id'], ['exercises.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('exercise_muscles',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('excercise_id', sa.Integer(), nullable=False),
    sa.Column('muscle_id', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['excercise_id'], ['exercises.id'], ),
    sa.ForeignKeyConstraint(['muscle_id'], ['muscles.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_table('variations',
    sa.Column('id', sa.Integer(), nullable=False),
    sa.Column('exercise_origin', sa.Integer(), nullable=False),
    sa.Column('exercise_to', sa.Integer(), nullable=False),
    sa.ForeignKeyConstraint(['exercise_origin'], ['exercises.id'], ),
    sa.ForeignKeyConstraint(['exercise_to'], ['exercises.id'], ),
    sa.PrimaryKeyConstraint('id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('variations')
    op.drop_table('exercise_muscles')
    op.drop_table('exercise_equipments')
    op.drop_table('user_recipes')
    op.drop_table('exercises')
    op.drop_table('user_ingredients')
    op.drop_table('template_prompts')
    op.drop_table('rutines')
    op.drop_table('recipes')
    op.drop_table('users')
    op.drop_table('muscles')
    op.drop_table('ingredients')
    op.drop_table('equipments')
    # ### end Alembic commands ###
