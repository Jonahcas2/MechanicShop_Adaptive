from Application import create_app
from Application.models import  db
import unittest

class TestCustomer(unittest.TestCase):
    def setUp(self):
        self.app = create_app("TestConfig")
        with self.app.app_context():
            db.drop_all()
            db.create_all()
        self.client = self.app.test_client()

    def test_create_customer(self):
        customer_payload= {
            "name": "John Doe",
            "email": "JD@email.com",
            "phone": "444-789-4598",
            "password": "securepassword143"
        }

        response = self.client.post('/customers/', json=customer_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'],"John Doe")