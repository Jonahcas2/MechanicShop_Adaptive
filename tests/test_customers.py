from Application import create_app
from Application.models import  db, Customers
from datetime import datetime
from Application.utils.token_utils import encode_token
import unittest, json, sys, os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class TestCustomer(unittest.TestCase):
    def setUp(self):
        """Set up test client and database before each test"""
        self.app = create_app("TestConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all tables
        db.create_all()
        self.client = self.app.test_client()

        # Create test customer for login
        self.test_customer_data = {
            "name": "Test User",
            "email": "test@email.com",
            "phone": "123-456-7890",
            "password": "testpass"
        }
        # Persist the test customer to the database so login can succeed
        test_customer = Customers(
            name=self.test_customer_data['name'],
            email=self.test_customer_data['email'],
            phone=self.test_customer_data['phone']
        )
        test_customer.set_password(self.test_customer_data['password'])
        db.session.add(test_customer)
        db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        try:
            db.session.close()
            db.drop_all()
            self.app_context.pop()
        except Exception as e:
            print(f"Teardown warning: {e}")

    # Customer creation test
    def test_create_customer(self):
        customer_payload= {
            "name": "John Doe",
            "email": "JD@email.com",
            "phone": "444-789-4598",
            "password": "securepassword143"
        }

        response = self.client.post('/customers', data=json.dumps(customer_payload),
                                    content_type='application/json')
        
        self.assertEqual(response.status_code, 201)

        # Parse JSON response
        response_data = json.loads(response.data)
        self.assertEqual(response_data['name'], "John Doe")
        self.assertEqual(response_data['email'], "JD@email.com")
        #Password should not be in response (load_only=True)
        self.assertNotIn('password', response_data)

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
        self.assertEqual(response.status_code, 401)
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