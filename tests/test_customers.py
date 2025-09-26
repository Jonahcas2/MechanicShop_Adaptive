from Application import create_app
from Application.models import  db, Customers
from datetime import datetime
from Application.utils.token_utils import encode_token
import unittest

class TestCustomer(unittest.TestCase):
    def setUp(self):
        self.app = create_app("TestConfig")
        self.customer = Customers(name="test_user", email="test@email.com", phone="888-999-1010", password="testpass")
        with self.app.app_context():
            db.drop_all()
            db.create_all()
            self.customer.set_password(self.customer.password)
            db.session.add(self.customer)
            db.session.commit()
        self.token = encode_token(1)
        self.client = self.app.test_client()

    # Customer creation test
    def test_create_customer(self):
        customer_payload= {
            "name": "John Doe",
            "email": "JD@email.com",
            "phone": "444-789-4598",
            "password": "securepassword143"
        }

        response = self.client.post('/customers', json=customer_payload)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json['name'],"John Doe")

    # Invalid Customer creation test
    def test_invalid_creation(self):
        customer_payload = {
            "name": "John Doe",
            "phone": "444-789-4598",
            "password": "securepassword143"
        }

        response = self.client.post('/customers', json=customer_payload)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['email'],['Missing data for required field.'])
    
    # Customer Login test
    def test_login_customer(self):
        credentials = {
            "email": "test@email.com",
            "password": "testpass"
        }

        response = self.client.post('/customers/login', json=credentials)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['status'], 'success')
        return response.json['token']
    
    # Invalid Customer Login Test
    def test_invalid_login(self):
        credentials = {
            "email": "bad_email@email.com",
            "password": "bad_passwd"
        }

        response = self.client.post('/customers/login', json=credentials)
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.json['message'], 'Invalid email or password!')
    
    # Token authentication update
    def test_update_customer(self):
        update_payload ={
            "name": "Peter",
            "phone": "",
            "email":"",
            "password": ""
        }

        headers = {'Authorization': "Bearer " + self.test_login_customer()}

        response = self.client.put('/customers', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], 'Peter')
        self.assertEqual(response.json['email'], 'test@email.com')