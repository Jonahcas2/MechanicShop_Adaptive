from flask import Flask
from .extensions import ma
from .models import db
from .Blueprints.customers import customers_bp

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(f'config.{config_name}')

    # Initialize extensions
    ma.init_app(app)
    db.init_app(app)

    # Register blueprints
    app.register_blueprint(customers_bp)

    return app