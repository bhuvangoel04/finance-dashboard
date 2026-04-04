"""
Dashboard views — all analyst + admin accessible.

Access control:
  Viewer   → blocked (dashboard is insight-level, not just raw data)
  Analyst  → full access to all dashboard endpoints
  Admin    → full access to all dashboard endpoints
"""

from datetime import date, timedelta

from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsActiveUser, IsAnalystOrAbove
from .services import DashboardService


class _BaseDashboardView(APIView):
    permission_classes = [IsAuthenticated, IsActiveUser, IsAnalystOrAbove]

    def _parse_date_params(self, request):
        """Extract and validate optional date_from / date_to query params."""
        date_from = request.query_params.get('date_from')
        date_to   = request.query_params.get('date_to')
        errors = {}

        if date_from:
            try:
                date_from = date.fromisoformat(date_from)
            except ValueError:
                errors['date_from'] = 'Invalid date format. Use YYYY-MM-DD.'

        if date_to:
            try:
                date_to = date.fromisoformat(date_to)
            except ValueError:
                errors['date_to'] = 'Invalid date format. Use YYYY-MM-DD.'

        if errors:
            return None, None, errors

        if date_from and date_to and date_from > date_to:
            return None, None, {'date_range': 'date_from must be before date_to.'}

        return date_from, date_to, None


class OverviewView(_BaseDashboardView):
    """
    GET /api/dashboard/overview/
    Query params: ?date_from=YYYY-MM-DD&date_to=YYYY-MM-DD

    Returns high-level financial summary:
    total income, total expenses, net balance, record counts.
    """
    def get(self, request):
        date_from, date_to, errors = self._parse_date_params(request)
        if errors:
            return Response(
                {"success": False, "error": {"code": "VALIDATION_ERROR", "details": errors}},
                status=400,
            )

        data = DashboardService.get_overview(date_from=date_from, date_to=date_to)
        return Response({"success": True, "data": data})


class CategoryBreakdownView(_BaseDashboardView):
    """
    GET /api/dashboard/categories/
    Query params: ?record_type=income|expense&date_from=...&date_to=...

    Returns per-category totals and transaction counts.
    """
    def get(self, request):
        date_from, date_to, errors = self._parse_date_params(request)
        if errors:
            return Response(
                {"success": False, "error": {"code": "VALIDATION_ERROR", "details": errors}},
                status=400,
            )

        record_type = request.query_params.get('record_type')
        if record_type and record_type not in ('income', 'expense'):
            return Response(
                {"success": False, "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "record_type must be 'income' or 'expense'."
                }},
                status=400,
            )

        data = DashboardService.get_category_breakdown(
            record_type=record_type,
            date_from=date_from,
            date_to=date_to,
        )
        return Response({"success": True, "data": data})


class MonthlyTrendsView(_BaseDashboardView):
    """
    GET /api/dashboard/trends/monthly/
    Query params: ?months=12  (default 12, max 36)

    Returns month-by-month income, expense, and net balance.
    Ideal for line/bar charts on the frontend.
    """
    def get(self, request):
        try:
            months = int(request.query_params.get('months', 12))
        except ValueError:
            return Response(
                {"success": False, "error": {"code": "VALIDATION_ERROR", "message": "'months' must be an integer."}},
                status=400,
            )
        months = max(1, min(months, 36))  # clamp between 1 and 36

        data = DashboardService.get_monthly_trends(months=months)
        return Response({"success": True, "data": data})


class WeeklyTrendsView(_BaseDashboardView):
    """
    GET /api/dashboard/trends/weekly/
    Query params: ?weeks=8  (default 8, max 52)
    """
    def get(self, request):
        try:
            weeks = int(request.query_params.get('weeks', 8))
        except ValueError:
            return Response(
                {"success": False, "error": {"code": "VALIDATION_ERROR", "message": "'weeks' must be an integer."}},
                status=400,
            )
        weeks = max(1, min(weeks, 52))

        data = DashboardService.get_weekly_trends(weeks=weeks)
        return Response({"success": True, "data": data})


class RecentActivityView(_BaseDashboardView):
    """
    GET /api/dashboard/recent/
    Query params: ?limit=10  (default 10, max 50)

    Returns the most recent N financial records.
    """
    def get(self, request):
        try:
            limit = int(request.query_params.get('limit', 10))
        except ValueError:
            return Response(
                {"success": False, "error": {"code": "VALIDATION_ERROR", "message": "'limit' must be an integer."}},
                status=400,
            )
        limit = max(1, min(limit, 50))

        data = DashboardService.get_recent_activity(limit=limit)
        return Response({"success": True, "data": data})


class TopCategoriesView(_BaseDashboardView):
    """
    GET /api/dashboard/top-categories/
    Query params: ?record_type=expense&limit=5&date_from=...&date_to=...

    Returns top spending or earning categories.
    record_type is required.
    """
    def get(self, request):
        record_type = request.query_params.get('record_type')
        if record_type not in ('income', 'expense'):
            return Response(
                {"success": False, "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "record_type query param is required and must be 'income' or 'expense'."
                }},
                status=400,
            )

        date_from, date_to, errors = self._parse_date_params(request)
        if errors:
            return Response(
                {"success": False, "error": {"code": "VALIDATION_ERROR", "details": errors}},
                status=400,
            )

        try:
            limit = int(request.query_params.get('limit', 5))
        except ValueError:
            limit = 5
        limit = max(1, min(limit, 20))

        data = DashboardService.get_top_categories(
            record_type=record_type,
            limit=limit,
            date_from=date_from,
            date_to=date_to,
        )
        return Response({"success": True, "data": data})


class FullDashboardView(_BaseDashboardView):
    """
    GET /api/dashboard/
    Returns everything in one request — useful for the initial dashboard page load.
    Combines overview + recent activity + monthly trends (last 6 months) + top categories.
    """
    def get(self, request):
        data = {
            "overview":         DashboardService.get_overview(),
            "recent_activity":  DashboardService.get_recent_activity(limit=5),
            "monthly_trends":   DashboardService.get_monthly_trends(months=6),
            "top_expenses":     DashboardService.get_top_categories('expense', limit=5),
            "top_income":       DashboardService.get_top_categories('income', limit=5),
        }
        return Response({"success": True, "data": data})