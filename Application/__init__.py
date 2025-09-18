from flask import Flask
from .extensions import ma, limiter, cache
from .models import db
from .Blueprints.customers import customers_bp
from .Blueprints.mechanics import mechanics_bp
from .Blueprints.service_tickets import tickets_bp
from .Blueprints.inventory import inventory_bp

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(f'config.{config_name}')

    # Initialize extensions
    ma.init_app(app)
    db.init_app(app)
    limiter.init_app(app)
    cache.init_app(app)

    # Register blueprints
    app.register_blueprint(customers_bp)
    app.register_blueprint(mechanics_bp)
    app.register_blueprint(tickets_bp)
    app.register_blueprint(inventory_bp)

    return app