import os

class DevConfig:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:0ff3ns1v3S3cur17y@localhost:3306/mechanic_shop'
    DEBUG = True

class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'
    DEBUG = True
    CACHE_TYPE = 'SimpleCache'

class ProductionConfig:
    # Get the database URL from environment
    database_url = os.environ.get('DATABASE_URL')
    
    # Render provides DATABASE_URL, but SQLAlchemy needs it in a specific format
    # Also need to ensure SSL is required
    if database_url and database_url.startswith('postgres://'):
        database_url = database_url.replace('postgres://', 'postgresql://', 1)
    
    # Add SSL requirement for PostgreSQL
    SQLALCHEMY_DATABASE_URI = database_url
    SQLALCHEMY_ENGINE_OPTIONS = {
        "connect_args": {
            "sslmode": "require"
        }
    }
    CACHE_TYPE = "SimpleCache"