from flask import Flask
from sqlalchemy import ForeignKey
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Create a base class for the modules
class Base(DeclarativeBase):
    pass

# Instantiate the SQLAlchemy db
db = SQLAlchemy(model_class=Base)

# Create Customer table
class Customers(Base):
    __tablename__ = 'customers'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)

    # Relationship: One customer can have many service tickets
    service_tickets: Mapped[list["Service_Tickets"]] = relationship("Service_Tickets", back_populates="customer")

# Service Tickets table
class Service_Tickets(Base):
    __tablename__ = 'service_tickets'

    id: Mapped[int] = mapped_column(primary_key=True)
    VIN: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    service_date: Mapped[str] = mapped_column(db.String(360), nullable=False)
    service_desc: Mapped[str] = mapped_column(db.String(255), nullable=False)
    customer_id: Mapped[int] = mapped_column(nullable=False)

    # ForeignKey Constraint
    customer_id: Mapped[int] = mapped_column(ForeignKey('customers.id'), nullable=False)

    # Relationships
    customer: Mapped["Customers"] = relationship("Customers", back_populates="service_tickets")
    service_mechanics: Mapped[list["Service_Mechanics"]] = relationship("Service_Mechanics", back_populates="ticket")

# Service Mechanics table (Junction table for many-to-many relationship)
class Service_Mechanics(Base):
    __tablename__ = 'service_mechanics'

    ticket_id: Mapped[int] = mapped_column(primary_key=True)
    mechanic_id: Mapped[int] = mapped_column(primary_key=True)

    # ForeignKey Constraints
    ticket_id: Mapped[int] = mapped_column(ForeignKey('service_tickets.id'), primary_key=True)
    mechanic_id: Mapped[int] = mapped_column(ForeignKey('mechanics.id'), primary_key=True)

    # Relationships
    ticket: Mapped["Service_Tickets"] = relationship("Service_Tickets", back_populates="service_mechanics")
    mechanics: Mapped["Mechanics"] = relationship("Mechanics", back_populates="service_mechanics")

# Mechanics table
class Mechanics(Base):
    __tablename__ = 'mechanics'

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    salary: Mapped[float] = mapped_column(nullable=False)

    # Relationship: One mechanic can work on many service tickets
    service_mechanics: Mapped[list["Service_Mechanics"]] = relationship("Service_Mechanics", back_populates="mechanics")