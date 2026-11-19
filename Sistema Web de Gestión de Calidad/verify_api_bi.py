import unittest
import sys
import os

# Ensure we can import from the current directory
sys.path.append(os.getcwd())

try:
    from main import app
except ImportError:
    # Fallback/Mock if main.py has issues being imported directly
    # But better to try real import first.
    print("Could not import app from main.py")
    sys.exit(1)

class TestPowerBIAuth(unittest.TestCase):
    def setUp(self):
        self.app = app.test_client()
        self.app.testing = True
        # Ensure we use the default if not set
        self.api_key = os.getenv('POWERBI_API_KEY', '')  # Configura POWERBI_API_KEY en tu .env

    def test_no_auth(self):
        """Test connection without any credentials"""
        response = self.app.get('/api/bi/subprocesos')
        self.assertEqual(response.status_code, 401)

    def test_query_key(self):
        """Test ?key=..."""
        response = self.app.get(f'/api/bi/subprocesos?key={self.api_key}')
        # We accept 200 (Success) or 500 (DB Error), just NOT 401 for valid key
        self.assertIn(response.status_code, [200, 500])

    def test_query_api_key(self):
        """Test ?api_key=..."""
        response = self.app.get(f'/api/bi/subprocesos?api_key={self.api_key}')
        self.assertIn(response.status_code, [200, 500])

    def test_header_api_key(self):
        """Test Header: ApiKey"""
        response = self.app.get('/api/bi/subprocesos', headers={'ApiKey': self.api_key})
        self.assertIn(response.status_code, [200, 500])
    
    def test_header_x_api_key(self):
        """Test Header: X-API-KEY"""
        response = self.app.get('/api/bi/subprocesos', headers={'X-API-KEY': self.api_key})
        self.assertIn(response.status_code, [200, 500])

    def test_header_bearer(self):
        """Test Header: Authorization: Bearer ..."""
        response = self.app.get('/api/bi/subprocesos', headers={'Authorization': f'Bearer {self.api_key}'})
        self.assertIn(response.status_code, [200, 500])

if __name__ == '__main__':
    unittest.main(verbosity=2)
