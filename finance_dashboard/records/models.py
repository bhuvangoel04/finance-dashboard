"""
FinancialRecord model — the core data entity of the system.
"""

from django.conf import settings
from django.db import models
from django.core.validators import MinValueValidator
from decimal import Decimal


class RecordType(models.TextChoices):
    INCOME  = 'income',  'Income'
    EXPENSE = 'expense', 'Expense'


class Category(models.TextChoices):
    SALARY      = 'salary',       'Salary'
    FREELANCE   = 'freelance',    'Freelance'
    INVESTMENT  = 'investment',   'Investment'
    RENT        = 'rent',         'Rent'
    UTILITIES   = 'utilities',    'Utilities'
    FOOD        = 'food',         'Food & Dining'
    TRANSPORT   = 'transport',    'Transport'
    HEALTHCARE  = 'healthcare',   'Healthcare'
    EDUCATION   = 'education',    'Education'
    INSURANCE   = 'insurance',    'Insurance'
    TAX         = 'tax',          'Tax'
    OTHER       = 'other',        'Other'


class FinancialRecord(models.Model):
    """
    A single financial transaction/entry.
    Created by admins; readable by all authenticated roles.
    """
    amount      = models.DecimalField(
                    max_digits=14, decimal_places=2,
                    validators=[MinValueValidator(Decimal('0.01'))]
                  )
    record_type = models.CharField(max_length=10, choices=RecordType.choices)
    category    = models.CharField(max_length=20, choices=Category.choices, default=Category.OTHER)
    date        = models.DateField()
    description = models.TextField(blank=True, default='')
    notes       = models.TextField(blank=True, default='')

    # Audit fields
    created_by  = models.ForeignKey(
                    settings.AUTH_USER_MODEL,
                    on_delete=models.SET_NULL,
                    null=True,
                    related_name='created_records',
                  )
    created_at  = models.DateTimeField(auto_now_add=True)
    updated_at  = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-date', '-created_at']
        indexes = [
            models.Index(fields=['date']),
            models.Index(fields=['record_type']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f'[{self.record_type.upper()}] {self.category} — {self.amount} on {self.date}'

    @property
    def signed_amount(self):
        """Returns positive for income, negative for expense — useful for balance math."""
        return self.amount if self.record_type == RecordType.INCOME else -self.amount