from Application import create_app
from Application.models import  db, Mechanics, Customers, Service_Mechanics, Service_Tickets
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
    def get_all_tickets(self):
        response = self.client.get('/service-tickets')
        self.assertEqual(response.status_code, 200)
        tickets = response.json
        self.assertIsInstance(tickets, list)
        self.assertGreaterEqual(len(tickets), 1)
        self.assertEqual(tickets[0]['VIN'], "A8E7W8U2")