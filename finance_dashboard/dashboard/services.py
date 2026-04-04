"""
DashboardService — all aggregation and analytics logic.

Keeping this separate from views means:
  - Views stay thin (just HTTP handling)
  - Logic is easily testable in isolation
  - Service can be reused by multiple views or tasks
"""

from datetime import date, timedelta
from decimal import Decimal

from django.db.models import Sum, Count, Q
from django.db.models.functions import TruncMonth, TruncWeek

from records.models import FinancialRecord, RecordType, Category


class DashboardService:

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _income_q():
        return Q(record_type=RecordType.INCOME)

    @staticmethod
    def _expense_q():
        return Q(record_type=RecordType.EXPENSE)

    @staticmethod
    def _base_qs(date_from=None, date_to=None):
        qs = FinancialRecord.objects.all()
        if date_from:
            qs = qs.filter(date__gte=date_from)
        if date_to:
            qs = qs.filter(date__lte=date_to)
        return qs

    # ------------------------------------------------------------------
    # Overview summary
    # ------------------------------------------------------------------

    @classmethod
    def get_overview(cls, date_from=None, date_to=None):
        """
        Returns total income, total expenses, net balance,
        and record counts — all in one DB query.
        """
        qs = cls._base_qs(date_from, date_to)

        result = qs.aggregate(
            total_income=Sum('amount', filter=cls._income_q()),
            total_expenses=Sum('amount', filter=cls._expense_q()),
            income_count=Count('id', filter=cls._income_q()),
            expense_count=Count('id', filter=cls._expense_q()),
            total_records=Count('id'),
        )

        total_income   = result['total_income']   or Decimal('0.00')
        total_expenses = result['total_expenses'] or Decimal('0.00')

        return {
            "total_income":    total_income,
            "total_expenses":  total_expenses,
            "net_balance":     total_income - total_expenses,
            "income_count":    result['income_count'],
            "expense_count":   result['expense_count'],
            "total_records":   result['total_records'],
        }

    # ------------------------------------------------------------------
    # Category breakdown
    # ------------------------------------------------------------------

    @classmethod
    def get_category_breakdown(cls, record_type=None, date_from=None, date_to=None):
        """
        Returns per-category totals and counts.
        Optionally filtered to a single record_type (income/expense).
        """
        qs = cls._base_qs(date_from, date_to)
        if record_type:
            qs = qs.filter(record_type=record_type)

        rows = (
            qs
            .values('category', 'record_type')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')
        )

        # Attach human-readable label
        label_map = {c.value: c.label for c in Category}
        return [
            {
                "category":    row['category'],
                "label":       label_map.get(row['category'], row['category']),
                "record_type": row['record_type'],
                "total":       row['total'],
                "count":       row['count'],
            }
            for row in rows
        ]

    # ------------------------------------------------------------------
    # Monthly trends
    # ------------------------------------------------------------------

    @classmethod
    def get_monthly_trends(cls, months=12):
        """
        Returns month-by-month income vs expenses for the last N months.
        Produces data ready for a line/bar chart.
        """
        cutoff = date.today().replace(day=1) - timedelta(days=30 * (months - 1))

        rows = (
            FinancialRecord.objects
            .filter(date__gte=cutoff)
            .annotate(month=TruncMonth('date'))
            .values('month', 'record_type')
            .annotate(total=Sum('amount'))
            .order_by('month')
        )

        # Pivot into { "YYYY-MM": { income: X, expense: Y } }
        pivot = {}
        for row in rows:
            key = row['month'].strftime('%Y-%m')
            if key not in pivot:
                pivot[key] = {"month": key, "income": Decimal('0'), "expense": Decimal('0')}
            pivot[key][row['record_type']] = row['total'] or Decimal('0')

        # Add net balance per month and return as sorted list
        result = []
        for month_data in sorted(pivot.values(), key=lambda x: x['month']):
            month_data['net'] = month_data['income'] - month_data['expense']
            result.append(month_data)

        return result

    # ------------------------------------------------------------------
    # Weekly trends
    # ------------------------------------------------------------------

    @classmethod
    def get_weekly_trends(cls, weeks=8):
        """Returns week-by-week income vs expenses for the last N weeks."""
        cutoff = date.today() - timedelta(weeks=weeks)

        rows = (
            FinancialRecord.objects
            .filter(date__gte=cutoff)
            .annotate(week=TruncWeek('date'))
            .values('week', 'record_type')
            .annotate(total=Sum('amount'))
            .order_by('week')
        )

        pivot = {}
        for row in rows:
            key = row['week'].strftime('%Y-W%W')
            if key not in pivot:
                pivot[key] = {
                    "week_start": row['week'].strftime('%Y-%m-%d'),
                    "week":       key,
                    "income":     Decimal('0'),
                    "expense":    Decimal('0'),
                }
            pivot[key][row['record_type']] = row['total'] or Decimal('0')

        result = []
        for week_data in sorted(pivot.values(), key=lambda x: x['week']):
            week_data['net'] = week_data['income'] - week_data['expense']
            result.append(week_data)

        return result

    # ------------------------------------------------------------------
    # Recent activity
    # ------------------------------------------------------------------

    @classmethod
    def get_recent_activity(cls, limit=10):
        """Returns the most recent N financial records with essential fields."""
        records = (
            FinancialRecord.objects
            .select_related('created_by')
            .order_by('-date', '-created_at')[:limit]
        )
        return [
            {
                "id":          r.id,
                "amount":      r.amount,
                "record_type": r.record_type,
                "category":    r.category,
                "date":        r.date,
                "description": r.description,
                "created_by":  r.created_by.full_name if r.created_by else None,
            }
            for r in records
        ]

    # ------------------------------------------------------------------
    # Top categories
    # ------------------------------------------------------------------

    @classmethod
    def get_top_categories(cls, record_type, limit=5, date_from=None, date_to=None):
        """Returns top N categories by total amount for a given record type."""
        qs = cls._base_qs(date_from, date_to).filter(record_type=record_type)
        label_map = {c.value: c.label for c in Category}

        rows = (
            qs
            .values('category')
            .annotate(total=Sum('amount'), count=Count('id'))
            .order_by('-total')[:limit]
        )
        return [
            {
                "category": row['category'],
                "label":    label_map.get(row['category'], row['category']),
                "total":    row['total'],
                "count":    row['count'],
            }
            for row in rows
        ]