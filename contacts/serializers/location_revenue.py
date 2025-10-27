from rest_framework import serializers
from contacts.models import LocationRevenue

class LocationRevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocationRevenue
        fields = ('id','location','periodo','ingresos')
