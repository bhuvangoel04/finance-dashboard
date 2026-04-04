"""
Django-filter FilterSet for FinancialRecord — supports powerful query-string filtering.
"""

import django_filters
from .models import FinancialRecord, RecordType, Category


class FinancialRecordFilter(django_filters.FilterSet):
    # Exact matches
    record_type = django_filters.ChoiceFilter(choices=RecordType.choices)
    category    = django_filters.ChoiceFilter(choices=Category.choices)

    # Date range filtering: ?date_from=2024-01-01&date_to=2024-03-31
    date_from   = django_filters.DateFilter(field_name='date', lookup_expr='gte')
    date_to     = django_filters.DateFilter(field_name='date', lookup_expr='lte')

    # Convenience: filter by year-month like ?month=2024-06
    month       = django_filters.CharFilter(method='filter_by_month')

    # Amount range: ?min_amount=100&max_amount=5000
    min_amount  = django_filters.NumberFilter(field_name='amount', lookup_expr='gte')
    max_amount  = django_filters.NumberFilter(field_name='amount', lookup_expr='lte')

    class Meta:
        model  = FinancialRecord
        fields = ['record_type', 'category', 'date_from', 'date_to', 'month', 'min_amount', 'max_amount']

    def filter_by_month(self, queryset, name, value):
        """Accepts YYYY-MM format and filters accordingly."""
        try:
            year, month = value.split('-')
            return queryset.filter(date__year=int(year), date__month=int(month))
        except (ValueError, AttributeError):
            return queryset.none()