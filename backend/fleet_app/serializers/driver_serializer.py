from rest_framework import serializers

from .common import camel_to_snake


class DriverComplianceSerializer(serializers.Serializer):
    """司机班次合规配置：每日驾驶上限 / 任务间最短休息 / 夜间连续休息（单位：分钟）。"""

    daily_driving_limit_minutes = serializers.IntegerField(required=False, min_value=0)
    min_rest_minutes = serializers.IntegerField(required=False, min_value=0)
    nightly_rest_minutes = serializers.IntegerField(required=False, min_value=0)

    def to_internal_value(self, data):
        normalized = {camel_to_snake(key): value for key, value in data.items()}
        return super().to_internal_value(normalized)
