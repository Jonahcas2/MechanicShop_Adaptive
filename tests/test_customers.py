from Application import create_app
from Application.models import  db, Customers, Service_Tickets
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

    # Get all customers test
    def test_get_all_customers(self):
        response = self.client.get('/customers')
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json, dict)
        customers = response.json.get('customers')
        self.assertIsInstance(customers, list)
        self.assertGreaterEqual(len(customers), 1)
        self.assertEqual(customers[0]['email'], 'test@email.com')
        self.assertNotIn('password', customers[0])
    
    # Get specific customer test
    def test_get_customer_by_id(self):
        # First, get all customers to find a valid ID
        all_response = self.client.get('/customers')
        self.assertEqual(all_response.status_code, 200)
        customers = all_response.json.get('customers')
        self.assertGreaterEqual(len(customers), 1)
        customer_id = customers[0]['id']

        # Now, get the specific customer by ID
        response = self.client.get(f'/customers/{customer_id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['id'], customer_id)
        self.assertEqual(response.json['email'], 'test@email.com')
        self.assertNotIn('password', response.json)

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
    
    # Invalid token update
    def test_invalid_customer_update(self):
        update_payload = {
            "name": "Peter",
            "phone": "",
            "email": "",
            "password": ""
        }

        headers = {'Authorization': "Bearer " + "BAD_TOKEN"}
        response = self.client.put('/customers', json=update_payload, headers=headers)
        self.assertEqual(response.status_code, 401)
        self.assertEqual(response.json['error'], 'Invalid or expired token')

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
    
    # Get service tickets for logged-in customer test
    

    # Delete customer test
    def test_delete_customer(self):
        # First, get all customers to find a valid ID
        all_response = self.client.get('/customers')
        self.assertEqual(all_response.status_code, 200)
        customers = all_response.json.get('customers')
        self.assertGreaterEqual(len(customers), 1)
        customer_id = customers[0]['id']

        # Now, delete the specific customer by ID
        response = self.client.delete(f'/customers/{customer_id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn('successfully deleted', response.json['message'])
        # Verify customer is actually deleted
        follow_up = self.client.get(f'/customers/{customer_id}')
        self.assertEqual(follow_up.status_code, 404)
        self.assertIn('Customer not found', follow_up.json['error'])
    
        