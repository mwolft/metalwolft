from flask_sqlalchemy import SQLAlchemy


db = SQLAlchemy()


class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    alias = db.Column(db.String(10), unique=True)
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    gender = db.Column(db.String(20))
    phone = db.Column(db.Integer)
    email = db.Column(db.String(50), unique=True, nullable=False)
    birth = db.Column(db.Integer)
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    rol = db.Column(db.Enum('user', 'admin', 'trainer', name='rol_enum'))
    roles = db.relationship('Roles', secondary='user_roles', back_populates='users')
    rutines = db.relationship('Rutines', backref='user', lazy=True)
    user_recipes = db.relationship('UserRecipes', backref='user', lazy=True)
    user_ingredients = db.relationship('UserIngredients', backref='user', lazy=True)
    template_prompts = db.relationship('TemplatePrompts', backref='author', lazy=True)

    def __repr__(self):
        return f'<User {self.id}: {self.alias}>'


class Exercises(db.Model):
    __tablename__ = "exercises"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    rutine_id = db.Column(db.Integer, db.ForeignKey('rutines.id'), nullable=True)
    equipments = db.relationship('ExerciseEquipments', backref='exercise', lazy=True)
    muscles = db.relationship('ExerciseMuscles', backref='exercise', lazy=True)
    variations_origin = db.relationship('Variations', foreign_keys='Variations.exercise_origin', backref='origin_exercise', lazy=True)
    variations_to = db.relationship('Variations', foreign_keys='Variations.exercise_to', backref='to_exercise', lazy=True)

    def __repr__(self):
        return f'<Exercise {self.id}: {self.name}>'


class Muscles(db.Model):
    __tablename__ = "muscles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Muscle {self.id}: {self.name}>'


class ExerciseEquipments(db.Model):
    __tablename__ = "exercise_equipments"
    id = db.Column(db.Integer, primary_key=True)
    excercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=False)


class ExerciseMuscles(db.Model):
    __tablename__ = "exercise_muscles"
    id = db.Column(db.Integer, primary_key=True)
    excercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    muscle_id = db.Column(db.Integer, db.ForeignKey('muscles.id'), nullable=False)


class Equipments(db.Model):
    __tablename__ = "equipments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Equipment {self.id}: {self.name}>'


class Variations(db.Model):
    __tablename__ = "variations"
    id = db.Column(db.Integer, primary_key=True)
    exercise_origin = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    exercise_to = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)


class Rutines(db.Model):
    __tablename__ = "rutines"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prompt = db.Column(db.Text)
    date = db.Column(db.DateTime)
    exercises = db.relationship('Exercises', backref='rutine', lazy=True)

    def __repr__(self):
        return f'<Rutine {self.id}>'


class Ingredients(db.Model):
    __tablename__ = "ingredients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    kcal = db.Column(db.Integer, nullable=False)
    proteins = db.Column(db.Integer, nullable=False)
    carbohydrates = db.Column(db.Integer, nullable=False)
    fats = db.Column(db.Integer, nullable=False)
    sugar = db.Column(db.Integer, nullable=False)

    def __repr__(self):
        return f'<Ingredient {self.id}: {self.name}>'


class Recipes(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    name = db.Column(db.String(100))

    def __repr__(self):
        return f'<Recipe {self.id}: {self.name}>'


class UserRecipes(db.Model):
    __tablename__ = "user_recipes"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prompt = db.Column(db.Text)


class UserIngredients(db.Model):
    __tablename__ = "user_ingredients"
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)


class TemplatePrompts(db.Model):
    __tablename__ = "template_prompts"
    id = db.Column(db.Integer, primary_key=True)
    body_prompt = db.Column(db.Text, unique=True, nullable=False)
    suggest = db.Column(db.Text)
    type = db.Column(db.Enum('Nutrition', 'exercise', name='prompt_type_enum'))
    date = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    title = db.Column(db.String(60))
    description = db.Column(db.String(60))

    def __repr__(self):
        return f'<TemplatePrompt {self.id}: {self.title}>'
