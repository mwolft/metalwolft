from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

class Users(db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    password = db.Column(db.String(100), nullable=False)
    alias = db.Column(db.String(10), unique=True, nullable=True)
    firstname = db.Column(db.String(30))
    lastname = db.Column(db.String(30))
    gender = db.Column(db.Enum('Male', 'Female', name='gender'), nullable=True)
    phone = db.Column(db.String(20))  # String is appropriate for phone numbers
    email = db.Column(db.String(50), unique=True, nullable=False, index=True)
    age = db.Column(db.Integer)
    height = db.Column(db.Integer)
    weight = db.Column(db.Integer)
    is_active = db.Column(db.Boolean, default=True)
    rol = db.Column(db.Enum('user', 'admin', 'trainer', name="rol"))
    location = db.Column(db.String(100), nullable=True)
    
    routines = db.relationship('Routines', backref='user', lazy=True, cascade="all, delete-orphan")
    user_recipes = db.relationship('UserRecipes', backref='user', lazy=True, cascade="all, delete-orphan")
    user_ingredients = db.relationship('UserIngredients', backref='user', lazy=True, cascade="all, delete-orphan")
    template_prompts = db.relationship('TemplatePrompts', backref='author', lazy=True, cascade="all, delete-orphan")
    favorite_recipes = db.relationship('FavoriteRecipes', backref='user', lazy=True, cascade="all, delete-orphan")
    favorite_routines = db.relationship('FavoriteRoutines', backref='user', lazy=True, cascade="all, delete-orphan")
    favorite_exercises = db.relationship('FavoriteExercises', backref='user', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<User {self.id}: {self.alias}>'

    def serialize(self):
        return {
            "id": self.id,
            "firstname": self.firstname,
            "lastname": self.lastname,
            "email": self.email,
            "is_active": self.is_active,
            "alias": self.alias,
            "gender": self.gender,
            "phone": self.phone,
            "age": self.birth,
            "height": self.height,
            "weight": self.weight,
            "rol": self.rol,
            "location": self.location,
            "favorite_recipes": [favorite_recipe.serialize() for favorite_recipe in self.favorite_recipes],
            "favorite_routines": [favorite_routine.serialize() for favorite_routine in self.favorite_routines],
            "favorite_exercises": [favorite_exercise.serialize() for favorite_exercise in self.favorite_exercises]
        }
        return {"id": self.id,
                "firstname": self.firstname,
                "lastname": self.lastname,
                "email": self.email,
                "is_active": self.is_active,
                "alias": self.alias,
                "gender": self.gender,
                "phone": self.phone,
                "age": self.age,
                "height": self.height,
                "weight": self.weight,
                "rol": self.rol,
                "location": self.location,
                "favorite_recipes": [favorite_recipe.serialize() for favorite_recipe in self.favorite_recipes],
                "favorite_routines": [favorite_routine.serialize() for favorite_routine in self.favorite_routines],
                "favorite_exercises": [favorite_exercise.serialize() for favorite_exercise in self.favorite_exercises]}


class Exercises(db.Model):
    __tablename__ = "exercises"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.Text)
    image_url = db.Column(db.String(255))
    routine_id = db.Column(db.Integer, db.ForeignKey('routines.id'), nullable=True)
    
    # Relationships
    equipments = db.relationship('ExerciseEquipments', backref='exercise', lazy=True, cascade="all, delete-orphan")
    muscles = db.relationship('ExerciseMuscles', backref='exercise', lazy=True, cascade="all, delete-orphan")
    variations_origin = db.relationship('Variations', foreign_keys='Variations.exercise_origin', backref='origin_exercise', lazy=True, cascade="all, delete-orphan")
    variations_to = db.relationship('Variations', foreign_keys='Variations.exercise_to', backref='to_exercise', lazy=True, cascade="all, delete-orphan")
    favorited_by = db.relationship('FavoriteExercises', backref='exercise', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Exercise {self.id}: {self.name}>'

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "image_url": self.image_url,
            "routine_id": self.routine_id,
            "equipments": [equipment.serialize() for equipment in self.equipments],
            # Proper serialization of muscles
            "muscles": [muscle_rel.muscle.serialize() for muscle_rel in self.muscles],
            "variations_origin": [variation.serialize() for variation in self.variations_origin],
            "variations_to": [variation.serialize() for variation in self.variations_to],
            "favorited_by": [favorite.user_id for favorite in self.favorited_by]
        }


class Muscles(db.Model):
    __tablename__ = "muscles"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Muscle {self.id}: {self.name}>'

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name
        }


class ExerciseMuscles(db.Model):
    __tablename__ = "exercise_muscles"
    
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), primary_key=True)
    muscle_id = db.Column(db.Integer, db.ForeignKey('muscles.id'), primary_key=True)

    # Define relationships to Muscles
    muscle = db.relationship('Muscles', backref='exercise_muscles')

    def __repr__(self):
        return f'<ExerciseMuscles Exercise {self.exercise_id} Muscle {self.muscle_id}>'

    def serialize(self):
        return {
            "exercise_id": self.exercise_id,
            "muscle_id": self.muscle_id
        }


class ExerciseEquipments(db.Model):
    __tablename__ = "exercise_equipments"
    id = db.Column(db.Integer, primary_key=True)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    equipment_id = db.Column(db.Integer, db.ForeignKey('equipments.id'), nullable=False)

    def __repr__(self):
        return f'<ExerciseEquipments {self.id}: Exercise {self.exercise_id} Equipment {self.equipment_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "exercise_id": self.exercise_id,
            "equipment_id": self.equipment_id
        }


class Equipments(db.Model):
    __tablename__ = "equipments"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)

    def __repr__(self):
        return f'<Equipment {self.id}: {self.name}>'

    def serialize(self):
        return {
            "id": self.id, 
            "name": self.name
        }


class Variations(db.Model):
    __tablename__ = "variations"
    id = db.Column(db.Integer, primary_key=True)
    exercise_origin = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)
    exercise_to = db.Column(db.Integer, db.ForeignKey('exercises.id'), nullable=False)

    def __repr__(self):
        return f'<Variations {self.id}: Origin {self.exercise_origin} -> To {self.exercise_to}>'

    def serialize(self):
        return {
            "id": self.id,
            "exercise_origin": self.exercise_origin,
            "exercise_to": self.exercise_to
        }


class Routines(db.Model):
    __tablename__ = "routines"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prompt = db.Column(db.Text)
    date = db.Column(db.DateTime)
    
    exercises = db.relationship('Exercises', backref='routine', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Routine {self.id}>'

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "prompt": self.prompt,
            "date": self.date,
            "exercises": [exercise.serialize() for exercise in self.exercises]
        }


class Ingredients(db.Model):
    __tablename__ = "ingredients"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), unique=True, nullable=False)
    type = db.Column(db.String(200), nullable=False)
    calories = db.Column(db.Float, nullable=False)
    proteins = db.Column(db.Float, nullable=False)
    carbs = db.Column(db.Float, nullable=False)
    fat = db.Column(db.Float, nullable=False)
    sugar = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f'<Ingredient {self.id}: {self.name}>'

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "type": self.type,
            "calories": self.calories,
            "proteins": self.proteins,
            "carbs": self.carbs,
            "fat": self.fat,
            "sugar": self.sugar
        }


class Recipes(db.Model):
    __tablename__ = "recipes"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100))
    ingredients_text = db.Column(db.Text)  # Add this field for storing ingredients as plain text

    favorited_by = db.relationship('FavoriteRecipes', backref='recipe', lazy=True, cascade="all, delete-orphan")

    def __repr__(self):
        return f'<Recipe {self.id}: {self.name}>'

    def serialize(self):
        return {
            "id": self.id,
            "name": self.name,
            "ingredients_text": self.ingredients_text,
            "favorited_by": [favorite.user_id for favorite in self.favorited_by]
        }


class UserRecipes(db.Model):
    __tablename__ = "user_recipes"
    id = db.Column(db.Integer, primary_key=True)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    prompt = db.Column(db.Text)

    def __repr__(self):
        return f'<UserRecipes {self.id}: User {self.user_id} Recipe {self.recipe_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "recipe_id": self.recipe_id,
            "user_id": self.user_id,
            "prompt": self.prompt
        }


class UserIngredients(db.Model):
    __tablename__ = "user_ingredients"
    id = db.Column(db.Integer, primary_key=True)
    ingredient_id = db.Column(db.Integer, db.ForeignKey('ingredients.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    def __repr__(self):
        return f'<UserIngredients {self.id}: User {self.user_id} Ingredient {self.ingredient_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "ingredient_id": self.ingredient_id,
            "user_id": self.user_id
        }


class TemplatePrompts(db.Model):
    __tablename__ = "template_prompts"
    id = db.Column(db.Integer, primary_key=True)
    body_prompt = db.Column(db.Text, unique=True, nullable=False)
    suggest = db.Column(db.Text)
    prompt_type = db.Column(db.Enum('nutrition', 'exercise', name="prompt_type"))
    date = db.Column(db.DateTime)
    author_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    is_active = db.Column(db.Boolean, default=True)
    title = db.Column(db.String(60))
    description = db.Column(db.String(60))

    def __repr__(self):
        return f'<TemplatePrompt {self.id}: {self.title}>'

    def serialize(self):
        return {
            "id": self.id,
            "body_prompt": self.body_prompt,
            "suggest": self.suggest,
            "prompt_type": self.prompt_type,
            "date": self.date,
            "author_id": self.author_id,
            "is_active": self.is_active,
            "title": self.title,
            "description": self.description
        }


class FavoriteRecipes(db.Model):
    __tablename__ = "favorite_recipes"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    recipe_id = db.Column(db.Integer, db.ForeignKey('recipes.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f'<FavoriteRecipe {self.id}: User {self.user_id} Recipe {self.recipe_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "recipe_id": self.recipe_id
        }


class FavoriteRoutines(db.Model):
    __tablename__ = "favorite_routines"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    routine_id = db.Column(db.Integer, db.ForeignKey('routines.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f'<FavoriteRoutine {self.id}: User {self.user_id} Routine {self.routine_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "routine_id": self.routine_id
        }


class FavoriteExercises(db.Model):
    __tablename__ = "favorite_exercises"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id', ondelete="CASCADE"), nullable=False)
    exercise_id = db.Column(db.Integer, db.ForeignKey('exercises.id', ondelete="CASCADE"), nullable=False)

    def __repr__(self):
        return f'<FavoriteExercise {self.id}: User {self.user_id} Exercise {self.exercise_id}>'

    def serialize(self):
        return {
            "id": self.id,
            "user_id": self.user_id,
            "exercise_id": self.exercise_id
        }