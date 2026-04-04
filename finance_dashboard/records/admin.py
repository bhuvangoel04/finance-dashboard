from django.contrib import admin
from .models import FinancialRecord


@admin.register(FinancialRecord)
class FinancialRecordAdmin(admin.ModelAdmin):
    list_display = ('id', 'record_type', 'category', 'amount', 'date', 'created_by', 'created_at')
    list_filter = ('record_type', 'category', 'date')
    search_fields = ('description', 'notes')
    ordering = ('-date',)
    readonly_fields = ('created_at', 'updated_at', 'created_by')

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        super().save_model(request, obj, form, change)