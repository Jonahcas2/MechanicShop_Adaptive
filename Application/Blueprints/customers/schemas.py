from Application.extensions import ma
from Application.models import Customers
from marshmallow import fields

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    password = fields.Str(load_only=True, required=True)

    class Meta:
        model = Customers
        load_instance = True
        include_relationships = False

class LoginSchema(ma.Schema):
    email = fields.Email(required=True)
    password = fields.Str(required=True)

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)
login_schema = LoginSchema()