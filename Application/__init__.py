from flask import Flask
from .extensions import ma, limiter, cache
from .models import db
from .Blueprints.customers import customers_bp
from .Blueprints.mechanics import mechanics_bp
from .Blueprints.service_tickets import tickets_bp
from .Blueprints.inventory import inventory_bp

from flask_swagger_ui import get_swaggerui_blueprint
SWAGGER_URL = '/api/docs'
API_URL = '/static/swagger.yaml'

swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={'app_name': "My API"}
)



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
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    return app