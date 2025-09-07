from .schemas import ticket_schema, tickets_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select
from Application.models import Service_Tickets

# POST '' - Passes in required information to create a service ticket



# PUT '/<ticket_id>/assign-mechanic/<mechanic-id>' -  
#       Adds a relationship between a service ticket and a mechanic (use relationship attributes)



# PUT '/<ticket_id>/remove-mechanic/<mechanic-id>' - Removes the relationship from the service ticket & mechanic.



# GET '' - Retrieves all service tickets