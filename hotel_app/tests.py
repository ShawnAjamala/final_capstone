import os

from django.test import TestCase
from rest_framework.test import APIClient

from django.contrib.auth.models import User
from hotel_app.models import UserProfile


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


class SuperuserRoleTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def authenticate_as_superuser(self, user):
        response = self.client.post(
            '/api/auth/login/',
            {'username': user.username, 'password': 'StrongPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['user']['role'], 'admin')
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Bearer {response.data['tokens']['access']}"
        )

    def test_superuser_without_profile_is_admin(self):
        user = User.objects.create_superuser(
            username='root', email='root@example.com', password='StrongPass123!'
        )

        self.authenticate_as_superuser(user)

        self.assertEqual(self.client.get('/api/admin/dashboard/').status_code, 200)
        self.assertEqual(self.client.get('/api/guest/dashboard/').status_code, 403)
        self.assertEqual(
            self.client.get('/api/auth/me/').data['user']['role'], 'admin'
        )

    def test_superuser_with_guest_profile_is_still_admin(self):
        user = User.objects.create_superuser(
            username='root-with-profile',
            email='root-with-profile@example.com',
            password='StrongPass123!',
        )
        UserProfile.objects.create(user=user, role='guest', is_approved=False)

        self.authenticate_as_superuser(user)

        self.assertEqual(self.client.get('/api/admin/dashboard/').status_code, 200)
        self.assertEqual(self.client.get('/api/guest/dashboard/').status_code, 403)
