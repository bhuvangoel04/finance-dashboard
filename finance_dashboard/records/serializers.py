"""
Serializers for FinancialRecord.
"""

from rest_framework import serializers
from .models import FinancialRecord, RecordType, Category


class FinancialRecordSerializer(serializers.ModelSerializer):
    """Full serializer — used for create, update, and detail reads."""
    created_by_name = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = FinancialRecord
        fields = [
            'id', 'amount', 'record_type', 'category', 'date',
            'description', 'notes',
            'created_by', 'created_by_name', 'created_at', 'updated_at',
        ]
        read_only_fields = ['id', 'created_by', 'created_by_name', 'created_at', 'updated_at']

    def get_created_by_name(self, obj):
        return obj.created_by.full_name if obj.created_by else None

    def validate_record_type(self, value):
        valid = [r.value for r in RecordType]
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid record_type. Choices: {', '.join(valid)}"
            )
        return value

    def validate_category(self, value):
        valid = [c.value for c in Category]
        if value not in valid:
            raise serializers.ValidationError(
                f"Invalid category. Choices: {', '.join(valid)}"
            )
        return value

    def validate_amount(self, value):
        if value <= 0:
            raise serializers.ValidationError("Amount must be greater than zero.")
        return value

    def create(self, validated_data):
        # created_by is injected from the view, not from user input
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class FinancialRecordListSerializer(serializers.ModelSerializer):
    """Lighter serializer for list endpoints — omits verbose fields."""

    class Meta:
        model = FinancialRecord
        fields = ['id', 'amount', 'record_type', 'category', 'date', 'description']