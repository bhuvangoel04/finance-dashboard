"""
Management command: seed_data
Creates sample users and financial records for development/demo purposes.

Usage:
    python manage.py seed_data
    python manage.py seed_data --records 100
"""

import random
from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand
from django.db import transaction

from users.models import User, Role
from records.models import FinancialRecord, RecordType, Category


INCOME_CATEGORIES  = [Category.SALARY, Category.FREELANCE, Category.INVESTMENT]
EXPENSE_CATEGORIES = [
    Category.RENT, Category.UTILITIES, Category.FOOD, Category.TRANSPORT,
    Category.HEALTHCARE, Category.EDUCATION, Category.INSURANCE, Category.TAX, Category.OTHER,
]


class Command(BaseCommand):
    help = 'Seed the database with sample users and financial records.'

    def add_arguments(self, parser):
        parser.add_argument('--records', type=int, default=50,
                            help='Number of financial records to generate (default: 50)')

    @transaction.atomic
    def handle(self, *args, **options):
        num_records = options['records']
        self.stdout.write('🌱 Seeding database...\n')

        # ── Users ──────────────────────────────────────────────
        users = {}
        user_configs = [
            ('admin@example.com',   'Admin',   'User',   Role.ADMIN),
            ('analyst@example.com', 'Analyst', 'User',   Role.ANALYST),
            ('viewer@example.com',  'Viewer',  'User',   Role.VIEWER),
        ]

        for email, first, last, role in user_configs:
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'first_name': first,
                    'last_name':  last,
                    'role':       role,
                    'is_active':  True,
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'  ✔ Created {role} user: {email}')
            else:
                self.stdout.write(f'  – Existing user: {email}')
            users[role] = user

        admin_user = users[Role.ADMIN]

        # ── Financial Records ──────────────────────────────────
        today = date.today()
        created_count = 0

        for i in range(num_records):
            record_type = random.choice([RecordType.INCOME, RecordType.EXPENSE])
            categories  = INCOME_CATEGORIES if record_type == RecordType.INCOME else EXPENSE_CATEGORIES
            category    = random.choice(categories)

            if record_type == RecordType.INCOME:
                amount = Decimal(str(round(random.uniform(500, 8000), 2)))
            else:
                amount = Decimal(str(round(random.uniform(20, 2000), 2)))

            record_date = today - timedelta(days=random.randint(0, 365))

            FinancialRecord.objects.create(
                amount=amount,
                record_type=record_type,
                category=category,
                date=record_date,
                description=f'Sample {record_type} — {category}',
                notes=f'Auto-generated record #{i + 1}',
                created_by=admin_user,
            )
            created_count += 1

        self.stdout.write(f'  ✔ Created {created_count} financial records\n')
        self.stdout.write(self.style.SUCCESS('✅ Seeding complete!\n'))
        self.stdout.write('Default credentials:')
        self.stdout.write('  admin@example.com   / password123  (Admin)')
        self.stdout.write('  analyst@example.com / password123  (Analyst)')
        self.stdout.write('  viewer@example.com  / password123  (Viewer)')