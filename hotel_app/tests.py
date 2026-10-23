import os
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from rest_framework.test import APIClient

from django.contrib.auth.models import User
from hotel_app.models import Booking, MpesaTransaction, Room, UserProfile
from hotel_app.mpesa import MPESA_CALLBACK_URL


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


class RoleAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_guest_cannot_open_staff_or_admin_dashboards(self):
        user = User.objects.create_user(username='guest', password='pass12345')
        UserProfile.objects.create(user=user, role='guest', is_approved=True)
        self.client.force_authenticate(user=user)

        self.assertEqual(self.client.get('/api/guest/dashboard/').status_code, 200)
        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code, 403)
        self.assertEqual(self.client.get('/api/admin/dashboard/').status_code, 403)

    def test_staff_cannot_open_guest_or_admin_dashboards(self):
        user = User.objects.create_user(username='staff', password='pass12345')
        UserProfile.objects.create(user=user, role='staff', is_approved=True)
        self.client.force_authenticate(user=user)

        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code, 200)
        self.assertEqual(self.client.get('/api/guest/dashboard/').status_code, 403)
        self.assertEqual(self.client.get('/api/admin/dashboard/').status_code, 403)

    def test_admin_cannot_open_guest_or_staff_dashboards(self):
        user = User.objects.create_user(username='admin', password='pass12345')
        UserProfile.objects.create(user=user, role='admin', is_approved=True)
        self.client.force_authenticate(user=user)

        self.assertEqual(self.client.get('/api/admin/dashboard/').status_code, 200)
        self.assertEqual(self.client.get('/api/guest/dashboard/').status_code, 403)
        self.assertEqual(self.client.get('/api/staff/dashboard/').status_code, 403)


class MpesaEndpointAccessTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.guest = User.objects.create_user(
            username='paying-guest', password='pass12345'
        )
        UserProfile.objects.create(user=self.guest, role='guest', is_approved=True)
        self.room = Room.objects.create(
            room_number='101',
            room_type='single',
            price_per_night=Decimal('120.00'),
            max_guests=2,
        )
        self.booking = Booking.objects.create(
            guest=self.guest,
            room=self.room,
            check_in='2026-11-01',
            check_out='2026-11-02',
            guests=1,
            total_price=Decimal('120.00'),
        )

    def test_stk_push_callback_uses_render_backend(self):
        self.assertEqual(
            MPESA_CALLBACK_URL,
            'https://final-capstone-lt3j.onrender.com/api/mpesa/callback/',
        )

    def test_payment_endpoints_require_login(self):
        response = self.client.post(
            '/api/mpesa/pay/',
            {'booking_id': f'BK-{self.booking.id}', 'phone_number': '0712345678'},
            format='json',
        )
        self.assertEqual(response.status_code, 401)
        self.assertEqual(
            self.client.get('/api/mpesa/status/not-a-checkout-id/').status_code,
            401,
        )

    @patch('hotel_app.views.initiate_stk_push')
    def test_guest_can_pay_only_own_pending_booking_and_amount_is_server_calculated(
        self, initiate_stk_push
    ):
        initiate_stk_push.return_value = {
            'ResponseCode': '0',
            'CheckoutRequestID': 'checkout-123',
        }
        self.client.force_authenticate(user=self.guest)

        response = self.client.post(
            '/api/mpesa/pay/',
            {
                'booking_id': f'BK-{self.booking.id}',
                'phone_number': '0712345678',
                'amount': 1,
            },
            format='json',
        )

        self.assertEqual(response.status_code, 201)
        initiate_stk_push.assert_called_once_with(
            phone_number='0712345678',
            amount=Decimal('120.00'),
            account_reference=f'BK-{self.booking.id}',
            transaction_desc='Hotel booking payment',
        )
        transaction = MpesaTransaction.objects.get(
            checkout_request_id='checkout-123'
        )
        self.assertEqual(transaction.amount, Decimal('120.00'))

    @patch('hotel_app.views.initiate_stk_push')
    def test_guest_cannot_pay_another_users_booking(self, initiate_stk_push):
        other_guest = User.objects.create_user(
            username='other-guest', password='pass12345'
        )
        UserProfile.objects.create(
            user=other_guest, role='guest', is_approved=True
        )
        self.client.force_authenticate(user=other_guest)

        response = self.client.post(
            '/api/mpesa/pay/',
            {
                'booking_id': f'BK-{self.booking.id}',
                'phone_number': '0712345678',
            },
            format='json',
        )

        self.assertEqual(response.status_code, 404)
        initiate_stk_push.assert_not_called()

    def test_payment_status_is_private_to_booking_owner(self):
        transaction = MpesaTransaction.objects.create(
            checkout_request_id='checkout-private',
            phone_number='254712345678',
            amount=Decimal('120.00'),
            reference=f'BK-{self.booking.id}',
        )
        other_guest = User.objects.create_user(
            username='other-status-guest', password='pass12345'
        )
        UserProfile.objects.create(
            user=other_guest, role='guest', is_approved=True
        )
        self.client.force_authenticate(user=other_guest)

        response = self.client.get(
            f'/api/mpesa/status/{transaction.checkout_request_id}/'
        )

        self.assertEqual(response.status_code, 404)

        self.client.force_authenticate(user=self.guest)
        response = self.client.get(
            f'/api/mpesa/status/{transaction.checkout_request_id}/'
        )
        self.assertEqual(response.status_code, 200)
        self.assertNotIn('phone_number', response.data)

    @patch('hotel_app.views.query_stk_push')
    def test_callback_only_confirms_after_daraja_verifies_payment(
        self, query_stk_push
    ):
        transaction = MpesaTransaction.objects.create(
            checkout_request_id='checkout-callback',
            phone_number='254712345678',
            amount=Decimal('120.00'),
            reference=f'BK-{self.booking.id}',
        )
        query_stk_push.return_value = {'ResponseCode': '0', 'ResultCode': '1032'}
        callback = {
            'Body': {
                'stkCallback': {
                    'CheckoutRequestID': transaction.checkout_request_id,
                    'ResultCode': 0,
                    'ResultDesc': 'Payment complete',
                    'CallbackMetadata': {
                        'Item': [{'Name': 'MpesaReceiptNumber', 'Value': 'ABC123'}]
                    },
                }
            }
        }

        response = self.client.post(
            '/api/mpesa/callback/',
            callback,
            format='json',
        )

        self.booking.refresh_from_db()
        transaction.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.booking.payment_status, 'unpaid')
        self.assertEqual(transaction.status, 'Pending')

        query_stk_push.return_value = {'ResponseCode': '0', 'ResultCode': '0'}
        response = self.client.post(
            '/api/mpesa/callback/',
            callback,
            format='json',
        )

        self.booking.refresh_from_db()
        transaction.refresh_from_db()
        self.assertEqual(response.status_code, 200)
        self.assertEqual(self.booking.payment_status, 'paid')
        self.assertEqual(transaction.status, 'Completed')
