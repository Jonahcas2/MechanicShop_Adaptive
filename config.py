import os

class DevConfig:
    SQLALCHEMY_DATABASE_URI = 'mysql+mysqlconnector://root:0ff3ns1v3S3cur17y@localhost:3306/mechanic_shop'
    DEBUG = True

class TestConfig:
    SQLALCHEMY_DATABASE_URI = 'sqlite:///testing.db'
    DEBUG = True
    CACHE_TYPE = 'SimpleCache'

class ProdConfig:
    SQLALCHEMY_DATABASE_URI = os.environ.get('SQLALCHEMY_DATABASE_URI')
    CACHE_TYPE = "SimpleCache"