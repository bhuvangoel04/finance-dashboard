"""
Test suite for Finance Dashboard backend.

Run with:  python manage.py test
"""

from decimal import Decimal
from datetime import date

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status

from users.models import User, Role
from records.models import FinancialRecord, RecordType, Category


# ─────────────────────────────────────────────
# Factories / helpers
# ─────────────────────────────────────────────

def make_user(email, role=Role.VIEWER, is_active=True):
    return User.objects.create_user(
        email=email,
        password='Testpass123!',
        first_name='Test',
        last_name='User',
        role=role,
        is_active=is_active,
    )


def make_record(**kwargs):
    defaults = dict(
        amount=Decimal('500.00'),
        record_type=RecordType.INCOME,
        category=Category.SALARY,
        date=date.today(),
        description='Test entry',
    )
    defaults.update(kwargs)
    return FinancialRecord.objects.create(**defaults)


def auth_client(user):
    client = APIClient()
    client.force_authenticate(user=user)
    return client


# ─────────────────────────────────────────────
# Auth Tests
# ─────────────────────────────────────────────

class AuthTests(TestCase):

    def setUp(self):
        self.user = make_user('auth@test.com', role=Role.ADMIN)

    def test_login_success(self):
        res = self.client.post(reverse('token_obtain_pair'), {
            'email': 'auth@test.com',
            'password': 'Testpass123!',
        }, content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('access', res.data)
        self.assertIn('user', res.data)

    def test_login_wrong_password(self):
        res = self.client.post(reverse('token_obtain_pair'), {
            'email': 'auth@test.com',
            'password': 'wrongpassword',
        }, content_type='application/json')
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_inactive_user_cannot_login(self):
        inactive = make_user('inactive@test.com', is_active=False)
        res = self.client.post(reverse('token_obtain_pair'), {
            'email': 'inactive@test.com',
            'password': 'Testpass123!',
        }, content_type='application/json')
        self.assertNotEqual(res.status_code, status.HTTP_200_OK)


# ─────────────────────────────────────────────
# User Management Tests
# ─────────────────────────────────────────────

class UserManagementTests(TestCase):

    def setUp(self):
        self.admin   = make_user('admin@test.com',   role=Role.ADMIN)
        self.viewer  = make_user('viewer@test.com',  role=Role.VIEWER)
        self.analyst = make_user('analyst@test.com', role=Role.ANALYST)

    def test_admin_can_list_users(self):
        client = auth_client(self.admin)
        res = client.get(reverse('user-list-create'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertTrue(res.data['success'])

    def test_viewer_cannot_list_users(self):
        client = auth_client(self.viewer)
        res = client.get(reverse('user-list-create'))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_cannot_list_users(self):
        client = auth_client(self.analyst)
        res = client.get(reverse('user-list-create'))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_create_user(self):
        client = auth_client(self.admin)
        res = client.post(reverse('user-list-create'), {
            'email': 'newuser@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': Role.VIEWER,
            'password': 'Testpass123!',
            'password_confirm': 'Testpass123!',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['role'], Role.VIEWER)

    def test_create_user_password_mismatch(self):
        client = auth_client(self.admin)
        res = client.post(reverse('user-list-create'), {
            'email': 'new2@test.com',
            'first_name': 'New',
            'last_name': 'User',
            'role': Role.VIEWER,
            'password': 'Testpass123!',
            'password_confirm': 'WrongPass999!',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_create_user_duplicate_email(self):
        client = auth_client(self.admin)
        res = client.post(reverse('user-list-create'), {
            'email': 'viewer@test.com',  # already exists
            'first_name': 'Dup',
            'last_name': 'User',
            'role': Role.VIEWER,
            'password': 'Testpass123!',
            'password_confirm': 'Testpass123!',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_admin_can_deactivate_user(self):
        client = auth_client(self.admin)
        res = client.post(reverse('user-deactivate', kwargs={'pk': self.viewer.pk}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.viewer.refresh_from_db()
        self.assertFalse(self.viewer.is_active)

    def test_me_endpoint_returns_own_profile(self):
        client = auth_client(self.viewer)
        res = client.get(reverse('user-me'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['email'], self.viewer.email)


# ─────────────────────────────────────────────
# Financial Records Tests
# ─────────────────────────────────────────────

class FinancialRecordTests(TestCase):

    def setUp(self):
        self.admin   = make_user('admin@test.com',   role=Role.ADMIN)
        self.viewer  = make_user('viewer@test.com',  role=Role.VIEWER)
        self.analyst = make_user('analyst@test.com', role=Role.ANALYST)

        self.record = make_record(
            amount=Decimal('1000.00'),
            record_type=RecordType.INCOME,
            category=Category.SALARY,
            created_by=self.admin,
        )

    def test_viewer_can_list_records(self):
        client = auth_client(self.viewer)
        res = client.get(reverse('record-list-create'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_analyst_can_list_records(self):
        client = auth_client(self.analyst)
        res = client.get(reverse('record-list-create'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)

    def test_admin_can_create_record(self):
        client = auth_client(self.admin)
        res = client.post(reverse('record-list-create'), {
            'amount': '250.00',
            'record_type': 'expense',
            'category': 'food',
            'date': str(date.today()),
            'description': 'Lunch',
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        self.assertEqual(res.data['data']['category'], 'food')

    def test_viewer_cannot_create_record(self):
        client = auth_client(self.viewer)
        res = client.post(reverse('record-list-create'), {
            'amount': '100.00',
            'record_type': 'expense',
            'category': 'food',
            'date': str(date.today()),
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_analyst_cannot_create_record(self):
        client = auth_client(self.analyst)
        res = client.post(reverse('record-list-create'), {
            'amount': '100.00',
            'record_type': 'expense',
            'category': 'food',
            'date': str(date.today()),
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_update_record(self):
        client = auth_client(self.admin)
        res = client.patch(
            reverse('record-detail', kwargs={'pk': self.record.pk}),
            {'description': 'Updated description'},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.record.refresh_from_db()
        self.assertEqual(self.record.description, 'Updated description')

    def test_viewer_cannot_delete_record(self):
        client = auth_client(self.viewer)
        res = client.delete(reverse('record-detail', kwargs={'pk': self.record.pk}))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_delete_record(self):
        client = auth_client(self.admin)
        res = client.delete(reverse('record-detail', kwargs={'pk': self.record.pk}))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertFalse(FinancialRecord.objects.filter(pk=self.record.pk).exists())

    def test_filter_by_record_type(self):
        make_record(record_type=RecordType.EXPENSE, category=Category.FOOD, created_by=self.admin)
        client = auth_client(self.viewer)
        res = client.get(reverse('record-list-create') + '?record_type=expense')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        for item in res.data['data']['results']:
            self.assertEqual(item['record_type'], 'expense')

    def test_negative_amount_rejected(self):
        client = auth_client(self.admin)
        res = client.post(reverse('record-list-create'), {
            'amount': '-50.00',
            'record_type': 'expense',
            'category': 'food',
            'date': str(date.today()),
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_invalid_category_rejected(self):
        client = auth_client(self.admin)
        res = client.post(reverse('record-list-create'), {
            'amount': '50.00',
            'record_type': 'expense',
            'category': 'unicorn',
            'date': str(date.today()),
        }, format='json')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_bulk_delete(self):
        r2 = make_record(created_by=self.admin)
        r3 = make_record(created_by=self.admin)
        client = auth_client(self.admin)
        res = client.post(
            reverse('record-bulk-delete'),
            {'ids': [self.record.pk, r2.pk, r3.pk]},
            format='json',
        )
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertEqual(res.data['data']['deleted_count'], 3)


# ─────────────────────────────────────────────
# Dashboard / Analytics Tests
# ─────────────────────────────────────────────

class DashboardTests(TestCase):

    def setUp(self):
        self.admin   = make_user('admin@test.com',   role=Role.ADMIN)
        self.analyst = make_user('analyst@test.com', role=Role.ANALYST)
        self.viewer  = make_user('viewer@test.com',  role=Role.VIEWER)

        make_record(amount=Decimal('3000'), record_type=RecordType.INCOME,
                    category=Category.SALARY, created_by=self.admin)
        make_record(amount=Decimal('500'),  record_type=RecordType.EXPENSE,
                    category=Category.FOOD, created_by=self.admin)
        make_record(amount=Decimal('200'),  record_type=RecordType.EXPENSE,
                    category=Category.TRANSPORT, created_by=self.admin)

    def test_analyst_can_access_overview(self):
        client = auth_client(self.analyst)
        res = client.get(reverse('dashboard-overview'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        data = res.data['data']
        self.assertEqual(data['total_income'],   Decimal('3000'))
        self.assertEqual(data['total_expenses'], Decimal('700'))
        self.assertEqual(data['net_balance'],    Decimal('2300'))

    def test_viewer_cannot_access_dashboard(self):
        client = auth_client(self.viewer)
        res = client.get(reverse('dashboard-overview'))
        self.assertEqual(res.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_access_full_dashboard(self):
        client = auth_client(self.admin)
        res = client.get(reverse('dashboard-full'))
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn('overview', res.data['data'])
        self.assertIn('recent_activity', res.data['data'])
        self.assertIn('monthly_trends', res.data['data'])

    def test_category_breakdown(self):
        client = auth_client(self.analyst)
        res = client.get(reverse('dashboard-categories') + '?record_type=expense')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        categories = [row['category'] for row in res.data['data']]
        self.assertIn('food', categories)
        self.assertIn('transport', categories)

    def test_monthly_trends(self):
        client = auth_client(self.analyst)
        res = client.get(reverse('dashboard-trends-monthly') + '?months=3')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        # Each entry should have income, expense, net keys
        for entry in res.data['data']:
            self.assertIn('income', entry)
            self.assertIn('expense', entry)
            self.assertIn('net', entry)

    def test_recent_activity_limit(self):
        client = auth_client(self.analyst)
        res = client.get(reverse('dashboard-recent') + '?limit=2')
        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertLessEqual(len(res.data['data']), 2)

    def test_invalid_date_range_rejected(self):
        client = auth_client(self.analyst)
        res = client.get(reverse('dashboard-overview') + '?date_from=2024-06-01&date_to=2024-01-01')
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_top_categories_requires_record_type(self):
        client = auth_client(self.analyst)
        res = client.get(reverse('dashboard-top-categories'))
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_unauthenticated_request_blocked(self):
        client = APIClient()  # no auth
        res = client.get(reverse('dashboard-full'))
        self.assertEqual(res.status_code, status.HTTP_401_UNAUTHORIZED)