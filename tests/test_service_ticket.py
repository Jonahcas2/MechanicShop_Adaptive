from Application import create_app
from Application.models import  db, Mechanics, Customers, Service_Mechanics, Service_Tickets
from datetime import datetime
from Application.utils.token_utils import encode_token
import unittest, json, sys, os

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
            "VIN": "",
            "service_date": "2023-10-06",
            "service_desc": "Test ticket 2"
        }

        # Persist the test tickets so the tests can succeed
        