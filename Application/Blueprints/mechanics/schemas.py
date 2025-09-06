from Application.extensions import ma
from Application.models import Mechanics

class MechanicSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Mechanics
        load_instance = True
        include_relationships = False

mechanic_schema = MechanicSchema()
mechanics_schema = MechanicSchema(many=True)