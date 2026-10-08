import os

from django.test import TestCase
from rest_framework.test import APIClient

from django.contrib.auth.models import User


class EndpointProtectionTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_admin_dashboard_requires_authentication(self):
        response = self.client.get('/api/admin/dashboard/')
        self.assertEqual(response.status_code, 401)

    def test_create_admin_route_requires_bootstrap_secret(self):
        os.environ['BOOTSTRAP_ADMIN_SECRET'] = 'test-secret'
        response = self.client.post(
            '/api/auth/create-admin/',
            {'username': 'newadmin', 'email': 'newadmin@example.com', 'password': 'StrongPass123!'},
            format='json',
            HTTP_X_ADMIN_BOOTSTRAP_KEY='wrong-secret',
        )

        self.assertEqual(response.status_code, 403)
        self.assertFalse(User.objects.filter(username='newadmin').exists())

    def tearDown(self):
        os.environ.pop('BOOTSTRAP_ADMIN_SECRET', None)
