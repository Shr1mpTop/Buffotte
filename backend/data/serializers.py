from rest_framework import serializers
from .models import Item, KlineData

class ItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = Item
        fields = '__all__'

class KlineDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = KlineData
        fields = '__all__'