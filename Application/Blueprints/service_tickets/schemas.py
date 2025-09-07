from Application.extensions import ma
from Application.models import Service_Tickets

class Service_TicketSchema(ma.SQLAlchemyAutoSchema):
    class Meta:
        model = Service_Tickets
        load_instance = True
        include_relationships = False

ticket_schema = Service_TicketSchema()
tickets_schema = Service_TicketSchema(many=True)