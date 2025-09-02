from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+mysqlconnector://root:<YOUR MYSQL PASSWORD>@localhost/<YOUR DATABASE>'

# Create a base class for the modules
class Base(DeclarativeBase):
    pass

# Instantiate the SQLAlchemy db
db = SQLAlchemy(model_class=Base)
db.init_app(app)

# Create Customer table
class Customers(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)

# Service Tickets table
class Service_Tickets(Base):
    __tablename__ = 'service_tickets'

    id: Mapped[int] = mapped_column(primary_key=True)
    VIN: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    service_date: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    service_desc: Mapped[str] = mapped_column(db.String(255), nullable=False)
    customer_id: Mapped[int] = mapped_column(nullable=False)

# Service Mechanics table
class Service_Mechanics(Base):
    __tablename__ = 'service_mechanics'

    ticket_id: Mapped[int] = mapped_column(primary_key=True)
    mechanic_id: Mapped[int] = mapped_column(primary_key=True)

# Mechanics table
class Mechanics(Base):
    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    salary: Mapped[float] = mapped_column(nullable=False)


# Create the table
with app.app_context():
    db.create_all()

app.run()