from rest_framework import serializers
from contacts.models import SupplierCertification

class SupplierCertificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupplierCertification
        fields = ('id','tipo','codigo','fecha_emision','fecha_caducidad','adjunto')
