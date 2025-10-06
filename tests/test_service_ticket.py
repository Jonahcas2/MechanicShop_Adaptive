from Application import create_app
from Application.models import  db, Mechanics, Customers, Service_Mechanics, Service_Tickets, Inventory, Service_Inventory
from datetime import datetime
from Application.utils.token_utils import encode_token
import unittest, json, sys, os
from sqlalchemy import select

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class TestServiceTickets(unittest.TestCase):
    def setUp(self):
        """Set up client and database before each test"""
        self.app = create_app("TestConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all tables
        db.create_all()
        self.client = self.app.test_client()

        # Create test Service Tickets
        self.test_ticket1 = {
            "VIN": "A8E7W8U2",
            "service_date": "2022-09-05",
            "service_desc": "Test ticket #1",
        }

        self.test_ticket2 ={
            "VIN": "C3T2V1N2",
            "service_date": "2023-10-06",
            "service_desc": "Test ticket 2"
        }

        # Persist the test tickets so the tests can succeed
        # Create and persist a customer to satisfy the NOT NULL customer_id FK
        self.test_customer = Customers(name="Ticket Owner", email="ticket@owner.com", phone="999-888-7777", password="placeholder")
        self.test_customer.set_password("placeholder")
        db.session.add(self.test_customer)
        db.session.commit()

        test_ST1 = Service_Tickets(
            VIN=self.test_ticket1['VIN'],
            service_date=self.test_ticket1['service_date'],
            service_desc=self.test_ticket1['service_desc'],
            customer_id=self.test_customer.id
        )

        test_ST2 = Service_Tickets(
            VIN=self.test_ticket2['VIN'],
            service_date=self.test_ticket2['service_date'],
            service_desc=self.test_ticket2['service_desc'],
            customer_id=self.test_customer.id
        )

        db.session.add_all([test_ST1, test_ST2])
        db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        try:
            db.session.close()
            db.drop_all()
            self.app_context.pop()
        except Exception as e:
            print(f"Teardown warning: {e}")

    # Create a new test service ticket
    def test_create_ticket(self):
        payload = {
            "VIN": "B7E9G6H0Q",
            "service_date": "2024-12-12",
            "service_desc": "Test ticket (from method)",
            "customer_id": self.test_customer.id
        }
        # Post to the correct service tickets endpoint
        response = self.client.post('/service-tickets', data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Parse JSON response
        response_data = json.loads(response.data)
        self.assertEqual(response_data['VIN'], "B7E9G6H0Q")
        self.assertEqual(response_data['service_date'], "2024-12-12")
        self.assertEqual(response_data['service_desc'], "Test ticket (from method)")

    # Test to add a relationship between a service ticket and a mechanic
    def test_mechanic_to_ticket(self):
        # Create a customer (FK requirement)
        customer = Customers(name="Assign Cust", email="assigncust@test.com", phone="101-202-3030", password="p@ssw0rd")
        customer.set_password('p@ssw0rd')
        db.session.add(customer)
        db.session.commit()

        # Create a mechanic
        mechanic = Mechanics(name="Assign Mech", email="assignmech@test.com", phone="444-555-6666", salary=60000.0)
        db.session.add(mechanic)
        db.session.commit()

        # Create a ticket for the customer (unique VIN)
        ticket = Service_Tickets(VIN="ASSIGNVIN001", service_date="2025-10-03", service_desc="Assign Test", customer_id=customer.id)
        db.session.add(ticket)
        db.session.commit()

        # Endpoint Call
        resp = self.client.put(f'/service-tickets/{ticket.id}/assign-mechanic/{mechanic.id}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('message', resp.json)

        # Verify relationship
        rel = db.session.execute(
            select(Service_Mechanics).where(
                Service_Mechanics.ticket_id == ticket.id,
                Service_Mechanics.mechanic_id == mechanic.id
            )
        ).scalars().first()
        self.assertIsNotNone(rel)

        # Handle reassignment of mechanic
        resp2 = self.client.put(f'/service-tickets/{ticket.id}/assign-mechanic/{mechanic.id}')
        self.assertEqual(resp2.status_code, 400)

    # Test retrieve all service tickets
    def test_get_all_tickets(self):
        response = self.client.get('/service-tickets')
        self.assertEqual(response.status_code, 200)
        tickets = response.json
        self.assertIsInstance(tickets, list)
        self.assertGreaterEqual(len(tickets), 1)
        self.assertEqual(tickets[0]['VIN'], "A8E7W8U2")

    # Test to add, then remove a mechanic from a service ticket
    def test_add_remove_mechanic(self):
        # Create two test mechanics
        mech1 = Mechanics(name="Edit Mech 1", email="editm1@test.com", phone="700-700-7000", salary=50000.0)
        mech2 = Mechanics(name="Edit Mech 2", email="editm2@test.com", phone="700-700-7001", salary=52000.0)
        db.session.add_all([mech1, mech2])
        db.session.commit()

        # Create a ticket for the existing customer
        ticket = Service_Tickets(
            VIN= f"EDITVIN-{mech1.email}",
            service_date="2025.10.03",
            service_desc="Edit test ticket",
            customer_id=self.test_customer.id 
        )
        db.session.add(ticket)
        db.session.commit()

        # Assign mech1 initially
        initial_rel = Service_Mechanics(ticket_id=ticket.id, mechanic_id=mech1.id)
        db.session.add(initial_rel)
        db.session.commit()

        # Sanity check
        rel_before = db.session.execute(
            select(Service_Mechanics).where(
                Service_Mechanics.ticket_id == ticket.id,
                Service_Mechanics.mechanic_id == mech1.id
            )
        ).scalars().first()
        self.assertIsNotNone(rel_before)

        # Call the endpoints: remove mech1, add mech2
        payload = {"remove_ids": [mech1.id], "add_ids": [mech2.id]}
        resp = self.client.put(f'/service-tickets/{ticket.id}/edit', json=payload)
        self.assertEqual(resp.status_code, 200)
        self.assertIn('message', resp.json)
        self.assertIn('removed_mechanics', resp.json)
        self.assertIn('added_mechanics',resp.json)
        self.assertEqual(resp.json['removed_mechanics'], [mech1.id])
        self.assertEqual(resp.json['added_mechanics'], [mech2.id])

        # Verify DB
        rel_after1 = db.session.execute(
            select(Service_Mechanics).where(
                Service_Mechanics.ticket_id == ticket.id,
                Service_Mechanics.mechanic_id == mech1.id
            )
        ).scalars().first()
        rel_after2 = db.session.execute(
            select(Service_Mechanics).where(
                Service_Mechanics.ticket_id == ticket.id,
                Service_Mechanics.mechanic_id == mech2.id
            )
        ).scalars().first()

        self.assertIsNone(rel_after1, "mechanic 1 should have been removed from the ticket")
        self.assertIsNotNone(rel_after2, "mechanic 2 should have been added to the ticket")

        # Cleanup
        db.session.delete(rel_after2)
        db.session.delete(ticket)
        db.session.delete(ticket)
        db.session.delete(mech1)
        db.session.delete(mech2)
        db.session.commit()

    # Test add a part to a service ticket
    def test_add_part(self):
        # Create an inventory item
        item = Inventory(name="Test Widget", price=19.99)
        db.session.add(item)
        db.session.commit()

        # Create a ticket
        testTicket = Service_Tickets(
            VIN="PARTVIN-001",
            service_date="2025-11-01",
            service_desc="Part add test",
            customer_id=self.test_customer.id
        )
        db.session.add(testTicket)
        db.session.commit()

        # Add part to ticket (quantity 2)
        payload = {"inventory_id": item.id, "quantity": 2}
        resp = self.client.post(f'/service-tickets/{testTicket.id}/add-part',
                                data=json.dumps(payload),
                                content_type='application/json')
        self.assertEqual(resp.status_code, 200)

        data = resp.json
        self.assertIn("message", data)
        self.assertEqual(data.get("part_name"), item.name)
        self.assertEqual(data.get("quantity"), 2)
        self.assertEqual(data.get("part_price"), item.price)

        # Verify DB relationship
        rel = db.session.execute(
            select(Service_Inventory).where(
                Service_Inventory.ticket_id == testTicket.id,
                Service_Inventory.inventory_id == item.id
            )
        ).scalars().first()
        self.assertIsNotNone(rel)
        self.assertEqual(rel.quantity, 2)

        # Post the same part, should increment to 5
        resp2 = self.client.post(f'/service-tickets/{testTicket.id}/add-part',
                                 data=json.dumps({"inventory_id": item.id, "quantity" : 3}),
                                 content_type='application/json')
        self.assertEqual(resp2.status_code, 200)
        self.assertEqual(resp2.json.get("part_name"), item.name)
        self.assertEqual(resp2.json.get("quantity"), 3)

        # Confirm DB updated total
        rel_after = db.session.execute(
            select(Service_Inventory).where(
                Service_Inventory.ticket_id == testTicket.id,
                Service_Inventory.inventory_id == item.id
            )
        ).scalars().first()
        self.assertIsNotNone(rel_after)
        self.assertEqual(rel_after.quantity, 5)