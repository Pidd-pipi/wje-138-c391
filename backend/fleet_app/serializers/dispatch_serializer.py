from rest_framework import serializers

from .common import camel_to_snake


class DispatchOrderCreateSerializer(serializers.Serializer):
    """建单入参校验，兼容前端 camelCase 与后端 snake_case。"""

    vehicle_id = serializers.IntegerField(required=False, allow_null=True)
    driver_id = serializers.IntegerField(required=False, allow_null=True)
    origin = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    destination = serializers.CharField(max_length=120, required=False, allow_blank=True, default='')
    plan_depart_at = serializers.DateTimeField(required=False, allow_null=True)
    plan_arrive_at = serializers.DateTimeField(required=False, allow_null=True)
    cargo = serializers.CharField(max_length=160, required=False, allow_blank=True, default='')
    weight = serializers.FloatField(required=False, min_value=0, default=0)
    freight = serializers.FloatField(required=False, min_value=0, default=0)
    note = serializers.CharField(required=False, allow_blank=True, default='')

    def to_internal_value(self, data):
        normalized = {camel_to_snake(key): value for key, value in data.items()}
        return super().to_internal_value(normalized)
