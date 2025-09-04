from Application.extensions import ma
from Application.models import Customers

class CustomerSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Customers
        load_instance = True
        include_relationships = False

customer_schema = CustomerSchema()
customers_schema = CustomerSchema(many=True)