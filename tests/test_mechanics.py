from Application import create_app
from Application.models import  db, Mechanics, Customers, Service_Mechanics, Service_Tickets
from datetime import datetime
from Application.utils.token_utils import encode_token
import unittest, json, sys, os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class TestMechanic(unittest.TestCase):
    def setUp(self):
        """Set up client and database before each test"""
        self.app = create_app("TestConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all tables
        db.create_all()
        self.client = self.app.test_client()

        # Create test mechanic
        self.test_mech1 = {
            "name": "Tom Jones",
            "email": "tj@mech_shop.com",
            "phone": "777-888-9999",
            "salary": 75000.0
        }

        self.test_mech2 = {
            "name": "Jacob Thomas",
            "email": "jt_nottom@mech_shop.com",
            "phone": "666-999-5555",
            "salary": 65000.00
        }

        # Persist the test mechanic item to the database so the tests can succeed
        test_mechanic1 = Mechanics(
            name = self.test_mech1['name'],
            email = self.test_mech1['email'],
            phone = self.test_mech1['phone'],
            salary = self.test_mech1['salary']
        )

        test_mechanic2 = Mechanics(
            name = self.test_mech2['name'],
            email = self.test_mech2['email'],
            phone = self.test_mech2['phone'],
            salary = self.test_mech2['salary']
        )

        db.session.add_all([test_mechanic1, test_mechanic2])
        db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        try:
            db.session.close()
            db.drop_all()
            self.app_context.pop()
        except Exception as e:
            print(f"Teardown warning: {e}")

    # Test creating a new mechanic
    def test_create_mechanic(self):
        payload = {
            "name": "Abel Blood",
            "email": "AB-positive@mech_shop.com",
            "phone": "222-555-8979",
            "salary": 70500.00
        }

        response = self.client.post('/mechanics', data=json.dumps(payload),
                                    content_type='application/json')
        self.assertEqual(response.status_code, 201)

        # Parse JSON response
        response_data = json.loads(response.data)
        self.assertEqual(response_data['name'], "Abel Blood")
        self.assertEqual(response_data['email'], "AB-positive@mech_shop.com")

    # Get all mechanics test
    def test_get_all_mechanics(self):
        response = self.client.get('/mechanics')
        self.assertEqual(response.status_code, 200)
        mechanics = response.json
        self.assertIsInstance(mechanics, list)
        self.assertGreaterEqual(len(mechanics), 2)
        self.assertEqual(mechanics[0]['name'], 'Tom Jones')
    
    # Updates a specific mechanic
    def test_update_specific_mechanic(self):
        """Test updating a mechanic"""
        # First, get an existing mechanic
        all_response = self.client.get('/mechanics')
        self.assertEqual(all_response.status_code, 200)
        all_items = all_response.json
        self.assertGreaterEqual(len(all_items), 1)
        mechanic_id = all_items[0]['id']

        # Update payload
        update_payload = {
            "name": "Tom Jacob Jones",
            "email": "tj@mech_shop.com",
            "phone": "777-888-9999",
            "salary": 75500.0
        }

        # Send PUT to the correct route
        response = self.client.put(
            f'/mechanics/{mechanic_id}',
            data=json.dumps(update_payload),
            content_type='application/json'
        )

        # Assert response
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json['name'], "Tom Jacob Jones")
        self.assertAlmostEqual(float(response.json['salary']), 75500.0, places=2)

        # Verify persistence
        mech = db.session.get(Mechanics, mechanic_id)
        self.assertIsNotNone(mech)
        self.assertEqual(mech.name, "Tom Jacob Jones")
        self.assertAlmostEqual(float(mech.salary), 75500.0, places=2)
    
    # Delete specific mechanic based on ID
    def test_delete_mechanic(self):
        # Pick an existing mechanic id
        all_resp = self.client.get('/mechanics')
        self.assertEqual(all_resp.status_code, 200)
        mechanics = all_resp.json
        self.assertGreaterEqual(len(mechanics), 1)
        mech_id = mechanics[0]['id']

        # Delete mechanic
        resp = self.client.delete(f'/mechanics/{mech_id}')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('message', resp.json)

        # Assert deletion
        self.assertIsNone(db.session.get(Mechanics, mech_id))