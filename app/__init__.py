# Η συνάρτηση create_app φτιάχνει και ρυθμίζει το Flask app σύμφωνα με το application factory pattern.

from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from dotenv import load_dotenv
from datetime import timedelta
import os

# Σύνδεση με MongoDB και συλλογές
from app.db.DB_config import db
from app.routes.auth_route import auth_bp
from app.routes.cart_route import cart_bp
from app.routes.products_route import product_bp
from app.routes.products_by_category_route import product_by_category_bp
from app.routes.profile_route import profile_bp
from app.routes.ai_route import ai_bp
from app.routes.analytics_route import analytics_bp
from app.routes.ml_route import ml_bp


def create_app():
    # Φόρτωση μεταβλητών περιβάλλοντος από .env για JWT_SECRET_KEY
    load_dotenv()

    # Δημιουργία της Flask εφαρμογής
    app = Flask(__name__)
    CORS(app)

    # Ρύθμιση JWT
    app.config['JWT_SECRET_KEY'] = os.getenv("JWT_SECRET_KEY", "super-secret-key")
    app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(hours=1)
    #app.config["JWT_ACCESS_TOKEN_EXPIRES"] = timedelta(minutes=2)
    JWTManager(app)

    # Σύνδεση με MongoDB
    app.db = db

    # Καταχώρηση των Blueprints για τα routes
    app.register_blueprint(auth_bp, url_prefix="/auth")
    app.register_blueprint(cart_bp, url_prefix="/")
    app.register_blueprint(product_bp, url_prefix="/")
    app.register_blueprint(product_by_category_bp, url_prefix="/")
    app.register_blueprint(profile_bp, url_prefix="/")
    app.register_blueprint(ai_bp)
    app.register_blueprint(analytics_bp)
    app.register_blueprint(ml_bp)

    return app