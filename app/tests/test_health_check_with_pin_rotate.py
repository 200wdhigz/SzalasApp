"""Test to verify that /health endpoint calls rotate_pin_if_due()"""
from __future__ import annotations

import os
import sys
import unittest
from datetime import datetime, timedelta
from unittest.mock import patch, MagicMock

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
os.environ.setdefault(
    'GOOGLE_APPLICATION_CREDENTIALS',
    os.path.join(os.path.dirname(__file__), '..', '..', 'credentials', 'service-account.json'),
)
# Set Authentik config to avoid import errors
os.environ.setdefault('AUTHENTIK_BASE_URL', 'https://authentik.example.local')
os.environ.setdefault('AUTHENTIK_CLIENT_ID', 'test-id')
os.environ.setdefault('AUTHENTIK_CLIENT_SECRET', 'test-secret')


class TestHealthCheckWithPinRotate(unittest.TestCase):
    """Verify that health check endpoint calls rotate_pin_if_due()"""

    def test_health_endpoint_calls_rotate_pin_if_due(self):
        """Test that GET /health triggers rotate_pin_if_due() check"""
        from src import create_app

        with patch('src.auth.rotate_pin_if_due') as mock_rotate:
            # Initialize app - this will trigger import of all blueprints
            app = create_app()

            # Verify the app was created successfully
            self.assertIsNotNone(app)

            with app.test_client() as client:
                # Call health endpoint
                response = client.get('/health')

                # Verify response is successful
                self.assertEqual(response.status_code, 200)
                self.assertEqual(response.json['status'], 'healthy')

                # Verify rotate_pin_if_due was called
                mock_rotate.assert_called_once()


if __name__ == '__main__':
    unittest.main()

