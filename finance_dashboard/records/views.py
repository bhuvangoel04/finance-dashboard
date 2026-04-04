"""
Financial Records views.

Access control matrix:
  Viewer   → GET list, GET detail
  Analyst  → GET list, GET detail
  Admin    → GET list, GET detail, POST, PATCH/PUT, DELETE
"""

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from users.permissions import IsActiveUser, IsAdmin, IsAdminOrReadOnly
from .filters import FinancialRecordFilter
from .models import FinancialRecord
from .serializers import FinancialRecordSerializer, FinancialRecordListSerializer


class FinancialRecordListCreateView(generics.ListCreateAPIView):
    """
    GET  /api/records/   → All authenticated active users (viewer, analyst, admin)
    POST /api/records/   → Admin only
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsAdminOrReadOnly]
    queryset = FinancialRecord.objects.select_related('created_by').all()
    filterset_class = FinancialRecordFilter
    search_fields = ['description', 'notes', 'category']
    ordering_fields = ['date', 'amount', 'created_at', 'category']
    ordering = ['-date']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return FinancialRecordSerializer
        return FinancialRecordListSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            paginated = self.get_paginated_response(serializer.data)
            return Response({"success": True, "data": paginated.data})
        serializer = self.get_serializer(queryset, many=True)
        return Response({"success": True, "data": serializer.data})

    def create(self, request, *args, **kwargs):
        serializer = FinancialRecordSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        record = serializer.save()
        return Response(
            {"success": True, "data": FinancialRecordSerializer(record).data},
            status=status.HTTP_201_CREATED,
        )


class FinancialRecordDetailView(generics.RetrieveUpdateDestroyAPIView):
    """
    GET    /api/records/<id>/   → All authenticated active users
    PATCH  /api/records/<id>/   → Admin only
    DELETE /api/records/<id>/   → Admin only
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsAdminOrReadOnly]
    queryset = FinancialRecord.objects.select_related('created_by').all()
    serializer_class = FinancialRecordSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({"success": True, "data": serializer.data})

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"success": True, "data": self.get_serializer(instance).data})

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.delete()
        return Response(
            {"success": True, "message": "Record deleted successfully."},
            status=status.HTTP_200_OK,
        )


class BulkDeleteRecordsView(APIView):
    """
    POST /api/records/bulk-delete/
    Body: { "ids": [1, 2, 3] }
    Admin only — deletes multiple records in one request.
    """
    permission_classes = [IsAuthenticated, IsActiveUser, IsAdmin]

    def post(self, request):
        ids = request.data.get('ids', [])
        if not isinstance(ids, list) or not ids:
            return Response(
                {"success": False, "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "'ids' must be a non-empty list of record IDs."
                }},
                status=status.HTTP_400_BAD_REQUEST,
            )

        records = FinancialRecord.objects.filter(id__in=ids)
        found_ids = list(records.values_list('id', flat=True))
        missing_ids = [i for i in ids if i not in found_ids]

        deleted_count, _ = records.delete()
        return Response({
            "success": True,
            "data": {
                "deleted_count": deleted_count,
                "missing_ids": missing_ids,
            }
        })