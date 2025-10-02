from Application import create_app
from Application.models import  db, Customers, Inventory
from datetime import datetime
from Application.utils.token_utils import encode_token
import unittest, json, sys, os

# Add project root to Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, project_root)

class TestInventory(unittest.TestCase):
    def setUp(self):
        """Set up client and database before each test"""
        self.app = create_app("TestConfig")
        self.app_context = self.app.app_context()
        self.app_context.push()

        # Create all tables
        db.create_all()
        self.client = self.app.test_client()

        # Create test inventory items
        self.test_item1 = {
            "name": "Oil Change",
            "price": 29.99
        }

        self.test_item2 = {
            "name": "Tire Rotation",
            "price": 49.99
        }

        # Persist the test inventory item to the database so the tests can succeed
        test_inventory1 = Inventory(
            name=self.test_item1['name'],
            price=self.test_item1['price']
        )
        test_inventory2 = Inventory(
            name=self.test_item2['name'],
            price=self.test_item2['price']
        )

        db.session.add_all([test_inventory1, test_inventory2])
        db.session.commit()

    def tearDown(self):
        """Clean up after each test"""
        try:
            db.session.close()
            db.drop_all()
            self.app_context.pop()
        except Exception as e:
            print(f"Teardown warning: {e}")

    # Test creating a new inventory item
    def test_create_inventory_item(self):
        payload = {
            "name": "Motor Oil 5W-30",
            "price": 39.99
        }

        response = self.client.post('/inventory', json=payload)
        self.assertEqual(response.status_code, 201)

        # Response is a Dict with the created item
        self.assertIsInstance(response.json, dict)
        self.assertIn('id', response.json)
        self.assertEqual(response.json['name'], payload['name'])
        # Price is seriaized as num or str
        self.assertAlmostEqual(float(response.json['price']), payload['price'],places=2)

        # Confirm the item was persisted by fetching it back
        item_id = response.json['id']
        get_resp = self.client.get(f'/inventory/{item_id}')
        self.assertEqual(get_resp.status_code, 200)
        self.assertEqual(get_resp.json['name'], payload['name'])
        self.assertAlmostEqual(float(get_resp.json['price']), payload['price'], places=2)

    # Test getting all inventory items
    def test_get_all_inventory_items(self):
        response = self.client.get('/inventory')
        self.assertEqual(response.status_code, 200)
        items = response.json
        self.assertIsInstance(items, list)
        self.assertGreaterEqual(len(items), 1)
        self.assertEqual(items[0]['name'], 'Oil Change')
        self.assertAlmostEqual(items[0]['price'], 29.99, places=2)

    # Test getting a specific inventory item by ID
    def test_get_item_by_id(self):
        # First, get all inventory items to find a valid ID
        all_response = self.client.get('/inventory')
        self.assertEqual(all_response.status_code, 200)
        all_items = all_response.json
        self.assertGreaterEqual(len(all_items), 1)
        item_id = all_items[0]['id']
        item_name = all_items[0]['name']

        # Now, get the specific inventory item by ID
        response = self.client.get(f'/inventory/{item_id}')
        self.assertEqual(response.status_code, 200)
        item = response.json
        self.assertEqual(item['id'], item_id)
        self.assertEqual(item['name'], item_name)
        self.assertAlmostEqual(item['price'], 29.99, places=2)
    
    # Update inventory item test
    def test_update_invItem(self):
        update_payload = {
            
        }
        pass