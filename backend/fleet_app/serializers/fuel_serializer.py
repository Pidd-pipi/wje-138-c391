from rest_framework import serializers
from fleet_app import models

class FuelSerializer(serializers.Serializer):
    id = serializers.IntegerField(required=False)
