from rest_framework import serializers
from .models import Inventory
        
class InventorySerializer(serializers.ModelSerializer):
    item_type = serializers.CharField(allow_blank=False)
    color_or_type = serializers.CharField(source='color', allow_blank=True, required=False)
    color = serializers.CharField(allow_blank=True, required=False)
    entity = serializers.CharField(allow_blank=True, required=False)
    size = serializers.CharField(allow_blank=True, required=False)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    def validate_quantity(self, value):
        if value is None:
            return 0
        try:
            iv = int(value)
        except (TypeError, ValueError):
            raise serializers.ValidationError('Quantity must be an integer')
        if iv < 0:
            raise serializers.ValidationError('Quantity must be non-negative')
        return iv

    class Meta:
        model = Inventory
        fields = ['id', 'item_type', 'color_or_type', 'color', 'size', 'quantity', 'entity', 'created_at', 'updated_at']

        
