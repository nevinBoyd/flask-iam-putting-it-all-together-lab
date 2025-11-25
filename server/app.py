#!/usr/bin/env python3

from flask import request, session
from flask_restful import Resource
from sqlalchemy.exc import IntegrityError

from config import app, db, api
from models import User, Recipe, UserSchema, RecipeSchema

user_schema = UserSchema()
recipe_schema = RecipeSchema()
recipes_schema = RecipeSchema(many=True)

class Signup(Resource):
    def post(self):
        data = request.get_json()

        username = data.get("username")
        password = data.get("password")
        image_url = data.get("image_url")  # can be None
        bio = data.get("bio")  # can be None

        # Create new user object
        user = User(
            username=username,
            image_url=image_url,
            bio=bio
        )
        user.password_hash = password  # bcrypt in model

        try:
            db.session.add(user)
            db.session.commit()
        except IntegrityError:
            db.session.rollback()
            return {"errors": ["Username must be unique"]}, 422

        # Log in
        session["user_id"] = user.id

        return UserSchema().dump(user), 201

class CheckSession(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "401 Unauthorized"}, 401

        user = User.query.get(user_id)
        return UserSchema().dump(user), 200

class Login(Resource):
    def post(self):
        data = request.get_json()
        username = data.get("username")
        password = data.get("password")

        user = User.query.filter_by(username=username).first()

        if user and user.authenticate(password):
            session["user_id"] = user.id
            return UserSchema().dump(user), 200
        
        return {"error": "401 Unauthorized"}, 401

class Logout(Resource):
    def delete(self):
        if session.get("user_id"):
            session.pop("user_id", None)
            return {}, 204

        return {"error": "401 Unauthorized"}, 401

class RecipeIndex(Resource):
    def get(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "401 Unauthorized"}, 401
        
        recipes = Recipe.query.all()
        return recipes_schema.dump(recipes), 200

    def post(self):
        user_id = session.get("user_id")
        if not user_id:
            return {"error": "401 Unauthorized"}, 401

        data = request.get_json()
        title = data.get("title")
        instructions = data.get("instructions")
        minutes = data.get("minutes_to_complete")
    
        try:
            recipe = Recipe(
            title=title,
            instructions=instructions,
            minutes_to_complete=minutes,
            user_id=user_id
            )

            db.session.add(recipe)
            db.session.commit()
            return recipe_schema.dump(recipe), 201
        
        except Exception:
            db.session.rollback()
            return {"errors": ["validation errors"]}, 422

    

api.add_resource(Signup, '/signup', endpoint='signup')
api.add_resource(CheckSession, '/check_session', endpoint='check_session')
api.add_resource(Login, '/login', endpoint='login')
api.add_resource(Logout, '/logout', endpoint='logout')
api.add_resource(RecipeIndex, '/recipes', endpoint='recipes')


if __name__ == '__main__':
    app.run(port=5555, debug=True)