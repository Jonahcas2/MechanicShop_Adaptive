from .schemas import ticket_schema, tickets_schema
from flask import request, jsonify, Blueprint
from marshmallow import ValidationError
from sqlalchemy import select
from Application.models import Service_Tickets, Mechanics, Service_Mechanics, Inventory, Service_Inventory, db
from Application.extensions import limiter, cache
from Application.utils.cache_utils import cache_response

tickets_bp = Blueprint('service_tickets', __name__, url_prefix='/service-tickets')

# POST '' - Passes in required information to create a service ticket
@tickets_bp.route('', methods=['POST'])
@limiter.limit("5 per minute")
def create_ticket():
    try:
        ticket_data = ticket_schema.load(request.json)
    except ValidationError as e:
        return jsonify(e.messages), 400
    
    query = select(Service_Tickets).where(Service_Tickets.VIN == ticket_data.VIN)
    existing_ticket = db.session.execute(query).scalars().all()
    if existing_ticket:
        return jsonify({"error": "VIN already associated with a service ticket"}), 400
    
    db.session.add(ticket_data)
    db.session.commit()

    cache.delete_memoized(getAll_tickets)

    return ticket_schema.jsonify(ticket_data), 201


# PUT '/<ticket_id>/assign-mechanic/<mechanic-id>' -  
#       Adds a relationship between a service ticket and a mechanic (use relationship attributes)
@tickets_bp.route('/<int:ticket_id>/assign-mechanic/<int:mechanic_id>', methods=['PUT'])
@limiter.limit("10 per minute")
def assign_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    mechanic = db.session.get(Mechanics, mechanic_id)

    if not ticket:
        return jsonify({"error": "Service Ticket not found"}), 404
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404

    # Check if the relationship already exists
    existing_relationship = db.session.execute(
        select(Service_Mechanics).where(
            Service_Mechanics.ticket_id == ticket_id,
            Service_Mechanics.mechanic_id == mechanic_id
        )
    ).scalars().first()

    if existing_relationship:
        return jsonify({"error": "Mechanic already assigned to this service ticket"}), 400

    # Create the relationship
    service_mechanic = Service_Mechanics(ticket_id=ticket_id, mechanic_id=mechanic_id)
    db.session.add(service_mechanic)
    db.session.commit()

    cache.delete_memoized(getAll_tickets)

    return jsonify({"message": f"Mechanic id: {mechanic_id} assigned to Service Ticket id: {ticket_id}"}), 200


# PUT '/<ticket_id>/remove-mechanic/<mechanic-id>' - Removes the relationship from the service ticket & mechanic.
@tickets_bp.route('/<int:ticket_id>/remove-mechanic/<int:mechanic_id>', methods=['PUT'])
@limiter.limit("10 per minute")
def remove_mechanic(ticket_id, mechanic_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    mechanic = db.session.get(Mechanics, mechanic_id)

    if not ticket:
        return jsonify({"error": "Service Ticket not found"}), 404
    if not mechanic:
        return jsonify({"error": "Mechanic not found"}), 404

    # Find the relationship
    service_mechanic = db.session.execute(
        select(Service_Mechanics).where(
            Service_Mechanics.ticket_id == ticket_id,
            Service_Mechanics.mechanic_id == mechanic_id
        )
    ).scalars().first()

    if not service_mechanic:
        return jsonify({"error": "Mechanic is not assigned to this service ticket"}), 400

    # Remove the relationship
    db.session.delete(service_mechanic)
    db.session.commit()

    cache.delete_memoized(getAll_tickets)

    return jsonify({"message": f"Mechanic id: {mechanic_id} removed from Service Ticket id: {ticket_id}"}), 200

# GET '' - Retrieves all service tickets
@tickets_bp.route('', methods=['GET'])
@limiter.limit("15 per minute")
@cache_response(timeout=300)
def getAll_tickets():
    query = select(Service_Tickets)
    tickets = db.session.execute(query).scalars().all()

    return tickets_schema.jsonify(tickets)

# PUT '/<int:ticket_id>/edit' - Add and remove mechanics from service ticket
@tickets_bp.route('<int:ticket_id>/edit', methods=['PUT'])
@limiter.limit("5 per minute")
def edit_ticket_mechanics(ticket_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"error": "Service Ticket not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "No data provided"}), 400
    
    remove_ids = data.get('remove_ids', [])
    add_ids = data.get('add_ids', [])

    # Remove mechanics
    if remove_ids:
        for mechanic_id in remove_ids:
            # Find the relationship
            service_mechanic = db.session.execute(
                select(Service_Mechanics).where(
                    Service_Mechanics.ticket_id == ticket_id,
                    Service_Mechanics.mechanic_id == mechanic_id,
                )
            ).scalars().first()

            if service_mechanic:
                db.session.delete(service_mechanic)
    
    # Add mechanics
    if add_ids:
        for mechanic_id in add_ids:
            # Verify mechanic exists
            mechanic = db.session.getZ(Mechanics, mechanic_id)
            if not mechanic:
                return jsonify({"error": f"Mechanic with id {mechanic_id} not found"}), 404
            
            # Check if relationship already exists
            existing_relationship = db.session.execute(
                select(Service_Mechanics).where(
                    Service_Mechanics.ticket_id == ticket_id,
                    Service_Mechanics.mechanic_id == mechanic_id
                )
            ).scalars().first()

            if not existing_relationship:
                service_mechanic = Service_Mechanics(ticket_id=ticket_id, mechanic_id=mechanic_id)
                db.session.add(service_mechanic)
    
    db.session.commit()
    cache.delete_memoized(getAll_tickets)

    return jsonify({
        "message": f"Ticket {ticket_id} mechanics updated successfully",
        "removed_mechanics": remove_ids,
        "added_mechanics": add_ids
    }), 200

# POST '/<int:ticket_id>/add-part' - Add a part to the service ticket
@tickets_bp.route('/int:ticket_id>/add-part', methods=['POST'])
@limiter.limit("10 per minute")
def add_part_to_ticket(ticket_id):
    ticket = db.session.get(Service_Tickets, ticket_id)
    if not ticket:
        return jsonify({"error": "Service Ticket not found"}), 404
    
    data = request.get_json()
    if not data:
        return jsonify({"error": "inventory_id is required"}), 400
    
    inventory_id = db.session.get(Inventory, inventory_id)
    quantity = data.get('quantity', 1)

    if not inventory_id:
        return jsonify({"error": "inventory_id is required"}), 400
    
    inventory_item = db.session.get(Inventory, inventory_id)
    if not inventory_item:
        return jsonify({"error": "Inventory item not found"})
    
    # Check if this part is already associated with the ticket
    existing_relationship = db.session.execute(
        select(Service_Inventory).where(
            Service_Inventory.ticket_id == ticket_id,
            Service_Inventory.inventory_id == inventory_id
        )
    ).scalars().first()

    if existing_relationship:
        # Update quantity if relationship exists
        existing_relationship.quantity += quantity
        message = f"Updated quantity for part '{inventory_item.name}' on ticket {ticket_id}"
    else:
        # Create new relationship
        service_inventory = Service_Inventory(
            ticket_id=ticket_id,
            inventory_id=inventory_id,
            quantity=quantity
        )
        db.session.add(service_inventory)
        message = f"Added part '{inventory_item.name}' to ticket {ticket_id}"

    db.session.commit()
    cache.delete_memoized(getAll_tickets)

    return jsonify({
        "message": message,
        "part_name": inventory_item.name,
        "quantity": quantity,
        "part_price": inventory_item.price
    }), 200


# Error handling
@tickets_bp.errorhandler(429)
def ratelimit_handler(e):
    return jsonify(error="Rate limit exceeded", message=str(e.description)), 429