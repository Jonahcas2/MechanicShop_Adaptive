from Application.extensions import ma
from Application.models import Inventory, Service_Inventory
from marshmallow import fields

class InventorySchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Inventory
        load_instance = True
        include_relationships = False

class ServiceInventorySchema(ma.SQLAlchemyAutoSchema):
    inventory_id = ma.Integer(required=True)
    quantity = ma.Integer(missing=1)

    class Meta:
        model = Service_Inventory
        load_instance = True
        include_relationships = False

inventory_schema = InventorySchema()
inventories_schema = InventorySchema(many=True)
service_inventory_schema = ServiceInventorySchema()